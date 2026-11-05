from __future__ import annotations
import sqlite3
from ...domain.models import AtomMastery, AtomScore, MasteryEvent
from .skills import SkillRepository


class ProgressRepository:
    def __init__(self, connection: sqlite3.Connection):
        self._conn = connection

    def scores(self, user_id: str) -> list[AtomScore]:
        scores = {r[0]: r[1] for r in self._conn.execute(
            "SELECT atomic_skill_id,score FROM user_atomic_scores WHERE user_id=?", (user_id,))}
        return [AtomScore(**atom.model_dump(), score=scores.get(atom.atomic_skill_id, 0.0),
                          current_score=scores.get(atom.atomic_skill_id, 0.0))
                for atom in SkillRepository(self._conn).atoms()]

    def save_score(self, user_id: str, atom_id: str, score: float, stamp: str, provenance: str) -> None:
        self._conn.execute("""INSERT INTO user_atomic_scores VALUES (?,?,?,?,?)
            ON CONFLICT(user_id,atomic_skill_id) DO UPDATE SET score=excluded.score,
            updated_at=excluded.updated_at,provenance=excluded.provenance""", (user_id, atom_id, score, stamp, provenance))

    def latest_mastery(self, user_id: str, atom_id: str) -> MasteryEvent | None:
        row = self._conn.execute("""SELECT mastery,created_at AS timestamp,performance FROM mastery_events
            WHERE user_id=? AND atomic_skill_id=? ORDER BY created_at DESC,event_id DESC LIMIT 1""",
            (user_id, atom_id)).fetchone()
        return MasteryEvent(**dict(row)) if row else None

    def add_event(self, user_id: str, atom_id: str, event: MasteryEvent,
                  session_id: str | None, provenance: str) -> None:
        self._conn.execute("""INSERT INTO mastery_events
            (user_id,atomic_skill_id,session_id,performance,mastery,created_at,provenance) VALUES (?,?,?,?,?,?,?)""",
            (user_id, atom_id, session_id, event.performance, event.mastery, event.timestamp, provenance))

    def all_mastery(self, user_id: str) -> list[AtomMastery]:
        states = {r["atomic_skill_id"]: r for r in self._conn.execute("""
            WITH ranked AS (SELECT atomic_skill_id,mastery,created_at,
                COUNT(*) OVER (PARTITION BY atomic_skill_id) AS practice_count,
                ROW_NUMBER() OVER (PARTITION BY atomic_skill_id ORDER BY created_at DESC,event_id DESC) AS position
                FROM mastery_events WHERE user_id=?)
            SELECT atomic_skill_id,mastery,created_at,practice_count FROM ranked WHERE position=1""", (user_id,))}
        values = []
        for atom in SkillRepository(self._conn).atoms():
            last = states.get(atom.atomic_skill_id)
            values.append(AtomMastery(**atom.model_dump(), mastery=last["mastery"] if last else 0.0,
                last_practice_time=last["created_at"] if last else None, practice_count=last["practice_count"] if last else 0))
        return values

    def curve(self, user_id: str, atom_id: str, threshold: str) -> list[MasteryEvent]:
        return [MasteryEvent(**dict(row)) for row in self._conn.execute("""SELECT created_at AS timestamp,performance,mastery
            FROM mastery_events WHERE user_id=? AND atomic_skill_id=? AND julianday(created_at)>=julianday(?)
            ORDER BY julianday(created_at),event_id""", (user_id, atom_id, threshold))]
