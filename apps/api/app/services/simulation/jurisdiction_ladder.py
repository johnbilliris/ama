"""5-step jurisdiction ladder (T-G02 / FR-021).

Pure-Python, byte-deterministic ladder producing a :class:`LadderResult`
that callers map onto a persisted :class:`packages.domain.src.domain.
models.routing_decision.RoutingDecision`:

1. **Explicit payload** — caller already supplied a jurisdiction code.
2. **Operator-asserted** — coordinator's chat turn override.
3. **Viewport-hint server-revalidated** — client hint MUST match the
   STRtree polygon at the viewport centroid (mismatch → audit + step 4).
4. **STRtree polygon lookup** — point-in-polygon against the loaded
   jurisdiction-boundary set.
5. **ABS SA4 fallback** — coarsest-grained fallback (Australian Bureau of
   Statistics SA4 area lookup) — deterministic last resort.

Each step is intentionally side-effect-free. The optional
``boundary_service`` callable is the only IO surface; tests can pass a
purely in-memory implementation.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal

LadderStepName = Literal[
    "explicit_payload",
    "operator_asserted",
    "viewport_hint_revalidated",
    "strtree_polygon",
    "abs_sa4_fallback",
]


@dataclass(frozen=True)
class LadderInput:
    explicit_jurisdiction_code: str | None = None
    operator_asserted_code: str | None = None
    viewport_centroid_lat: float | None = None
    viewport_centroid_lng: float | None = None
    client_jurisdiction_hint: str | None = None
    signal_lat: float | None = None
    signal_lng: float | None = None


@dataclass(frozen=True)
class LadderResult:
    jurisdiction_code: str | None
    ladder_step: LadderStepName
    confidence: Literal["high", "medium", "ambiguous"]
    steps_attempted: tuple[LadderStepName, ...]
    viewport_hint_match: bool | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)


PolygonLookup = Callable[[float, float], str | None]
SA4Lookup = Callable[[float, float], str | None]


def resolve(
    *,
    request: LadderInput,
    polygon_lookup: PolygonLookup | None = None,
    sa4_lookup: SA4Lookup | None = None,
) -> LadderResult:
    """Apply the 5-step ladder; never raises, always returns a decision."""
    attempted: list[LadderStepName] = []
    notes: list[str] = []

    # Step 1 — explicit payload.
    attempted.append("explicit_payload")
    if request.explicit_jurisdiction_code:
        return LadderResult(
            jurisdiction_code=request.explicit_jurisdiction_code,
            ladder_step="explicit_payload",
            confidence="high",
            steps_attempted=tuple(attempted),
        )

    # Step 2 — operator-asserted.
    attempted.append("operator_asserted")
    if request.operator_asserted_code:
        return LadderResult(
            jurisdiction_code=request.operator_asserted_code,
            ladder_step="operator_asserted",
            confidence="high",
            steps_attempted=tuple(attempted),
        )

    # Step 3 — viewport-hint server-revalidated.
    attempted.append("viewport_hint_revalidated")
    viewport_match: bool | None = None
    if (
        request.client_jurisdiction_hint
        and request.viewport_centroid_lat is not None
        and request.viewport_centroid_lng is not None
        and polygon_lookup is not None
    ):
        server = polygon_lookup(request.viewport_centroid_lat, request.viewport_centroid_lng)
        viewport_match = server == request.client_jurisdiction_hint
        if viewport_match:
            return LadderResult(
                jurisdiction_code=server,
                ladder_step="viewport_hint_revalidated",
                confidence="high",
                steps_attempted=tuple(attempted),
                viewport_hint_match=True,
            )
        notes.append(f"viewport_hint_mismatch client={request.client_jurisdiction_hint!r} server={server!r}")

    # Step 4 — STRtree polygon lookup at the signal coordinates.
    attempted.append("strtree_polygon")
    if request.signal_lat is not None and request.signal_lng is not None and polygon_lookup is not None:
        code = polygon_lookup(request.signal_lat, request.signal_lng)
        if code:
            return LadderResult(
                jurisdiction_code=code,
                ladder_step="strtree_polygon",
                confidence="medium",
                steps_attempted=tuple(attempted),
                viewport_hint_match=viewport_match,
                notes=tuple(notes),
            )

    # Step 5 — ABS SA4 fallback.
    attempted.append("abs_sa4_fallback")
    if request.signal_lat is not None and request.signal_lng is not None and sa4_lookup is not None:
        code = sa4_lookup(request.signal_lat, request.signal_lng)
        if code:
            return LadderResult(
                jurisdiction_code=code,
                ladder_step="abs_sa4_fallback",
                confidence="ambiguous",
                steps_attempted=tuple(attempted),
                viewport_hint_match=viewport_match,
                notes=tuple(notes + ["sa4 fallback"]),
            )

    # Final degenerate path — return AU national code as low-confidence.
    return LadderResult(
        jurisdiction_code="AU",
        ladder_step="abs_sa4_fallback",
        confidence="ambiguous",
        steps_attempted=tuple(attempted),
        viewport_hint_match=viewport_match,
        notes=tuple(notes + ["no_lookup_available_returning_au_national"]),
    )


__all__ = ["LadderInput", "LadderResult", "LadderStepName", "resolve"]
