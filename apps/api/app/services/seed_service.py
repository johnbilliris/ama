from pathlib import Path

from packages.domain.src.domain.seed.bootstrap import bootstrap_seed_data


class SeedService:
    def load(self, seed_root: Path) -> dict[str, list[dict[str, object]]]:
        return bootstrap_seed_data(seed_root)
