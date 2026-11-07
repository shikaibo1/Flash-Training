"""Task-to-atom definitions; learner evidence belongs to the v2 evidence service."""
from ..domain.models import AtomScore, SkillMapping
from ..domain.ports import UnitOfWorkFactory


class ProgressService:
    def __init__(self, work: UnitOfWorkFactory):
        self._work = work

    def mapping(self, user_id: str, skill_id: str) -> SkillMapping:
        # Keep the existing mapping input; definitions are independent of learner identity.
        with self._work.read() as unit:
            skill = unit.skills.get(skill_id)
            atoms = [unit.skills.atom(atom_id) for atom_id in skill.atomic_skills]
        return SkillMapping(
            skill_id=skill_id,
            skill_name=skill.display_name,
            atomic_skills=[
                AtomScore(**atom.model_dump(), score=None, current_score=None)
                for atom in atoms
            ],
        )
