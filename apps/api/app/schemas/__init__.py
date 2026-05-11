"""Spec-035 schema-layer re-exports."""

from app.schemas.extension_envelope import (
    ERROR_CODE_TO_HTTP_STATUS,
    ERROR_PRECEDENCE,
    EXTENSION_ERROR_CODES,
    ExtensionEnvelope,
    ExtensionErrorCode,
)

__all__ = [
    "ERROR_CODE_TO_HTTP_STATUS",
    "ERROR_PRECEDENCE",
    "EXTENSION_ERROR_CODES",
    "ExtensionEnvelope",
    "ExtensionErrorCode",
]
