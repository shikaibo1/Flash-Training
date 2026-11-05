from __future__ import annotations
import uuid
from ..domain.learning import utc_now
from ..domain.models import (
    Evaluation, JsonObject, PracticeContent, PracticeRecord, PracticeSession,
    SessionDetails, SessionHistory, SessionStarted, Submission,
)
from ..domain.ports import UnitOfWork, UnitOfWorkFactory
from ..errors import AppError
from .content import ContentService
from .learning import record_performance
from .skills import require_active


class PracticeService:
    def __init__(self, work: UnitOfWorkFactory, content: ContentService):
        self._work, self._content = work, content

    def generate(self, skill_id: str, params: JsonObject) -> PracticeContent:
        with self._work.read() as unit:
            skill = require_active(unit.skills.get(skill_id))
        return self._content.generate(skill, {**skill.default_params, **params})

    def start(self, user_id: str, skill_id: str, params: JsonObject) -> SessionStarted:
        with self._work.read() as unit:
            skill = require_active(unit.skills.get(skill_id))
        effective = {**skill.default_params, **params}
        content = self._content.generate(skill, effective)
        session = PracticeSession(session_id=uuid.uuid4().hex, user_id=user_id, skill_id=skill_id,
            content=content, skill_snapshot=skill, params=effective, started_at=utc_now())
        with self._work.write() as unit:
            # Recheck after model latency, while preserving the actual generation snapshot.
            require_active(unit.skills.get(skill_id))
            unit.users.ensure(user_id)
            unit.practices.add(session)
            names = {a: unit.skills.atom(a).name for a in skill.atomic_skills}
        return SessionStarted(session_id=session.session_id, skill_id=skill_id, question=content.title,
            content=content, start_time=session.started_at, atomic_skill_names=names)

    def evaluate(self, skill_id: str, answer: str, reference: str, params: JsonObject) -> Evaluation:
        with self._work.read() as unit:
            skill = require_active(unit.skills.get(skill_id))
            atoms = [unit.skills.atom(a) for a in skill.atomic_skills]
        return self._content.evaluate(skill, atoms, answer, reference, {**skill.default_params, **params})

    @staticmethod
    def _completed(unit: UnitOfWork, session: PracticeSession, answer: str | None = None) -> Submission:
        if answer is not None and unit.practices.latest_answer(session.session_id) != answer:
            raise AppError("该会话已提交其他答案，请开始新的练习。", 409, "session_answer_conflict")
        return Submission(session_id=session.session_id, evaluation_result=session.result or {},
                          record_id=unit.practices.record_id(session.session_id))

    def submit(self, user_id: str, session_id: str, answer: str) -> Submission:
        with self._work.read() as unit:
            session = unit.practices.get(session_id, user_id)
            if session.status == "completed":
                return self._completed(unit, session, answer)
            atoms = [unit.skills.atom(a) for a in session.skill_snapshot.atomic_skills]
        skill = session.skill_snapshot
        result = self._content.evaluate(skill, atoms, answer, session.content.model_dump(mode="json"), session.params)
        with self._work.write() as unit:
            current = unit.practices.get(session_id, user_id)
            if current.status == "completed":
                return self._completed(unit, current, answer)
            # Timestamp follows acquisition of the write lock so evidence stays ordered.
            stamp = utc_now()
            record = PracticeRecord(record_id=uuid.uuid4().hex, session_id=session_id, user_id=user_id,
                skill_id=skill.skill_id, skill_name=skill.display_name, **session.content.model_dump(),
                input_type="text", transcript=answer, score=round(result.score * 10, 2),
                strengths=result.strengths, improvements=result.improvements, ai_comment=result.aiComment,
                start_time=session.started_at, end_time=stamp, atomic_skill_scores=result.atomic_skill_scores,
                atomic_skill_names={a: unit.skills.atom(a).name for a in skill.atomic_skills})
            unit.practices.complete(session_id, answer, result, stamp)
            unit.practices.add_record(record)
            for atom_id, score in result.atomic_skill_scores.items():
                unit.progress.save_score(user_id, atom_id, score, stamp, "live")
                record_performance(unit, user_id, atom_id, score / 10, stamp, session_id)
            return Submission(session_id=session_id, evaluation_result=result, record_id=record.record_id)

    def session_details(self, user_id: str, session_id: str) -> SessionDetails:
        with self._work.read() as unit:
            session = unit.practices.get(session_id, user_id)
            names = {a: unit.skills.atom(a).name for a in session.skill_snapshot.atomic_skills}
            details = SessionDetails(session_id=session_id, skill_id=session.skill_id, status=session.status,
                content=session.content, start_time=session.started_at, atomic_skill_names=names)
            if session.status == "completed":
                completed = self._completed(unit, session)
                details = details.model_copy(update={"evaluation_result": completed.evaluation_result,
                    "record_id": completed.record_id, "answer": unit.practices.latest_answer(session_id) or ""})
            return details

    def history(self, user_id: str, skill_id: str | None = None) -> list[SessionHistory]:
        with self._work.read() as unit:
            return unit.practices.history(user_id, skill_id)
