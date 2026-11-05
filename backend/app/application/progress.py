from __future__ import annotations
from datetime import datetime, timedelta, timezone
from ..domain.commands import AtomicScoreRequest, MasteryRequest, OptimizeRequest
from ..domain.learning import utc_now
from ..domain.models import (
    AtomMastery, LearningCurve, ManualScore, MasteryUpdated, Optimization, Prediction,
    Recommendation, Recommendations, ScoreValue, SkillMapping, UserMastery, UserScores,
)
from ..domain.ports import UnitOfWorkFactory
from ..errors import AppError
from .content import ContentService
from .learning import record_performance


class ProgressService:
    def __init__(self, work: UnitOfWorkFactory, content: ContentService):
        self._work, self._content = work, content

    def scores(self, user_id: str) -> UserScores:
        with self._work.read() as unit:
            return UserScores(user_id=user_id, atomic_skills=unit.progress.scores(user_id))

    def score(self, user_id: str, atom_id: str) -> ScoreValue:
        with self._work.read() as unit:
            unit.skills.atom(atom_id)
            value = next(a.score for a in unit.progress.scores(user_id) if a.atomic_skill_id == atom_id)
            return ScoreValue(user_id=user_id, atomic_skill_id=atom_id, score=value)

    def manual_score(self, command: AtomicScoreRequest) -> ManualScore:
        with self._work.write() as unit:
            unit.skills.atom(command.atomic_skill_id)
            unit.users.ensure(command.user_id)
            unit.progress.save_score(command.user_id, command.atomic_skill_id, command.score, utc_now(), "manual")
        return ManualScore(user_id=command.user_id, atomic_skill_id=command.atomic_skill_id, score=command.score)

    def update_mastery(self, command: MasteryRequest) -> MasteryUpdated:
        with self._work.write() as unit:
            value = record_performance(unit, command.user_id, command.atomic_skill_id,
                command.performance, command.timestamp, provenance="manual")
        return MasteryUpdated(atomic_skill_id=command.atomic_skill_id, new_mastery=value)

    def all_mastery(self, user_id: str) -> UserMastery:
        with self._work.read() as unit:
            return UserMastery(user_id=user_id, atomic_skills=unit.progress.all_mastery(user_id))

    def mastery(self, user_id: str, atom_id: str) -> AtomMastery:
        with self._work.read() as unit:
            unit.skills.atom(atom_id)
            return next(a for a in unit.progress.all_mastery(user_id) if a.atomic_skill_id == atom_id)

    def predict(self, user_id: str, atom_id: str) -> Prediction:
        return Prediction(atomic_skill_id=atom_id, predicted_performance=self.mastery(user_id, atom_id).mastery)

    def mapping(self, user_id: str, skill_id: str) -> SkillMapping:
        with self._work.read() as unit:
            skill = unit.skills.get(skill_id)
            scores = unit.progress.scores(user_id)
            return SkillMapping(skill_id=skill_id, skill_name=skill.display_name,
                atomic_skills=[a for a in scores if a.atomic_skill_id in skill.atomic_skills])

    def curve(self, user_id: str, atom_id: str, days: int) -> LearningCurve:
        threshold = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        with self._work.read() as unit:
            unit.skills.atom(atom_id)
            return LearningCurve(atomic_skill_id=atom_id, learning_curve=unit.progress.curve(user_id, atom_id, threshold), days=days)

    def recommendations(self, user_id: str, top_n: int) -> Recommendations:
        with self._work.read() as unit:
            skills = unit.skills.list(enabled_only=True)
            values = {a.atomic_skill_id: a.mastery for a in unit.progress.all_mastery(user_id)}
        recommendations = [Recommendation(**skill.model_dump(), mastery=(
            sum(values.get(a, 0.0) for a in skill.atomic_skills) / len(skill.atomic_skills) if skill.atomic_skills else 0.0))
            for skill in skills]
        return Recommendations(recommendations=sorted(recommendations, key=lambda s: s.mastery)[:top_n], top_n=top_n)

    def optimize(self, command: OptimizeRequest) -> Optimization:
        with self._work.read() as unit:
            targets = [a for a in unit.progress.scores(command.user_id) if a.atomic_skill_id in command.atomic_skill_ids]
        if len(targets) != len(set(command.atomic_skill_ids)):
            raise AppError("部分原子技能不存在", 404, "atomic_skill_not_found")
        targets = sorted(targets, key=lambda a: a.score)[:3]
        return Optimization(user_id=command.user_id, targeted_skills=targets,
            optimization_advice=self._content.optimize(command.optimization_goal, targets),
            optimization_goal=command.optimization_goal)
