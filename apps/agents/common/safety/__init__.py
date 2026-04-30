"""Safety sub-package — content safety, PII redaction, prompt validation, classification.

Spec 032 (FR-A05/Q05). Re-exports legacy modules + the new ``classification`` module
required by FR-AI03 (Phi shadow boundary) and FR-O05 (PII hash-redaction).
"""

from __future__ import annotations

from common.content_safety import ContentSafetyValidator
from common.warning_compliance import (
    WarningComplianceResult,
    validate_warning_compliance,
)

from .classification import (
    ClassificationAction,
    ClassificationClass,
    ClassificationResult,
    ClassificationVerdict,
    SensitiveContentClassifier,
    classify,
    hash_redact,
)

__all__ = [
    # Legacy re-exports
    "ContentSafetyValidator",
    "WarningComplianceResult",
    "validate_warning_compliance",
    # New in spec 032
    "ClassificationAction",
    "ClassificationClass",
    "ClassificationResult",
    "ClassificationVerdict",
    "SensitiveContentClassifier",
    "classify",
    "hash_redact",
]
