"""Spec-035 domain layer.

Closed-set enums and value objects mirroring the canonical TypeScript exports at
``packages/domain/src``. Cardinality and string values MUST stay byte-identical;
contract tests under ``apps/api/tests/contract/spec_035`` enforce this.
"""

from app.domain.app_role import (
    ADMIN_APP_ROLE,
    AIIMS_FUNCTION_APP_ROLES,
    APP_ROLE_COUNT,
    APP_ROLES,
    AppRole,
)
from app.domain.audit_outcome import AUDIT_OUTCOME_COUNT, AUDIT_OUTCOMES, AuditOutcome
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

__all__ = [
    "ADMIN_APP_ROLE",
    "AIIMS_FUNCTION_APP_ROLES",
    "APP_ROLE_COUNT",
    "APP_ROLES",
    "AppRole",
    "AUDIT_OUTCOME_COUNT",
    "AUDIT_OUTCOMES",
    "AuditOutcome",
    "ERROR_CODE_TO_HTTP_STATUS",
    "ERROR_PRECEDENCE",
    "EXTENSION_ERROR_CODES",
    "ExtensionEnvelope",
    "ExtensionErrorCode",
    "OFFLINE_QUEUE_CAP_PER_PERSONA",
    "OFFLINE_QUEUE_LIFE_SAFETY_BATCH_SIZE",
    "OFFLINE_QUEUE_TIERS",
    "OfflineQueueTier",
]
