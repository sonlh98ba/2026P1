from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from .database import Base
import uuid
from datetime import datetime
from sqlalchemy import Float


class ErrorKnowledgeBase(Base):
    __tablename__ = "error_knowledge_base"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fingerprint = Column(String(64), unique=True, index=True)

    normalized_message = Column(Text, nullable=False)
    raw_message = Column(Text, nullable=False)

    error_type = Column(String(100))
    service = Column(String(100))
    api = Column(String(255))

    label = Column(String(30), default="unconfirmed")
    severity = Column(String(20))

    solution = Column(Text)
    auto_fix_script = Column(Text)

    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    occurrence = Column(Integer, default=1)
    confidence_score = Column(Float, default=1.0)


class ErrorTraceMap(Base):
    __tablename__ = "error_trace_map"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trace_id = Column(String(255), unique=True, index=True, nullable=False)
    error_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ProcessedLogEvent(Base):
    __tablename__ = "processed_log_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    fingerprint = Column(String(64), index=True)

    message = Column(Text, nullable=False)
    error_type = Column(String(50))   # SYSTEM | BUSINESS | VALIDATION | UNKNOWN
    severity = Column(String(20))     # CRITICAL | HIGH | MEDIUM | LOW

    service = Column(String(100))
    api = Column(String(255))

    status = Column(String(20), default="OPEN")
    assigned_to = Column(String(100))

    count = Column(Integer, default=1)

    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
