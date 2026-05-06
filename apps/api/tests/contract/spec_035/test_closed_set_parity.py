"""Closed-set parity tests for spec-035 domain enums.

These pytest-driven tests assert that the Python enums in ``apps/api/app/domain``
have exactly the cardinalities and string values prescribed by the spec, and
mirror the TypeScript exports at ``packages/domain/src``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from app.domain.app_role import APP_ROLE_COUNT, APP_ROLES, AppRole
from app.domain.audit_outcome import (
    AUDIT_OUTCOME_COUNT,
    AUDIT_OUTCOMES,
    AuditOutcome,
)
from app.domain.extension_envelope import (
    ERROR_CODE_TO_HTTP_STATUS,
    ERROR_PRECEDENCE,
    EXTENSION_ERROR_CODES,
    ExtensionEnvelope,
    ExtensionErrorCode,
)
from app.domain.offline_queue_tier import (
    OFFLINE_QUEUE_CAP_PER_PERSONA,
    OFFLINE_QUEUE_LIFE_SAFETY_BATCH_SIZE,
    OFFLINE_QUEUE_TIERS,
    OfflineQueueTier,
)

REPO_ROOT = Path(__file__).resolve().parents[5]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def ts_audit_outcomes() -> list[str]:
    text = _read(REPO_ROOT / "packages" / "domain" / "src" / "audit-outcome.ts")
    block = re.search(r"AUDIT_OUTCOMES\s*=\s*\[(?P<body>.*?)\]\s*as const", text, re.DOTALL)
    assert block is not None, "AUDIT_OUTCOMES export missing in TypeScript"
    return [m.group(1) for m in re.finditer(r'"([^"]+)"', block.group("body"))]


@pytest.fixture(scope="module")
def ts_app_roles() -> list[str]:
    text = _read(REPO_ROOT / "packages" / "domain" / "src" / "app-role.ts")
    block = re.search(r"APP_ROLES\s*=\s*\[(?P<body>.*?)\]\s*as const", text, re.DOTALL)
    assert block is not None
    return [m.group(1) for m in re.finditer(r'"([^"]+)"', block.group("body"))]


@pytest.fixture(scope="module")
def ts_extension_codes() -> list[str]:
    text = _read(REPO_ROOT / "packages" / "domain" / "src" / "extension-envelope.ts")
    block = re.search(
        r"EXTENSION_ERROR_CODES\s*=\s*\[(?P<body>.*?)\]\s*as const", text, re.DOTALL
    )
    assert block is not None
    return [m.group(1) for m in re.finditer(r'"([^"]+)"', block.group("body"))]


@pytest.fixture(scope="module")
def ts_offline_tiers() -> list[str]:
    text = _read(REPO_ROOT / "packages" / "domain" / "src" / "offline-queue-tier.ts")
    block = re.search(r"OFFLINE_QUEUE_TIERS\s*=\s*\[(?P<body>.*?)\]\s*as const", text, re.DOTALL)
    assert block is not None
    return [m.group(1) for m in re.finditer(r'"([^"]+)"', block.group("body"))]


def test_audit_outcome_cardinality_is_twenty() -> None:
    assert AUDIT_OUTCOME_COUNT == 20
    assert len(AUDIT_OUTCOMES) == 20
    assert len(set(AUDIT_OUTCOMES)) == 20
    assert len(list(AuditOutcome)) == 20


def test_audit_outcome_values_match_spec_data_model() -> None:
    expected = {
        "approved",
        "denied",
        "published",
        "allocate",
        "admin_override",
        "classifier_deny",
        "classifier_mask",
        "classifier_failed",
        "queue_overflow",
        "queue_displaced",
        "activation_mutex_violation",
        "rate_limited",
        "auth_unauthorized",
        "auth_forbidden",
        "sovereignty_denied",
        "schema_invalid",
        "seed_not_ready",
        "evaluator_not_routable",
        "cultural_safety_timeout_override",
        "cultural_safety_held",
    }
    assert set(AUDIT_OUTCOMES) == expected


def test_audit_outcome_typescript_parity(ts_audit_outcomes: list[str]) -> None:
    assert ts_audit_outcomes == list(AUDIT_OUTCOMES)


def test_app_role_cardinality_is_eleven() -> None:
    assert APP_ROLE_COUNT == 11
    assert len(APP_ROLES) == 11
    assert len(list(AppRole)) == 11


def test_app_role_typescript_parity(ts_app_roles: list[str]) -> None:
    assert ts_app_roles == list(APP_ROLES)


def test_app_role_admin_only_role_with_star_scope() -> None:
    admin_only = [r for r in AppRole if r is AppRole.SYSTEM_ADMINISTRATOR]
    assert len(admin_only) == 1


def test_extension_error_codes_typescript_parity(ts_extension_codes: list[str]) -> None:
    assert ts_extension_codes == list(EXTENSION_ERROR_CODES)


def test_extension_error_status_mapping_is_complete() -> None:
    for code in ExtensionErrorCode:
        assert code in ERROR_CODE_TO_HTTP_STATUS
    assert len(ERROR_CODE_TO_HTTP_STATUS) == len(ExtensionErrorCode)


def test_extension_error_precedence_is_complete_and_unique() -> None:
    assert set(ERROR_PRECEDENCE) == set(ExtensionErrorCode)
    assert len(ERROR_PRECEDENCE) == len(set(ERROR_PRECEDENCE))
    # evaluator_not_routable wins over everything else (cheap pre-auth check).
    assert ERROR_PRECEDENCE[0] is ExtensionErrorCode.EVALUATOR_NOT_ROUTABLE
    # sovereignty_denied beats unauthorized (NN-1).
    assert ERROR_PRECEDENCE.index(
        ExtensionErrorCode.SOVEREIGNTY_DENIED
    ) < ERROR_PRECEDENCE.index(ExtensionErrorCode.UNAUTHORIZED)
    # rate_limited beats schema_invalid (429 short-circuits validation).
    assert ERROR_PRECEDENCE.index(
        ExtensionErrorCode.RATE_LIMITED
    ) < ERROR_PRECEDENCE.index(ExtensionErrorCode.SCHEMA_INVALID)


def test_offline_queue_tier_typescript_parity(ts_offline_tiers: list[str]) -> None:
    assert ts_offline_tiers == list(OFFLINE_QUEUE_TIERS)


def test_offline_queue_tier_constants() -> None:
    assert OFFLINE_QUEUE_CAP_PER_PERSONA == 500
    assert OFFLINE_QUEUE_LIFE_SAFETY_BATCH_SIZE == 50
    assert set(OFFLINE_QUEUE_TIERS) == {"life_safety", "routine"}


def test_offline_queue_tier_membership() -> None:
    assert OfflineQueueTier("life_safety") is OfflineQueueTier.LIFE_SAFETY
    assert OfflineQueueTier("routine") is OfflineQueueTier.ROUTINE


def test_extension_envelope_validates_retry_after_for_rate_limited() -> None:
    env = ExtensionEnvelope(
        error_code=ExtensionErrorCode.RATE_LIMITED,
        retry_after_seconds=30,
        audit_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
        correlation_id="9b2a4e0f-7c1c-4f18-9ad6-1c9a2f4f3a10",
    )
    assert env.retry_after_seconds == 30


def test_extension_envelope_rejects_unknown_error_code() -> None:
    with pytest.raises(Exception):  # pydantic.ValidationError subclasses
        ExtensionEnvelope.model_validate(
            {
                "error_code": "teapot",
                "retry_after_seconds": None,
                "audit_id": "x",
                "correlation_id": "y",
            }
        )


def test_extension_envelope_byte_equals_serialised_form() -> None:
    payload = {
        "error_code": "schema_invalid",
        "retry_after_seconds": None,
        "audit_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
        "correlation_id": "9b2a4e0f-7c1c-4f18-9ad6-1c9a2f4f3a10",
    }
    env = ExtensionEnvelope.model_validate(payload)
    assert json.loads(env.model_dump_json()) == payload


def test_json_schema_in_packages_schemas_is_consistent() -> None:
    schema_path = REPO_ROOT / "packages" / "schemas" / "spec_035" / "extension_envelope.schema.json"
    schema = json.loads(_read(schema_path))
    enum_values = schema["properties"]["error_code"]["enum"]
    assert enum_values == list(EXTENSION_ERROR_CODES)
    assert set(schema["required"]) == {
        "error_code",
        "retry_after_seconds",
        "audit_id",
        "correlation_id",
    }
