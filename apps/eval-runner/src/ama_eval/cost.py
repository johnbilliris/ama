"""Cost attribution — converts token + duration usage into AUD attribution rows."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

# AUD pricing per 1K tokens — must be reviewed quarterly. Source: pricing/azure-ai-foundry.md
DEFAULT_PRICE_PER_1K_AUD: Mapping[str, dict[str, float]] = {
    "gpt-4o": {"prompt": 0.0075, "completion": 0.0225},
    "gpt-4o-mini": {"prompt": 0.00045, "completion": 0.0018},
    "phi-3": {"prompt": 0.0002, "completion": 0.0008},
    "phi-3.5": {"prompt": 0.0002, "completion": 0.0008},
    "o1-mini": {"prompt": 0.0045, "completion": 0.0180},
}


@dataclass
class CostEntry:
    runId: str
    modelId: str
    promptTokens: int
    completionTokens: int
    promptCostAud: float
    completionCostAud: float
    totalCostAud: float


def compute_cost(
    run_id: str,
    model_id: str,
    prompt_tokens: int,
    completion_tokens: int,
    prices: Mapping[str, dict[str, float]] | None = None,
) -> CostEntry:
    table = prices or DEFAULT_PRICE_PER_1K_AUD
    price = table.get(model_id, {"prompt": 0.0, "completion": 0.0})
    p_cost = round(prompt_tokens / 1000 * price["prompt"], 6)
    c_cost = round(completion_tokens / 1000 * price["completion"], 6)
    return CostEntry(
        runId=run_id,
        modelId=model_id,
        promptTokens=prompt_tokens,
        completionTokens=completion_tokens,
        promptCostAud=p_cost,
        completionCostAud=c_cost,
        totalCostAud=round(p_cost + c_cost, 6),
    )


def aggregate_run_cost(entries: list[CostEntry]) -> float:
    return round(sum(e.totalCostAud for e in entries), 6)


__all__ = ["CostEntry", "compute_cost", "aggregate_run_cost", "DEFAULT_PRICE_PER_1K_AUD"]
