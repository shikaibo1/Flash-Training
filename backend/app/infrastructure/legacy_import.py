"""One-time, transactional import. Original JSON files remain unchanged."""
from __future__ import annotations
import hashlib
import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from ..domain.learning import utc_now as now, event_time, next_mastery
from ..domain.models import AtomicSkill, Skill, MasteryEvent
from .serialization import dump
from .repositories.skills import SkillRepository
from .repositories.progress import ProgressRepository
from .repositories.users import UserRepository

MIGRATION_KEY = "legacy_json_v1"


def migrate_legacy(database, legacy_dir):
    legacy_dir = Path(legacy_dir)
    with database.read() as conn:
        previous = conn.execute("SELECT report_json FROM migration_reports WHERE migration_key=?", (MIGRATION_KEY,)).fetchone()
        if previous:
            return json.loads(previous[0])
    sources = sorted(legacy_dir.glob("*.json"))
    nested = legacy_dir.parent / "backend" / "data" / "practice_records.json"
    if nested.exists():
        sources.append(nested)
    # Parse every file BEFORE writes. Corrupt input aborts; it is never silently reset.
    payloads = [(p, json.loads(p.read_text(encoding="utf-8-sig"))) for p in sources]
    report = {"version": 1, "sources": [], "warnings": [], "counts": {}, "backup": None}
    backup = legacy_dir / "backups" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8])
    if sources:
        backup.mkdir(parents=True)
        for index, (path, _) in enumerate(payloads):
            shutil.copy2(path, backup / f"{index:02d}-{path.name}")
        report["backup"] = str(backup)

    with database.transaction() as conn:
        # Another worker may have finished while this process read the files.
        previous = conn.execute("SELECT report_json FROM migration_reports WHERE migration_key=?", (MIGRATION_KEY,)).fetchone()
        if previous:
            return json.loads(previous[0])
        docs = {p.name: d for p, d in payloads if p.parent == legacy_dir}
        skills = SkillRepository(conn)
        progress = ProgressRepository(conn)
        users = UserRepository(conn)

        def insert_atom(value):
            # Import only known definition fields; the full source remains archived.
            return skills.add_atom(AtomicSkill(atomic_skill_id=value.get("atomic_skill_id") or "as_" + uuid.uuid4().hex,
                name=value["name"], description=value["description"], categories=value.get("categories", [])))

        def insert_skill(value):
            fields = {k: v for k, v in value.items() if k in Skill.model_fields}
            fields.setdefault("skill_id", "skill_" + uuid.uuid4().hex)
            return skills.add(Skill.model_validate(fields))

        def ensure_atom(atom_id):
            if not conn.execute("SELECT 1 FROM atomic_skills WHERE atomic_skill_id=?", (atom_id,)).fetchone():
                insert_atom({"atomic_skill_id": atom_id, "name": atom_id,
                                             "description": "历史数据引用的原子技能（待补全）"})
                report["warnings"].append(f"Created placeholder atomic skill: {atom_id}")

        def ensure_skill(skill_id):
            if not conn.execute("SELECT 1 FROM skills WHERE skill_id=?", (skill_id,)).fetchone():
                insert_skill({"skill_id": skill_id, "name": "legacy:" + skill_id,
                    "display_name": skill_id, "description": "仅用于保留历史记录", "enabled": False})
                report["warnings"].append(f"Created disabled historical skill: {skill_id}")

        for atom in docs.get("atomic_skills.json", {}).get("atomic_skills", []):
            insert_atom(atom)
        for skill in docs.get("skill_library.json", {}).get("skills", []):
            for atom_id in skill.get("atomic_skills", []):
                ensure_atom(atom_id)
            insert_skill(skill)

        seen_records = set()
        for path, doc in payloads:
            source = str(path.relative_to(legacy_dir.parent))
            report["sources"].append(source)
            conn.execute("INSERT INTO legacy_imports VALUES (?,?,?,?)", (
                source, hashlib.sha256(path.read_bytes()).hexdigest(), dump(doc), now()))
            if path.name != "practice_records.json":
                continue
            for value in doc:
                record = dict(value)
                semantic = {k: v for k, v in record.items() if k != "record_id"}
                fingerprint = hashlib.sha256(json.dumps(semantic, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
                if fingerprint in seen_records:
                    report["warnings"].append(f"Duplicate practice record skipped in {source}")
                    continue
                seen_records.add(fingerprint)
                record_id = record.get("record_id") or "legacy_" + fingerprint[:32]
                if conn.execute("SELECT 1 FROM practice_records WHERE record_id=?", (record_id,)).fetchone():
                    report["warnings"].append(f"Conflicting record id reassigned: {record_id}")
                    record_id = "legacy_" + fingerprint[:32]
                uid, sid = record.get("user_id", "default_user"), record.get("skill_id", "legacy_unknown")
                users.ensure(uid)
                ensure_skill(sid)
                score = float(record.get("score", 0))
                if not 0 <= score <= 100:
                    raise ValueError(f"Invalid historical score in {source}: {record_id}")
                record.update(record_id=record_id, user_id=uid, skill_id=sid)
                conn.execute("""INSERT INTO practice_records
                    (record_id,user_id,skill_id,score,started_at,ended_at,payload_json,provenance)
                    VALUES (?,?,?,?,?,?,?,?)""", (record_id, uid, sid, score,
                    record.get("start_time", now()), record.get("end_time", now()), dump(record), "legacy"))

        for value in docs.get("unified_practice_records.json", []):
            uid, sid = value["user_id"], value["skill_id"]
            users.ensure(uid)
            ensure_skill(sid)
            snapshot = skills.get(sid)
            result = value.get("final_result")
            conn.execute("""INSERT INTO practice_sessions
                (session_id,user_id,skill_id,content_json,skill_snapshot_json,status,started_at,
                 completed_at,result_json,provenance) VALUES (?,?,?,?,?,?,?,?,?,?)""", (
                value["session_id"], uid, sid, dump({"title": value.get("question", "历史题目"),
                "description": value.get("question", ""), "category": snapshot.name, "difficulty": "历史",
                "hint": "", "example_answer": ""}), dump(snapshot),
                "completed" if value.get("status") == "completed" else "active",
                value.get("start_time", now()), value.get("end_time"), dump(result) if result else None, "legacy"))
            for index, attempt in enumerate(value.get("attempts", [])):
                conn.execute("INSERT INTO practice_attempts VALUES (?,?,?,?,?)", (
                    "legacy_" + uuid.uuid5(uuid.NAMESPACE_URL, value["session_id"] + str(index)).hex,
                    value["session_id"], attempt.get("answer", ""), dump(attempt.get("evaluation", {})),
                    attempt.get("timestamp", now())))

        for uid, scores in docs.get("user_atomic_scores.json", {}).items():
            for atom_id, score in scores.items():
                ensure_atom(atom_id)
                users.ensure(uid)
                progress.save_score(uid, atom_id, float(score), now(), "legacy")

        # Replay evidence instead of importing mastery=1 caused by the old 0..10/0..1 bug.
        for uid, value in docs.get("knowledge_tracing.json", {}).get("users", {}).items():
            for atom_id, state in value.get("atomic_skills", {}).items():
                ensure_atom(atom_id)
                history = sorted(state.get("history", []), key=lambda h: h["timestamp"])
                for event in history:
                    performance = float(event["performance"])
                    if performance > 1:
                        performance /= 10
                        report["warnings"].append(f"Normalized legacy performance /10: {uid}/{atom_id}")
                    stamp = event_time(event["timestamp"], "legacy_replayed")
                    last = progress.latest_mastery(uid, atom_id)
                    mastery = next_mastery(performance, last.mastery if last else 0.0,
                                            stamp, last.timestamp if last else None)
                    users.ensure(uid)
                    progress.add_event(uid, atom_id, MasteryEvent(timestamp=stamp, performance=performance,
                        mastery=mastery), None, "legacy_replayed")
                if state.get("mastery") and not history:
                    report["warnings"].append(f"Mastery without evidence archived only: {uid}/{atom_id}")

        for uid, profiles in docs.get("skill_profiles.json", {}).items():
            users.ensure(uid)
            for key, profile in profiles.items():
                conn.execute("INSERT OR IGNORE INTO user_skill_profiles VALUES (?,?,?)", (uid, key, dump(profile)))
        for key, profile in docs.get("user_skill_profiles.json", {}).items():
            uid = profile.get("user_id", "default_user")
            users.ensure(uid)
            conn.execute("INSERT OR IGNORE INTO user_skill_profiles VALUES (?,?,?)", (
                uid, profile.get("skill_id", key), dump(profile)))
        for table in ("skills", "atomic_skills", "skill_atoms", "practice_sessions", "practice_attempts",
                      "practice_records", "mastery_events", "user_skill_profiles"):
            report["counts"][table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        conn.execute("INSERT INTO migration_reports VALUES (?,?,?)", (MIGRATION_KEY, dump(report), now()))
    if sources:
        (backup / "migration-report.json").write_text(dump(report), encoding="utf-8")
    return report
