from typing import Any

from .elastic import es

INDEX = "banking-audit-*"


def _first_value(value: Any):
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _insert_dotted(data: dict, dotted_key: str, value: Any):
    parts = dotted_key.split(".")
    current = data
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value


def _hit_to_log(hit: dict) -> dict:
    event_id = hit.get("_id")
    source = hit.get("_source")
    if isinstance(source, dict) and source:
        enriched = dict(source)
        if isinstance(event_id, str) and event_id:
            enriched["__event_id"] = event_id
        return enriched

    # Kibana Discover can return data under `fields` instead of `_source`.
    fields = hit.get("fields") or {}
    normalized: dict[str, Any] = {}
    for key, value in fields.items():
        _insert_dotted(normalized, key, _first_value(value))
    if isinstance(event_id, str) and event_id:
        normalized["__event_id"] = event_id
    return normalized


def fetch_failed_logs(size=50):
    query = {
        "query": {
            "bool": {
                "filter": [
                    {"term": {"event.status": "FAILED"}}
                ]
            }
        },
        "sort": [{"@timestamp": {"order": "desc"}}],
        "size": size,
        "_source": True,
        "fields": ["*"],
    }

    res = es.search(index=INDEX, body=query)
    return [_hit_to_log(hit) for hit in res.get("hits", {}).get("hits", [])]


def fetch_log_by_trace_id(trace_id: str):
    """Fetch one log from Kibana/Elasticsearch by trace id."""
    value = (trace_id or "").strip()
    if not value:
        return None

    fields = [
        "trace_id",
        "trace.id",
        "event.trace_id",
        "event.traceId",
        "kibana.trace_id",
        "extra.trace_id",
    ]

    should = []
    for field in fields:
        should.append({"term": {field: value}})
        should.append({"term": {f"{field}.keyword": value}})

    query = {
        "query": {
            "bool": {
                "should": should,
                "minimum_should_match": 1,
            }
        },
        "sort": [{"@timestamp": {"order": "desc"}}],
        "size": 1,
        "_source": True,
        "fields": ["*"],
    }

    try:
        res = es.search(index=INDEX, body=query)
    except Exception:
        return None

    hits = res.get("hits", {}).get("hits", [])
    if not hits:
        return None

    return _hit_to_log(hits[0])
