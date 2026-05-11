"""Phase 2 model unit tests — covers T-AA031…T-AA047."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from ama_domain import (
    AUTHORITY_RANK,
    AUTO_PROMOTE_THRESHOLD,
    AnnotatedScreenshot,
    Approver,
    Callout,
    ChatAuditEntry,
    ChatSession,
    ChatTurn,
    ContentReviewBacklogItem,
    GlossaryTerm,
    HelpArticle,
    HelpFeedback,
    KnowledgeCorpusSource,
    PersonaHelpProfile,
    SnapshotRecord,
    StalenessFlag,
    SupportHandoffRecord,
    authority_rank,
    compute_pattern_id,
    compute_screen_id_hash,
    sort_personas_by_authority,
)

NOW = datetime.now(UTC)


def _article(**overrides):
    base = {
        "id": "getting-started",
        "tenant_id": "__global__",
        "kind": "article",
        "title": "Getting started",
        "slug": "getting-started",
        "domain": "getting-started",
        "body_uri": "apps/web/src/content/help/articles/getting-started.mdx",
        "snapshot_id": "2026.05.11-01",
        "last_reviewed_at": NOW,
        "created_at": NOW,
        "updated_at": NOW,
    }
    base.update(overrides)
    return HelpArticle(**base)


def test_help_article_round_trip():
    a = _article()
    assert a.status == "published"
    assert a.version == 1


def test_help_article_rejects_uppercase_slug():
    with pytest.raises(ValueError):
        _article(slug="GettingStarted")


def test_glossary_term_bcp47_validation():
    GlossaryTerm(
        id="aiims.controller",
        term="AIIMS Controller",
        definition="...",
        domain="aiims",
        lang="en-AU",
        created_at=NOW,
        updated_at=NOW,
    )
    with pytest.raises(ValueError):
        GlossaryTerm(
            id="x",
            term="x",
            definition="x",
            domain="aiims",
            lang="not!bcp47",
            created_at=NOW,
            updated_at=NOW,
        )


def test_persona_help_profile_authority_rank_matches_registry():
    PersonaHelpProfile(
        id="incident-commander",
        persona_kind="operational",
        authority_rank=AUTHORITY_RANK["incident-commander"],
        decision_rights_summary="...",
        created_at=NOW,
        updated_at=NOW,
    )
    with pytest.raises(ValueError):
        PersonaHelpProfile(
            id="incident-commander",
            persona_kind="operational",
            authority_rank=999,
            decision_rights_summary="...",
            created_at=NOW,
            updated_at=NOW,
        )


def test_knowledge_corpus_source_rejects_draft_spec():
    with pytest.raises(ValueError):
        KnowledgeCorpusSource(
            id="s1",
            snapshot_id="2026.05.11-01",
            source_kind="spec",
            source_path="specs/foo/spec.md",
            content_hash="a" * 64,
            spec_id="foo",
            spec_status=None,  # noqa
            indexed_at=NOW,
        )


def test_snapshot_record_dual_approval_required():
    with pytest.raises(ValueError):
        SnapshotRecord(
            id="2026.05.11-01",
            ai_search_index_name="help-corpus-2026.05.11-01",
            approvers=[Approver(identity="alice", role="help_content_owner", approved_at=NOW)],
            published_at=NOW,
            published_by="alice",
        )
    rec = SnapshotRecord(
        id="2026.05.11-01",
        ai_search_index_name="help-corpus-2026.05.11-01",
        approvers=[
            Approver(identity="alice", role="help_content_owner", approved_at=NOW),
            Approver(identity="bob", role="safety_lead", approved_at=NOW),
        ],
        published_at=NOW,
        published_by="alice",
    )
    assert rec.model_config["frozen"] is True


def test_help_feedback_chat_requires_pattern_id():
    with pytest.raises(ValueError):
        HelpFeedback(
            id="fb1",
            tenant_id="t",
            target_kind="chat_turn",
            target_id="session:0",
            rating="not_helpful",
            submitted_by="u",
            created_at=NOW,
        )


def test_chat_audit_entry_frozen():
    e = ChatAuditEntry(
        id="ae",
        tenant_id="t",
        chat_session_id="s",
        turn_index=0,
        user_id="u",
        persona_id="incident-commander",
        persona_source="idp_default",
        snapshot_id="2026.05.11-01",
        user_input_redacted="...",
        response_text="...",
        pattern_id="abc",
        gateway_decision="allow",
        created_at=NOW,
    )
    with pytest.raises(Exception):
        e.response_text = "edited"  # type: ignore


def test_pattern_id_order_matters():
    a = compute_pattern_id("intent", ["src1", "src2"])
    b = compute_pattern_id("intent", ["src2", "src1"])
    assert a != b


def test_screen_id_hash_callout_order_matters():
    c1 = Callout(number=1, anchor_dom_path="#a", alt_text="a")
    c2 = Callout(number=2, anchor_dom_path="#b", alt_text="b")
    h_normal = compute_screen_id_hash("/route", [c1, c2])
    h_swapped = compute_screen_id_hash("/route", [Callout(number=1, anchor_dom_path="#b", alt_text="b"),
                                                  Callout(number=2, anchor_dom_path="#a", alt_text="a")])
    assert h_normal != h_swapped
    # input list order is irrelevant — only callout.number matters
    assert h_normal == compute_screen_id_hash("/route", [c2, c1])


def test_staleness_flag_requires_grace_release_id():
    StalenessFlag(
        id="sf1",
        target_kind="screenshot",
        target_id="ss1",
        raised_reason="screen_id_hash_mismatch",
        raised_at=NOW,
        grace_release_id="2026.05.18",
    )
    with pytest.raises(ValueError):
        StalenessFlag(
            id="sf2",
            target_kind="screenshot",
            target_id="ss2",
            raised_reason="manual",
            raised_at=NOW,
            grace_release_id="",
        )


def test_support_handoff_defaults():
    h = SupportHandoffRecord(
        id="sh1",
        tenant_id="t",
        channel_kind="email",
        address="ops@example.com",
        created_at=NOW,
        updated_at=NOW,
    )
    assert h.sla_routine_business_hours == 4
    assert h.sla_incident_minutes == 5
    assert h.auto_activate_on_nema_level3 is True


def test_content_review_threshold_constant():
    assert AUTO_PROMOTE_THRESHOLD == 3
    item = ContentReviewBacklogItem(
        id="i1",
        tenant_id="t",
        target_kind="article",
        target_id="getting-started",
        negative_count_30d=4,
        status="needs_review",
        created_at=NOW,
        updated_at=NOW,
    )
    assert item.status == "needs_review"


def test_authority_rank_sort_descending_by_authority():
    ranked = sort_personas_by_authority(["incident-commander", "executive-leader", "observer-auditor"])
    # executive-leader has rank 5 (highest), incident-commander 10, observer-auditor 90
    assert ranked[0] == "executive-leader"
    assert ranked[-1] == "observer-auditor"
    assert authority_rank("incident-commander") == 10


def test_chat_session_default_ttl():
    s = ChatSession(
        id="s1",
        tenant_id="t",
        user_id="u",
        persona_id="incident-commander",
        persona_source="idp_default",
        snapshot_id_at_open="2026.05.11-01",
        started_at=NOW,
        last_turn_at=NOW,
        turns=[
            ChatTurn(
                turn_index=0,
                user_input_redacted="hi",
                answer_text="hello",
                pattern_id="abc",
                audit_entry_id="ae1",
                created_at=NOW,
            )
        ],
    )
    assert s.ttl_seconds == 30 * 24 * 3600


def test_annotated_screenshot_hash_pattern():
    AnnotatedScreenshot(
        id="ss1",
        screen_id="disaster-mapper.main",
        route_id="/disasters/[id]",
        screen_id_hash="a" * 64,
        light_blob_uri="https://x/l.png",
        dark_blob_uri="https://x/d.png",
        alt_text_blob_uri="https://x/alt.json",
        captured_at=NOW,
        captured_by="alice",
        created_at=NOW,
        updated_at=NOW,
    )
