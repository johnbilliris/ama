from __future__ import annotations

from pathlib import Path

MAIN_BICEP = Path("infra/main.bicep")


def test_active_bicep_provisions_simulation_event_container() -> None:
    main = MAIN_BICEP.read_text(encoding="utf-8")

    resource_start = main.index("resource simEventsContainer")
    resource_end = main.index("resource seedContainer", resource_start)
    resource = main[resource_start:resource_end]

    assert "name: 'sim-events'" in resource
    assert "id: 'sim-events'" in resource
    assert "partitionKey: { paths: ['/tenant_id'], kind: 'Hash' }" in resource
    assert "{ path: '/event_seq', order: 'ascending' }" in resource
    assert "{ path: '/sim_time_offset', order: 'ascending' }" in resource
    assert "autoscaleSettings: { maxThroughput: 1000 }" in resource
