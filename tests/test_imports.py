"""Import smoke test: every module under src/ must import cleanly.

Each module is imported in a fresh Python process, so a module cannot pass just because
another module happened to import one of its dependencies first. A module must also be
silent on import (no print output) and must not exit during import (e.g. by reading
sys.argv at module level and calling sys.exit()).

Only Python-level output is checked: compiled third-party code may write to stdout
directly (importing pcraster.framework prints an empty line from C), which is outside
our control.
"""

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

SRC_DIR = pathlib.Path(__file__).resolve().parents[1] / "src"
IMPORT_SCRIPT = """
import contextlib, importlib, io, json, sys
captured = io.StringIO()
with contextlib.redirect_stdout(captured):
    importlib.import_module(sys.argv[1])
sys.stderr.write("\\n" + json.dumps({"imported": True, "stdout": captured.getvalue()}))
"""


def discover_modules() -> list[str]:
    modules = []
    for path in sorted(SRC_DIR.rglob("*.py")):
        parts = path.relative_to(SRC_DIR).with_suffix("").parts
        if parts[-1] == "__init__":
            parts = parts[:-1]
        modules.append(".".join(parts))
    return modules


MODULES = discover_modules()


class TestImports(unittest.TestCase):
    def test_modules_are_discovered(self) -> None:
        self.assertLessEqual({"pcrglobwb", "qualloc"}, set(MODULES))

    def test_modules_import_cleanly(self) -> None:
        for module in MODULES:
            with self.subTest(module=module):
                self.assert_imports_cleanly(module)

    def assert_imports_cleanly(self, module: str) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = subprocess.run(
                [sys.executable, "-c", IMPORT_SCRIPT, module],
                cwd=tmp_dir,
                capture_output=True,
                text=True,
                timeout=300,
            )
        *stderr_lines, last_line = result.stderr.rstrip("\n").split("\n")
        stderr = "\n".join(stderr_lines).strip()

        self.assertEqual(
            result.returncode, 0, f"import of {module} failed:\n{result.stderr}"
        )
        self.assertTrue(
            last_line.startswith('{"imported"'),
            f"{module} exits during import:\n{stderr}",
        )
        captured = json.loads(last_line)["stdout"]
        self.assertEqual(captured, "", f"{module} prints on import:\n{captured}")


if __name__ == "__main__":
    unittest.main()
