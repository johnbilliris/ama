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
# spec-038 Help entities — see specs/038-help-docs-chat/data-model.md
from .annotated_screenshot import AnnotatedScreenshot, Callout
from .audit_record import AuditRecord, OperatorAction, RetrievedChunkRef
from .authority_rank_registry import (
    AUTHORITY_RANK,
    authority_rank,
    is_known_persona,
    sort_personas_by_authority,
)
from .chat_audit_entry import AUDIT_TTL_SECONDS, ChatAuditEntry
from .chat_pattern_id import compute_pattern_id
from .chat_session import DEFAULT_TTL_SECONDS, ChatSession, ChatTurn, RefusalReason
from .citation import Citation
from .content_review_backlog_item import (
    AUTO_PROMOTE_THRESHOLD,
    AUTO_PROMOTE_WINDOW_DAYS,
    ContentReviewBacklogItem,
)
from .equivalence_test_result import EquivalenceTestResult
from .glossary_term import GlossaryTerm
from .help_article import ArticleDomain, ArticleKind, ArticleStatus, HelpArticle
from .help_feedback import HelpFeedback
from .knowledge_corpus_source import KnowledgeCorpusSource
from .offline_cache import (
    OfflineCacheEntry,
    OfflineCacheManifest,
    OfflineCacheSignatures,
)
from .persona_help_profile import PersonaHelpProfile
from .retrieval import (
    Jurisdiction,
    LicenceMode,
    RetrievalRequest,
    RetrievalResult,
    RetrievedChunk,
)
from .screen_id_hash import compute_screen_id_hash
from .snapshot_record import Approver, SnapshotRecord
from .staleness_flag import StalenessFlag
from .support_handoff_record import ChannelKind, SupportHandoffRecord

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
    # spec-038
    "AUDIT_TTL_SECONDS",
    "AUTHORITY_RANK",
    "AUTO_PROMOTE_THRESHOLD",
    "AUTO_PROMOTE_WINDOW_DAYS",
    "AnnotatedScreenshot",
    "Approver",
    "ArticleDomain",
    "ArticleKind",
    "ArticleStatus",
    "Callout",
    "ChannelKind",
    "ChatAuditEntry",
    "ChatSession",
    "ChatTurn",
    "ContentReviewBacklogItem",
    "DEFAULT_TTL_SECONDS",
    "GlossaryTerm",
    "HelpArticle",
    "HelpFeedback",
    "KnowledgeCorpusSource",
    "PersonaHelpProfile",
    "RefusalReason",
    "SnapshotRecord",
    "StalenessFlag",
    "SupportHandoffRecord",
    "authority_rank",
    "compute_pattern_id",
    "compute_screen_id_hash",
    "is_known_persona",
    "sort_personas_by_authority",
]
