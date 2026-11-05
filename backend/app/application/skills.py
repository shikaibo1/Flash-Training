from __future__ import annotations
import uuid
from ..domain.commands import AtomicCreate, SkillCreate, SkillPatch
from ..domain.learning import utc_now
from ..domain.models import AtomicSkill, Skill
from ..domain.ports import UnitOfWorkFactory
from ..errors import AppError
from .content import ContentService


def require_active(skill: Skill) -> Skill:
    if not skill.enabled:
        raise AppError("该技能已停用", 409, "skill_disabled")
    return skill


class SkillService:
    def __init__(self, work: UnitOfWorkFactory, content: ContentService):
        self._work, self._content = work, content

    def get(self, skill_id: str, active: bool = False) -> Skill:
        with self._work.read() as unit:
            skill = unit.skills.get(skill_id)
        return require_active(skill) if active else skill

    def list(self, enabled_only: bool = False) -> list[Skill]:
        with self._work.read() as unit:
            return unit.skills.list(enabled_only)

    def create(self, command: SkillCreate) -> Skill:
        with self._work.write() as unit:
            if unit.skills.name_exists(command.name):
                raise AppError("同名技能已存在", 409, "skill_conflict")
            return unit.skills.add(Skill(skill_id="skill_" + uuid.uuid4().hex, **command.model_dump()))

    def update(self, skill_id: str, command: SkillPatch) -> Skill:
        with self._work.write() as unit:
            return unit.skills.update(skill_id, command)

    def delete(self, skill_id: str) -> None:
        with self._work.write() as unit:
            unit.skills.delete(skill_id, utc_now())

    def atoms(self) -> list[AtomicSkill]:
        with self._work.read() as unit:
            return unit.skills.atoms()

    def create_atom(self, command: AtomicCreate) -> AtomicSkill:
        with self._work.write() as unit:
            return unit.skills.add_atom(AtomicSkill(atomic_skill_id="as_" + uuid.uuid4().hex, **command.model_dump()))

    def custom(self, name: str) -> Skill:
        with self._work.read() as unit:
            if unit.skills.name_exists(name):
                raise AppError("同名技能已存在", 409, "skill_conflict")
        proposal = self._content.propose_skill(name)
        with self._work.write() as unit:
            if unit.skills.name_exists(name):
                raise AppError("同名技能已存在", 409, "skill_conflict")
            atoms = [unit.skills.add_atom(AtomicSkill(atomic_skill_id="as_" + uuid.uuid4().hex, **a.model_dump()))
                     for a in proposal.atomic_skills]
            return unit.skills.add(Skill(skill_id="skill_" + uuid.uuid4().hex, name=name, display_name=name + "技能练习",
                description=proposal.description, generate_prompt=proposal.generate_prompt,
                evaluate_prompt=proposal.evaluate_prompt, default_params=proposal.default_params,
                atomic_skills=[a.atomic_skill_id for a in atoms]))
