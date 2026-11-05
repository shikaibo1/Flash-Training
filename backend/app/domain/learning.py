"""Pure learning rules shared by live use cases and historical replay."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from ..errors import AppError


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def event_time(timestamp: str | None, provenance: str) -> str:
    try:
        parsed = datetime.fromisoformat((timestamp or utc_now()).replace("Z", "+00:00"))
        parsed = parsed.replace(tzinfo=parsed.tzinfo or timezone.utc).astimezone(timezone.utc)
    except (ValueError, AttributeError):
        raise AppError("时间格式应为 ISO 8601", 422, "invalid_timestamp") from None
    if provenance == "manual" and parsed > datetime.now(timezone.utc) + timedelta(seconds=5):
        raise AppError("不能使用未来时间更新掌握度", 422, "future_timestamp")
    return parsed.isoformat()


def next_mastery(performance: float, previous: float, stamp: str, last_time: str | None) -> float:
    if isinstance(performance, bool) or not 0 <= performance <= 1:
        raise AppError("performance 必须在 0 到 1 之间", 422, "invalid_performance")
    if last_time and datetime.fromisoformat(stamp) < datetime.fromisoformat(last_time):
        raise AppError("不能插入早于最近一次练习的掌握度记录", 409, "out_of_order_event")
    return round(0.7 * previous + 0.3 * performance, 6)
