import json
import os
import smtplib
from email.message import EmailMessage
from string import Formatter
from typing import Any
from urllib import error as url_error
from urllib import request as url_request

from sqlalchemy import create_engine, text

from app.database import DATABASE_URL


class AutomationError(Exception):
    pass


class AutomationStepFailed(AutomationError):
    def __init__(self, step_index: int, reason: str):
        super().__init__(f"Thuc thi khong thanh cong tai buoc {step_index}: {reason}")
        self.step_index = step_index
        self.reason = reason


_DB_ENGINES: dict[str, Any] = {}


def _load_db_targets() -> dict[str, str]:
    targets = {"default": DATABASE_URL}
    raw = os.getenv("AUTOMATION_DB_TARGETS_JSON", "").strip()
    if not raw:
        return targets
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            for key, value in parsed.items():
                if isinstance(key, str) and isinstance(value, str) and value.strip():
                    targets[key.strip()] = value.strip()
    except Exception:
        return targets
    return targets


def _get_db_engine(target: str):
    target_name = target.strip() or "default"
    targets = _load_db_targets()
    db_url = targets.get(target_name)
    if not db_url:
        supported = ", ".join(sorted(targets.keys()))
        raise AutomationError(
            f"Unknown database target '{target_name}'. Supported: {supported}"
        )
    if db_url not in _DB_ENGINES:
        _DB_ENGINES[db_url] = create_engine(db_url, pool_pre_ping=True)
    return target_name, _DB_ENGINES[db_url]


def _collect_template_fields(value: str) -> set[str]:
    fields: set[str] = set()
    for _, field_name, _, _ in Formatter().parse(value):
        if field_name:
            fields.add(field_name)
    return fields


def _render_templates(value: Any, context: dict[str, Any]) -> Any:
    if isinstance(value, str):
        required_fields = _collect_template_fields(value)
        missing = [name for name in required_fields if name not in context]
        if missing:
            raise AutomationError(f"Missing template fields: {', '.join(missing)}")
        return value.format_map(context)
    if isinstance(value, dict):
        return {k: _render_templates(v, context) for k, v in value.items()}
    if isinstance(value, list):
        return [_render_templates(item, context) for item in value]
    return value


def _execute_call_api(step: dict[str, Any], timeout_seconds: int) -> dict[str, Any]:
    method = str(step.get("method") or "POST").upper()
    url = step.get("url")
    if not isinstance(url, str) or not url.strip():
        raise AutomationError("call_api requires a non-empty 'url'")

    headers = step.get("headers")
    if headers is None:
        headers = {}
    if not isinstance(headers, dict):
        raise AutomationError("call_api 'headers' must be an object")

    body = step.get("body")
    encoded_body = None
    if body is not None:
        encoded_body = json.dumps(body).encode("utf-8")
        headers = {**headers, "Content-Type": "application/json"}

    req = url_request.Request(
        url=url.strip(),
        data=encoded_body,
        headers={str(k): str(v) for k, v in headers.items()},
        method=method,
    )

    try:
        with url_request.urlopen(req, timeout=timeout_seconds) as response:
            raw_full = response.read().decode("utf-8", errors="replace")
            parsed_json = None
            try:
                parsed_json = json.loads(raw_full)
            except Exception:
                parsed_json = None
            return {
                "ok": True,
                "status_code": int(response.getcode() or 200),
                "response_preview": raw_full[:1024],
                "response_json": parsed_json,
            }
    except url_error.HTTPError as exc:
        raw = exc.read(1024).decode("utf-8", errors="replace")
        return {
            "ok": False,
            "status_code": int(exc.code),
            "error": f"HTTPError: {exc.reason}",
            "response_preview": raw,
        }
    except Exception as exc:
        return {
            "ok": False,
            "status_code": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _execute_send_email(step: dict[str, Any], timeout_seconds: int) -> dict[str, Any]:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM")
    smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"}

    if not smtp_host:
        raise AutomationError("Missing SMTP_HOST env for send_email action")
    if not smtp_from:
        raise AutomationError("Missing SMTP_FROM env for send_email action")

    to = step.get("to")
    if isinstance(to, str):
        recipients = [to]
    elif isinstance(to, list):
        recipients = [str(item).strip() for item in to if str(item).strip()]
    else:
        recipients = []
    if not recipients:
        raise AutomationError("send_email requires 'to' (string or list)")

    subject = str(step.get("subject") or "AIOps Auto Fix Notification")
    body = str(step.get("body") or "")

    message = EmailMessage()
    message["From"] = smtp_from
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port, timeout=timeout_seconds) as smtp:
        if smtp_use_tls:
            smtp.starttls()
        if smtp_username:
            smtp.login(smtp_username, smtp_password or "")
        smtp.send_message(message)

    return {
        "ok": True,
        "sent_to": recipients,
        "subject": subject,
    }


def _execute_db_query(step: dict[str, Any], timeout_seconds: int) -> dict[str, Any]:
    _ = timeout_seconds
    target = str(step.get("database") or "default")
    sql = step.get("sql")
    if not isinstance(sql, str) or not sql.strip():
        raise AutomationError("db_query requires non-empty 'sql'")

    params = step.get("params")
    if params is None:
        params = {}
    if not isinstance(params, dict):
        raise AutomationError("db_query 'params' must be an object")

    max_rows = int(step.get("max_rows") or 50)
    target_name, engine = _get_db_engine(target)
    sql_text = sql.strip()
    lower_sql = sql_text.lower()
    is_read_query = lower_sql.startswith("select") or lower_sql.startswith("with") or lower_sql.startswith("show")

    with engine.begin() as connection:
        result = connection.execute(text(sql_text), params)
        if is_read_query:
            rows = [dict(row._mapping) for row in result.fetchmany(max_rows)]
            return {
                "ok": True,
                "database": target_name,
                "row_count": len(rows),
                "rows": rows,
            }
        return {
            "ok": True,
            "database": target_name,
            "affected_rows": int(result.rowcount or 0),
        }


def _get_value_by_path(payload: Any, path: str) -> Any:
    current = payload
    for token in path.split("."):
        key = token.strip()
        if not key:
            continue
        if isinstance(current, list):
            if not key.isdigit():
                raise AutomationError(f"Invalid list index '{key}' in expect path '{path}'")
            idx = int(key)
            if idx < 0 or idx >= len(current):
                raise AutomationError(f"List index '{idx}' out of range in expect path '{path}'")
            current = current[idx]
            continue
        if not isinstance(current, dict):
            raise AutomationError(f"Cannot read path '{path}' from non-object value")
        if key not in current:
            raise AutomationError(f"Field '{key}' not found in expect path '{path}'")
        current = current[key]
    return current


def _validate_expectation(step: dict[str, Any], action_result: dict[str, Any]) -> tuple[bool, str]:
    expects_raw = step.get("expects")
    single_expect = step.get("expect")

    if expects_raw is not None and single_expect is not None:
        raise AutomationError("Use either 'expect' or 'expects', not both")

    if expects_raw is None:
        if single_expect is None:
            return True, ""
        expects = [single_expect]
    else:
        if not isinstance(expects_raw, list):
            raise AutomationError("'expects' must be an array")
        expects = expects_raw

    if not expects:
        return True, ""

    source = action_result.get("response_json")
    if source is None:
        return False, "response is not JSON, cannot evaluate expect(s)"

    for idx, expect in enumerate(expects, start=1):
        if not isinstance(expect, dict):
            raise AutomationError(f"expect at position {idx} must be an object")

        path = str(expect.get("path") or "").strip()
        if not path:
            raise AutomationError(f"expect[{idx}].path is required")

        actual = _get_value_by_path(source, path)
        if "equals" in expect:
            expected = expect.get("equals")
            if actual != expected:
                return False, f"expect[{idx}] '{path}' == {expected!r} but got {actual!r}"
        elif "not_equals" in expect:
            expected = expect.get("not_equals")
            if actual == expected:
                return False, f"expect[{idx}] '{path}' != {expected!r} but got {actual!r}"
        else:
            raise AutomationError(f"expect[{idx}] must include 'equals' or 'not_equals'")

    return True, ""


def execute_auto_fix_script(script: str, context: dict[str, Any]) -> dict[str, Any]:
    try:
        parsed = json.loads(script)
    except json.JSONDecodeError as exc:
        raise AutomationError(f"Invalid JSON script: {exc}") from exc

    actions = parsed.get("actions") if isinstance(parsed, dict) else None
    if not isinstance(actions, list) or not actions:
        raise AutomationError("Script must be a JSON object with non-empty 'actions' array")

    timeout_seconds = int(parsed.get("timeout_seconds") or 10)
    stop_on_error = bool(parsed.get("stop_on_error", True))
    results: list[dict[str, Any]] = []

    for idx, step in enumerate(actions, start=1):
        if not isinstance(step, dict):
            raise AutomationError(f"Action at index {idx} must be an object")

        rendered_step = _render_templates(step, context)
        action_type = str(rendered_step.get("action") or "").strip().lower()
        if not action_type:
            raise AutomationError(f"Action at index {idx} missing 'action' field")

        if action_type == "call_api":
            action_result = _execute_call_api(rendered_step, timeout_seconds)
            expect_ok, expect_reason = _validate_expectation(rendered_step, action_result)
            if not expect_ok:
                action_result["ok"] = False
                action_result["expect_failed"] = True
                action_result["error"] = expect_reason
        elif action_type == "send_email":
            action_result = _execute_send_email(rendered_step, timeout_seconds)
        elif action_type in {"db_query", "database"}:
            action_result = _execute_db_query(rendered_step, timeout_seconds)
        else:
            raise AutomationError(f"Unsupported action '{action_type}' at index {idx}")

        results.append(
            {
                "index": idx,
                "action": action_type,
                **action_result,
            }
        )

        if not action_result.get("ok") and stop_on_error:
            reason = str(action_result.get("error") or "step execution failed")
            raise AutomationStepFailed(idx, reason)

    success_count = sum(1 for result in results if result.get("ok"))
    return {
        "ok": success_count == len(results),
        "total_actions": len(results),
        "success_actions": success_count,
        "failed_actions": len(results) - success_count,
        "results": results,
    }
