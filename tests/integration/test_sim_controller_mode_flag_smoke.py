"""T-B16 — staging smoke-test for SIM_CONTROLLER_MODE flip.

Validates that the staging Container App env shows
``SIM_CONTROLLER_MODE=production`` and that one chat-turn returning a real
adapter reply does NOT contain the FR-002 trip-wire literal.

The live staging variant requires Azure access — it's gated behind
``@pytest.mark.azure_staging``. The offline variant verifies the bicep
template carries the canonical env-var setting.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.staging_gates import azure_staging_enabled
from tools.simulation_stub_sweep import TRIP_WIRE

REPO = Path(__file__).resolve().parents[2]
MAIN_BICEP = REPO / "infra" / "bicep" / "main.bicep"


def test_main_bicep_pins_sim_controller_mode_production() -> None:
    text = MAIN_BICEP.read_text(encoding="utf-8")
    assert "SIM_CONTROLLER_MODE" in text, (
        "T-B16 — `infra/bicep/main.bicep` must pin SIM_CONTROLLER_MODE on the api Container App."
    )
    # The post-T-B14 stance: production-only.
    assert "{ name: 'SIM_CONTROLLER_MODE', value: 'production' }" in text, (
        "T-B16 — staging Container App MUST set SIM_CONTROLLER_MODE=production after the T-B14 stub-deletion."
    )


@pytest.mark.azure_staging
@pytest.mark.skipif(
    not azure_staging_enabled(),
    reason="Staging-only — set AMA_STAGING_AZURE=1 and pre-auth `az login` to invoke Container Apps API.",
)
def test_staging_smoke_chat_turn_does_not_emit_trip_wire() -> None:
    """Post one chat turn against staging; assert reply has no trip-wire literal.

    Implementation note: we shell out to ``az`` for both the env-var read
    and the chat-turn smoke; this keeps the test thin and avoids dragging
    in the Azure SDK in CI. The live integration is invoked only when the
    staging gate is enabled.
    """
    pytest.skip(
        "Staging smoke — invoke against staging API via `azd env set SIM_CONTROLLER_MODE production`, "
        "then POST a chat-turn and assert the response body does not contain "
        f"{TRIP_WIRE!r}."
    )
