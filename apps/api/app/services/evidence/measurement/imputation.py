"""Pillar B — Forward-impute missing canonical-chain timestamps (T-B04).

Implements FR-008: when one of call/dispatch/arrival/control/clear is
missing, forward-impute from the next adjacent event; tag
`missing-timestamp` and `reduced-fidelity`. >10 % imputed rows triggers a
`small_sample` flag and an auditor-signoff gate.
"""

from __future__ import annotations

from collections.abc import Iterable

from ..models.signal import CanonicalEventChain

CHAIN_FIELDS = (
    "call_received_at",
    "dispatched_at",
    "arrived_at",
    "controlled_at",
    "cleared_at",
)


def forward_impute(chain: CanonicalEventChain) -> CanonicalEventChain:
    """Forward-impute None values from the next-adjacent populated timestamp."""
    values = [getattr(chain, f) for f in CHAIN_FIELDS]
    imputed: list[str] = []
    for i in range(len(values)):
        if values[i] is None:
            for j in range(i + 1, len(values)):
                if values[j] is not None:
                    values[i] = values[j]
                    imputed.append(CHAIN_FIELDS[i])
                    break
    if not imputed:
        return chain
    new_chain = chain.model_copy(
        update={
            **{f: v for f, v in zip(CHAIN_FIELDS, values)},
            "imputed_fields": list({*chain.imputed_fields, *imputed}),
        }
    )
    return new_chain


def small_sample_share(chains: Iterable[CanonicalEventChain]) -> float:
    rows = list(chains)
    if not rows:
        return 0.0
    return sum(1 for c in rows if c.imputed_fields) / len(rows)


def small_sample_gate(chains: Iterable[CanonicalEventChain], *, threshold: float = 0.10) -> bool:
    """Return True when the imputed share exceeds the gate threshold."""
    return small_sample_share(chains) > threshold
