import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class MisinformationDetector:
    """Detects misinformation patterns in social media signals."""

    def burst_detection(
        self,
        signals: list[dict[str, Any]],
        threshold: int = 20,
        window_minutes: int = 10,
    ) -> list[int]:
        """Counts posts per topic/location within a time window. Returns indices of signals in burst clusters."""
        if not signals:
            return []

        flagged_indices: list[int] = []
        buckets: dict[str, list[int]] = {}

        for i, signal in enumerate(signals):
            payload = signal.get("payload", {})
            location = signal.get("location", {})
            coords = location.get("coordinates", [0, 0])
            topic = payload.get("topic", payload.get("category", "unknown"))
            coord_key = f"{round(coords[0], 1)},{round(coords[1], 1)}" if coords else "0,0"
            bucket_key = f"{topic}:{coord_key}"
            buckets.setdefault(bucket_key, []).append(i)

        for _key, indices in buckets.items():
            if len(indices) < threshold:
                continue
            timestamps = []
            for idx in indices:
                occurred = signals[idx].get("occurredAt", "")
                try:
                    timestamps.append(datetime.fromisoformat(occurred.replace("Z", "+00:00")))
                except (ValueError, AttributeError):
                    continue

            if len(timestamps) < 2:
                continue
            timestamps.sort()
            window_start = 0
            for window_end in range(len(timestamps)):
                while (timestamps[window_end] - timestamps[window_start]).total_seconds() > window_minutes * 60:
                    window_start += 1
                if (window_end - window_start + 1) >= threshold:
                    flagged_indices.extend(indices[window_start : window_end + 1])
                    break

        return sorted(set(flagged_indices))

    def contradiction_detection(
        self,
        signal: dict[str, Any],
        authoritative_signals: list[dict[str, Any]],
        window_minutes: int = 30,
    ) -> bool:
        """Checks if social signal contradicts authoritative signals for same location/hazard."""
        signal_location = signal.get("location", {}).get("coordinates", [])
        signal_category = signal.get("category", "")

        if not signal_location or not authoritative_signals:
            return True

        signal_time_str = signal.get("occurredAt", "")
        try:
            signal_time = datetime.fromisoformat(signal_time_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return True

        for auth_signal in authoritative_signals:
            auth_location = auth_signal.get("location", {}).get("coordinates", [])
            auth_category = auth_signal.get("category", "")

            if auth_category != signal_category:
                continue

            if not auth_location:
                continue

            distance = abs(auth_location[0] - signal_location[0]) + abs(auth_location[1] - signal_location[1])
            if distance > 1.0:
                continue

            auth_time_str = auth_signal.get("occurredAt", "")
            try:
                auth_time = datetime.fromisoformat(auth_time_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                continue

            if abs((signal_time - auth_time).total_seconds()) <= window_minutes * 60:
                return False

        return True

    def duplicate_amplification_detection(
        self,
        signals: list[dict[str, Any]],
        similarity_threshold: float = 0.9,
        window_minutes: int = 5,
    ) -> list[int]:
        """Flags near-duplicate posts using Jaccard similarity on word sets."""
        if len(signals) < 2:
            return []

        flagged_indices: list[int] = []

        def get_text(s: dict[str, Any]) -> str:
            payload = s.get("payload", {})
            return str(payload.get("text", payload.get("title", payload.get("content", "")))).lower()

        def get_time(s: dict[str, Any]) -> datetime | None:
            try:
                return datetime.fromisoformat(s.get("occurredAt", "").replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                return None

        def jaccard_similarity(a: str, b: str) -> float:
            words_a = set(a.split())
            words_b = set(b.split())
            if not words_a or not words_b:
                return 0.0
            intersection = words_a & words_b
            union = words_a | words_b
            return len(intersection) / len(union)

        for i in range(len(signals)):
            text_i = get_text(signals[i])
            time_i = get_time(signals[i])
            if not text_i or not time_i:
                continue
            for j in range(i + 1, len(signals)):
                text_j = get_text(signals[j])
                time_j = get_time(signals[j])
                if not text_j or not time_j:
                    continue
                if abs((time_i - time_j).total_seconds()) > window_minutes * 60:
                    continue
                if jaccard_similarity(text_i, text_j) >= similarity_threshold:
                    flagged_indices.append(j)

        return sorted(set(flagged_indices))

    def detect(
        self,
        signal: dict[str, Any],
        recent_signals: list[dict[str, Any]],
        authoritative_signals: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Run all detections and return validation result with adjusted confidence."""
        confidence = signal.get("confidenceScore", 0.3)
        validation_status = signal.get("validationStatus", "pending")
        flags: list[str] = []

        burst_indices = self.burst_detection(recent_signals)
        signal_idx = None
        for i, s in enumerate(recent_signals):
            if s is signal:
                signal_idx = i
                break
        if signal_idx is not None and signal_idx in burst_indices:
            flags.append("burst_detected")
            validation_status = "escalated"

        has_contradiction = self.contradiction_detection(signal, authoritative_signals)
        if has_contradiction:
            flags.append("no_authoritative_corroboration")
            confidence *= 0.5

        dup_indices = self.duplicate_amplification_detection(recent_signals)
        if signal_idx is not None and signal_idx in dup_indices:
            flags.append("duplicate_amplification")
            validation_status = "escalated"
            confidence *= 0.7

        return {
            "validationStatus": validation_status,
            "confidenceScore": round(max(0.0, min(1.0, confidence)), 4),
            "flags": flags,
        }
