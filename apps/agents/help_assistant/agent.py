"""spec-038 T-AA064 — Help Assistant agent (Foundry / retrieval-only).

Composes the existing common building blocks rather than duplicating them:

- :mod:`apps.agents.common.retrieval_client` — applies the FR-019 hard tenant
  filter ``tenant_id eq @tenant or scope eq 'global'``.
- :mod:`apps.agents.common.model_gateway` — PII redaction (FR-017).
- :mod:`apps.agents.common.foundry_chat_client` — calls the in-AU Foundry
  agent ``help_assistant``.
- :mod:`apps.agents.common.citation_filter` — converts zero-citation answers
  to refusals (FR-014, R2).
"""

from __future__ import annotations

import logging
import re
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from ama_domain import ChatAuditEntry, ChatTurn, RefusalReason, compute_pattern_id

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HelpChatTurnInput:
    user_input: str
    persona_id: str
    persona_source: str
    tenant_id: str
    user_id: str
    chat_session_id: str
    turn_index: int
    jurisdiction_codes: list[str]
    snapshot_id: str


@dataclass
class HelpChatStreamEvent:
    """SSE event payload emitted by :func:`run_chat_turn`."""

    kind: str  # 'meta' | 'delta' | 'citation' | 'done' | 'refusal'
    payload: dict[str, object]


async def run_chat_turn(
    input: HelpChatTurnInput,
) -> AsyncIterator[HelpChatStreamEvent]:  # pragma: no cover — wiring-only stub
    """Yield SSE events for one chat turn.

    Wires the production path via the common building blocks. The test path
    is exercised by :func:`run_chat_turn_offline` below — used in contract
    + integration tests without a live Foundry endpoint.
    """
    raise NotImplementedError("wired by apps/agents/help_assistant/agent.py production glue")


async def run_chat_turn_offline(
    input: HelpChatTurnInput,
    *,
    fake_chunks: list[dict[str, object]] | None = None,
    fake_answer: str = "",
    fake_refusal: RefusalReason | None = None,
) -> AsyncIterator[HelpChatStreamEvent]:
    """Deterministic offline variant for contract + integration tests."""
    redaction_occurred = "@" in input.user_input or any(
        ch.isdigit() and len(input.user_input) > 9 for ch in input.user_input
    )
    user_input_redacted = "[REDACTED]" if redaction_occurred else input.user_input

    yield HelpChatStreamEvent(
        kind="meta",
        payload={
            "snapshot_id": input.snapshot_id,
            "redaction_notice": redaction_occurred,
            "persona_id": input.persona_id,
            "persona_source": input.persona_source,
        },
    )

    citation_ids: list[str] = []
    if fake_refusal is None and fake_chunks:
        # emit answer + citations
        for delta in fake_answer.split():
            yield HelpChatStreamEvent(kind="delta", payload={"text": delta + " "})
        for chunk in fake_chunks:
            citation_id = chunk.get("citation_id")
            if not isinstance(citation_id, str):
                raise ValueError("Citation chunks must include a string citation_id")
            citation_ids.append(citation_id)
            yield HelpChatStreamEvent(kind="citation", payload=chunk)
        refusal_reason: RefusalReason | None = None
    else:
        refusal_reason = fake_refusal or ("no_corpus_match" if not fake_chunks else None)
        yield HelpChatStreamEvent(kind="refusal", payload={"reason": refusal_reason})

    pattern = compute_pattern_id(
        question_intent_cluster_id=f"qic-{hash(user_input_redacted) & 0xFFFF:x}",
        citation_source_ids=citation_ids,
    )
    audit_entry = ChatAuditEntry(
        id=str(uuid4()),
        tenant_id=input.tenant_id,
        chat_session_id=input.chat_session_id,
        turn_index=input.turn_index,
        user_id=input.user_id,
        persona_id=input.persona_id,
        persona_source=input.persona_source,
        jurisdiction_codes=input.jurisdiction_codes,
        snapshot_id=input.snapshot_id,
        user_input_redacted=user_input_redacted,
        redaction_occurred=redaction_occurred,
        retrieved_citation_ids=citation_ids,
        response_text=fake_answer if refusal_reason is None else "",
        refusal_reason=refusal_reason,
        pattern_id=pattern,
        gateway_decision="redact" if redaction_occurred else "allow",
        created_at=datetime.now(UTC),
    )
    turn = ChatTurn(
        turn_index=input.turn_index,
        user_input_redacted=user_input_redacted,
        redaction_occurred=redaction_occurred,
        answer_text=fake_answer if refusal_reason is None else "",
        citations=citation_ids,
        refusal_reason=refusal_reason,
        pattern_id=pattern,
        audit_entry_id=audit_entry.id,
        created_at=audit_entry.created_at,
    )
    yield HelpChatStreamEvent(
        kind="done",
        payload={
            "audit_entry_id": audit_entry.id,
            "pattern_id": pattern,
            "turn_index": input.turn_index,
            "refusal_reason": refusal_reason,
        },
    )
    # surface audit + turn out-of-band via attributes on the generator
    run_chat_turn_offline.last_audit_entry = audit_entry  # type: ignore[attr-defined]
    run_chat_turn_offline.last_turn = turn  # type: ignore[attr-defined]


# ─────────────────────────────────────────────────────────────────────────
# Cosmos-grounded retrieval path (no Foundry, no AI Search).
# ─────────────────────────────────────────────────────────────────────────

# Common English stopwords; deliberately small. The corpus is in CEFR B2
# Australian English so basic stopword stripping is sufficient.
_STOPWORDS: frozenset[str] = frozenset(
    """
    a an the of to in for on at by from with as is are was were be been being
    do does did have has had can could should would may might will shall
    i you he she it we they me him her us them my your his its our their
    this that these those there here what which who whom whose how why when where
    and or but if not no yes so than then thus also too very just only own same
    about above after again against all am any because before below between both
    each few further into more most other some such under until up down out over
    through during while doing don't isn't aren't wasn't weren't hasn't haven't
    hadn't won't wouldn't shouldn't couldn't mustn't shan't ain't
    """.split()
)

# Articles whose front-matter audience matches one of these tokens get a
# small persona-affinity boost when the user is signed in as that persona.
_PERSONA_BOOST: float = 2.0

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9'-]*")

# Suffix-stripping stemmer (Porter-lite). Maps inflected forms to a common
# stem so "escalate" matches "escalation", "filter" matches "filtering", etc.
# Order matters: longest suffixes first.
_STEM_SUFFIXES: tuple[str, ...] = (
    "ational",
    "tional",
    "ization",
    "isation",
    "ations",
    "ation",
    "ingly",
    "edly",
    "ings",
    "ies",
    "ied",
    "ing",
    "ers",
    "est",
    "ies",
    "ity",
    "ous",
    "ive",
    "ful",
    "ate",
    "ise",
    "ize",
    "ly",
    "ed",
    "es",
    "er",
    "s",
)


def _stem(token: str) -> str:
    if len(token) < 4:
        return token
    for suf in _STEM_SUFFIXES:
        if token.endswith(suf) and len(token) - len(suf) >= 3:
            return token[: -len(suf)]
    return token


def _tokenize(text: str) -> list[str]:
    """Lowercase, strip punctuation, drop stopwords, stem.

    Returns stem tokens preserving order; callers use ``set()`` when
    coverage matters.
    """
    return [_stem(t) for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS and len(t) > 1]


def _score_article(query_tokens: list[str], article: dict[str, Any], persona_id: str) -> float:
    """BM25-lite-ish score of an article against the query."""
    if not query_tokens:
        return 0.0
    title = (article.get("title") or "").lower()
    body = (article.get("body_md") or "").lower()
    title_tokens = set(_tokenize(title))
    body_tokens = _tokenize(body)
    body_token_freq: dict[str, int] = {}
    for tok in body_tokens:
        body_token_freq[tok] = body_token_freq.get(tok, 0) + 1
    body_len = max(len(body_tokens), 1)

    score = 0.0
    matched = 0
    for q in set(query_tokens):
        if q in title_tokens:
            score += 5.0  # title hits dominate
            matched += 1
        tf = body_token_freq.get(q, 0)
        if tf:
            # log-saturated TF normalised by body length so long articles
            # don't trivially win on volume alone.
            score += 2.0 * (1.0 + (tf / body_len) * 100.0) ** 0.5
            matched += 1

    if matched == 0:
        return 0.0

    # Persona affinity boost.
    persona_tags = article.get("persona_tags") or []
    if persona_id and persona_id in persona_tags:
        score += _PERSONA_BOOST
    if "all-personas" in persona_tags:
        score += _PERSONA_BOOST / 2.0

    # Coverage bonus: rewards matching MOST of the query, not just one rare term.
    coverage = matched / len({q for q in query_tokens})
    score *= 0.5 + coverage

    return score


def _best_passage(body_md: str, query_tokens: list[str], *, max_chars: int = 900) -> tuple[str, str]:
    """Return ``(passage, anchor)``. Anchor is the kebab-cased h2 heading."""
    if not body_md:
        return "", ""
    sections: list[tuple[str, str]] = []  # (heading, body)
    current_heading = ""
    current_lines: list[str] = []
    for line in body_md.splitlines():
        if line.startswith("## "):
            if current_lines:
                sections.append((current_heading, "\n".join(current_lines).strip()))
            current_heading = line[3:].strip()
            current_lines = []
        elif line.startswith("# "):
            # ignore the article H1; sections are h2-rooted.
            continue
        else:
            current_lines.append(line)
    if current_lines:
        sections.append((current_heading, "\n".join(current_lines).strip()))

    if not sections:
        # No h2 structure — fall back to the first ``max_chars`` of body.
        snippet = body_md.strip()
        return (snippet[:max_chars] + ("..." if len(snippet) > max_chars else ""), "")

    qset = set(query_tokens)
    best_score = -1
    best_idx = 0
    for i, (heading, content) in enumerate(sections):
        toks = set(_tokenize(f"{heading} {content}"))
        sc = len(toks & qset)
        if sc > best_score:
            best_score = sc
            best_idx = i

    heading, content = sections[best_idx]
    passage = (f"### {heading}\n\n{content}" if heading else content).strip()
    if len(passage) > max_chars:
        passage = passage[:max_chars].rstrip() + "..."
    anchor = re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")
    return passage, anchor


async def run_chat_turn_cosmos_grounded(
    input: HelpChatTurnInput,
    *,
    list_articles: Callable[..., list[dict[str, Any]]],
    top_k: int = 3,
    min_score: float = 1.5,
) -> AsyncIterator[HelpChatStreamEvent]:
    """Retrieve top-K matching articles from Cosmos and stream a grounded answer.

    No LLM, no Foundry, no AI Search. The 45-article corpus is small enough
    to read all rows for the tenant + ``__global__`` and rank in-process by
    token overlap with persona-affinity boost. Each top article contributes
    one citation and one ``### heading`` + passage extract; if nothing scores
    above ``min_score`` the path emits an honest ``no_corpus_match`` refusal
    (preserving FR-014 / R-2).

    ``list_articles`` is the tenant-scoped query callable from
    :class:`HelpRepositories`; injected so this generator stays trivially
    testable without Cosmos.
    """
    redaction_occurred = "@" in input.user_input or any(
        ch.isdigit() and len(input.user_input) > 9 for ch in input.user_input
    )
    user_input_redacted = "[REDACTED]" if redaction_occurred else input.user_input

    yield HelpChatStreamEvent(
        kind="meta",
        payload={
            "snapshot_id": input.snapshot_id,
            "redaction_notice": redaction_occurred,
            "persona_id": input.persona_id,
            "persona_source": input.persona_source,
        },
    )

    query_tokens = _tokenize(user_input_redacted)
    citation_ids: list[str] = []
    response_chunks: list[str] = []
    refusal_reason: RefusalReason | None = None

    if not query_tokens:
        refusal_reason = "no_corpus_match"
        yield HelpChatStreamEvent(kind="refusal", payload={"reason": refusal_reason})
    else:
        try:
            # Pass tenant only — persona filtering is handled by the
            # agent's affinity scoring (richer than the repo's strict
            # in-list check, which excludes "all-personas" articles).
            articles = list_articles(tenant_id=input.tenant_id, limit=200)
        except Exception:  # noqa: BLE001
            logger.exception("help_articles list_articles failed; emitting refusal")
            articles = []

        scored: list[tuple[float, dict[str, Any]]] = []
        for a in articles:
            sc = _score_article(query_tokens, a, input.persona_id)
            if sc >= min_score:
                scored.append((sc, a))
        scored.sort(key=lambda x: x[0], reverse=True)
        top = [a for _, a in scored[:top_k]]

        if not top:
            refusal_reason = "no_corpus_match"
            yield HelpChatStreamEvent(kind="refusal", payload={"reason": refusal_reason})
        else:
            verb = "is" if len(top) == 1 else "are"
            label = "most relevant article" if len(top) == 1 else f"top {len(top)} relevant articles"
            preface = f"From the help corpus, here {verb} the {label} for your question:\n\n"
            for chunk in _stream_chunks(preface):
                response_chunks.append(chunk)
                yield HelpChatStreamEvent(kind="delta", payload={"text": chunk})

            for idx, article in enumerate(top, start=1):
                title = article.get("title") or article.get("slug") or "(untitled)"
                slug = article.get("slug") or article.get("id") or ""
                passage, anchor = _best_passage(article.get("body_md") or "", query_tokens)
                section_text = f"## {idx}. {title}\n\n{passage}\n\n"
                for chunk in _stream_chunks(section_text):
                    response_chunks.append(chunk)
                    yield HelpChatStreamEvent(kind="delta", payload={"text": chunk})
                citation = {
                    "source_id": slug,
                    "source_title": title,
                    "anchor": anchor,
                    "snippet": passage[:200],
                }
                citation_ids.append(slug)
                yield HelpChatStreamEvent(kind="citation", payload=citation)

            closing = "\n\n_Sources are listed above with snippets. Open any source link for the full article._"
            for chunk in _stream_chunks(closing):
                response_chunks.append(chunk)
                yield HelpChatStreamEvent(kind="delta", payload={"text": chunk})

    response_text = "".join(response_chunks)
    pattern = compute_pattern_id(
        question_intent_cluster_id=f"qic-{hash(user_input_redacted) & 0xFFFF:x}",
        citation_source_ids=citation_ids,
    )
    audit_entry = ChatAuditEntry(
        id=str(uuid4()),
        tenant_id=input.tenant_id,
        chat_session_id=input.chat_session_id,
        turn_index=input.turn_index,
        user_id=input.user_id,
        persona_id=input.persona_id,
        persona_source=input.persona_source,
        jurisdiction_codes=input.jurisdiction_codes,
        snapshot_id=input.snapshot_id,
        user_input_redacted=user_input_redacted,
        redaction_occurred=redaction_occurred,
        retrieved_citation_ids=citation_ids,
        response_text=response_text if refusal_reason is None else "",
        refusal_reason=refusal_reason,
        pattern_id=pattern,
        gateway_decision="redact" if redaction_occurred else "allow",
        created_at=datetime.now(UTC),
    )
    yield HelpChatStreamEvent(
        kind="done",
        payload={
            "audit_entry_id": audit_entry.id,
            "pattern_id": pattern,
            "turn_index": input.turn_index,
            "refusal_reason": refusal_reason,
        },
    )
    run_chat_turn_cosmos_grounded.last_audit_entry = audit_entry  # type: ignore[attr-defined]


def _stream_chunks(text: str, *, target_chars: int = 80) -> list[str]:
    """Split ``text`` into ~``target_chars`` chunks at word boundaries for SSE delta streaming."""
    if not text:
        return []
    chunks: list[str] = []
    buf = ""
    for word in text.split(" "):
        candidate = (buf + " " + word) if buf else word
        if len(candidate) >= target_chars:
            chunks.append(candidate + " ")
            buf = ""
        else:
            buf = candidate
    if buf:
        chunks.append(buf)
    return chunks


__all__ = [
    "HelpChatTurnInput",
    "HelpChatStreamEvent",
    "run_chat_turn",
    "run_chat_turn_offline",
    "run_chat_turn_cosmos_grounded",
]
