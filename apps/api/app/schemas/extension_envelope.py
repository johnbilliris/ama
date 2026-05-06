"""Spec-035 production-auth extension envelope (schema layer).

This module re-exports the canonical Pydantic v2 model from ``app.domain``.
The task spec (T008) writes the path ``apps/api/app/schemas/extension_envelope.py``;
the canonical implementation lives at ``apps/api/app/domain/extension_envelope.py``
to keep all closed-set value objects co-located. Both import paths resolve to
the same model.
"""

from app.domain.extension_envelope import (
    ERROR_CODE_TO_HTTP_STATUS,
    ERROR_PRECEDENCE,
    EXTENSION_ERROR_CODES,
    ExtensionEnvelope,
    ExtensionErrorCode,
    http_status_for,
    precedence_index,
)

__all__ = [
    "ERROR_CODE_TO_HTTP_STATUS",
    "ERROR_PRECEDENCE",
    "EXTENSION_ERROR_CODES",
    "ExtensionEnvelope",
    "ExtensionErrorCode",
    "http_status_for",
    "precedence_index",
]
