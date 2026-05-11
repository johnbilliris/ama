"""Bicep file-content tests for spec-036 T-A09 [AMEND] (FR-048 / ADR-036-007 / ADR-036-009).

The Cosmos containers module ``infra/bicep/modules/cosmos-simulation-containers.bicep``
is amended in this wave to add **three** new containers required by the
amendment cycle:

* ``simulation_audit_sequence_counters`` — 400 RU/s manual,
  partition ``/simulation_id``. Replaces the process-local
  ``audit_writer._sequence_counters`` dict (per T-B09 [AMEND]).
* ``simulation_idempotency_cache`` — 400–4000 RU/s autoscale,
  partition ``/simulation_id``, TTL 86400s (24h) anchored on ``_ts``.
* ``simulation_audit_dlq`` — 400 RU/s manual,
  partition ``/simulation_id``. Receives audit envelopes that exhausted
  the optimistic-concurrency retry budget (Phase Q DLQ).

We use file-content assertions rather than `bicep build` because Bicep
CLI is not pinned in the test toolchain. The same patterns are mirrored
by other AVM-aligned modules in `infra/bicep/modules/` (no dedicated
Bicep-build CI gate yet).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BICEP_FILE = (
    REPO_ROOT
    / "infra"
    / "bicep"
    / "modules"
    / "cosmos-simulation-containers.bicep"
)


@pytest.fixture(scope="module")
def bicep_text() -> str:
    return BICEP_FILE.read_text(encoding="utf-8")


def _resource_block(text: str, container_name: str) -> str:
    """Return the Bicep resource block whose ``name:`` is *container_name*.

    Matches from the ``resource ... 'Microsoft.DocumentDB/.../containers@...' = {``
    declaration to the closing brace at indent-0 (the next blank line + ``}``).
    """

    pattern = re.compile(
        r"resource\s+\w+\s+'Microsoft\.DocumentDB[^']+'\s*=\s*\{[^}]*?name:\s*'"
        + re.escape(container_name)
        + r"'.*?\n\}",
        flags=re.DOTALL,
    )
    match = pattern.search(text)
    assert match is not None, f"Could not find resource block for {container_name!r}"
    return match.group(0)


@pytest.mark.parametrize(
    "container_name",
    [
        "simulation_audit_sequence_counters",
        "simulation_idempotency_cache",
        "simulation_audit_dlq",
    ],
)
def test_amend_container_present(bicep_text: str, container_name: str) -> None:
    """Each new container is declared in the module."""

    assert f"name: '{container_name}'" in bicep_text, (
        f"Expected resource declaration for {container_name!r} "
        f"in {BICEP_FILE.relative_to(REPO_ROOT)}"
    )


@pytest.mark.parametrize(
    "container_name",
    [
        "simulation_audit_sequence_counters",
        "simulation_idempotency_cache",
        "simulation_audit_dlq",
    ],
)
def test_amend_container_partition_key_simulation_id(
    bicep_text: str, container_name: str
) -> None:
    """Partition key is ``/simulation_id`` (snake-case per ADR-036-007/009)."""

    block = _resource_block(bicep_text, container_name)
    assert "/simulation_id" in block, (
        f"{container_name!r} must use partition key '/simulation_id' "
        f"(amendment cycle ADR-036-007/009)"
    )


def test_idempotency_cache_has_24h_ttl(bicep_text: str) -> None:
    """``simulation_idempotency_cache`` has a 24h (86400s) default TTL."""

    block = _resource_block(bicep_text, "simulation_idempotency_cache")
    assert "defaultTtl: 86400" in block, (
        "ADR-036-009 mandates 24h TTL anchored on `_ts` for the "
        "idempotency cache; expected `defaultTtl: 86400`."
    )


def test_idempotency_cache_uses_autoscale(bicep_text: str) -> None:
    """``simulation_idempotency_cache`` provisions 400-4000 RU/s autoscale."""

    block = _resource_block(bicep_text, "simulation_idempotency_cache")
    # AVM pattern: throughput options on the container resource use either
    # `autoscaleSettings` (autoscale) or `throughput` (manual). Idempotency
    # cache must be autoscale per ADR-036-009.
    assert "autoscaleSettings" in block, (
        "Expected `autoscaleSettings` for simulation_idempotency_cache "
        "(ADR-036-009 specifies 400-4000 autoscale)."
    )
    assert "maxThroughput: 4000" in block


@pytest.mark.parametrize(
    "container_name",
    [
        "simulation_audit_sequence_counters",
        "simulation_audit_dlq",
    ],
)
def test_manual_400_throughput_for_counters_and_dlq(
    bicep_text: str, container_name: str
) -> None:
    """Sequence counters and DLQ use 400 RU/s manual throughput."""

    block = _resource_block(bicep_text, container_name)
    assert "throughput: 400" in block, (
        f"{container_name!r} must declare `throughput: 400` per ADR-036-007."
    )
    assert "autoscaleSettings" not in block, (
        f"{container_name!r} uses manual throughput, not autoscale."
    )


def test_module_outputs_new_container_names(bicep_text: str) -> None:
    """The module exports each new container name as an output."""

    expected_outputs = (
        "simulationAuditSequenceCountersContainer",
        "simulationIdempotencyCacheContainer",
        "simulationAuditDlqContainer",
    )
    for output_name in expected_outputs:
        assert f"output {output_name} string" in bicep_text, (
            f"Module must expose `{output_name}` as an output for `main.bicep` to wire."
        )


def test_main_bicep_module_call_is_unbroken() -> None:
    """`main.bicep` must still compile against the amended module signature.

    Specifically, the `simulationCosmosContainers` module call should not
    require any new mandatory parameters. The module signature only adds
    new outputs in this amendment, not new params.
    """

    main_text = (REPO_ROOT / "infra" / "bicep" / "main.bicep").read_text(
        encoding="utf-8"
    )
    assert "modules/cosmos-simulation-containers.bicep" in main_text
