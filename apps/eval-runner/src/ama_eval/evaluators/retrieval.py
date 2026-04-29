"""Retrieval / groundedness evaluators."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .base import EvalInput, EvalResult, ModelOutput, register


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[A-Za-z][A-Za-z0-9'-]{2,}", (text or "").lower())}


def _groundedness(inp: EvalInput, out: ModelOutput) -> EvalResult:
    if not inp.retrieval_scope or not inp.retrieved_context:
        return EvalResult(metric_id="groundedness", score=1.0, pass_=True, rationale="no retrieval scope")
    out_toks = _tokens(out.text)
    if not out_toks:
        return EvalResult(metric_id="groundedness", score=0.0, pass_=False, rationale="empty output")
    ctx_toks: set[str] = set()
    for doc in inp.retrieved_context:
        ctx_toks |= _tokens(doc.get("content", ""))
    overlap = out_toks & ctx_toks
    score = len(overlap) / max(len(out_toks), 1)
    return EvalResult(
        metric_id="groundedness",
        score=score,
        pass_=score >= 0.4,
        rationale=f"{len(overlap)}/{len(out_toks)} output tokens supported",
        evidence={"overlapCount": len(overlap)},
    )


def _context_recall(inp: EvalInput, out: ModelOutput) -> EvalResult:
    if not inp.retrieval_scope or not inp.retrieved_context:
        return EvalResult(metric_id="context-recall", score=1.0, pass_=True, rationale="no retrieval scope")
    relevant = [d for d in inp.retrieved_context if d.get("relevanceLabel") in ("relevant", "partially-relevant")]
    if not relevant:
        return EvalResult(metric_id="context-recall", score=1.0, pass_=True, rationale="no relevant docs")
    text = (out.text or "").lower()
    cited = sum(1 for d in relevant if any(tok in text for tok in _tokens(d.get("content", "")[:80])))
    score = cited / len(relevant)
    return EvalResult(
        metric_id="context-recall",
        score=score,
        pass_=score >= 0.5,
        rationale=f"cited {cited}/{len(relevant)} relevant docs",
    )


def _context_precision(inp: EvalInput, out: ModelOutput) -> EvalResult:
    if not inp.retrieval_scope or not inp.retrieved_context:
        return EvalResult(metric_id="context-precision", score=1.0, pass_=True, rationale="no retrieval scope")
    irrelevant = [d for d in inp.retrieved_context if d.get("relevanceLabel") == "irrelevant"]
    if not irrelevant:
        return EvalResult(metric_id="context-precision", score=1.0, pass_=True, rationale="no irrelevant")
    text = (out.text or "").lower()
    over = sum(1 for d in irrelevant if any(tok in text for tok in _tokens(d.get("content", "")[:60])))
    score = 1.0 - (over / max(len(irrelevant), 1))
    return EvalResult(
        metric_id="context-precision",
        score=score,
        pass_=over == 0,
        rationale=f"{over} irrelevant docs cited" if over else "clean",
    )


@dataclass(frozen=True)
class _Eval:
    metric_id: str
    family: str
    tier: str
    fn: callable

    def evaluate(self, inp: EvalInput, out: ModelOutput) -> EvalResult:
        return self.fn(inp, out)


register(_Eval("groundedness", "groundedness", "rule-based", _groundedness))
register(_Eval("context-recall", "retrieval", "rule-based", _context_recall))
register(_Eval("context-precision", "retrieval", "rule-based", _context_precision))


__all__: list[str] = []
