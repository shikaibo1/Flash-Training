"""SQLite schema and connection lifecycle; writes use explicit transactions."""
from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA_VERSION = 1
SCHEMA = """
CREATE TABLE users (user_id TEXT PRIMARY KEY, created_at TEXT NOT NULL);
CREATE TABLE atomic_skills (
    atomic_skill_id TEXT PRIMARY KEY, name TEXT NOT NULL,
    description TEXT NOT NULL, categories_json TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE skills (
    skill_id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL, description TEXT NOT NULL,
    generate_prompt TEXT NOT NULL DEFAULT '', evaluate_prompt TEXT NOT NULL DEFAULT '',
    enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1)),
    default_params_json TEXT NOT NULL DEFAULT '{}', deleted_at TEXT
);
CREATE TABLE skill_atoms (
    skill_id TEXT NOT NULL REFERENCES skills(skill_id),
    atomic_skill_id TEXT NOT NULL REFERENCES atomic_skills(atomic_skill_id),
    position INTEGER NOT NULL,
    PRIMARY KEY(skill_id, atomic_skill_id)
);
CREATE TABLE practice_sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id),
    skill_id TEXT NOT NULL REFERENCES skills(skill_id),
    content_json TEXT NOT NULL, skill_snapshot_json TEXT NOT NULL,
    params_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL CHECK(status IN ('active','completed')),
    started_at TEXT NOT NULL, completed_at TEXT, result_json TEXT,
    provenance TEXT NOT NULL DEFAULT 'live'
);
CREATE INDEX sessions_user_idx ON practice_sessions(user_id, started_at);
CREATE TABLE practice_attempts (
    attempt_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES practice_sessions(session_id),
    answer TEXT NOT NULL, evaluation_json TEXT NOT NULL, created_at TEXT NOT NULL,
    UNIQUE(session_id, attempt_id)
);
CREATE TABLE practice_records (
    record_id TEXT PRIMARY KEY,
    session_id TEXT UNIQUE REFERENCES practice_sessions(session_id),
    user_id TEXT NOT NULL REFERENCES users(user_id),
    skill_id TEXT NOT NULL REFERENCES skills(skill_id),
    score REAL NOT NULL CHECK(score >= 0 AND score <= 100),
    started_at TEXT NOT NULL, ended_at TEXT NOT NULL,
    payload_json TEXT NOT NULL, deleted_at TEXT,
    provenance TEXT NOT NULL DEFAULT 'live'
);
CREATE INDEX records_user_idx ON practice_records(user_id, started_at);
CREATE TABLE user_atomic_scores (
    user_id TEXT NOT NULL REFERENCES users(user_id),
    atomic_skill_id TEXT NOT NULL REFERENCES atomic_skills(atomic_skill_id),
    score REAL NOT NULL CHECK(score >= 0 AND score <= 10),
    updated_at TEXT NOT NULL, provenance TEXT NOT NULL,
    PRIMARY KEY(user_id, atomic_skill_id)
);
CREATE TABLE mastery_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL REFERENCES users(user_id),
    atomic_skill_id TEXT NOT NULL REFERENCES atomic_skills(atomic_skill_id),
    session_id TEXT REFERENCES practice_sessions(session_id),
    performance REAL NOT NULL CHECK(performance >= 0 AND performance <= 1),
    mastery REAL NOT NULL CHECK(mastery >= 0 AND mastery <= 1),
    created_at TEXT NOT NULL, provenance TEXT NOT NULL,
    UNIQUE(session_id, atomic_skill_id)
);
CREATE INDEX mastery_user_atom_idx ON mastery_events(user_id, atomic_skill_id, created_at, event_id);
CREATE TABLE user_skill_profiles (
    user_id TEXT NOT NULL REFERENCES users(user_id), skill_key TEXT NOT NULL,
    payload_json TEXT NOT NULL, PRIMARY KEY(user_id, skill_key)
);
CREATE TABLE legacy_imports (
    source TEXT PRIMARY KEY, sha256 TEXT NOT NULL, payload_json TEXT NOT NULL,
    imported_at TEXT NOT NULL
);
CREATE TABLE migration_reports (
    migration_key TEXT PRIMARY KEY, report_json TEXT NOT NULL, created_at TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)

    def connect(self):
        conn = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=15000")
        return conn

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = self.connect()
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("BEGIN IMMEDIATE")
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if version > SCHEMA_VERSION:
                raise RuntimeError("Database schema is newer than this application")
            if version == 0:
                for statement in SCHEMA.split(";"):
                    if statement.strip():
                        conn.execute(statement)
                conn.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    def check_health(self) -> int:
        with self.read() as connection:
            return connection.execute("PRAGMA user_version").fetchone()[0]

    @contextmanager
    def read(self):
        conn = self.connect()
        try:
            # A consistent snapshot for multi-query reads.
            conn.execute("PRAGMA query_only=ON")
            conn.execute("BEGIN")
            yield conn
        finally:
            conn.rollback()
            conn.close()

    @contextmanager
    def transaction(self):
        conn = self.connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()
