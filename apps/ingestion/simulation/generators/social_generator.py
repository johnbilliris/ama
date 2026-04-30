import random
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

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
        **_kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Generate a batch of social media signals: accurate, duplicates, and misinformation."""
        results: list[dict[str, Any]] = []
        now = datetime.now(UTC)

        accurate_count = int(count * accurate_ratio)
        duplicate_count = int(count * duplicate_ratio)
        misinfo_count = count - accurate_count - duplicate_count

        # Accurate posts
        for i in range(accurate_count):
            template = random.choice(ACCURATE_TEMPLATES)
            text = template.format(
                location=location,
                direction=random.choice(["north", "south", "east", "west"]),
                road=f"{random.choice(['Main', 'Station', 'Highway', 'Creek'])} Road",
                hazard=topic,
            )
            results.append(self._make_envelope(text, now, topic, "accurate", location))

        # Duplicate posts (near-identical to first accurate post)
        base_text = results[0]["payload"]["text"] if results else f"Emergency at {location}"
        for i in range(duplicate_count):
            # Slight variation to test similarity detection
            dup_text = base_text
            if i % 2 == 1:
                dup_text = base_text + " " + random.choice(["!!", "please share", "RT"])
            results.append(self._make_envelope(dup_text, now, topic, "duplicate", location))

        # Misinfo posts
        for i in range(misinfo_count):
            template = random.choice(MISINFO_TEMPLATES)
            text = template.format(location=location, hazard=topic)
            results.append(self._make_envelope(text, now, topic, "misinformation", location))

        return results

    def _make_envelope(
        self,
        text: str,
        timestamp: datetime,
        topic: str,
        post_type: str,
        location_name: str,
    ) -> dict[str, Any]:
        now_str = timestamp.isoformat()
        lon = 150.3 + random.uniform(-0.5, 0.5)
        lat = -33.7 + random.uniform(-0.5, 0.5)

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
                "userId": f"user-{uuid4().hex[:8]}",
            },
            "confidenceScore": 0.30,
            "freshnessScore": 0.85,
            "validationStatus": "pending",
            "provenance": {
                "collectionMethod": "simulation",
                "sourceUri": "sim://social-generator",
            },
        }
