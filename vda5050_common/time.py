from __future__ import annotations

from datetime import datetime, timezone

_counters: dict[str, int] = {}


def now_iso8601() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def next_header_id(topic_name: str) -> int:
    current = _counters.get(topic_name, -1) + 1
    _counters[topic_name] = current
    return current
