from __future__ import annotations
from datetime import datetime
from ..domain.learning import utc_now
from ..domain.models import PracticeRecord, SkillProgress, SkillStatistics, UserProfile
from ..domain.ports import UnitOfWorkFactory


class RecordService:
    def __init__(self, work: UnitOfWorkFactory):
        self._work = work

    def list(self, user_id: str) -> list[PracticeRecord]:
        with self._work.read() as unit:
            return unit.practices.records(user_id)

    def delete(self, user_id: str, record_id: str) -> None:
        with self._work.write() as unit:
            unit.practices.delete_record(record_id, user_id, utc_now())

    def progress(self, user_id: str, skill_id: str) -> SkillProgress:
        with self._work.read() as unit:
            unit.skills.get(skill_id)
            records = [r for r in unit.practices.records(user_id) if r.skill_id == skill_id]
        return SkillProgress(user_id=user_id, skill_id=skill_id, practice_count=len(records),
            avg_score=sum(r.score for r in records) / len(records) if records else 0.0)

    def profile(self, user_id: str) -> UserProfile:
        with self._work.read() as unit:
            records = unit.practices.records(user_id)
        # Completion order can differ from session start order.
        records = sorted(records, key=lambda record: datetime.fromisoformat(record.end_time), reverse=True)
        skills: dict[str, SkillStatistics] = {}
        for record in records:
            entry = skills.get(record.skill_id)
            if entry is None:
                entry = SkillStatistics(last_score=record.score, last_practice_time=record.end_time)
            count = entry.practice_count
            skills[record.skill_id] = SkillStatistics(practice_count=count + 1,
                avg_score=(entry.avg_score * count + record.score) / (count + 1),
                last_score=entry.last_score, last_practice_time=entry.last_practice_time)
        return UserProfile(user_id=user_id, skills=skills)
