from datetime import UTC, datetime, timedelta

from apps.api.app.services.ingestion.misinformation_detector import MisinformationDetector


def _make_signal(
    text: str = "test post",
    topic: str = "bushfire",
    category: str = "fire",
    coordinates: list[float] | None = None,
    occurred_at: str | None = None,
    confidence: float = 0.3,
    validation_status: str = "pending",
) -> dict:
    coords = coordinates or [151.21, -33.86]
    now = occurred_at or datetime.now(UTC).isoformat()
    return {
        "source": {"dataSourceId": "twitter-disaster", "name": "Twitter", "kind": "social"},
        "category": category,
        "occurredAt": now,
        "receivedAt": now,
        "location": {"type": "Point", "coordinates": coords, "precisionMeters": 5000},
        "payload": {"text": text, "topic": topic},
        "confidenceScore": confidence,
        "freshnessScore": 0.85,
        "validationStatus": validation_status,
        "provenance": {"collectionMethod": "streaming_api"},
    }


def _make_authoritative_signal(
    category: str = "fire",
    coordinates: list[float] | None = None,
    occurred_at: str | None = None,
) -> dict:
    coords = coordinates or [151.21, -33.86]
    now = occurred_at or datetime.now(UTC).isoformat()
    return {
        "source": {"dataSourceId": "bom-warnings", "name": "BoM", "kind": "authoritative"},
        "category": category,
        "occurredAt": now,
        "receivedAt": now,
        "location": {"type": "Point", "coordinates": coords, "precisionMeters": 100},
        "payload": {"title": "Warning"},
        "confidenceScore": 0.95,
        "freshnessScore": 0.90,
        "validationStatus": "validated",
        "provenance": {"collectionMethod": "api_pull"},
    }


class TestBurstDetection:
    def test_burst_detection_flags_20_posts_in_10_min(self) -> None:
        detector = MisinformationDetector()
        base_time = datetime.now(UTC)
        signals = []
        for i in range(25):
            t = base_time + timedelta(seconds=i * 20)
            signals.append(_make_signal(
                text=f"Fire spotted near Blue Mountains #{i}",
                occurred_at=t.isoformat(),
            ))

        flagged = detector.burst_detection(signals, threshold=20, window_minutes=10)
        assert len(flagged) >= 20


class TestContradictionDetection:
    def test_contradiction_detection_reduces_confidence(self) -> None:
        detector = MisinformationDetector()
        now = datetime.now(UTC).isoformat()
        signal = _make_signal(text="Huge fire at Penrith", occurred_at=now)
        # No authoritative signal -> contradiction detected
        result = detector.detect(signal, [signal], [])
        assert result["confidenceScore"] < signal["confidenceScore"]
        assert "no_authoritative_corroboration" in result["flags"]

    def test_no_contradiction_when_authoritative_match(self) -> None:
        detector = MisinformationDetector()
        now = datetime.now(UTC).isoformat()
        signal = _make_signal(text="Fire at Penrith", occurred_at=now)
        auth = _make_authoritative_signal(category="fire", occurred_at=now)
        has_contradiction = detector.contradiction_detection(signal, [auth])
        assert has_contradiction is False


class TestDuplicateAmplification:
    def test_duplicate_amplification_flags_similar_text(self) -> None:
        detector = MisinformationDetector()
        now = datetime.now(UTC)
        signals = [
            _make_signal(
                text="Massive bushfire near Blue Mountains evacuate now",
                occurred_at=now.isoformat(),
            ),
            _make_signal(
                text="Massive bushfire near Blue Mountains evacuate now",
                occurred_at=(now + timedelta(seconds=30)).isoformat(),
            ),
            _make_signal(
                text="Massive bushfire near Blue Mountains evacuate now please share",
                occurred_at=(now + timedelta(seconds=60)).isoformat(),
            ),
        ]
        flagged = detector.duplicate_amplification_detection(signals, similarity_threshold=0.9, window_minutes=5)
        assert len(flagged) >= 1
        # The first signal (index 0) should be kept; duplicates flagged
        assert 0 not in flagged


class TestNormalSignals:
    def test_normal_signals_pass_without_flags(self) -> None:
        detector = MisinformationDetector()
        now = datetime.now(UTC).isoformat()
        signal = _make_signal(text="Smoke visible from Katoomba", occurred_at=now)
        auth = _make_authoritative_signal(category="fire", occurred_at=now)
        result = detector.detect(signal, [signal], [auth])
        # With auth match, should not have contradiction flag
        assert "no_authoritative_corroboration" not in result["flags"]
