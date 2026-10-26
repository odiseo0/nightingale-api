import ast
import importlib.util
import inspect
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from pydantic import BaseModel as PydanticModel

from src.core.schema import BaseModel, PageQuery, PaginatedResponse


ROOT = Path(__file__).resolve().parents[1]


class ProjectStructureTests(unittest.TestCase):
    def test_retired_modules_have_no_sources_or_imports(self):
        for name in ("src/cli.py", "src/core/cursors.py", "src/settings/cursor_settings.py"):
            self.assertFalse((ROOT / name).exists(), name)
        self.assertEqual(list((ROOT / "src/api/access").rglob("*.py")), [])

        retired = ("src.cli", "src.core.cursors", "src.settings.cursor_settings", "src.api.access")
        for path in (ROOT / "src").rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                modules = []
                if isinstance(node, ast.ImportFrom):
                    modules = [node.module or ""]
                elif isinstance(node, ast.Import):
                    modules = [name.name for name in node.names]
                for module in modules:
                    self.assertFalse(any(
                        module == prefix or module.startswith(prefix + ".") for prefix in retired
                    ), f"Retired import in {path}")
                    self.assertFalse(module == "scripts" or module.startswith("scripts."), str(path))

    def test_data_schemas_inherit_the_project_base_and_its_aliases(self):
        files = list((ROOT / "src/api").glob("*/domain/*.py"))
        files.append(ROOT / "src/core/schema/http.py")
        checked = 0
        for path in files:
            if path.name == "__init__.py":
                continue
            module_name = ".".join(path.relative_to(ROOT).with_suffix("").parts)
            # Read the schema file without starting a component through its __init__.
            spec = importlib.util.spec_from_file_location(module_name, path)
            module = importlib.util.module_from_spec(spec)
            with patch.dict(sys.modules, {module_name: module}):
                spec.loader.exec_module(module)
            for value in vars(module).values():
                if (
                    inspect.isclass(value) and value.__module__ == module_name
                    and issubclass(value, PydanticModel)
                ):
                    self.assertTrue(issubclass(value, BaseModel), value.__name__)
                    self.assertIs(value.model_config.get("alias_generator"), BaseModel.model_config["alias_generator"])
                    checked += 1
        self.assertGreater(checked, 0)

    def test_shared_pagination_has_only_page_shows_items_and_total(self):
        self.assertEqual(set(PageQuery.model_fields), {"page", "shows"})
        self.assertEqual(set(PaginatedResponse.model_fields), {"items", "total"})
        settings = ROOT / "src/settings"
        for path in settings.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            self.assertFalse(any(
                isinstance(node, ast.Constant) and node.value == "CURSOR_"
                for node in ast.walk(tree)
            ), str(path))


if __name__ == "__main__":
    unittest.main()
