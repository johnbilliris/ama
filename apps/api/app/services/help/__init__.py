"""spec-038 service module — bundles all Help-domain orchestration services.

Imports below establish the module-level surface so dependencies between
services are wired in a single place; routes import only what they need.
"""

from .chat_audit_writer import append_audit_entry
from .conflict_surfacer import detect_conflict
from .content_classification_guard import filter_by_classification
from .deprecation_resolver import resolve_deprecation
from .feedback_aggregator import record_feedback
from .persona_resolver import resolve_persona
from .snapshot_indexer import build_index, swing_alias
from .snapshot_publisher import publish_snapshot, rollback_snapshot
from .staleness_checker import raise_or_clear_flag, recompute_screenshot_hash
from .support_handoff_sla_monitor import check_open_handoffs, sla_for
from .transcript_reconstructor import reconstruct_session

__all__ = [
    "append_audit_entry",
    "build_index",
    "check_open_handoffs",
    "detect_conflict",
    "filter_by_classification",
    "publish_snapshot",
    "raise_or_clear_flag",
    "recompute_screenshot_hash",
    "reconstruct_session",
    "record_feedback",
    "resolve_deprecation",
    "resolve_persona",
    "rollback_snapshot",
    "sla_for",
    "swing_alias",
]
