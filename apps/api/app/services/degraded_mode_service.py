from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class DegradedModeState:
    degraded_sources: tuple[str, ...]
    requires_manual_review: bool
    degraded_source_details: tuple[dict[str, str], ...] = ()


class DegradedModeService:
    _DEGRADED_STATES = {"degraded", "offline", "stale", "untrusted", "unavailable", "open"}

    def evaluate(self, source_status: dict[str, str | dict[str, Any]]) -> DegradedModeState:
        degraded: list[str] = []
        details: list[dict[str, str]] = []
        for source_id, status_value in source_status.items():
            if isinstance(status_value, dict):
                state = str(status_value.get("status", "available"))
                reason = str(status_value.get("reason", state))
                since = str(status_value.get("since", datetime.now(UTC).isoformat()))
            else:
                state = str(status_value)
                reason = state
                since = datetime.now(UTC).isoformat()

            if state in self._DEGRADED_STATES:
                degraded.append(source_id)
                details.append(
                    {
                        "sourceId": source_id,
                        "status": state,
                        "reason": reason,
                        "since": since,
                    }
                )

        return DegradedModeState(
            degraded_sources=tuple(degraded),
            requires_manual_review=bool(degraded),
            degraded_source_details=tuple(details),
        )
