"""Schema validator helpers for spec-034 artefacts.

Wraps ``jsonschema`` so the gap-register / trace-merge / review-log CLIs share
one validation surface against the contracts under
``specs/034-webapp-capstone-coverage/contracts/``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:  # Optional import — CLI scripts gracefully degrade if jsonschema absent.
    from jsonschema import Draft202012Validator  # type: ignore[import-not-found]
    _HAS_JSONSCHEMA = True
except ImportError:  # pragma: no cover - validated by CI
    Draft202012Validator = None  # type: ignore[assignment]
    _HAS_JSONSCHEMA = False


CONTRACTS_DIR = (
    Path(__file__).resolve().parents[3]
    / "specs"
    / "034-webapp-capstone-coverage"
    / "contracts"
)


def load_schema(name: str) -> dict[str, Any]:
    """Load a schema by short name (e.g., ``"gap-register-entry"``)."""

    path = CONTRACTS_DIR / f"{name}.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


def validate_or_raise(name: str, instance: Any) -> None:
    """Validate ``instance`` against the named schema, raising on error.

    Falls back to a no-op when ``jsonschema`` is unavailable; CI installs it.
    """

    if not _HAS_JSONSCHEMA or Draft202012Validator is None:  # pragma: no cover
        return
    schema = load_schema(name)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    if errors:
        details = "; ".join(f"{list(e.path)}: {e.message}" for e in errors)
        raise ValueError(f"schema '{name}' failed: {details}")
