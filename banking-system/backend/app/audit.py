from elasticsearch import Elasticsearch
from datetime import datetime
import uuid

es = Elasticsearch(
    hosts=["http://localhost:9200"],
    headers={
        "Accept": "application/vnd.elasticsearch+json; compatible-with=8",
        "Content-Type": "application/json"
    },
    request_timeout=10
)

INDEX = "banking-audit-v3"

def audit_log(
    action: str,
    api: str,
    method: str,
    user: str = None,
    amount: int = None,
    description: str = None,
    status: str = "SUCCESS",
    error: str = None,
    error_type: str = None,
    stacktrace: str = None,
    validation_errors: list = None,
    http_status: int = None,
    extra: dict = None
):
    doc = {
        "@timestamp": datetime.utcnow(),
        "event": {
            "action": action,
            "status": status,
            "api": api,
            "method": method
        },
        "user": {
            "account_no": user
        },
        "transaction": {
            "amount": amount,
            "description": description
        },
        "error": {
            "message": error,
            "type": error_type,
            "stacktrace": stacktrace
        },
        "http": {
            "status_code": http_status
        },
        "validation": {
            "errors": validation_errors
        },
        "trace": {
            "id": str(uuid.uuid4())
        },
        "extra": extra or {}
    }

    es.index(index=INDEX, document=doc)
