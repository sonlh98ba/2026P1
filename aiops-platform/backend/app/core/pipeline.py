import uuid
from datetime import datetime

from app.database import SessionLocal
from app.models import Incident, ProcessedLogEvent

from .extractor import fetch_failed_logs
from .fingerprint import generate_fingerprint
from .kb_matcher import match_or_create_error
from .normalizer import normalize
from .system_router import parse_log


def handle_incident(db, normalized_error, fingerprint):
    incident = db.query(Incident).filter(Incident.fingerprint == fingerprint).first()

    if incident:
        incident.count += 1
        incident.last_seen = datetime.utcnow()
        db.commit()
        return

    incident = Incident(
        id=uuid.uuid4(),
        fingerprint=fingerprint,
        message=normalized_error["message"],
        error_type=normalized_error["error_type"],
        severity=normalized_error["severity"],
        service=normalized_error["service"],
        api=normalized_error["api"],
        status="OPEN",
        count=1,
    )

    db.add(incident)
    db.commit()


def _is_duplicate_event(db, event_id: str | None) -> bool:
    if not event_id:
        return False
    existing = (
        db.query(ProcessedLogEvent)
        .filter(ProcessedLogEvent.event_id == event_id)
        .first()
    )
    return existing is not None


def _mark_event_processed(db, event_id: str | None):
    if not event_id:
        return
    if _is_duplicate_event(db, event_id):
        return
    db.add(ProcessedLogEvent(event_id=event_id))
    db.commit()


def run_pipeline(limit=50):
    db = SessionLocal()
    logs = fetch_failed_logs(limit)

    stats = {"new": 0, "existing": 0, "duplicate_trace": 0, "duplicate_event": 0}

    for log in logs:
        event_id = log.get("__event_id")
        if _is_duplicate_event(db, event_id):
            stats["duplicate_event"] += 1
            continue

        normalized_error = parse_log(log)
        if not normalized_error:
            continue

        normalized_message = normalize(normalized_error["message"])
        fingerprint = generate_fingerprint(
            normalized_error["service"],
            normalized_error["api"],
            normalized_message,
        )

        _, is_new, is_duplicate_trace = match_or_create_error(db, normalized_error)

        if is_duplicate_trace:
            stats["duplicate_trace"] += 1
            _mark_event_processed(db, event_id)
            continue

        handle_incident(db, normalized_error, fingerprint)
        _mark_event_processed(db, event_id)

        if is_new:
            stats["new"] += 1
        else:
            stats["existing"] += 1

    db.close()
    return stats
