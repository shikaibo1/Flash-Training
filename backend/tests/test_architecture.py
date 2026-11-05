"""Guard dependency direction and published contracts as the project grows."""
import ast
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
import unittest
from fastapi.routing import APIRoute
from app.application.skills import SkillService
from app.domain.models import Skill
from app.main import create_app
from app.settings import Settings

APP = Path(__file__).resolve().parents[1] / "app"


class ArchitectureTests(unittest.TestCase):
    def test_domain_and_application_do_not_depend_on_infrastructure_or_http(self):
        banned = {"sqlite3", "fastapi", "openai", "infrastructure", "api"}
        for folder in ("domain", "application"):
            for path in (APP / folder).rglob("*.py"):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    modules = []
                    if isinstance(node, ast.Import):
                        modules = [alias.name for alias in node.names]
                    elif isinstance(node, ast.ImportFrom):
                        modules = [node.module or ""]
                    for module in modules:
                        self.assertFalse(set(module.split(".")) & banned, f"Dependency leak in {path}: {module}")
                    if isinstance(node, ast.Attribute):
                        self.assertNotIn(node.attr, {"execute", "executemany", "connect", "commit", "rollback"}, str(path))

    def test_routes_delegate_without_sql_repositories_or_transaction_scopes(self):
        for path in (APP / "api").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute):
                    self.assertNotIn(node.attr, {"repo", "db", "read", "write", "transaction", "execute",
                        "generate_json", "connect", "commit", "rollback"}, str(path))
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn("infrastructure", (node.module or "").split("."), str(path))
            self.assertFalse(any(isinstance(n, (ast.With, ast.AsyncWith)) for n in ast.walk(tree)), str(path))

    def test_every_http_route_publishes_a_response_schema(self):
        app = create_app(Settings())
        for route in app.routes:
            if isinstance(route, APIRoute):
                self.assertIsNotNone(route.response_model, route.path)
        document = app.openapi()
        for path, methods in document["paths"].items():
            for operation in methods.values():
                for code, response in operation["responses"].items():
                    if code.startswith("2"):
                        self.assertTrue(response["content"]["application/json"]["schema"], path)

    def test_skill_service_can_run_without_sqlite_or_model_sdk(self):
        expected = Skill(skill_id="s1", name="calculus", display_name="Calculus", description="Integrals")

        class InMemoryWork:
            @contextmanager
            def read(self):
                yield SimpleNamespace(skills=SimpleNamespace(get=lambda _: expected))

        service = SkillService(InMemoryWork(), content=None)
        self.assertEqual(service.get("s1"), expected)
