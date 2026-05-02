"""Cross-cutting MAF agent middleware (FR-013, FR-014, FR-015, FR-016).

This package exports three middleware classes that every Agent in
``maf_runtime/agents/`` binds (per ``agent-definition.schema.yaml``
``middleware_bindings``):

- ``ContentSafetyMiddleware``  — refuses agent invocation on policy block (FR-013)
- ``AuditMiddleware``          — emits one immutable audit entry per invocation (FR-014)
- ``OtelMiddleware``           — adds workflow.* span attributes (FR-016)

The order of binding matters: content_safety FIRST (so blocked inputs short-
circuit before audit/OTel are spent), then audit, then otel. The concrete
``Agent`` constructor passes them as ``middleware=[content_safety, audit, otel]``.
"""

from .audit_middleware import AuditMiddleware, AuditOutcome
from .content_safety_middleware import ContentSafetyMiddleware
from .otel_middleware import OtelMiddleware

__all__ = [
    "AuditMiddleware",
    "AuditOutcome",
    "ContentSafetyMiddleware",
    "OtelMiddleware",
]
