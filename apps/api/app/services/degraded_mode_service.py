from dataclasses import dataclass


@dataclass(frozen=True)
class DegradedModeState:
    degraded_sources: tuple[str, ...]
    requires_manual_review: bool


class DegradedModeService:
    def evaluate(self, source_status: dict[str, str]) -> DegradedModeState:
        degraded = tuple(
            name for name, status in source_status.items() if status in {"degraded", "offline", "stale", "untrusted"}
        )
        return DegradedModeState(
            degraded_sources=degraded,
            requires_manual_review=bool(degraded),
        )
