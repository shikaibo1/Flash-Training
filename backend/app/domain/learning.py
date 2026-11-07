"""UTC timestamps shared by session, evidence and catalog operations."""
from __future__ import annotations
from datetime import datetime, timezone


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
