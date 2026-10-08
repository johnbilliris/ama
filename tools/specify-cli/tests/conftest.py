from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PACKAGE_ROOT / "src"
FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures"

sys.path.insert(0, str(SOURCE_ROOT))


def load_fixture_builder(relative_path: str, module_name: str) -> ModuleType:
    fixture_path = (FIXTURES_ROOT / relative_path).resolve(strict=True)
    if FIXTURES_ROOT.resolve() not in fixture_path.parents or fixture_path.suffix != ".py":
        raise ValueError("fixture builder must be a Python file beneath tests/fixtures")

    spec = importlib.util.spec_from_file_location(module_name, fixture_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load fixture builder: {relative_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
