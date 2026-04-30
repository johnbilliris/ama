"""Tests for the disaster-response synthetic generator."""

from __future__ import annotations

from collections import Counter

import pytest
from ama_eval_dataset.distribution import (
    HAZARD_TARGETS,
    LANGUAGE_TARGETS,
    SENSITIVITY_THRESHOLDS,
)
from ama_eval_dataset.generator import generate_corpus
from ama_eval_dataset.manifest import build_manifest

SEED = 20251121
SIZE = 5000


@pytest.fixture(scope="module")
def corpus():
    return generate_corpus(seed=SEED, target_size=SIZE)


def test_corpus_has_target_size(corpus):
    assert len(corpus) == SIZE


def test_determinism_same_seed_same_hash():
    a = generate_corpus(seed=SEED, target_size=200)
    b = generate_corpus(seed=SEED, target_size=200)
    ma = build_manifest(a, "test", "1.0.0", "tester", "file:///tmp/a")
    mb = build_manifest(b, "test", "1.0.0", "tester", "file:///tmp/b")
    assert ma.contentHash == mb.contentHash


def test_determinism_different_seed_different_hash():
    a = generate_corpus(seed=SEED, target_size=200)
    b = generate_corpus(seed=SEED + 1, target_size=200)
    ma = build_manifest(a, "test", "1.0.0", "tester", "file:///tmp/a")
    mb = build_manifest(b, "test", "1.0.0", "tester", "file:///tmp/b")
    assert ma.contentHash != mb.contentHash


def test_each_hazard_at_least_100_cases(corpus):
    counts = Counter(h for c in corpus for h in c.hazardTags)
    for hazard in HAZARD_TARGETS:
        assert counts[hazard] >= 100, f"{hazard} has only {counts[hazard]} cases"


def test_language_distribution_within_2pct(corpus):
    counts = Counter(c.language for c in corpus)
    n = len(corpus)
    for lang, target in LANGUAGE_TARGETS.items():
        actual = counts[lang] / n
        assert abs(actual - target) <= 0.02, f"{lang}: actual {actual:.3f} vs target {target}"


def test_all_caseIds_unique(corpus):
    ids = [c.caseId for c in corpus]
    assert len(ids) == len(set(ids))


def test_refuse_cases_have_referToAuthority(corpus):
    for c in corpus:
        if (
            str(c.expectedBehaviour.expectedAction) in ("ExpectedAction.refuse", "refuse")
            or getattr(c.expectedBehaviour.expectedAction, "value", c.expectedBehaviour.expectedAction) == "refuse"
        ):
            assert c.expectedBehaviour.referToAuthority is not None, c.caseId


def test_graphic_hazards_have_required_sensitivity(corpus):
    required = {"graphic-fatality", "human-remains", "mass-casualty"}
    for c in corpus:
        if "fatality-report" in c.hazardTags or "remains-recovery" in c.hazardTags:
            assert any(label in required for label in c.sensitivityLabels), c.caseId


def test_sensitivity_coverage_thresholds(corpus):
    n = len(corpus)
    counts = Counter(label for c in corpus for label in c.sensitivityLabels)
    for label, threshold in SENSITIVITY_THRESHOLDS.items():
        share = counts[label] / n
        assert share >= threshold, f"{label} share {share:.4f} below threshold {threshold}"


def test_retrieval_scope_band(corpus):
    rs_count = sum(1 for c in corpus if c.retrievalScope)
    share = rs_count / len(corpus)
    assert 0.08 <= share <= 0.12, f"retrieval share {share:.3f} not in [0.08, 0.12]"
    for c in corpus:
        if c.retrievalScope:
            assert len(c.retrievedContext) >= 1, c.caseId


def test_jurisdictions_present(corpus):
    juris = {j for c in corpus for j in c.jurisdictionTags}
    assert "AU-NSW" in juris
    assert "NZ-AUK" in juris


def test_manifest_content_hash_format(corpus):
    m = build_manifest(corpus, "disaster-response-core", "1.0.0", "tester", "file:///tmp/x")
    assert m.contentHash.startswith("sha256:")
    assert len(m.contentHash) == len("sha256:") + 64
    assert m.caseCount == len(corpus)
    assert sorted(m.languageScope) == sorted(LANGUAGE_TARGETS.keys())


def test_pydantic_round_trip(corpus):
    from ama_eval_core.models import EvaluationCase

    for c in corpus[:50]:
        EvaluationCase.model_validate_json(c.model_dump_json())


def test_all_actions_represented(corpus):
    actions = {getattr(c.expectedBehaviour.expectedAction, "value", c.expectedBehaviour.expectedAction) for c in corpus}
    assert actions == {"answer", "refuse", "escalate", "clarify", "redirect"}


def test_all_severities_represented(corpus):
    sev = {c.severity for c in corpus}
    assert sev == {"low", "medium", "high", "critical"}
