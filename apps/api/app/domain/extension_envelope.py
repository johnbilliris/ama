"""Spec-035 production-auth extension envelope (Q10 / FR-009).

Pydantic v2 model + helpers for the error envelope returned by every
production-reachable endpoint. Mirrors ``packages/domain/src/extension-envelope.ts``.

Source: ``specs/035-webapp-capstone-closure/contracts/production-auth-extension.contract.md``.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final

from pydantic import BaseModel, ConfigDict, Field


class ExtensionErrorCode(StrEnum):
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    SOVEREIGNTY_DENIED = "sovereignty_denied"
    RATE_LIMITED = "rate_limited"
    EVALUATOR_NOT_ROUTABLE = "evaluator_not_routable"
    SCHEMA_INVALID = "schema_invalid"
    SEED_NOT_READY = "seed_not_ready"


EXTENSION_ERROR_CODES: Final[tuple[str, ...]] = tuple(member.value for member in ExtensionErrorCode)


ERROR_CODE_TO_HTTP_STATUS: Final[dict[ExtensionErrorCode, int]] = {
    ExtensionErrorCode.UNAUTHORIZED: 401,
    ExtensionErrorCode.FORBIDDEN: 403,
    ExtensionErrorCode.SOVEREIGNTY_DENIED: 403,
    ExtensionErrorCode.RATE_LIMITED: 429,
    ExtensionErrorCode.EVALUATOR_NOT_ROUTABLE: 400,
    ExtensionErrorCode.SCHEMA_INVALID: 422,
    ExtensionErrorCode.SEED_NOT_READY: 503,
}


# Error precedence ladder (highest → lowest), per the contract document.
# The first match short-circuits the middleware stack.
ERROR_PRECEDENCE: Final[tuple[ExtensionErrorCode, ...]] = (
    ExtensionErrorCode.EVALUATOR_NOT_ROUTABLE,
    ExtensionErrorCode.SOVEREIGNTY_DENIED,
    ExtensionErrorCode.UNAUTHORIZED,
    ExtensionErrorCode.FORBIDDEN,
    ExtensionErrorCode.RATE_LIMITED,
    ExtensionErrorCode.SCHEMA_INVALID,
    ExtensionErrorCode.SEED_NOT_READY,
)


class ExtensionEnvelope(BaseModel):
    """Error response envelope returned by production endpoints.

    The envelope MUST byte-equal the value persisted on the audit row's
    ``extension_envelope`` field (per contract).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    error_code: ExtensionErrorCode = Field(..., description="Closed-set error code.")
    retry_after_seconds: int | None = Field(
        None,
        ge=0,
        description="Non-null only for rate_limited and seed_not_ready.",
    )
    audit_id: str = Field(..., min_length=1, description="ULID/UUID of the appended audit row.")
    correlation_id: str = Field(..., min_length=1, description="Per-request correlation id.")


def http_status_for(code: ExtensionErrorCode) -> int:
    """Return the canonical HTTP status for an envelope error_code."""
    return ERROR_CODE_TO_HTTP_STATUS[code]


def precedence_index(code: ExtensionErrorCode) -> int:
    """Return ladder position (0 = highest precedence)."""
    return ERROR_PRECEDENCE.index(code)
