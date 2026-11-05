"""Run with: python -m unittest discover -s tests -v. No API key/network required."""
import asyncio
import json
import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.infrastructure.ai import OpenAIJSONClient
from app.infrastructure.database import Database
from app.errors import AIError, AppError
from app.main import create_app
from app.infrastructure.legacy_import import migrate_legacy
from app.infrastructure.serialization import dump
from app.infrastructure.unit_of_work import SQLiteUnitOfWorkFactory
from app.infrastructure.repositories.skills import SkillRepository
from app.infrastructure.repositories.progress import ProgressRepository
from app.domain.commands import SkillPatch, MasteryRequest
from app.bootstrap import build_services
from app.settings import Settings

ATOM = {"atomic_skill_id": "a1", "name": "换元", "description": "正确识别和执行变量替换", "categories": ["高数"]}
SKILL = {"skill_id": "s1", "name": "高数", "display_name": "高数练习", "description": "积分练习",
         "atomic_skills": ["a1"], "default_params": {"difficulty": "入门"}}
CONTENT = {"title": "积分题", "description": "计算给定积分并解释换元步骤。", "hint": "观察复合函数。",
           "example_answer": "令 u=x²+1，再作代换。", "category": "高数", "difficulty": "入门"}
EVALUATION = {"score": 8.0, "strengths": ["正确换元"], "improvements": ["写明积分限"],
              "aiComment": "思路正确，需补充积分限。", "atomic_skill_scores": {"a1": 8.0}}


class FakeAI:
    configured = True

    def __init__(self):
        self.failure = False
        self.bad_scores = False
        self.reference = None
        self.generations = 0
        self.evaluations = 0
        self.barrier = None

    def generate_json(self, task, payload):
        if self.failure:
            raise AIError("test unavailable")
        if "answer" in payload:
            self.evaluations += 1
            self.reference = payload["question"]
            if self.barrier:
                self.barrier.wait(timeout=5)
            return {**EVALUATION, "atomic_skill_scores": {} if self.bad_scores else {"a1": 8.0}}
        self.generations += 1
        return dict(CONTENT)


class TrainingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.legacy = self.root / "data"
        self.legacy.mkdir()
        (self.legacy / "atomic_skills.json").write_text(dump({"atomic_skills": [ATOM]}), encoding="utf-8")
        (self.legacy / "skill_library.json").write_text(dump({"skills": [SKILL]}), encoding="utf-8")
        self.settings = Settings(database_path=self.root / "test.sqlite3", legacy_dir=self.legacy)
        self.db = Database(self.settings.database_path)
        self.db.initialize()
        migrate_legacy(self.db, self.legacy)
        self.ai = FakeAI()
        self.work = SQLiteUnitOfWorkFactory(self.db)
        self.services = build_services(self.work, self.ai)
        self.svc = self.services.practice
        self.skills = self.services.skills
        self.progress = self.services.progress
        self.records = self.services.records

    def tearDown(self):
        self.tmp.cleanup()

    def count(self, table):
        with self.db.read() as conn:
            return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    def test_session_uses_the_question_shown_and_persists_after_restart(self):
        session = self.svc.start("u1", "s1", {})
        reopened = build_services(SQLiteUnitOfWorkFactory(Database(self.settings.database_path)), self.ai)
        completed = reopened.practice.submit("u1", session.session_id, "令 u=x²+1")
        self.assertEqual(self.ai.reference, session.content.model_dump())
        self.assertEqual(self.ai.generations, 1)
        self.assertEqual(completed.evaluation_result.score, 8)
        self.assertEqual(reopened.records.list("u1")[0].score, 80)
        self.assertEqual(reopened.progress.all_mastery("u1").atomic_skills[0].mastery, .24)

    def test_duplicate_submit_is_idempotent(self):
        session = self.svc.start("u1", "s1", {})
        first = self.svc.submit("u1", session.session_id, "answer")
        second = self.svc.submit("u1", session.session_id, "answer")
        self.assertEqual(first, second)
        self.assertEqual(self.ai.evaluations, 1)
        self.assertEqual(self.count("practice_attempts"), 1)
        self.assertEqual(self.count("mastery_events"), 1)

    def test_completed_session_rejects_a_different_answer(self):
        session = self.svc.start("u1", "s1", {})
        self.svc.submit("u1", session.session_id, "first answer")
        with self.assertRaises(AppError) as error:
            self.svc.submit("u1", session.session_id, "a different answer")
        self.assertEqual(error.exception.status, 409)
        self.assertEqual(self.ai.evaluations, 1)

    def test_generation_and_evaluation_use_the_same_effective_params(self):
        self.skills.update("s1", SkillPatch(default_params={"difficulty": "进阶", "duration": "3分钟"}))
        with patch.object(self.ai, "generate_json", wraps=self.ai.generate_json) as generate:
            session = self.svc.start("u1", "s1", {"duration": "1分钟"})
            self.skills.update("s1", SkillPatch(default_params={"difficulty": "专家"}))
            self.svc.submit("u1", session.session_id, "answer")
        self.assertEqual(generate.call_args_list[0].args[1]["params"],
                         generate.call_args_list[1].args[1]["params"])

    def test_completed_session_can_be_recovered_after_lost_response(self):
        session = self.svc.start("u1", "s1", {})
        result = self.svc.submit("u1", session.session_id, "saved answer")
        status, recovered = self.request("GET", f'/api/v1/practice/sessions/{session.session_id}', query=b'user_id=u1')
        self.assertEqual(status, 200)
        self.assertEqual(recovered["data"]["answer"], "saved answer")
        self.assertEqual(recovered["data"]["evaluation_result"], result.evaluation_result.model_dump())
        record = self.records.list("u1")[0]
        self.assertEqual(record.atomic_skill_scores, {"a1": 8.0})
        self.assertEqual(record.atomic_skill_names, {"a1": "换元"})

    def test_future_manual_mastery_does_not_poison_future_submissions(self):
        with self.assertRaises(AppError):
            self.progress.update_mastery(MasteryRequest(user_id="u1", atomic_skill_id="a1", performance=.8, timestamp="2099-01-01T00:00:00Z"))
        self.assertEqual(self.count("mastery_events"), 0)

    def test_user_profile_reflects_new_practice_instead_of_only_legacy_data(self):
        session = self.svc.start("u1", "s1", {})
        self.svc.submit("u1", session.session_id, "answer")
        status, profile = self.request("GET", "/api/user/u1/profile")
        self.assertEqual(status, 200)
        self.assertEqual(profile["skills"]["s1"]["practice_count"], 1)
        self.assertEqual(profile["skills"]["s1"]["avg_score"], 80)

    def test_record_columns_are_canonical_even_if_old_payload_score_is_a_string(self):
        session = self.svc.start("u1", "s1", {})
        result = self.svc.submit("u1", session.session_id, "answer")
        with self.db.transaction() as conn:
            conn.execute("UPDATE practice_records SET payload_json=? WHERE record_id=?",
                         (dump({"score": "invalid legacy value"}), result.record_id))
        record = self.records.list("u1")[0]
        self.assertEqual(record.score, 80)
        self.assertEqual(record.record_id, result.record_id)

    def test_boolean_scores_and_empty_feedback_are_rejected(self):
        from app.application.content import validated
        from app.domain.models import Evaluation
        for changed in ({"score": True}, {"strengths": [" "]}):
            with self.subTest(changed=changed), self.assertRaises(AIError):
                validated(Evaluation, {**EVALUATION, **changed})

    def test_concurrent_submit_writes_once(self):
        session = self.svc.start("u1", "s1", {})
        self.ai.barrier = threading.Barrier(2)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.svc.submit("u1", session.session_id, "answer"), range(2)))
        self.assertEqual(results[0], results[1])
        self.assertEqual(self.count("practice_records"), 1)
        self.assertEqual(self.count("mastery_events"), 1)

    def test_ai_failure_does_not_write_grade_and_retry_succeeds(self):
        session = self.svc.start("u1", "s1", {})
        self.ai.failure = True
        with self.assertRaises(AIError):
            self.svc.submit("u1", session.session_id, "answer")
        for table in ("practice_records", "practice_attempts", "mastery_events", "user_atomic_scores"):
            self.assertEqual(self.count(table), 0)
        with self.work.read() as unit:
            self.assertEqual(unit.practices.get(session.session_id, "u1").status, "active")
        self.ai.failure = False
        self.svc.submit("u1", session.session_id, "answer")
        self.assertEqual(self.count("practice_records"), 1)

    def test_invalid_ai_scores_do_not_write(self):
        session = self.svc.start("u1", "s1", {})
        self.ai.bad_scores = True
        with self.assertRaises(AIError):
            self.svc.submit("u1", session.session_id, "answer")
        self.assertEqual(self.count("practice_attempts"), 0)

    def test_mid_transaction_failure_rolls_back_all_writes(self):
        session = self.svc.start("u1", "s1", {})
        with patch.object(ProgressRepository, "add_event", side_effect=RuntimeError("simulated disk failure")):
            with self.assertRaises(RuntimeError):
                self.svc.submit("u1", session.session_id, "answer")
        for table in ("practice_records", "practice_attempts", "user_atomic_scores", "mastery_events"):
            self.assertEqual(self.count(table), 0)
        with self.work.read() as unit:
            self.assertEqual(unit.practices.get(session.session_id, "u1").status, "active")

    def test_cannot_submit_other_users_session(self):
        session = self.svc.start("u1", "s1", {})
        with self.assertRaises(AppError) as error:
            self.svc.submit("u2", session.session_id, "answer")
        self.assertEqual(error.exception.status, 404)
        self.assertEqual(self.ai.evaluations, 0)

    def test_foreign_key_and_score_constraints(self):
        with self.assertRaises(sqlite3.IntegrityError):
            with self.db.transaction() as conn:
                conn.execute("INSERT INTO skill_atoms VALUES ('missing','a1',0)")
        with self.assertRaises(sqlite3.IntegrityError):
            with self.work.write() as unit:
                unit.users.ensure("u1")
                unit.progress.save_score("u1", "a1", 80, "2026-01-01T00:00:00+00:00", "test")
        self.assertEqual(self.count("users"), 0)

    def test_atomic_mapping_failure_preserves_skill(self):
        with self.assertRaises(AppError):
            self.skills.update("s1", SkillPatch(description="changed", atomic_skills=["missing"]))
        self.assertEqual(self.skills.get("s1").description, SKILL["description"])

    def test_delete_skill_retains_history_and_snapshot(self):
        session = self.svc.start("u1", "s1", {})
        self.skills.delete("s1")
        self.assertEqual(self.skills.list(), [])
        self.svc.submit("u1", session.session_id, "answer")
        self.assertEqual(len(self.records.list("u1")), 1)
        with self.assertRaises(AppError):
            self.svc.start("u1", "s1", {})

    def test_soft_delete_record_does_not_destroy_learning_evidence(self):
        session = self.svc.start("u1", "s1", {})
        result = self.svc.submit("u1", session.session_id, "answer")
        with self.assertRaises(AppError):
            self.records.delete("u2", result.record_id)
        self.records.delete("u1", result.record_id)
        self.assertEqual(self.records.list("u1"), [])
        self.assertEqual(self.count("mastery_events"), 1)

    def test_migration_is_once_only_and_archives_original(self):
        original = (self.legacy / "skill_library.json").read_bytes()
        report = migrate_legacy(self.db, self.legacy)
        self.assertEqual(self.count("skills"), 1)
        self.assertEqual(self.count("legacy_imports"), 2)
        self.assertEqual((self.legacy / "skill_library.json").read_bytes(), original)
        self.assertTrue(Path(report["backup"]).is_dir())

    def test_migration_merges_both_record_directories_and_replays_scale(self):
        second = self.root / "second.sqlite3"
        db = Database(second)
        db.initialize()
        record = {"user_id": "u1", "skill_id": "s1", "score": 80, "transcript": "answer", "record_id": "r1"}
        (self.legacy / "practice_records.json").write_text(dump([record]), encoding="utf-8")
        nested = self.root / "backend" / "data"
        nested.mkdir(parents=True)
        (nested / "practice_records.json").write_text(dump([record, {**record, "record_id": "r2", "transcript": "different"}]), encoding="utf-8")
        (self.legacy / "knowledge_tracing.json").write_text(dump({"users": {"u1": {"atomic_skills": {"a1": {
            "mastery": 1.0, "history": [{"timestamp": "2026-01-01 12:00:00", "performance": 8, "mastery": 1.0}]}}}}}), encoding="utf-8")
        report = migrate_legacy(db, self.legacy)
        self.assertEqual(len(build_services(SQLiteUnitOfWorkFactory(db), self.ai).records.list("u1")), 2)
        self.assertEqual(build_services(SQLiteUnitOfWorkFactory(db), self.ai).progress.all_mastery("u1").atomic_skills[0].mastery, .24)
        self.assertTrue(any("Normalized" in x for x in report["warnings"]))

    def test_corrupt_migration_is_not_silently_reset(self):
        db = Database(self.root / "bad.sqlite3")
        db.initialize()
        (self.legacy / "practice_records.json").write_text("broken", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            migrate_legacy(db, self.legacy)
        with db.read() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM skills").fetchone()[0], 0)

    def test_migration_constraint_failure_rolls_back_whole_import(self):
        db = Database(self.root / "bad2.sqlite3")
        db.initialize()
        (self.legacy / "user_atomic_scores.json").write_text(dump({"u1": {"a1": 800}}), encoding="utf-8")
        with self.assertRaises(sqlite3.IntegrityError):
            migrate_legacy(db, self.legacy)
        with db.read() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM skills").fetchone()[0], 0)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM migration_reports").fetchone()[0], 0)

    def test_unconfigured_ai_starts_but_generation_is_explicit_failure(self):
        client = OpenAIJSONClient(self.settings)
        with self.assertRaises(AIError) as result:
            client.generate_json("task", {})
        self.assertEqual(result.exception.status, 503)
        self.assertEqual(result.exception.code, "ai_not_configured")

    def test_api_transport_responses_and_chat_preserve_multiline_json(self):
        raw = json.dumps(CONTENT, ensure_ascii=False, indent=2)
        response = SimpleNamespace(output_text=raw, status="completed")
        completion = SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content=raw))])
        def compatible_responses_gateway(**request):
            # The real compatible provider rejected JSON mode when only the
            # instructions field mentioned JSON and the input did not.
            if "json" not in request["input"].lower():
                raise ValueError("Response input messages must contain the word json")
            return response
        for style in ("responses", "chat_completions"):
            with self.subTest(style=style), patch("openai.OpenAI") as factory:
                sdk = factory.return_value.__enter__.return_value
                sdk.responses.create.side_effect = compatible_responses_gateway
                sdk.chat.completions.create.return_value = completion
                settings = replace(self.settings, ai_api_key="test", ai_model="test", ai_api_style=style)
                self.assertEqual(OpenAIJSONClient(settings).generate_json("task", {}), CONTENT)
                factory.assert_called_once()

    async def _request(self, method, path, body=None, query=b"", ai=None):
        app = create_app(self.settings, ai=ai or self.ai)
        messages = []
        sent = False

        async def receive():
            nonlocal sent
            if not sent:
                sent = True
                return {"type": "http.request", "body": json.dumps(body).encode() if body is not None else b"", "more_body": False}
            return {"type": "http.disconnect"}

        async def send(message):
            messages.append(message)

        scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": method,
                 "scheme": "http", "path": path, "raw_path": path.encode(), "query_string": query,
                 "headers": [(b"content-type", b"application/json")], "client": ("127.0.0.1", 1234), "server": ("127.0.0.1", 8001)}
        async with app.router.lifespan_context(app):
            await app(scope, receive, send)
        status = next(m["status"] for m in messages if m["type"] == "http.response.start")
        value = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
        return status, json.loads(value)

    def request(self, *args, **kwargs):
        return asyncio.run(self._request(*args, **kwargs))

    def test_http_full_flow(self):
        status, data = self.request("POST", "/api/v1/practice/start", {"user_id": "u1", "skill_id": "s1"})
        self.assertEqual(status, 201)
        session_id = data["data"]["session_id"]
        status, data = self.request("POST", "/api/v1/practice/submit", {"user_id": "u1", "session_id": session_id, "answer": "answer"})
        self.assertEqual(status, 200)
        status, data = self.request("GET", "/api/practice/records/u1")
        self.assertEqual(data["records"][0]["score"], 80)

    def test_http_boundaries_errors_and_missing_configuration(self):
        status, health = self.request("GET", "/api/health", ai=OpenAIJSONClient(self.settings))
        self.assertEqual(status, 200)
        self.assertFalse(health["ai_configured"])
        status, error = self.request("POST", "/api/v1/practice/start", {"user_id": "u1", "skill_id": "s1"}, ai=OpenAIJSONClient(self.settings))
        self.assertEqual((status, error["code"]), (503, "ai_not_configured"))
        status, _ = self.request("POST", "/api/v1/practice/submit", {"user_id": "u1", "session_id": "x", "answer": "  "})
        self.assertEqual(status, 422)
        status, _ = self.request("POST", "/api/v1/knowledge-tracing/update-mastery", {"user_id": "u1", "atomic_skill_id": "a1", "performance": 8})
        self.assertEqual(status, 422)
        status, _ = self.request("POST", "/api/practice/record", {"score": 100})
        self.assertEqual(status, 410)
        status, _ = self.request("GET", "/api/v1/skills/missing")
        self.assertEqual(status, 404)

    def test_http_skill_crud_and_atomic_mapping(self):
        status, created = self.request("POST", "/api/v1/skills", {"name": "test", "display_name": "Test", "description": "Test skill", "atomic_skills": ["a1"]})
        self.assertEqual(status, 201)
        sid = created["skill"]["skill_id"]
        self.assertEqual(self.request("PATCH", f"/api/v1/skills/{sid}", {"enabled": False})[0], 200)
        self.assertEqual(self.request("PATCH", f"/api/v1/skills/{sid}", {"enabled": None})[0], 422)
        status, _ = self.request("POST", "/api/v1/skills", {"name": "test", "display_name": "Test", "description": "Test skill"})
        self.assertEqual(status, 409)
        self.assertEqual(self.request("DELETE", f"/api/skills/{sid}")[0], 200)

    def proposal(self):
        return {"description": "微积分中的换元积分训练", "generate_prompt": "生成换元积分题",
                "evaluate_prompt": "检查换元与积分限", "default_params": {}, "atomic_skills": [
                    {"name": name, "description": "能独立完成" + name, "categories": ["高数"]}
                    for name in ("识别复合函数", "变换微分", "转换积分限")]}

    def test_custom_skill_and_all_atom_relations_are_saved_together(self):
        with patch.object(self.ai, "generate_json", return_value=self.proposal()):
            status, result = self.request("POST", "/api/skills/custom", {"skill_name": "换元积分"})
        self.assertEqual(status, 201)
        self.assertEqual(len(result["skill"]["atomic_skills"]), 3)
        self.assertEqual(self.count("atomic_skills"), 4)
        self.assertEqual(self.count("skill_atoms"), 4)

    def test_custom_skill_failure_rolls_back_new_atoms(self):
        with patch.object(self.ai, "generate_json", return_value=self.proposal()), \
                patch.object(SkillRepository, "add", side_effect=RuntimeError("simulated write failure")):
            with self.assertRaises(RuntimeError):
                self.skills.custom("换元积分")
        self.assertEqual(self.count("atomic_skills"), 1)
        self.assertEqual(self.count("skills"), 1)

    def test_invalid_model_json_is_not_an_accepted_grade(self):
        with patch("openai.OpenAI") as factory:
            sdk = factory.return_value.__enter__.return_value
            sdk.responses.create.return_value = SimpleNamespace(output_text="not json", status="completed")
            settings = replace(self.settings, ai_api_key="test", ai_model="test")
            with self.assertRaises(AIError):
                OpenAIJSONClient(settings).generate_json("task", {})

    def test_manual_score_is_separate_from_mastery_and_checks_path_identity(self):
        path = "/api/v1/atomic/users/u1/skills/a1/score"
        body = {"user_id": "u1", "atomic_skill_id": "a1", "score": 6}
        self.assertEqual(self.request("POST", path, {**body, "user_id": "u2"})[0], 422)
        self.assertEqual(self.count("users"), 0)
        status, result = self.request("POST", path, body)
        self.assertEqual((status, result["source"]), (200, "manual"))
        self.assertEqual(self.request("GET", path)[1]["score"], 6)
        self.assertEqual(self.count("mastery_events"), 0)

    def test_manual_mastery_rejects_out_of_order_evidence_without_partial_write(self):
        path = "/api/v1/knowledge-tracing/update-mastery"
        body = {"user_id": "u1", "atomic_skill_id": "a1", "performance": .8,
                "timestamp": "2020-02-01T00:00:00Z"}
        self.assertEqual(self.request("POST", path, body)[0], 200)
        status, error = self.request("POST", path, {**body, "timestamp": "2020-01-01T00:00:00Z"})
        self.assertEqual((status, error["code"]), (409, "out_of_order_event"))
        self.assertEqual(self.count("mastery_events"), 1)

    def test_read_scope_rejects_writes(self):
        with self.assertRaises(sqlite3.OperationalError):
            with self.work.read() as unit:
                unit.users.ensure("must-not-be-created")
        self.assertEqual(self.count("users"), 0)

    def test_model_calls_have_no_open_unit_of_work(self):
        class TrackedWork:
            scopes = 0

            @contextmanager
            def read(inner):
                with self.work.read() as unit:
                    inner.scopes += 1
                    try:
                        yield unit
                    finally:
                        inner.scopes -= 1

            @contextmanager
            def write(inner):
                with self.work.write() as unit:
                    inner.scopes += 1
                    try:
                        yield unit
                    finally:
                        inner.scopes -= 1

        tracked = TrackedWork()
        services = build_services(tracked, self.ai)
        original = self.ai.generate_json

        def generate(task, payload):
            self.assertEqual(tracked.scopes, 0)
            return original(task, payload)

        with patch.object(self.ai, "generate_json", side_effect=generate):
            session = services.practice.start("u1", "s1", {})
            services.practice.submit("u1", session.session_id, "answer")

    def test_skill_deleted_during_generation_cannot_create_a_session(self):
        def generate(task, payload):
            self.skills.delete("s1")
            return dict(CONTENT)

        with patch.object(self.ai, "generate_json", side_effect=generate), self.assertRaises(AppError):
            self.svc.start("u1", "s1", {})
        self.assertEqual(self.count("practice_sessions"), 0)
        self.assertEqual(self.count("users"), 0)

    def test_all_learning_read_routes_keep_their_response_contracts(self):
        session = self.svc.start("u1", "s1", {})
        self.svc.submit("u1", session.session_id, "answer")
        cases = {
            "/api/v1/practice/history/u1": ("history",),
            "/api/v1/practice/progress/u1/s1": ("practice_count", "avg_score", "score_scale"),
            "/api/v1/atomic/users/u1/skills": ("user_id", "atomic_skills"),
            "/api/v1/atomic/skills/s1/mapping": ("skill_id", "skill_name", "atomic_skills"),
            "/api/v1/knowledge-tracing/mastery/all/u1": ("error", "msg", "data"),
            "/api/v1/knowledge-tracing/mastery/u1/a1": ("data",),
            "/api/v1/knowledge-tracing/predict/u1/a1": ("data",),
            "/api/v1/knowledge-tracing/learning-curve/u1/a1": ("data",),
            "/api/v1/knowledge-tracing/recommendations/u1": ("data",),
        }
        for path, keys in cases.items():
            with self.subTest(path=path):
                status, data = self.request("GET", path)
                self.assertEqual(status, 200)
                self.assertTrue(all(key in data for key in keys))

    def test_preview_evaluation_never_writes_learning_evidence(self):
        status, value = self.request("POST", "/api/v1/practice/evaluate",
            {"skill_id": "s1", "content": "answer", "reference": "question"})
        self.assertEqual((status, value["evaluation"]["score"]), (200, 8))
        for table in ("practice_sessions", "practice_attempts", "practice_records", "mastery_events"):
            self.assertEqual(self.count(table), 0)

    def test_optimization_validates_output_and_does_not_write_scores(self):
        body = {"user_id": "u1", "atomic_skill_ids": ["a1"], "optimization_goal": "积分"}
        with patch.object(self.ai, "generate_json", return_value={"optimization_advice": "先确定换元，再检查积分限。"}):
            status, value = self.request("POST", "/api/v1/atomic/optimize", body)
        self.assertEqual(status, 200)
        self.assertEqual(value["targeted_skills"][0]["atomic_skill_id"], "a1")
        with patch.object(self.ai, "generate_json", return_value={"optimization_advice": " "}):
            self.assertEqual(self.request("POST", "/api/v1/atomic/optimize", body)[0], 502)
        self.assertEqual(self.count("user_atomic_scores"), 0)
        self.assertEqual(self.count("mastery_events"), 0)

    def test_partial_legacy_session_remains_readable_without_fabricated_grade(self):
        with self.db.transaction() as conn:
            conn.execute("INSERT INTO users VALUES ('u1','2020-01-01T00:00:00Z')")
            conn.execute("""INSERT INTO practice_sessions
                (session_id,user_id,skill_id,content_json,skill_snapshot_json,status,started_at,result_json,provenance)
                VALUES (?,?,?,?,?,'completed',?,?,'legacy')""", ("old-session", "u1", "s1",
                dump({"title": "old", "description": "", "example_answer": "", "difficulty": 9}),
                dump(SKILL), "2020-01-01T00:00:00Z", dump({"historical_note": "unstructured"})))
        status, value = self.request("GET", "/api/v1/practice/sessions/old-session", query=b"user_id=u1")
        self.assertEqual(status, 200)
        self.assertEqual(value["data"]["content"]["difficulty"], 9)
        self.assertEqual(value["data"]["evaluation_result"], {"historical_note": "unstructured"})
        self.assertIsNone(value["data"]["record_id"])
        self.assertEqual(self.count("practice_records"), 0)

    def test_legacy_record_extra_fields_and_numeric_difficulty_survive(self):
        session = self.svc.start("u1", "s1", {})
        result = self.svc.submit("u1", session.session_id, "answer")
        with self.db.transaction() as conn:
            conn.execute("UPDATE practice_records SET payload_json=? WHERE record_id=?", (
                dump({"difficulty": 9, "legacy_annotation": {"source": "original"}}), result.record_id))
        status, data = self.request("GET", "/api/practice/records/u1")
        self.assertEqual(status, 200)
        self.assertEqual(data["records"][0]["difficulty"], 9)
        self.assertEqual(data["records"][0]["legacy_annotation"], {"source": "original"})


if __name__ == "__main__":
    unittest.main()
