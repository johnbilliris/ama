"""ama_domain — pydantic-v2 mirror of spec 036 contracts.

Scaffolded by T004 (Spec 036 — Microsoft Foundry-Based RAG Grounding).

Sibling-namespace to ``packages/domain/src/domain/`` (existing spec 030/032/034
domain models). This package holds **only** the spec-036 contract mirrors so
upstream agents can ``from ama_domain import RetrievalRequest`` without
coupling to the broader ``domain`` namespace's lifecycle.

Bound to:
- ``packages/schemas/spec_036/citation-envelope.json``
- ``packages/schemas/spec_036/audit-record-llm-call.json``
- ``packages/schemas/spec_036/offline-cache-manifest.json``

Schema-mirror parity verified by ``tests/contract/test_schema_mirror_parity.py``
(T005) and entity-level field parity by ``tests/contract/test_*_entity.py``
(T063, T064, T114).
"""

# Re-exports for the public surface (T071–T074 filled).
from .audit_record import AuditRecord, OperatorAction, RetrievedChunkRef
from .citation import Citation
from .equivalence_test_result import EquivalenceTestResult
from .offline_cache import (
    OfflineCacheEntry,
    OfflineCacheManifest,
    OfflineCacheSignatures,
)
from .retrieval import (
    Jurisdiction,
    LicenceMode,
    RetrievalRequest,
    RetrievalResult,
    RetrievedChunk,
)

__all__ = [
    "AuditRecord",
    "Citation",
    "EquivalenceTestResult",
    "Jurisdiction",
    "LicenceMode",
    "OfflineCacheEntry",
    "OfflineCacheManifest",
    "OfflineCacheSignatures",
    "OperatorAction",
    "RetrievalRequest",
    "RetrievalResult",
    "RetrievedChunk",
    "RetrievedChunkRef",
]
