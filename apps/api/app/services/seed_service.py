from functools import lru_cache
from pathlib import Path
from typing import Any

from packages.domain.src.domain.seed.bootstrap import bootstrap_seed_data


@lru_cache(maxsize=4)
def _cached_load(seed_root: str) -> dict[str, Any]:
    return bootstrap_seed_data(Path(seed_root))


class SeedService:
    def load(self, seed_root: Path) -> dict[str, Any]:
        return _cached_load(str(seed_root))
