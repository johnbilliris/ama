# Forward imputation for the canonical incident timestamp chain.

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
    # A missing timestamp may only inherit the next available adjacent value.
    values = [getattr(chain, field) for field in CHAIN_FIELDS]
    newly_imputed: list[str] = []
    for index, value in enumerate(values):
        if value is not None:
            continue
        replacement = next((candidate for candidate in values[index + 1 :] if candidate is not None), None)
        if replacement is not None:
            values[index] = replacement
            newly_imputed.append(CHAIN_FIELDS[index])

    if not newly_imputed:
        return chain
    imputed_fields = list(chain.imputed_fields)
    imputed_fields.extend(field for field in newly_imputed if field not in imputed_fields)
    return chain.model_copy(
        update={
            **dict(zip(CHAIN_FIELDS, values, strict=True)),
            "imputed_fields": imputed_fields,
        }
    )


def small_sample_share(chains: Iterable[CanonicalEventChain]) -> float:
    rows = list(chains)
    if not rows:
        return 0.0
    return sum(bool(chain.imputed_fields) for chain in rows) / len(rows)


def small_sample_gate(chains: Iterable[CanonicalEventChain], *, threshold: float = 0.10) -> bool:
    # Exactly ten percent is allowed; the gate is strictly greater than ten percent.
    return small_sample_share(chains) > threshold


def interval_eligible(chains: Iterable[CanonicalEventChain]) -> list[CanonicalEventChain]:
    # Imputed point values remain visible but never enter confidence calculations.
    return [chain for chain in chains if not chain.imputed_fields]
