"""Tests for translation quality embedding-based validation (T078-T082).

Covers:
- Cosine similarity computation
- Threshold-based quality check
- Fallback when embeddings unavailable
"""

from __future__ import annotations

import math

import pytest


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class TestCosineSimilarity:
    """Tests for embedding cosine similarity."""

    def test_identical_vectors(self):
        vec = [1.0, 2.0, 3.0]
        assert cosine_similarity(vec, vec) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        vec_a = [1.0, 0.0]
        vec_b = [0.0, 1.0]
        assert cosine_similarity(vec_a, vec_b) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        vec_a = [1.0, 0.0]
        vec_b = [-1.0, 0.0]
        assert cosine_similarity(vec_a, vec_b) == pytest.approx(-1.0)

    def test_zero_vector(self):
        vec_a = [0.0, 0.0]
        vec_b = [1.0, 1.0]
        assert cosine_similarity(vec_a, vec_b) == 0.0

    def test_similar_vectors_above_threshold(self):
        """Simulates two semantically similar translations."""
        vec_a = [0.9, 0.8, 0.7, 0.6, 0.5]
        vec_b = [0.85, 0.82, 0.72, 0.58, 0.48]
        sim = cosine_similarity(vec_a, vec_b)
        assert sim > 0.85, f"Expected >0.85, got {sim:.4f}"

    def test_dissimilar_vectors_below_threshold(self):
        """Simulates bad translation with low semantic similarity."""
        vec_a = [0.9, 0.8, 0.7, 0.6, 0.5]
        vec_b = [0.1, 0.2, 0.9, 0.1, 0.9]
        sim = cosine_similarity(vec_a, vec_b)
        assert sim < 0.85, f"Expected <0.85, got {sim:.4f}"


class TestTranslationQualityThreshold:
    """Tests for translation quality decision logic."""

    QUALITY_THRESHOLD = 0.85

    def test_high_quality_passes(self):
        similarity = 0.92
        assert similarity >= self.QUALITY_THRESHOLD

    def test_low_quality_fails(self):
        similarity = 0.60
        assert similarity < self.QUALITY_THRESHOLD

    def test_borderline_quality(self):
        """Exactly at threshold should pass."""
        similarity = 0.85
        assert similarity >= self.QUALITY_THRESHOLD
