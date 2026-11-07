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
            skill = Skill(skill_id="skill_" + uuid.uuid4().hex, **command.model_dump())
            self._validate_task(unit, skill)
            return unit.skills.add(skill)

    @staticmethod
    def _validate_task(unit, skill: Skill) -> None:
        if not skill.atomic_skills or len(set(skill.atomic_skills)) != len(skill.atomic_skills):
            raise AppError("任务需要非空且不重复的目标原子。", 422, "invalid_targets")
        if skill.role_id and skill.role_id not in {role.role_id for role in unit.skills.catalog_roles()}:
            raise AppError("岗位不存在。", 422, "invalid_role")
        for atom_id in skill.atomic_skills:
            if skill.context not in unit.skills.atom(atom_id).contexts:
                raise AppError("任务情境不在原子适用范围内。", 422, "invalid_context")

    def update(self, skill_id: str, command: SkillPatch) -> Skill:
        with self._work.write() as unit:
            current = unit.skills.get(skill_id)
            self._validate_task(unit, current.model_copy(update=command.model_dump(exclude_unset=True)))
            return unit.skills.update(skill_id, command)

    def delete(self, skill_id: str) -> None:
        with self._work.write() as unit:
            unit.skills.delete(skill_id, utc_now())

    def atoms(self) -> list[AtomicSkill]:
        with self._work.read() as unit:
            return unit.skills.atoms()

    def create_atom(self, command: AtomicCreate) -> AtomicSkill:
        with self._work.write() as unit:
            for references in (command.knowledge_ids, command.prerequisite_ids, command.contexts):
                if len(set(references)) != len(references):
                    raise AppError("知识、先修原子和情境列表不能包含重复项。", 422, "duplicate_reference")
            if any(atom.name.strip() == command.name for atom in unit.skills.atoms()):
                raise AppError("同名原子已存在，请复用现有定义。", 409, "atomic_conflict")
            knowledge = {item.knowledge_id for item in unit.skills.catalog_knowledge()}
            if not set(command.knowledge_ids).issubset(knowledge):
                raise AppError("关联知识不存在。", 422, "invalid_knowledge")
            for prerequisite in command.prerequisite_ids:
                unit.skills.atom(prerequisite)
            return unit.skills.add_atom(AtomicSkill(atomic_skill_id="as_" + uuid.uuid4().hex, **command.model_dump()))

    def custom(self, name: str) -> Skill:
        with self._work.read() as unit:
            if unit.skills.name_exists(name):
                raise AppError("同名技能已存在", 409, "skill_conflict")
            atoms = unit.skills.atoms()
            roles = [role.role_id for role in unit.skills.catalog_roles()]
        proposal = self._content.propose_task(name, atoms, roles)
        with self._work.write() as unit:
            if unit.skills.name_exists(name):
                raise AppError("同名技能已存在", 409, "skill_conflict")
            skill = Skill(skill_id="task_" + uuid.uuid4().hex, name=name, display_name=name,
                description=proposal.description, task_brief=proposal.task_brief, deliverable=proposal.deliverable,
                context=proposal.context, role_id=proposal.role_id, atomic_skills=proposal.atomic_skills,
                default_params={"difficulty": "入门", "duration": "5分钟"})
            self._validate_task(unit, skill)
            return unit.skills.add(skill)
