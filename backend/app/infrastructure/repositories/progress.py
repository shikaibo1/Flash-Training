from __future__ import annotations
import sqlite3
from ...domain.models import EvidenceRecord


class ProgressRepository:
    def __init__(self, connection: sqlite3.Connection):
        self._conn = connection

    def add_evidence(self, user_id: str, evidence: EvidenceRecord) -> None:
        self._conn.execute("""INSERT INTO atom_evidence
            (session_id,user_id,atomic_skill_id,context,mode,assistance_used,status,score,quote,reason,next_action,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", (
            evidence.session_id, user_id, evidence.atomic_skill_id, evidence.context, evidence.mode,
            int(evidence.assistance_used), evidence.status, evidence.score, evidence.quote,
            evidence.reason, evidence.next_action, evidence.created_at))

    def evidence(self, user_id: str) -> list[EvidenceRecord]:
        return [EvidenceRecord(**dict(record)) for record in self._conn.execute("""SELECT
            session_id,atomic_skill_id,context,mode,assistance_used,status,score,quote,reason,next_action,created_at
            FROM atom_evidence WHERE user_id=? ORDER BY created_at DESC,event_id DESC""", (user_id,))]
