from __future__ import annotations
import json
import sqlite3
from ...domain.commands import SkillPatch
from ...domain.models import AtomicSkill, Skill
from ...errors import AppError
from ..serialization import dump


class SkillRepository:
    def __init__(self, connection: sqlite3.Connection):
        self._conn = connection

    def atom(self, atom_id: str) -> AtomicSkill:
        row = self._conn.execute("SELECT * FROM atomic_skills WHERE atomic_skill_id=?", (atom_id,)).fetchone()
        if not row:
            raise AppError("原子技能不存在", 404, "atomic_skill_not_found")
        return self._atom(row)

    @staticmethod
    def _atom(row: sqlite3.Row) -> AtomicSkill:
        return AtomicSkill(atomic_skill_id=row["atomic_skill_id"], name=row["name"],
                           description=row["description"], categories=json.loads(row["categories_json"]))

    def atoms(self) -> list[AtomicSkill]:
        return [self._atom(row) for row in self._conn.execute("SELECT * FROM atomic_skills ORDER BY rowid")]

    def add_atom(self, atom: AtomicSkill) -> AtomicSkill:
        self._conn.execute("INSERT INTO atomic_skills VALUES (?,?,?,?)", (
            atom.atomic_skill_id, atom.name, atom.description, dump(atom.categories)))
        return atom

    @staticmethod
    def _skill(row: sqlite3.Row, atom_ids: list[str]) -> Skill:
        return Skill(**{key: row[key] for key in (
            "skill_id", "name", "display_name", "description", "generate_prompt", "evaluate_prompt")},
            enabled=bool(row["enabled"]), default_params=json.loads(row["default_params_json"]),
            atomic_skills=atom_ids)

    def get(self, skill_id: str, include_deleted: bool = False) -> Skill:
        row = self._conn.execute("SELECT * FROM skills WHERE skill_id=?", (skill_id,)).fetchone()
        if not row or (row["deleted_at"] and not include_deleted):
            raise AppError("技能不存在", 404, "skill_not_found")
        atoms = [r[0] for r in self._conn.execute(
            "SELECT atomic_skill_id FROM skill_atoms WHERE skill_id=? ORDER BY position", (skill_id,))]
        return self._skill(row, atoms)

    def list(self, enabled_only: bool = False) -> list[Skill]:
        sql = "SELECT * FROM skills WHERE deleted_at IS NULL"
        if enabled_only:
            sql += " AND enabled=1"
        rows = self._conn.execute(sql + " ORDER BY rowid").fetchall()
        mappings: dict[str, list[str]] = {}
        for relation in self._conn.execute("SELECT skill_id,atomic_skill_id FROM skill_atoms ORDER BY skill_id,position"):
            mappings.setdefault(relation[0], []).append(relation[1])
        return [self._skill(row, mappings.get(row["skill_id"], [])) for row in rows]

    def name_exists(self, name: str) -> bool:
        return self._conn.execute("SELECT 1 FROM skills WHERE name=?", (name,)).fetchone() is not None

    def add(self, skill: Skill) -> Skill:
        self._conn.execute("""INSERT INTO skills (skill_id,name,display_name,description,generate_prompt,
            evaluate_prompt,enabled,default_params_json) VALUES (?,?,?,?,?,?,?,?)""", (
            skill.skill_id, skill.name, skill.display_name, skill.description, skill.generate_prompt,
            skill.evaluate_prompt, int(skill.enabled), dump(skill.default_params)))
        self._set_atoms(skill.skill_id, skill.atomic_skills)
        return self.get(skill.skill_id)

    def _set_atoms(self, skill_id: str, atom_ids: list[str]) -> None:
        for atom_id in atom_ids:
            self.atom(atom_id)
        self._conn.execute("DELETE FROM skill_atoms WHERE skill_id=?", (skill_id,))
        self._conn.executemany("INSERT INTO skill_atoms VALUES (?,?,?)", [
            (skill_id, atom_id, i) for i, atom_id in enumerate(dict.fromkeys(atom_ids))])

    def update(self, skill_id: str, changes: SkillPatch) -> Skill:
        self.get(skill_id)
        updates = changes.model_dump(exclude_unset=True)
        # Column names come only from this allowlist.
        for key in ("display_name", "description", "generate_prompt", "evaluate_prompt", "enabled", "default_params"):
            if key in updates:
                column = "default_params_json" if key == "default_params" else key
                value = dump(updates[key]) if key == "default_params" else updates[key]
                self._conn.execute(f"UPDATE skills SET {column}=? WHERE skill_id=?", (value, skill_id))
        if changes.atomic_skills is not None:
            self._set_atoms(skill_id, changes.atomic_skills)
        return self.get(skill_id)

    def delete(self, skill_id: str, stamp: str) -> None:
        self.get(skill_id)
        self._conn.execute("UPDATE skills SET enabled=0,deleted_at=? WHERE skill_id=?", (stamp, skill_id))
