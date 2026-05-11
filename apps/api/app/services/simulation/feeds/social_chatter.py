"""Spec-039 T090: social-media chatter feed (FR-020).

Fictitious social-media-shaped chatter — synthetic handles only,
no real users, no real platforms. Includes optional misinformation flags
(NN-IV) so downstream classifiers can be exercised end-to-end.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Final

from ._base import build_record, ensure_clock, validate_jurisdiction
from ._canonical import SimulatedClock
from ._models import CanonicalRecord, FeedParams
from ._seeded_random import seeded_rng

SOURCE_SHAPE: Final[str] = "social.chatter.v1"
FEED_VERSION: Final[str] = "v1"

_TOPICS: Final[tuple[str, ...]] = (
    "bushfire", "flood", "storm", "evacuation", "road_closure",
    "power_outage", "donation_drive", "rescue_request"
)


def emit(
    scenario_id: str,
    seed: int,
    *,
    jurisdiction: str = "au",
    count: int = 5,
    params: FeedParams | None = None,
    clock: SimulatedClock | None = None,
) -> Iterator[CanonicalRecord]:
    j = validate_jurisdiction(jurisdiction)
    rng = seeded_rng(scenario_id, seed, SOURCE_SHAPE)
    clk = ensure_clock(clock, scenario_id, seed)
    for i in range(count):
        ts = clk.tick(rng.randint(1_000_000, 30_000_000))
        topic = rng.choice(_TOPICS)
        is_misinfo = rng.random() < 0.15
        body = {
            "post_id": f"fict-post-{j}-{i:08d}",
            "synthetic_handle": f"@fict_user_{rng.randint(1000, 99999):05d}",
            "platform": rng.choice([
                "fictitious-microblog", "fictitious-photoshare",
                "fictitious-shortvid", "fictitious-forum"
            ]),
            "posted_at": ts,
            "topic": topic,
            "text": (
                f"FICTITIOUS post about {topic.replace('_', ' ')} — "
                "synthetic test data, do not redistribute."
            ),
            "language": rng.choice(["en-AU", "ar", "el", "it", "vi", "zh-Hans"]),
            "engagement": {
                "likes": rng.randint(0, 5_000),
                "shares": rng.randint(0, 2_000),
            },
            "misinformation_flag": is_misinfo,
            "provenance": "fictitious-stream-v1",
            "jurisdiction": j,
        }
        yield build_record(
            scenario_id=scenario_id,
            seed=seed,
            source_shape=SOURCE_SHAPE,
            feed_version=FEED_VERSION,
            timestamp=ts,
            ordinal=i,
            body=body,
        )


__all__ = ["FEED_VERSION", "SOURCE_SHAPE", "emit"]
