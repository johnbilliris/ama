from __future__ import annotations

import pytest

from apps.ingestion.simulation.generators.social_generator import SocialMediaGenerator
from apps.ingestion.simulation.region_sampling import point_in_polygon


def _count_types(batch: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {"accurate": 0, "duplicate": 0, "misinformation": 0}
    for signal in batch:
        counts[str(signal["payload"]["postType"])] += 1
    return counts


def test_default_count_20_produces_14_3_3_split() -> None:
    gen = SocialMediaGenerator()
    batch = gen.generate_batch(count=20, random_seed=7)
    assert _count_types(batch) == {"accurate": 14, "duplicate": 3, "misinformation": 3}


def test_override_ratio_changes_misinformation_count() -> None:
    gen = SocialMediaGenerator()
    batch = gen.generate_batch(
        count=20,
        accurate_ratio=0.5,
        duplicate_ratio=0.2,
        misinfo_ratio=0.3,
        random_seed=17,
    )
    assert _count_types(batch) == {"accurate": 10, "duplicate": 4, "misinformation": 6}


def test_ratio_sum_validation_rejects_invalid_mix() -> None:
    gen = SocialMediaGenerator()
    with pytest.raises(ValueError, match="ratios must sum"):
        gen.generate_batch(count=10, accurate_ratio=0.7, duplicate_ratio=0.2, misinfo_ratio=0.2)


def test_seeded_generation_replays_identically() -> None:
    gen = SocialMediaGenerator()
    run_a = gen.generate_batch(count=10, random_seed=99)
    run_b = gen.generate_batch(count=10, random_seed=99)
    sig_a = [
        (
            item["payload"]["postType"],
            item["payload"]["text"],
            tuple(item["location"]["coordinates"]),
            item["payload"]["userId"],
        )
        for item in run_a
    ]
    sig_b = [
        (
            item["payload"]["postType"],
            item["payload"]["text"],
            tuple(item["location"]["coordinates"]),
            item["payload"]["userId"],
        )
        for item in run_b
    ]
    assert sig_a == sig_b


def test_concurrent_runs_with_different_seeds_are_distinct() -> None:
    gen = SocialMediaGenerator()
    run_a = gen.generate_batch(count=10, random_seed=100)
    run_b = gen.generate_batch(count=10, random_seed=101)
    assert run_a != run_b


def test_target_region_sampling_stays_inside_polygon() -> None:
    gen = SocialMediaGenerator()
    polygon = {
        "type": "Polygon",
        "coordinates": [
            [
                [150.0, -34.0],
                [151.0, -34.0],
                [151.0, -33.0],
                [150.0, -33.0],
                [150.0, -34.0],
            ]
        ],
    }
    batch = gen.generate_batch(count=10, random_seed=33, target_region=polygon)
    for signal in batch:
        lon, lat = signal["location"]["coordinates"]
        assert point_in_polygon(lon, lat, polygon["coordinates"])
