import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "src/api/authorization"


class AuthorizationStructureTests(unittest.TestCase):
    component = COMPONENT
    dao_names = {"AppUserDAO", "DeviceDAO", "DeviceTokenDAO"}

    def test_cases_have_no_runtime_sqlalchemy_or_direct_session_operations(self):
        for path in (self.component / "application").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            type_imports = {
                id(node)
                for block in tree.body
                if isinstance(block, ast.If) and isinstance(block.test, ast.Name)
                and block.test.id == "TYPE_CHECKING"
                for node in block.body
            }
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    if module.startswith(("sqlalchemy", "fastapi")):
                        self.assertIn(id(node), type_imports, str(path))
                        self.assertEqual(module, "sqlalchemy.ext.asyncio")
                        self.assertEqual([name.name for name in node.names], ["AsyncSession"])
                if isinstance(node, ast.Import):
                    self.assertFalse(any(
                        name.name.startswith(("sqlalchemy", "fastapi")) for name in node.names
                    ), str(path))
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    owner = node.func.value
                    self.assertFalse(
                        isinstance(owner, ast.Name) and owner.id == "db",
                        f"Direct session access in {path}:{node.lineno}",
                    )

    def test_infrastructure_has_only_endpoints_and_router_configuration(self):
        for path in (self.component / "infrastructure").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign, ast.TypeAlias)):
                    continue
                self.assertIsInstance(node, ast.AsyncFunctionDef, str(path))
                self.assertTrue(any(
                    isinstance(decorator, ast.Call)
                    and isinstance(decorator.func, ast.Attribute)
                    and isinstance(decorator.func.value, ast.Name)
                    and decorator.func.value.id == "router"
                    for decorator in node.decorator_list
                ), f"Helper in infrastructure: {path}:{node.lineno}")
                self.assertFalse(any(
                    isinstance(annotation, ast.Name) and annotation.id == "Request"
                    for annotation in ast.walk(node.args)
                ))

    def test_repository_uses_derived_daos_without_top_level_data_functions(self):
        path = self.component / "repository/dao.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]

        self.assertEqual({node.name for node in classes}, self.dao_names)
        self.assertFalse(any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) for node in tree.body))
        for node in classes:
            self.assertTrue(any(
                isinstance(base, ast.Subscript) and isinstance(base.value, ast.Name)
                and base.value.id == "DAO" for base in node.bases
            ), node.name)

    def test_domain_has_no_provider_code_or_direct_pydantic_base(self):
        for path in (self.component / "domain").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            self.assertFalse(any(
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) for node in tree.body
            ), str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    self.assertFalse((node.module or "").startswith(("fastapi", "sqlalchemy", "httpx", "jwt")))
                    if node.module == "pydantic":
                        self.assertNotIn("BaseModel", [name.name for name in node.names])

    def test_component_does_not_import_other_component_repositories(self):
        for path in self.component.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                modules = []
                if isinstance(node, ast.ImportFrom):
                    modules = [node.module or ""]
                elif isinstance(node, ast.Import):
                    modules = [name.name for name in node.names]
                for module in modules:
                    parts = module.split(".")
                    if parts[:2] == ["src", "api"] and "repository" in parts:
                        self.assertEqual(parts[2], self.component.name, f"Foreign repository in {path}")


if __name__ == "__main__":
    unittest.main()
