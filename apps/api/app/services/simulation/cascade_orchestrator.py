"""Cascade orchestrator (T-D02 / FR-043..047).

Cycle 2 / T-AA20 / A2-03 — :func:`packages.domain.src.domain.sim_cascade_matrix.cascade_targets_for`
is now the SOLE source of truth for cascade fan-out targets. The legacy
``apps/api/app/config/cascade_rules.yaml`` ``fan_out_rules:`` block is
removed; the YAML retains only the operational ``ladder:`` + ``cap:``
keys for FR-057 affinity-ladder tuning.

**Depth-2 refusal (FR-057 / T-D12).** A cascade child that itself produces
a triggering signal MUST NOT initiate a second-level fan-out; instead the
orchestrator emits a ``cascade.depth2_refused`` audit and issues a fresh
top-level ``injection_correlation_id`` so that ``origin_cascade_id`` does
NOT propagate transitively.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from packages.domain.src.domain.models.synthetic_signal import SyntheticSignal
from packages.domain.src.domain.sim_cascade_matrix import cascade_targets_for

logger = logging.getLogger(__name__)


_RULES_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "cascade_rules.yaml"
)


# Cycle 2 / T-AA20 — translation of the matrix's PascalCase SubAgent
# names to the kebab-case role identifiers the legacy dispatcher consumes.
# The matrix continues to expose PascalCase (Constitution V predictable
# vocabulary); the dispatcher contract for sub-agent invocations is
# kebab-case (Cycle 1 history) so we map at the boundary.
_MATRIX_TO_ROLE: dict[str, str] = {
    "Comms": "communication",
    "Evac": "evacuation",
    "Health": "health",
    "Intel": "monitoring",
    "Logistics": "logistics",
    "Operations": "operations",
    "Planning": "planning",
    "Resource": "resource-allocation",
    "Risk": "risk-assessment",
}


@dataclass(frozen=True)
class CascadeRule:
    rule_id: str
    trigger_category: str
    targets: tuple[str, ...]


@dataclass
class CascadeRulesConfig:
    ladder: list[str] = field(default_factory=list)
    cap: int = 5
    fan_out_rules: list[CascadeRule] = field(default_factory=list)


_RULES_CACHE: CascadeRulesConfig | None = None


def _matrix_targets_for_category(category: str) -> list[str]:
    """Return kebab-case role names for *category* via the canonical matrix.

    Cycle 2 / T-AA20 / A2-03 — the canonical
    :func:`packages.domain.src.domain.sim_cascade_matrix.cascade_targets_for`
    is the sole source of truth; this helper translates the PascalCase
    SubAgent names to the kebab-case role identifiers the dispatcher
    expects (Cycle 1 vocabulary). Lex-sorted for deterministic order.
    """

    pascal_targets = cascade_targets_for(category)
    if not pascal_targets:
        return []
    return sorted(
        _MATRIX_TO_ROLE[name]
        for name in pascal_targets
        if name in _MATRIX_TO_ROLE
    )


def _parse_yaml(text: str) -> dict[str, Any]:
    """Parse the cascade-rules YAML using PyYAML if available, else minimal parser.

    The repo already depends on ``PyYAML`` for other agents; this fallback
    parser is intentionally minimal — it only handles the subset of YAML
    used by ``cascade_rules.yaml`` so the test environment can import the
    module without installing PyYAML.
    """
    try:
        import yaml  # type: ignore[import-not-found]

        return yaml.safe_load(text)
    except ModuleNotFoundError:
        pass

    out: dict[str, Any] = {}
    current_list_key: str | None = None
    current_rule: dict[str, Any] | None = None
    rules: list[dict[str, Any]] = []
    in_targets = False
    targets: list[str] = []

    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if indent == 0 and stripped.endswith(":"):
            key = stripped[:-1].strip()
            if key in {"ladder", "fan_out_rules"}:
                current_list_key = key
                if key == "fan_out_rules":
                    rules = []
                else:
                    out["ladder"] = []
            else:
                current_list_key = None
            continue

        if indent == 0 and ":" in stripped:
            key, _, value = stripped.partition(":")
            out[key.strip()] = value.strip()
            current_list_key = None
            continue

        if current_list_key == "ladder" and stripped.startswith("- "):
            out.setdefault("ladder", []).append(stripped[2:].strip())
            continue

        if current_list_key == "fan_out_rules":
            if stripped.startswith("- "):
                if current_rule is not None and targets:
                    current_rule["targets"] = targets
                if current_rule is not None:
                    rules.append(current_rule)
                current_rule = {}
                targets = []
                in_targets = False
                rest = stripped[2:].strip()
                if rest and ":" in rest:
                    k, _, v = rest.partition(":")
                    current_rule[k.strip()] = v.strip()
                continue
            if stripped == "targets:":
                in_targets = True
                continue
            if in_targets and stripped.startswith("- "):
                targets.append(stripped[2:].strip())
                continue
            if ":" in stripped and current_rule is not None:
                k, _, v = stripped.partition(":")
                current_rule[k.strip()] = v.strip()
                in_targets = False
                continue

    if current_rule is not None and current_list_key == "fan_out_rules":
        if targets:
            current_rule["targets"] = targets
        rules.append(current_rule)
    if rules:
        out["fan_out_rules"] = rules
    return out


def load_rules(*, path: Path | None = None) -> CascadeRulesConfig:
    """Load and cache the cascade-rules YAML."""
    global _RULES_CACHE
    if _RULES_CACHE is not None and path is None:
        return _RULES_CACHE
    p = path or _RULES_PATH
    if not p.exists():
        cfg = CascadeRulesConfig()
    else:
        data = _parse_yaml(p.read_text(encoding="utf-8"))
        ladder = list(data.get("ladder", []))
        cap = int(data.get("cap", 5))
        rules: list[CascadeRule] = []
        for r in data.get("fan_out_rules", []) or []:
            rules.append(
                CascadeRule(
                    rule_id=str(r.get("id", "")),
                    trigger_category=str(r.get("trigger_category", "")),
                    targets=tuple(r.get("targets", []) or []),
                )
            )
        cfg = CascadeRulesConfig(ladder=ladder, cap=cap, fan_out_rules=rules)
    if path is None:
        _RULES_CACHE = cfg
    return cfg


def reset_cache_for_tests() -> None:
    global _RULES_CACHE
    _RULES_CACHE = None


# ---------------------------------------------------------------------------
# Fan-out
# ---------------------------------------------------------------------------


SubAgentDispatch = Callable[[str, str, str], Awaitable[Any]]
"""``(role, prompt, correlation_id) -> Awaitable``.

The dispatcher performs the actual sub-agent invocation; the orchestrator
remains hermetic so tests can pin behaviour without HTTP.
"""


@dataclass
class CascadeFanOutResult:
    origin_cascade_id: str
    triggered: list[str]
    skipped_reason: str | None = None


async def fan_out(
    *,
    trigger_signal: SyntheticSignal,
    dispatcher: SubAgentDispatch,
    parent_origin_cascade_id: str | None = None,
    rules: CascadeRulesConfig | None = None,
    audit_writer: Any | None = None,
    thread_cap_service: Any | None = None,
) -> CascadeFanOutResult:
    """Fan-out a triggering signal to its declared target sub-agents.

    If *parent_origin_cascade_id* is supplied, the orchestrator refuses
    depth-2 fan-out (per FR-057), emits the
    ``cascade.depth2_refused`` audit, and issues a fresh top-level
    correlation in the result.

    If *thread_cap_service* is supplied (T-Q01 / T-Q02), the orchestrator
    consults its hazard-thread counter BEFORE dispatching. When the cap
    is reached, it emits a ``thread.cap_exceeded`` audit per
    audit-envelope.md §3.10 and returns
    ``skipped_reason="thread_cap_exceeded"`` with no dispatch.
    """
    cfg = rules or load_rules()

    # Depth-2 refusal: a cascade child cannot itself trigger a cascade.
    if parent_origin_cascade_id is not None:
        new_top_level = str(uuid4())
        if audit_writer is not None:
            try:
                from datetime import UTC, datetime

                # Cycle 2 / T-AA21 / A2-06 — `sequence_number` is allocated
                # by the gap-free allocator (Cycle 1 ADR-036-007). Caller-
                # supplied values are an attractive nuisance: the previous
                # `1` placeholder was always overwritten, but a future
                # writer-side refactor might respect it and silently
                # collapse the gap-free invariant. Removed here; the
                # `audit_writer.write` guard rejects any caller-supplied
                # `sequence_number` defensively.
                await audit_writer.write(
                    "cascade.depth2_refused",
                    simulation_id=trigger_signal.simulation_id,
                    actor="cascade_orchestrator",
                    details={
                        "audit_id": str(uuid4()),
                        "simulation_id": trigger_signal.simulation_id,
                        "tenant_id": trigger_signal.tenant_id,
                        "timestamp_utc": datetime.now(UTC),
                        "actor": "cascade_orchestrator",
                        "entry_type": "cascade.depth2_refused",
                        "attempted_signal_id": trigger_signal.signal_id,
                        "originating_cascade_id": parent_origin_cascade_id,
                        "refusal_reason": "depth2_cascade_disallowed",
                        "chat_reply_text": (
                            "Depth-2 cascade is not allowed; new top-level "
                            "correlation issued."
                        ),
                        "new_top_level_correlation_id": new_top_level,
                    },
                )
            except Exception:  # pragma: no cover - defensive
                logger.exception(
                    "cascade.depth2_refused audit write failed sim=%s",
                    trigger_signal.simulation_id,
                )
        return CascadeFanOutResult(
            origin_cascade_id=new_top_level,
            triggered=[],
            skipped_reason="depth2_refused",
        )

    # T-Q01 / T-Q02 — hazard-thread cap enforcement; T-Q03/T-Q04/T-Q05 —
    # degraded-to-annotation fallback via affinity ladder.
    acquired_thread_id: str | None = None
    annotation_host: str | None = None
    affinity_step: int | None = None
    if thread_cap_service is not None:
        result = await thread_cap_service.try_acquire(
            trigger_signal.simulation_id, thread_kind="hazard"
        )
        # Local import to avoid widening the surface API for callers that
        # don't supply a service.
        from apps.api.app.services.simulation.thread_cap_service import (
            AcquireDenied,
            AcquireGranted,
        )

        if isinstance(result, AcquireDenied):
            # T-Q03/Q04/Q05 — instead of refusing, walk the 5-step affinity
            # ladder to choose an existing thread to absorb the cascade as
            # an annotation, and emit ``cascade.degraded_to_annotation``.
            try:
                from apps.api.app.services.simulation.cascade_affinity_ladder import (
                    CandidateThread,
                    CascadeTrigger,
                )
                from apps.api.app.services.simulation.cascade_affinity_ladder import (
                    select as ladder_select,
                )

                candidates = []
                # The ThreadCapService exposes the active thread ids; if
                # the service implements ``list_active_threads`` we walk
                # them, otherwise we fall back to the legacy
                # ``thread.cap_exceeded`` audit.
                lister = getattr(thread_cap_service, "list_active_threads", None)
                if callable(lister):
                    raw = await lister(trigger_signal.simulation_id)
                    for t in raw:
                        candidates.append(
                            CandidateThread(
                                thread_id=t["thread_id"],
                                jurisdiction_code=t.get("jurisdiction_code"),
                                hazard_class=t.get("hazard_class"),
                                origin_cascade_id=t.get("origin_cascade_id"),
                                last_mutated_at=t["last_mutated_at"],
                                thread_creation_id=t.get(
                                    "thread_creation_id", t["thread_id"]
                                ),
                            )
                        )

                if candidates:
                    trigger = CascadeTrigger(
                        jurisdiction_code=trigger_signal.jurisdiction_code,
                        hazard_class=trigger_signal.parameters.get("hazard_class")
                        if isinstance(trigger_signal.parameters, dict)
                        else None,
                        origin_cascade_id=parent_origin_cascade_id,
                    )
                    chosen = ladder_select(trigger=trigger, candidates=candidates)
                    if chosen is not None:
                        annotation_host = chosen.chosen.thread_id
                        affinity_step = chosen.step
            except Exception:  # pragma: no cover - defensive
                logger.exception(
                    "cascade.affinity_ladder_failed sim=%s",
                    trigger_signal.simulation_id,
                )

            if audit_writer is not None:
                try:
                    if annotation_host is not None:
                        await audit_writer.write(
                            "cascade.degraded_to_annotation",
                            simulation_id=trigger_signal.simulation_id,
                            actor="cascade_orchestrator",
                            details={
                                "trigger_signal_id": trigger_signal.signal_id,
                                "annotation_host_thread_id": annotation_host,
                                "affinity_step": affinity_step,
                                "current_thread_count": result.current_count,
                                "category": trigger_signal.category,
                            },
                        )
                    else:
                        await audit_writer.write(
                            "thread.cap_exceeded",
                            simulation_id=trigger_signal.simulation_id,
                            actor="cascade_orchestrator",
                            details={
                                "proposed_thread": {
                                    "trigger_signal_id": trigger_signal.signal_id,
                                    "category": trigger_signal.category,
                                },
                                "current_thread_count": result.current_count,
                                "rejection_source": "coordinator_injection",
                            },
                        )
                except Exception:  # pragma: no cover - defensive
                    logger.exception(
                        "cascade.thread_cap_audit_failed sim=%s",
                        trigger_signal.simulation_id,
                    )
            return CascadeFanOutResult(
                origin_cascade_id=str(uuid4()),
                triggered=[],
                skipped_reason=(
                    "degraded_to_annotation"
                    if annotation_host is not None
                    else "thread_cap_exceeded"
                ),
            )
        if isinstance(result, AcquireGranted):
            acquired_thread_id = result.thread_id

    matching = [
        r for r in cfg.fan_out_rules if r.trigger_category == trigger_signal.category
    ]
    # Cycle 2 / T-AA20 / A2-03 — when no YAML rule matches (the YAML
    # fan_out_rules block has been removed; this is the steady-state
    # path), fall back to the canonical
    # `sim_cascade_matrix.cascade_targets_for(category)`.
    if not matching:
        matrix_targets = _matrix_targets_for_category(trigger_signal.category)
        if matrix_targets:
            matching = [
                CascadeRule(
                    rule_id=f"matrix:{trigger_signal.category}",
                    trigger_category=trigger_signal.category,
                    targets=tuple(matrix_targets),
                )
            ]
    if not matching:
        if (
            thread_cap_service is not None
            and acquired_thread_id is not None
        ):
            # No work to do — release the slot we just took.
            await thread_cap_service.release(
                trigger_signal.simulation_id, acquired_thread_id
            )
        return CascadeFanOutResult(
            origin_cascade_id=str(uuid4()),
            triggered=[],
            skipped_reason="no_matching_rule",
        )

    origin = str(uuid4())
    targets: list[str] = []
    for rule in matching:
        targets.extend(rule.targets)

    triggered: list[str] = []
    for role in targets:
        try:
            await dispatcher(role, _build_cascade_prompt(trigger_signal), origin)
            triggered.append(role)
        except Exception:
            logger.exception(
                "cascade.dispatch_failed role=%s sim=%s",
                role,
                trigger_signal.simulation_id,
            )

    return CascadeFanOutResult(origin_cascade_id=origin, triggered=triggered)


def _build_cascade_prompt(signal: SyntheticSignal) -> str:
    """Render a short prompt describing *signal* for the receiving sub-agent."""
    return (
        f"Cascade trigger: category={signal.category!r} "
        f"confidence={signal.confidence!r} parameters={signal.parameters!r}"
    )


def list_fan_out_targets(category: str, *, rules: CascadeRulesConfig | None = None) -> list[str]:
    """Helper exposed for unit tests."""
    cfg = rules or load_rules()
    out: list[str] = []
    for rule in cfg.fan_out_rules:
        if rule.trigger_category == category:
            out.extend(rule.targets)
    if not out:
        # Cycle 2 / T-AA20 — matrix fallback (canonical source).
        out.extend(_matrix_targets_for_category(category))
    return out


__all__ = [
    "CascadeFanOutResult",
    "CascadeRule",
    "CascadeRulesConfig",
    "fan_out",
    "list_fan_out_targets",
    "load_rules",
    "reset_cache_for_tests",
]
