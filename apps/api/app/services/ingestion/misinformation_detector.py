import logging
import math
import re
from collections import Counter
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


class MisinformationDetector:
    """Detects misinformation patterns in social media signals."""

    def __init__(
        self,
        *,
        burst_threshold: int = 20,
        burst_window_minutes: int = 10,
        contradiction_window_minutes: int = 30,
        contradiction_distance_km: float = 25.0,
        duplicate_similarity_threshold: float = 0.9,
        duplicate_window_minutes: int = 5,
    ) -> None:
        self.burst_threshold = burst_threshold
        self.burst_window_minutes = burst_window_minutes
        self.contradiction_window_minutes = contradiction_window_minutes
        self.contradiction_distance_km = contradiction_distance_km
        self.duplicate_similarity_threshold = duplicate_similarity_threshold
        self.duplicate_window_minutes = duplicate_window_minutes

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime | None:
        if not isinstance(value, str):
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _signal_id(signal: dict[str, Any]) -> str | None:
        candidates = [
            signal.get("signalId"),
            signal.get("signal_id"),
            signal.get("id"),
            _mapping(signal.get("payload")).get("signalId"),
        ]
        for candidate in candidates:
            if candidate is None:
                continue
            value = str(candidate).strip()
            if value:
                return value
        return None

    @staticmethod
    def _account_id(signal: dict[str, Any]) -> str:
        payload = _mapping(signal.get("payload"))
        source = _mapping(signal.get("source"))
        for key in ("accountId", "authorId", "userId", "sourceAccountId", "account"):
            value = payload.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
        for key in ("accountId", "authorId", "userId"):
            value = source.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
        return "unknown"

    @staticmethod
    def _topic_bucket(signal: dict[str, Any]) -> str:
        payload = _mapping(signal.get("payload"))
        topic = str(payload.get("topic", payload.get("category", signal.get("category", "unknown")))).strip().lower()
        location = _mapping(signal.get("location"))
        points = MisinformationDetector._extract_points(location)
        if points:
            lon, lat = points[0]
            return f"{topic}:{round(lon, 1)},{round(lat, 1)}"
        return f"{topic}:unknown"

    @staticmethod
    def _extract_points(geometry: dict[str, Any]) -> list[tuple[float, float]]:
        kind = str(geometry.get("type", ""))
        coords = geometry.get("coordinates")
        if kind == "Point" and isinstance(coords, list) and len(coords) >= 2:
            return [(float(coords[0]), float(coords[1]))]
        points: list[tuple[float, float]] = []
        if kind == "Polygon" and isinstance(coords, list):
            for ring in coords:
                if isinstance(ring, list):
                    for point in ring:
                        if isinstance(point, list) and len(point) >= 2:
                            points.append((float(point[0]), float(point[1])))
        if kind == "MultiPolygon" and isinstance(coords, list):
            for polygon in coords:
                if not isinstance(polygon, list):
                    continue
                for ring in polygon:
                    if not isinstance(ring, list):
                        continue
                    for point in ring:
                        if isinstance(point, list) and len(point) >= 2:
                            points.append((float(point[0]), float(point[1])))
        return points

    @staticmethod
    def _extract_polygons(geometry: dict[str, Any]) -> list[list[tuple[float, float]]]:
        kind = str(geometry.get("type", ""))
        coords = geometry.get("coordinates")
        polygons: list[list[tuple[float, float]]] = []
        if kind == "Polygon" and isinstance(coords, list):
            for ring in coords:
                if not isinstance(ring, list):
                    continue
                poly = [
                    (float(point[0]), float(point[1])) for point in ring if isinstance(point, list) and len(point) >= 2
                ]
                if poly:
                    polygons.append(poly)
        if kind == "MultiPolygon" and isinstance(coords, list):
            for polygon in coords:
                if not isinstance(polygon, list):
                    continue
                for ring in polygon:
                    if not isinstance(ring, list):
                        continue
                    poly = [
                        (float(point[0]), float(point[1]))
                        for point in ring
                        if isinstance(point, list) and len(point) >= 2
                    ]
                    if poly:
                        polygons.append(poly)
        return polygons

    @staticmethod
    def _haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
        lon1, lat1 = a
        lon2, lat2 = b
        r = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        lat1r = math.radians(lat1)
        lat2r = math.radians(lat2)
        h = math.sin(dlat / 2) ** 2 + math.cos(lat1r) * math.cos(lat2r) * math.sin(dlon / 2) ** 2
        return 2 * r * math.asin(math.sqrt(h))

    @staticmethod
    def _point_in_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
        if len(polygon) < 3:
            return False
        x, y = point
        inside = False
        j = len(polygon) - 1
        for i in range(len(polygon)):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            intersects = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi)
            if intersects:
                inside = not inside
            j = i
        return inside

    @staticmethod
    def _bbox(polygons: list[list[tuple[float, float]]]) -> tuple[float, float, float, float] | None:
        points = [p for poly in polygons for p in poly]
        if not points:
            return None
        lons = [p[0] for p in points]
        lats = [p[1] for p in points]
        return min(lons), min(lats), max(lons), max(lats)

    @classmethod
    def _geometries_overlap(
        cls,
        lhs: dict[str, Any],
        rhs: dict[str, Any],
        *,
        max_distance_km: float,
    ) -> bool:
        lhs_points = cls._extract_points(lhs)
        rhs_points = cls._extract_points(rhs)
        lhs_polys = cls._extract_polygons(lhs)
        rhs_polys = cls._extract_polygons(rhs)

        if lhs_points and rhs_points:
            return any(cls._haversine_km(a, b) <= max_distance_km for a in lhs_points for b in rhs_points)

        if lhs_points and rhs_polys:
            return any(any(cls._point_in_polygon(point, poly) for poly in rhs_polys) for point in lhs_points)

        if rhs_points and lhs_polys:
            return any(any(cls._point_in_polygon(point, poly) for poly in lhs_polys) for point in rhs_points)

        if lhs_polys and rhs_polys:
            bbox_l = cls._bbox(lhs_polys)
            bbox_r = cls._bbox(rhs_polys)
            if bbox_l is None or bbox_r is None:
                return False
            l_min_lon, l_min_lat, l_max_lon, l_max_lat = bbox_l
            r_min_lon, r_min_lat, r_max_lon, r_max_lat = bbox_r
            return not (
                l_max_lon < r_min_lon or r_max_lon < l_min_lon or l_max_lat < r_min_lat or r_max_lat < l_min_lat
            )

        return False

    @staticmethod
    def _token_frequency(text: str) -> Counter[str]:
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        return Counter(tokens)

    @staticmethod
    def _cosine_similarity(left: Counter[str], right: Counter[str]) -> float:
        if not left or not right:
            return 0.0
        dot = sum(left[token] * right.get(token, 0) for token in left)
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        if left_norm == 0.0 or right_norm == 0.0:
            return 0.0
        return dot / (left_norm * right_norm)

    def _is_authoritative_signal(self, signal: dict[str, Any]) -> bool:
        source = _mapping(signal.get("source"))
        return str(source.get("kind", "")).strip().lower() == "authoritative"

    def has_authoritative_corroboration(
        self,
        signal: dict[str, Any],
        authoritative_signals: list[dict[str, Any]],
        *,
        window_minutes: int | None = None,
        max_distance_km: float | None = None,
    ) -> bool:
        if not authoritative_signals:
            return False

        signal_time = self._parse_timestamp(signal.get("occurredAt"))
        if signal_time is None:
            return False
        signal_category = str(signal.get("category", "")).strip()
        signal_location = _mapping(signal.get("location"))
        if not signal_location:
            return False

        time_window = window_minutes if window_minutes is not None else self.contradiction_window_minutes
        distance_km = max_distance_km if max_distance_km is not None else self.contradiction_distance_km

        for auth_signal in authoritative_signals:
            if not self._is_authoritative_signal(auth_signal):
                continue
            if str(auth_signal.get("category", "")).strip() != signal_category:
                continue
            auth_time = self._parse_timestamp(auth_signal.get("occurredAt"))
            if auth_time is None:
                continue
            if abs((signal_time - auth_time).total_seconds()) > time_window * 60:
                continue
            auth_location = _mapping(auth_signal.get("location"))
            if not auth_location:
                continue
            if self._geometries_overlap(signal_location, auth_location, max_distance_km=distance_km):
                return True
        return False

    def burst_detection(
        self,
        signals: list[dict[str, Any]],
        threshold: int | None = None,
        window_minutes: int | None = None,
        authoritative_signals: list[dict[str, Any]] | None = None,
    ) -> list[int]:
        """Flags bursts by distinct account count for uncorroborated posts only."""
        if not signals:
            return []

        min_accounts = threshold if threshold is not None else self.burst_threshold
        window = window_minutes if window_minutes is not None else self.burst_window_minutes

        flagged_indices: list[int] = []
        buckets: dict[str, list[tuple[int, datetime, str]]] = {}

        for i, signal in enumerate(signals):
            if authoritative_signals and self.has_authoritative_corroboration(signal, authoritative_signals):
                continue
            signal_time = self._parse_timestamp(signal.get("occurredAt"))
            if signal_time is None:
                continue
            bucket_key = self._topic_bucket(signal)
            account_id = self._account_id(signal)
            buckets.setdefault(bucket_key, []).append((i, signal_time, account_id))

        for tuples in buckets.values():
            if len(tuples) < min_accounts:
                continue

            tuples.sort(key=lambda item: item[1])
            window_start = 0
            for window_end in range(len(tuples)):
                while (tuples[window_end][1] - tuples[window_start][1]).total_seconds() > window * 60:
                    window_start += 1

                window_tuples = tuples[window_start : window_end + 1]
                distinct_accounts = {entry[2] for entry in window_tuples if entry[2] != "unknown"}
                account_count = len(distinct_accounts) if distinct_accounts else len(window_tuples)
                if account_count >= min_accounts:
                    flagged_indices.extend([entry[0] for entry in window_tuples])

        return sorted(set(flagged_indices))

    def contradiction_detection(
        self,
        signal: dict[str, Any],
        authoritative_signals: list[dict[str, Any]],
        window_minutes: int | None = None,
        max_distance_km: float | None = None,
    ) -> bool:
        """Checks contradiction against corroborating authoritative signals only."""
        time_window = window_minutes if window_minutes is not None else self.contradiction_window_minutes
        distance_km = max_distance_km if max_distance_km is not None else self.contradiction_distance_km
        if not self.has_authoritative_corroboration(
            signal,
            authoritative_signals,
            window_minutes=time_window,
            max_distance_km=distance_km,
        ):
            return False

        payload = _mapping(signal.get("payload"))
        text_blob = " ".join(
            str(payload.get(key, "")) for key in ("text", "title", "content", "status", "hazard_state", "condition")
        ).lower()
        social_hazard_claim = any(token in text_blob for token in ("fire", "flood", "cyclone", "evacuat", "emergency"))

        for auth_signal in authoritative_signals:
            if not self._is_authoritative_signal(auth_signal):
                continue
            if str(auth_signal.get("category", "")).strip() != str(signal.get("category", "")).strip():
                continue
            if not self.has_authoritative_corroboration(
                signal,
                [auth_signal],
                window_minutes=time_window,
                max_distance_km=distance_km,
            ):
                continue

            auth_payload = _mapping(auth_signal.get("payload"))
            auth_text = " ".join(
                str(auth_payload.get(key, "")) for key in ("status", "hazard_state", "condition", "text", "title")
            ).lower()
            authoritative_denial = any(
                token in auth_text for token in ("contained", "controlled", "false alarm", "all clear", "resolved")
            )
            if social_hazard_claim and authoritative_denial:
                return True

        return False

    def duplicate_amplification_detection(
        self,
        signals: list[dict[str, Any]],
        similarity_threshold: float | None = None,
        window_minutes: int | None = None,
        comparison_context: list[dict[str, Any]] | None = None,
    ) -> list[int]:
        """Flags duplicate amplification using cosine similarity; retains earliest timestamp member."""
        if len(signals) < 2 and not comparison_context:
            return []

        threshold = similarity_threshold if similarity_threshold is not None else self.duplicate_similarity_threshold
        window = window_minutes if window_minutes is not None else self.duplicate_window_minutes

        flagged_indices: list[int] = []
        context = comparison_context or []

        def get_text(s: dict[str, Any]) -> str:
            payload = s.get("payload", {})
            return str(payload.get("text", payload.get("title", payload.get("content", "")))).lower()

        def get_time(s: dict[str, Any]) -> datetime | None:
            return self._parse_timestamp(s.get("occurredAt"))

        # Include cross-batch context as immutable candidates; only current-batch indices are returned.
        candidates: list[tuple[int | None, datetime, Counter[str]]] = []
        for signal in context:
            text = get_text(signal)
            timestamp = get_time(signal)
            if not text or timestamp is None:
                continue
            candidates.append((None, timestamp, self._token_frequency(text)))

        indexed_batch: list[tuple[int, datetime, Counter[str]]] = []
        for index, signal in enumerate(signals):
            text = get_text(signal)
            timestamp = get_time(signal)
            if not text or timestamp is None:
                continue
            indexed_batch.append((index, timestamp, self._token_frequency(text)))

        candidates.extend(indexed_batch)
        candidates.sort(key=lambda item: item[1])

        for i in range(len(candidates)):
            left_index, left_time, left_tokens = candidates[i]
            if left_tokens is None:
                continue
            for j in range(i + 1, len(candidates)):
                right_index, right_time, right_tokens = candidates[j]
                if (right_time - left_time).total_seconds() > window * 60:
                    break
                similarity = self._cosine_similarity(left_tokens, right_tokens)
                if similarity < threshold:
                    continue

                # Keep earliest timestamp member of similar cluster.
                if left_index is not None and right_index is not None:
                    flagged_indices.append(right_index)
                elif left_index is None and right_index is not None:
                    flagged_indices.append(right_index)

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

        burst_indices = self.burst_detection(
            recent_signals,
            threshold=self.burst_threshold,
            window_minutes=self.burst_window_minutes,
            authoritative_signals=authoritative_signals,
        )
        signal_idx = None
        signal_id = self._signal_id(signal)
        for i, s in enumerate(recent_signals):
            if signal_id and self._signal_id(s) == signal_id:
                signal_idx = i
                break
        if signal_idx is not None and signal_idx in burst_indices:
            flags.append("burst_detected")
            validation_status = "escalated"

        has_corroboration = self.has_authoritative_corroboration(signal, authoritative_signals)
        if not has_corroboration:
            flags.append("no_authoritative_corroboration")
            confidence *= 0.5
        elif self.contradiction_detection(signal, authoritative_signals):
            flags.append("authoritative_contradiction")
            validation_status = "escalated"
            confidence *= 0.5

        dup_indices = self.duplicate_amplification_detection(
            recent_signals,
            similarity_threshold=self.duplicate_similarity_threshold,
            window_minutes=self.duplicate_window_minutes,
            comparison_context=authoritative_signals,
        )
        if signal_idx is not None and signal_idx in dup_indices:
            flags.append("duplicate_amplification")
            validation_status = "escalated"
            confidence *= 0.7

        return {
            "validationStatus": validation_status,
            "confidenceScore": round(max(0.0, min(1.0, confidence)), 4),
            "flags": flags,
        }
