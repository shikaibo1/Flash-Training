"""Validate a catalog completely before writing its first transactional seed."""
import json
from pathlib import Path
from pydantic import Field
from ..domain.catalog import KnowledgeConcept, Role
from ..domain.models import AtomicSkill, Model, Skill
from .database import Database
from .repositories.skills import SkillRepository


class CatalogSeed(Model):
    version: int = Field(ge=2, le=2)
    roles: list[Role]
    knowledge: list[KnowledgeConcept]
    atoms: list[AtomicSkill]
    tasks: list[Skill]


def _unique_ids(records, field: str) -> set[str]:
    identifiers = [getattr(record, field) for record in records]
    if any(not identifier.strip() for identifier in identifiers):
        raise ValueError(f"Catalog {field} must not be blank")
    if len(set(identifiers)) != len(identifiers):
        raise ValueError(f"Catalog contains duplicate {field}")
    return set(identifiers)


def _validate_references(catalog: CatalogSeed) -> None:
    role_ids = _unique_ids(catalog.roles, "role_id")
    knowledge_ids = _unique_ids(catalog.knowledge, "knowledge_id")
    atom_ids = _unique_ids(catalog.atoms, "atomic_skill_id")
    atoms_by_id = {atom.atomic_skill_id: atom for atom in catalog.atoms}
    _unique_ids(catalog.tasks, "skill_id")
    if len({task.name for task in catalog.tasks}) != len(catalog.tasks):
        raise ValueError("Catalog contains duplicate task names")
    for atom in catalog.atoms:
        for field in ("knowledge_ids", "prerequisite_ids", "contexts"):
            references = getattr(atom, field)
            if len(references) != len(set(references)):
                raise ValueError(f"Duplicate {field} in atom {atom.atomic_skill_id}")
        if not set(atom.knowledge_ids) <= knowledge_ids:
            raise ValueError(f"Unknown knowledge reference in atom {atom.atomic_skill_id}")
        if not set(atom.prerequisite_ids) <= atom_ids:
            raise ValueError(f"Unknown prerequisite in atom {atom.atomic_skill_id}")
    for task in catalog.tasks:
        if len(task.atomic_skills) != len(set(task.atomic_skills)):
            raise ValueError(f"Duplicate atom references in task {task.skill_id}")
        if task.role_id not in role_ids:
            raise ValueError(f"Unknown role in task {task.skill_id}")
        if not task.atomic_skills or not set(task.atomic_skills) <= atom_ids:
            raise ValueError(f"Task {task.skill_id} must reference existing atoms")
        if any(task.context not in atoms_by_id[atom_id].contexts for atom_id in task.atomic_skills):
            raise ValueError(f"Task {task.skill_id} context is outside its atoms' supported contexts")
    # Kahn's algorithm also detects self-dependencies without recursive stack limits.
    prerequisites = {atom.atomic_skill_id: set(atom.prerequisite_ids) for atom in catalog.atoms}
    dependents: dict[str, list[str]] = {atom_id: [] for atom_id in atom_ids}
    for atom_id, required in prerequisites.items():
        for prior_id in required:
            dependents[prior_id].append(atom_id)
    ready = [atom_id for atom_id, required in prerequisites.items() if not required]
    visited = 0
    while ready:
        prior_id = ready.pop()
        visited += 1
        for atom_id in dependents[prior_id]:
            prerequisites[atom_id].remove(prior_id)
            if not prerequisites[atom_id]:
                ready.append(atom_id)
    if visited != len(atom_ids):
        raise ValueError("Catalog atomic prerequisites contain a cycle")


def seed_catalog(database: Database, path: Path) -> None:
    with database.transaction() as connection:
        seeded = connection.execute("SELECT value FROM catalog_metadata WHERE key='catalog_version'").fetchone()
        if seeded:
            if seeded[0] != "2":
                raise RuntimeError("Unsupported catalog version; select a fresh schema v2 database")
            return
        catalog = CatalogSeed.model_validate(json.loads(Path(path).read_text(encoding="utf-8")))
        _validate_references(catalog)
        connection.executemany("INSERT INTO roles(role_id,name,description) VALUES (?,?,?)",
                               [(role.role_id, role.name, role.description) for role in catalog.roles])
        connection.executemany("INSERT INTO knowledge_concepts(knowledge_id,name,description,course) VALUES (?,?,?,?)",
                               [(item.knowledge_id, item.name, item.description, item.course) for item in catalog.knowledge])
        repository = SkillRepository(connection)
        for atom in catalog.atoms:
            repository.add_atom(atom)
        for task in catalog.tasks:
            repository.add(task)
        connection.execute("INSERT INTO catalog_metadata(key,value) VALUES ('catalog_version',?)", (str(catalog.version),))
