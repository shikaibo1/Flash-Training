from __future__ import annotations
import sqlite3
from ...domain.learning import utc_now


class UserRepository:
    def __init__(self, connection: sqlite3.Connection):
        self._conn = connection

    def ensure(self, user_id: str) -> None:
        self._conn.execute("INSERT OR IGNORE INTO users VALUES (?,?)", (user_id, utc_now()))
