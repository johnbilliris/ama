"""Foundry carve-out registry repository (spec-035 T070 / FR-029).

Backs the ``GET /api/governance/carveout-registry`` route. Each registry
entry pairs a model identifier with its review cadence (``review_date`` and
``approver_identities``) per ``research.md`` § R-011 in
[035-webapp-capstone-closure](../../../../specs/035-webapp-capstone-closure/research.md).

The seed file lives under
[`data/governance/foundry_carveout_registry.json`](../../../../data/governance/foundry_carveout_registry.json)
and is shipped with the repository so the CI gate in T071 has a deterministic
list to evaluate. The runtime container is Cosmos DB (``carveout_registry``);
this repository is currently file-backed but exposes the same async surface
so the swap to Cosmos is local to this file.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Final

_SEED_PATH: Final[Path] = (
    Path(__file__).resolve().parents[4]
    / "data"
    / "governance"
    / "foundry_carveout_registry.json"
)

_STALE_AFTER = timedelta(days=90)


@dataclass(frozen=True)
class CarveoutEntry:
    model_id: str
    review_date: str
    approver_identities: tuple[str, ...]
    notes: str | None = None

    def is_stale(self, *, now: datetime | None = None) -> bool:
        reference = now or datetime.now(tz=UTC)
        review_dt = datetime.fromisoformat(self.review_date)
        if review_dt.tzinfo is None:
            review_dt = review_dt.replace(tzinfo=UTC)
        return reference - review_dt > _STALE_AFTER


@dataclass
class CarveoutRegistryRepository:
    entries: tuple[CarveoutEntry, ...]

    @classmethod
    def from_seed(cls, seed_path: Path = _SEED_PATH) -> CarveoutRegistryRepository:
        if not seed_path.exists():
            return cls(entries=())
        payload = json.loads(seed_path.read_text(encoding="utf-8"))
        rows: list[CarveoutEntry] = []
        for row in payload:
            rows.append(
                CarveoutEntry(
                    model_id=row["model_id"],
                    review_date=row["review_date"],
                    approver_identities=tuple(row.get("approver_identities", [])),
                    notes=row.get("notes"),
                ),
            )
        return cls(entries=tuple(rows))

    def list_entries(self) -> list[dict[str, object]]:
        return [
            {
                **asdict(entry),
                "approver_identities": list(entry.approver_identities),
                "is_stale": entry.is_stale(),
            }
            for entry in self.entries
        ]

    def stale_entries(self) -> list[CarveoutEntry]:
        return [entry for entry in self.entries if entry.is_stale()]


@lru_cache(maxsize=1)
def get_carveout_registry_repository() -> CarveoutRegistryRepository:
    return CarveoutRegistryRepository.from_seed()


def reset_carveout_registry_repository() -> None:
    get_carveout_registry_repository.cache_clear()


__all__ = [
    "CarveoutEntry",
    "CarveoutRegistryRepository",
    "get_carveout_registry_repository",
    "reset_carveout_registry_repository",
]
