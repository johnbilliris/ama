from datetime import UTC, datetime, timedelta

from apps.api.app.services.ingestion.misinformation_detector import MisinformationDetector


def _make_signal(
    signal_id: str = "sig-social-1",
    text: str = "test post",
    topic: str = "bushfire",
    category: str = "fire",
    account_id: str = "acct-1",
    coordinates: list[float] | None = None,
    occurred_at: str | None = None,
    confidence: float = 0.3,
    validation_status: str = "pending",
) -> dict:
    coords = coordinates or [151.21, -33.86]
    now = occurred_at or datetime.now(UTC).isoformat()
    return {
        "signalId": signal_id,
        "source": {"dataSourceId": "twitter-disaster", "name": "Twitter", "kind": "social"},
        "category": category,
        "occurredAt": now,
        "receivedAt": now,
        "location": {"type": "Point", "coordinates": coords, "precisionMeters": 5000},
        "payload": {"text": text, "topic": topic, "accountId": account_id},
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
            signals.append(
                _make_signal(
                    signal_id=f"sig-burst-{i}",
                    account_id=f"acct-burst-{i}",
                    text=f"Fire spotted near Blue Mountains #{i}",
                    occurred_at=t.isoformat(),
                )
            )

        flagged = detector.burst_detection(signals, threshold=20, window_minutes=10)
        assert len(flagged) >= 20

    def test_burst_detection_requires_distinct_accounts(self) -> None:
        detector = MisinformationDetector()
        base_time = datetime.now(UTC)
        one_account = [
            _make_signal(
                signal_id=f"sig-one-{i}",
                account_id="acct-only",
                occurred_at=(base_time + timedelta(seconds=i * 20)).isoformat(),
            )
            for i in range(20)
        ]
        distinct_accounts = [
            _make_signal(
                signal_id=f"sig-many-{i}",
                account_id=f"acct-{i}",
                occurred_at=(base_time + timedelta(seconds=i * 20)).isoformat(),
            )
            for i in range(20)
        ]

        one_account_flags = detector.burst_detection(one_account, threshold=20, window_minutes=10)
        many_account_flags = detector.burst_detection(distinct_accounts, threshold=20, window_minutes=10)

        assert one_account_flags == []
        assert len(many_account_flags) == 20

    def test_burst_detection_preserves_sorted_window_to_original_indices_when_shuffled(self) -> None:
        detector = MisinformationDetector()
        base_time = datetime.now(UTC)
        ordered = [
            _make_signal(
                signal_id=f"sig-{i}",
                account_id=f"acct-{i}",
                occurred_at=(base_time + timedelta(seconds=i * 20)).isoformat(),
            )
            for i in range(21)
        ]
        shuffled = [
            ordered[10],
            ordered[0],
            ordered[11],
            ordered[1],
            ordered[12],
            ordered[2],
            ordered[13],
            ordered[3],
            ordered[14],
            ordered[4],
            ordered[15],
            ordered[5],
            ordered[16],
            ordered[6],
            ordered[17],
            ordered[7],
            ordered[18],
            ordered[8],
            ordered[19],
            ordered[9],
            ordered[20],
        ]

        flagged = detector.burst_detection(shuffled, threshold=20, window_minutes=10)
        flagged_ids = {shuffled[index]["signalId"] for index in flagged}
        expected_ids = {f"sig-{i}" for i in range(21)}
        assert flagged_ids == expected_ids

    def test_authoritative_corroboration_suppresses_burst_flags(self) -> None:
        detector = MisinformationDetector()
        base_time = datetime.now(UTC)
        signals = [
            _make_signal(
                signal_id=f"sig-{i}",
                account_id=f"acct-{i}",
                occurred_at=(base_time + timedelta(seconds=i * 10)).isoformat(),
            )
            for i in range(20)
        ]
        authoritative = [
            _make_authoritative_signal(
                category="fire",
                occurred_at=(base_time + timedelta(seconds=60)).isoformat(),
            )
        ]

        flagged = detector.burst_detection(
            signals,
            threshold=20,
            window_minutes=10,
            authoritative_signals=authoritative,
        )
        assert flagged == []


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

    def test_duplicate_amplification_uses_cosine_threshold_and_retains_earliest_timestamp(self) -> None:
        detector = MisinformationDetector()
        now = datetime.now(UTC)
        earliest = _make_signal(
            signal_id="sig-earliest",
            text="fire near town emergency emergency",
            account_id="acct-a",
            occurred_at=now.isoformat(),
        )
        # Same tokens with frequency differences still keep cosine high.
        later_similar = _make_signal(
            signal_id="sig-later",
            text="fire near town emergency",
            account_id="acct-b",
            occurred_at=(now + timedelta(seconds=30)).isoformat(),
        )
        boundary = _make_signal(
            signal_id="sig-boundary",
            text="river update normal conditions",
            account_id="acct-c",
            occurred_at=(now + timedelta(seconds=40)).isoformat(),
        )

        flagged = detector.duplicate_amplification_detection(
            [later_similar, earliest, boundary],
            similarity_threshold=0.8,
            window_minutes=5,
        )
        flagged_ids = {[later_similar, earliest, boundary][index]["signalId"] for index in flagged}
        assert "sig-earliest" not in flagged_ids
        assert "sig-later" in flagged_ids
        assert "sig-boundary" not in flagged_ids

    def test_duplicate_detection_honors_cross_batch_context(self) -> None:
        detector = MisinformationDetector()
        now = datetime.now(UTC)
        context = [
            _make_signal(
                signal_id="sig-context",
                text="evacuate now major fire at ridge",
                occurred_at=now.isoformat(),
                account_id="acct-context",
            )
        ]
        batch = [
            _make_signal(
                signal_id="sig-new",
                text="evacuate now major fire at ridge",
                occurred_at=(now + timedelta(seconds=50)).isoformat(),
                account_id="acct-new",
            )
        ]

        flagged = detector.duplicate_amplification_detection(
            batch,
            similarity_threshold=0.9,
            window_minutes=5,
            comparison_context=context,
        )
        assert flagged == [0]


class TestNormalSignals:
    def test_normal_signals_pass_without_flags(self) -> None:
        detector = MisinformationDetector()
        now = datetime.now(UTC).isoformat()
        signal = _make_signal(text="Smoke visible from Katoomba", occurred_at=now)
        auth = _make_authoritative_signal(category="fire", occurred_at=now)
        result = detector.detect(signal, [signal], [auth])
        # With auth match, should not have contradiction flag
        assert "no_authoritative_corroboration" not in result["flags"]


class TestContradictionAndGeometry:
    def test_polygon_authoritative_corroboration(self) -> None:
        detector = MisinformationDetector()
        now = datetime.now(UTC).isoformat()
        signal = _make_signal(
            signal_id="sig-poly",
            occurred_at=now,
            coordinates=[151.20, -33.80],
        )
        polygon_auth = {
            **_make_authoritative_signal(category="fire", occurred_at=now),
            "location": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [151.10, -33.90],
                        [151.30, -33.90],
                        [151.30, -33.70],
                        [151.10, -33.70],
                        [151.10, -33.90],
                    ]
                ],
                "precisionMeters": 100,
            },
        }
        assert detector.has_authoritative_corroboration(signal, [polygon_auth]) is True

    def test_invalid_timestamps_do_not_raise_and_do_not_flag_duplicates(self) -> None:
        detector = MisinformationDetector()
        signals = [
            _make_signal(signal_id="sig-bad-1", occurred_at="not-a-time"),
            _make_signal(signal_id="sig-bad-2", occurred_at="also-not-a-time"),
        ]
        assert detector.burst_detection(signals, threshold=2, window_minutes=10) == []
        assert detector.duplicate_amplification_detection(signals, similarity_threshold=0.1, window_minutes=5) == []
