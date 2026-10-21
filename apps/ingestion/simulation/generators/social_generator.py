import random
from datetime import UTC, datetime
from typing import Any

from apps.ingestion.simulation.region_sampling import sample_point_in_target_region

ACCURATE_TEMPLATES = [
    "Smoke visible from {location} heading {direction}. Stay safe everyone.",
    "Heavy rain and flooding on {road} near {location}. Road is impassable.",
    "Power lines down near {location}. Authorities have been notified.",
    "Evacuation centre open at {location} community hall. Supplies available.",
    "Water rising fast at {location} bridge. Do not attempt to cross.",
    "Fire crews actively fighting blaze near {location}. Multiple trucks on scene.",
    "Strong winds causing damage at {location}. Roof tiles flying.",
    "Creek at {location} has broken its banks. Water entering properties.",
]

MISINFO_TEMPLATES = [
    "CONFIRMED: {location} completely destroyed by {hazard}. No survivors.",
    "Government hiding true death toll from {hazard} at {location}!",
    "BREAKING: Nuclear plant meltdown at {location} due to {hazard}!",
    "Military deployed to {location} for forced evacuations. Martial law declared!",
    "Scientists say {hazard} at {location} is worst in 1000 years. Cover-up exposed!",
]


class SocialMediaGenerator:
    """Generates batches of simulated social media signals for testing."""

    def generate_batch(
        self,
        count: int = 20,
        accurate_ratio: float = 0.70,
        duplicate_ratio: float = 0.15,
        misinfo_ratio: float = 0.15,
        topic: str = "bushfire",
        location: str = "Blue Mountains",
        target_region: dict[str, Any] | None = None,
        random_seed: int | None = None,
        rng_version: str = "python-random-v1",
        **_kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Generate a batch of social media signals: accurate, duplicates, and misinformation."""
        if count < 0:
            raise ValueError("count must be >= 0")
        if min(accurate_ratio, duplicate_ratio, misinfo_ratio) < 0:
            raise ValueError("ratios must be >= 0")
        ratio_sum = accurate_ratio + duplicate_ratio + misinfo_ratio
        tolerance = 1e-6
        if abs(ratio_sum - 1.0) > tolerance:
            raise ValueError(f"ratios must sum to 1.0 ± {tolerance}")

        results: list[dict[str, Any]] = []
        now = datetime.now(UTC)
        rng = random.Random(random_seed)

        accurate_count, duplicate_count, misinfo_count = _allocate_counts(
            count,
            [accurate_ratio, duplicate_ratio, misinfo_ratio],
        )

        # Accurate posts
        for i in range(accurate_count):
            template = rng.choice(ACCURATE_TEMPLATES)
            text = template.format(
                location=location,
                direction=rng.choice(["north", "south", "east", "west"]),
                road=f"{rng.choice(['Main', 'Station', 'Highway', 'Creek'])} Road",
                hazard=topic,
            )
            results.append(
                self._make_envelope(
                    text,
                    now,
                    topic,
                    "accurate",
                    location,
                    target_region=target_region,
                    rng=rng,
                    rng_version=rng_version,
                )
            )

        # Duplicate posts (near-identical to first accurate post)
        base_text = results[0]["payload"]["text"] if results else f"Emergency at {location}"
        for i in range(duplicate_count):
            # Slight variation to test similarity detection
            dup_text = base_text
            if i % 2 == 1:
                dup_text = base_text + " " + rng.choice(["!!", "please share", "RT"])
            results.append(
                self._make_envelope(
                    dup_text,
                    now,
                    topic,
                    "duplicate",
                    location,
                    target_region=target_region,
                    rng=rng,
                    rng_version=rng_version,
                )
            )

        # Misinfo posts
        for i in range(misinfo_count):
            template = rng.choice(MISINFO_TEMPLATES)
            text = template.format(location=location, hazard=topic)
            results.append(
                self._make_envelope(
                    text,
                    now,
                    topic,
                    "misinformation",
                    location,
                    target_region=target_region,
                    rng=rng,
                    rng_version=rng_version,
                )
            )

        return results

    def _make_envelope(
        self,
        text: str,
        timestamp: datetime,
        topic: str,
        post_type: str,
        location_name: str,
        *,
        target_region: dict[str, Any] | None,
        rng: random.Random,
        rng_version: str,
    ) -> dict[str, Any]:
        now_str = timestamp.isoformat()
        lon, lat = sample_point_in_target_region(
            target_region,
            fallback=[150.3 + rng.uniform(-0.5, 0.5), -33.7 + rng.uniform(-0.5, 0.5)],
            rng=rng,
        )

        category = "community_report"
        if topic in ("bushfire", "fire"):
            category = "fire"
        elif topic in ("flood",):
            category = "hydrology"
        elif topic in ("cyclone", "storm"):
            category = "weather"

        return {
            "source": {
                "dataSourceId": "twitter-disaster",
                "name": "X (Twitter) Disaster Stream",
                "kind": "social",
            },
            "category": category,
            "occurredAt": now_str,
            "receivedAt": now_str,
            "location": {
                "type": "Point",
                "coordinates": [round(lon, 4), round(lat, 4)],
                "precisionMeters": 5000,
            },
            "payload": {
                "text": text,
                "postType": post_type,
                "topic": topic,
                "locationName": location_name,
                "userId": f"user-{rng.randint(0, 16**8 - 1):08x}",
            },
            "confidenceScore": 0.30,
            "freshnessScore": 0.85,
            "validationStatus": "pending",
            "provenance": {
                "collectionMethod": "simulation",
                "sourceUri": "sim://social-generator",
                "validationNotes": f"rngVersion={rng_version}",
            },
        }


def _allocate_counts(total: int, ratios: list[float]) -> tuple[int, int, int]:
    raw = [total * ratio for ratio in ratios]
    floors = [int(value) for value in raw]
    remaining = total - sum(floors)
    ranked = sorted(range(len(raw)), key=lambda index: raw[index] - floors[index], reverse=True)
    for index in ranked[:remaining]:
        floors[index] += 1
    return floors[0], floors[1], floors[2]
