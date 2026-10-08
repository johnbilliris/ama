from __future__ import annotations

from scripts.dr_drill_residency_inventory import build_inventory


def test_residency_inventory_passes_for_au_locations() -> None:
    inventory = build_inventory(
        resources=[
            {
                "id": "1",
                "name": "api",
                "type": "Microsoft.App/containerApps",
                "location": "australiaeast",
            }
        ],
        cosmos={
            "id": "cosmos1",
            "name": "cdb",
            "locations": [{"locationName": "australiaeast", "failoverPriority": 0}],
            "backupPolicy": {"type": "Continuous"},
        },
        storage_accounts=[
            {"id": "sa1", "name": "stg", "location": "australiasoutheast", "sku": {"name": "Standard_ZRS"}}
        ],
        telemetry_components=[
            {"id": "ai1", "name": "insights", "type": "Microsoft.Insights/components", "location": "australiaeast"}
        ],
    )

    assert inventory["non_au_resources"] == []


def test_residency_inventory_flags_non_au_locations() -> None:
    inventory = build_inventory(
        resources=[
            {
                "id": "1",
                "name": "api",
                "type": "Microsoft.App/containerApps",
                "location": "eastus",
            }
        ],
        cosmos={
            "id": "cosmos1",
            "name": "cdb",
            "locations": [{"locationName": "japaneast", "failoverPriority": 1}],
            "backupPolicy": {"type": "Periodic"},
        },
        storage_accounts=[],
        telemetry_components=[],
    )

    assert len(inventory["non_au_resources"]) >= 2
