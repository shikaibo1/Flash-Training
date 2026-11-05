from __future__ import annotations
import json
import sqlite3
from ...domain.learning import utc_now
from ...domain.models import JsonValue


class UserRepository:
    def __init__(self, connection: sqlite3.Connection):
        self._conn = connection

    def ensure(self, user_id: str) -> None:
        self._conn.execute("INSERT OR IGNORE INTO users VALUES (?,?)", (user_id, utc_now()))

    def legacy_profiles(self, user_id: str) -> dict[str, JsonValue]:
        return {r[0]: json.loads(r[1]) for r in self._conn.execute(
            "SELECT skill_key,payload_json FROM user_skill_profiles WHERE user_id=?", (user_id,))}
