"""Contract checks for the local Cosmos emulator schema."""

from scripts.seed_loader import LOCAL_COSMOS_CONTAINER_SPECS


def test_simulation_container_partition_key_matches_infrastructure() -> None:
    specs = {name: (paths, kind) for name, paths, kind in LOCAL_COSMOS_CONTAINER_SPECS}

    assert specs["simulation"] == (("/scenario_id",), "Hash")
