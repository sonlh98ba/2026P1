from typing import Any, Generator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.automation import AutomationError, execute_auto_fix_script
from app.core.extractor import fetch_log_by_trace_id
from app.core.fingerprint import generate_fingerprint
from app.core.normalizer import normalize
from app.core.system_router import parse_log
from app.database import SessionLocal
from app.models import ErrorKnowledgeBase, Incident

router = APIRouter()
ERROR_TYPES = ("SYSTEM", "BUSINESS", "VALIDATION", "UNKNOWN")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _build_solution_item(row: ErrorKnowledgeBase) -> dict[str, Any]:
    has_solution = bool(row.solution and row.solution.strip())
    return {
        "id": str(row.id),
        "fingerprint": row.fingerprint,
        "message": row.raw_message or row.normalized_message,
        "raw_message": row.raw_message,
        "normalized_message": row.normalized_message,
        "type": row.error_type,
        "service": row.service,
        "api": row.api,
        "label": row.label,
        "severity": row.severity,
        "count": row.occurrence,
        "confidence": row.confidence_score,
        "solution": row.solution,
        "auto_fix_script": row.auto_fix_script,
        "first_seen": row.first_seen.isoformat() if row.first_seen else None,
        "last_seen": row.last_seen.isoformat() if row.last_seen else None,
        "status": "resolved" if has_solution else "unresolve",
    }


def _find_solution_by_trace_id(db: Session, trace_id: str) -> list[dict[str, Any]]:
    log = fetch_log_by_trace_id(trace_id)
    if not log:
        return []

    normalized_error = parse_log(log)
    if not normalized_error:
        return []

    msg = normalized_error.get("message", "")
    api = normalized_error.get("api") or "unknown"
    normalized_message = normalize(msg)

    service_candidates: list[str] = []
    for candidate in [
        normalized_error.get("service"),
        normalized_error.get("system"),
        "unknown",
    ]:
        if isinstance(candidate, str) and candidate and candidate not in service_candidates:
            service_candidates.append(candidate)

    row = None
    for service in service_candidates:
        fingerprint = generate_fingerprint(service, api, normalized_message)
        row = (
            db.query(ErrorKnowledgeBase)
            .filter(ErrorKnowledgeBase.fingerprint == fingerprint)
            .first()
        )
        if row:
            break

    if not row:
        # Backward-compatible fallback for old fingerprints/service naming.
        row = (
            db.query(ErrorKnowledgeBase)
            .filter(
                ErrorKnowledgeBase.normalized_message == normalized_message,
                ErrorKnowledgeBase.api == api,
            )
            .order_by(ErrorKnowledgeBase.occurrence.desc())
            .first()
        )

    if not row:
        return []

    return [_build_solution_item(row)]


def _split_filter_values(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def _normalize_filter_statuses(value: str | None) -> set[str]:
    normalized: set[str] = set()
    for raw in _split_filter_values(value):
        token = raw.lower()
        if token in {"resolved", "close", "closed"}:
            normalized.add("resolved")
        elif token in {"unresolve", "unresolved", "open"}:
            normalized.add("unresolved")
    return normalized


@router.get("/overview")
def dashboard_overview(db: Session = Depends(get_db)) -> dict[str, Any]:
    total = db.query(ErrorKnowledgeBase).count()

    by_type: dict[str, int] = {}
    for error_type in ERROR_TYPES:
        by_type[error_type] = (
            db.query(ErrorKnowledgeBase)
            .filter(ErrorKnowledgeBase.error_type == error_type)
            .count()
        )

    top_errors = (
        db.query(ErrorKnowledgeBase)
        .order_by(ErrorKnowledgeBase.occurrence.desc())
        .limit(5)
        .all()
    )

    return {
        "total_errors": total,
        "by_type": by_type,
        "top_errors": [
            {
                "message": e.raw_message,
                "count": e.occurrence,
                "type": e.error_type,
                "confidence": e.confidence_score,
            }
            for e in top_errors
        ],
    }


@router.get("/trends")
def error_trends(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = (
        db.query(
            func.date_trunc("hour", ErrorKnowledgeBase.first_seen).label("hour"),
            func.count().label("count"),
        )
        .group_by("hour")
        .order_by("hour")
        .all()
    )

    return [{"time": str(r.hour), "count": int(r.count)} for r in rows]


@router.get("/unknown")
def unknown_errors(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = (
        db.query(ErrorKnowledgeBase)
        .filter(ErrorKnowledgeBase.error_type == "UNKNOWN")
        .order_by(ErrorKnowledgeBase.occurrence.desc())
        .limit(20)
        .all()
    )

    return [
        {
            "message": r.normalized_message,
            "count": r.occurrence,
            "confidence": r.confidence_score,
        }
        for r in rows
    ]


@router.get("/incidents")
def list_incidents(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = (
        db.query(Incident)
        .order_by(Incident.last_seen.desc())
        .limit(100)
        .all()
    )

    return [
        {
            "id": str(i.id),
            "message": i.message,
            "error_type": i.error_type,
            "severity": i.severity,
            "service": i.service,
            "api": i.api,
            "status": i.status,
            "assigned": i.assigned_to,
            "count": i.count,
            "created_at": i.first_seen,
            "first_seen": i.first_seen,
            "last_seen": i.last_seen,
        }
        for i in rows
    ]


@router.get("/top-services")
def top_services(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = (
        db.query(
            ErrorKnowledgeBase.service,
            func.sum(ErrorKnowledgeBase.occurrence).label("count"),
        )
        .group_by(ErrorKnowledgeBase.service)
        .order_by(func.sum(ErrorKnowledgeBase.occurrence).desc())
        .all()
    )

    return [{"service": r.service, "count": int(r.count or 0)} for r in rows]


@router.get("/solutions")
def list_solutions(
    db: Session = Depends(get_db),
    trace_id: str | None = Query(default=None),
    error_type: str | None = Query(default=None, alias="type"),
    status: str | None = Query(default=None),
    service: str | None = Query(default=None),
    api: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    label: str | None = Query(default=None),
    q: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    trace_id = trace_id.strip() if isinstance(trace_id, str) else None
    q = q.strip() if isinstance(q, str) and q.strip() else None

    filter_types = {value.upper() for value in _split_filter_values(error_type)}
    filter_services = {value.lower() for value in _split_filter_values(service)}
    filter_apis = {value.lower() for value in _split_filter_values(api)}
    filter_severities = {value.upper() for value in _split_filter_values(severity)}
    filter_labels = {value.lower() for value in _split_filter_values(label)}
    filter_statuses = _normalize_filter_statuses(status)

    if trace_id:
        rows = _find_solution_by_trace_id(db, trace_id)
        filtered: list[dict[str, Any]] = []
        for row in rows:
            row_type = str(row.get("type") or "").upper()
            row_service = str(row.get("service") or "").lower()
            row_api = str(row.get("api") or "").lower()
            row_severity = str(row.get("severity") or "").upper()
            row_label = str(row.get("label") or "").lower()
            row_status = str(row.get("status") or "").lower()
            row_message = str(row.get("message") or "")

            if filter_types and row_type not in filter_types:
                continue
            if filter_services and row_service not in filter_services:
                continue
            if filter_apis and row_api not in filter_apis:
                continue
            if filter_severities and row_severity not in filter_severities:
                continue
            if filter_labels and row_label not in filter_labels:
                continue
            if filter_statuses and row_status not in filter_statuses:
                continue
            if q and q.lower() not in row_message.lower():
                continue
            filtered.append(row)

        return filtered

    has_solution = func.length(func.trim(func.coalesce(ErrorKnowledgeBase.solution, ""))) > 0
    no_solution = func.length(func.trim(func.coalesce(ErrorKnowledgeBase.solution, ""))) == 0

    query = db.query(ErrorKnowledgeBase)

    if filter_types:
        query = query.filter(func.upper(func.coalesce(ErrorKnowledgeBase.error_type, "")).in_(filter_types))
    if filter_services:
        query = query.filter(func.lower(func.coalesce(ErrorKnowledgeBase.service, "")).in_(filter_services))
    if filter_apis:
        query = query.filter(func.lower(func.coalesce(ErrorKnowledgeBase.api, "")).in_(filter_apis))
    if filter_severities:
        query = query.filter(func.upper(func.coalesce(ErrorKnowledgeBase.severity, "")).in_(filter_severities))
    if filter_labels:
        query = query.filter(func.lower(func.coalesce(ErrorKnowledgeBase.label, "")).in_(filter_labels))
    if filter_statuses == {"resolved"}:
        query = query.filter(has_solution)
    elif filter_statuses == {"unresolved"}:
        query = query.filter(no_solution)
    if q:
        keyword = f"%{q}%"
        query = query.filter(
            or_(
                ErrorKnowledgeBase.raw_message.ilike(keyword),
                ErrorKnowledgeBase.normalized_message.ilike(keyword),
            )
        )

    rows = (
        query
        .order_by(ErrorKnowledgeBase.occurrence.desc())
        .limit(200)
        .all()
    )

    return [_build_solution_item(row) for row in rows]


@router.put("/solutions/{error_id}")
def update_solution(
    error_id: str, payload: dict[str, Any], db: Session = Depends(get_db)
) -> dict[str, Any]:
    try:
        error_uuid = UUID(error_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid error id") from exc

    row = db.query(ErrorKnowledgeBase).filter(ErrorKnowledgeBase.id == error_uuid).first()
    if not row:
        raise HTTPException(status_code=404, detail="Error not found")

    if "solution" in payload:
        solution = payload.get("solution")
        row.solution = solution.strip() if isinstance(solution, str) and solution.strip() else None

    if "auto_fix_script" in payload:
        script = payload.get("auto_fix_script")
        row.auto_fix_script = script.strip() if isinstance(script, str) and script.strip() else None

    db.commit()
    db.refresh(row)

    has_solution = bool(row.solution and row.solution.strip())
    return {
        "id": str(row.id),
        "solution": row.solution,
        "auto_fix_script": row.auto_fix_script,
        "status": "resolved" if has_solution else "unresolve",
    }


@router.post("/solutions/{error_id}/execute")
def execute_solution_script(error_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        error_uuid = UUID(error_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid error id") from exc

    row = db.query(ErrorKnowledgeBase).filter(ErrorKnowledgeBase.id == error_uuid).first()
    if not row:
        raise HTTPException(status_code=404, detail="Error not found")

    script = (row.auto_fix_script or "").strip()
    if not script:
        raise HTTPException(status_code=400, detail="auto_fix_script is empty")

    context = {
        "error_id": str(row.id),
        "fingerprint": row.fingerprint or "",
        "service": row.service or "",
        "api": row.api or "",
        "error_type": row.error_type or "",
        "severity": row.severity or "",
        "label": row.label or "",
        "message": row.raw_message or row.normalized_message or "",
    }

    try:
        execution = execute_auto_fix_script(script, context)
    except AutomationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Execution failed: {exc}") from exc

    return {
        "id": str(row.id),
        "execution": execution,
    }
