from .base import BaseParser


def extract_error_message(log: dict) -> str:
    msg = log.get("error", {}).get("message")
    if msg:
        return str(msg)

    validation = log.get("validation", {}).get("errors")
    if validation:
        return str(validation)

    extra_errors = log.get("extra", {}).get("errors")

    if isinstance(extra_errors, list) and extra_errors:
        return extra_errors[0].get("msg", "validation error")

    if isinstance(extra_errors, dict):
        return extra_errors.get("msg", "validation error")

    reason = log.get("extra", {}).get("reason")
    if reason:
        return str(reason)

    extra_error = log.get("extra", {}).get("error")
    if extra_error:
        return str(extra_error)

    return "unknown error"


def detect_error_type(log: dict) -> str:
    if log.get("extra", {}).get("errors"):
        return "VALIDATION"
    if log.get("extra", {}).get("reason"):
        return "BUSINESS"
    if log.get("extra", {}).get("error"):
        return "SYSTEM"
    if log.get("error", {}).get("message"):
        return "SYSTEM"
    return "UNKNOWN"


def extract_trace_id(log: dict) -> str | None:
    # Support common trace_id locations from Kibana/Elastic logs.
    candidates = [
        log.get("trace_id"),
        log.get("trace", {}).get("id"),
        log.get("event", {}).get("trace_id"),
        log.get("event", {}).get("traceId"),
        log.get("kibana", {}).get("trace_id"),
        log.get("extra", {}).get("trace_id"),
    ]

    for value in candidates:
        if isinstance(value, str) and value.strip():
            return value.strip()

    return None


class BankingAPIParser(BaseParser):
    @property
    def system_name(self) -> str:
        return "banking-api"

    def can_parse(self, log: dict) -> bool:
        api = log.get("event", {}).get("api", "")
        return isinstance(api, str) and api.startswith("/api")

    def parse(self, log: dict) -> dict:
        return {
            "event_id": log.get("__event_id"),
            "system": self.system_name,
            "service": "transfer",
            "api": log.get("event", {}).get("api"),
            "trace_id": extract_trace_id(log),
            "error_code": log.get("extra", {}).get("code"),
            "error_type": detect_error_type(log),
            "message": extract_error_message(log),
            "severity": "HIGH"
            if log.get("event", {}).get("status") == "FAILED"
            else "LOW",
            "raw_log": log,
        }
