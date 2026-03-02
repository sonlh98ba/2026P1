from datetime import datetime

from sqlalchemy.orm import Session

from app.models import ErrorKnowledgeBase, ErrorTraceMap

from .fingerprint import generate_fingerprint
from .normalizer import normalize


def compute_confidence(log: dict) -> float:
    etype = log.get("error_type")

    if etype == "BUSINESS":
        return 1.0
    if etype == "SYSTEM":
        return 0.9
    if etype == "VALIDATION":
        return 0.8
    if etype == "UNKNOWN":
        return 0.2

    return 0.3


def _find_by_trace_id(db: Session, trace_id: str | None) -> ErrorKnowledgeBase | None:
    if not trace_id:
        return None

    trace_map = db.query(ErrorTraceMap).filter(ErrorTraceMap.trace_id == trace_id).first()
    if not trace_map:
        return None

    return db.query(ErrorKnowledgeBase).filter(ErrorKnowledgeBase.id == trace_map.error_id).first()


def _insert_trace_map_if_needed(db: Session, trace_id: str | None, error_id):
    if not trace_id:
        return

    exists = db.query(ErrorTraceMap).filter(ErrorTraceMap.trace_id == trace_id).first()
    if exists:
        return

    db.add(ErrorTraceMap(trace_id=trace_id, error_id=error_id))


def match_or_create_error(db: Session, log: dict):
    msg = log.get("message", "")
    api = log.get("api") or "unknown"
    service = log.get("service") or log.get("system") or "unknown"
    trace_id = log.get("trace_id")

    record = _find_by_trace_id(db, trace_id)
    if record:
        # This trace_id was already processed, so this log is a duplicate.
        return record, False, True

    normalized = normalize(msg)
    fingerprint = generate_fingerprint(service, api, normalized)

    record = (
        db.query(ErrorKnowledgeBase)
        .filter(ErrorKnowledgeBase.fingerprint == fingerprint)
        .first()
    )

    if record:
        record.occurrence += 1
        record.last_seen = datetime.utcnow()
        _insert_trace_map_if_needed(db, trace_id, record.id)
        db.commit()
        return record, False, False

    confidence = compute_confidence(log)

    record = ErrorKnowledgeBase(
        fingerprint=fingerprint,
        normalized_message=normalized,
        raw_message=msg,
        error_type=log.get("error_type"),
        service=service,
        api=api,
        label="unconfirmed",
        severity=log.get("severity"),
        confidence_score=confidence,
    )

    db.add(record)
    db.flush()
    _insert_trace_map_if_needed(db, trace_id, record.id)
    db.commit()
    return record, True, False
