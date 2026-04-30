"""Communication-agent prompt invariant test (T040b, FR-024a, Constitution V).

This invariant prevents silent prompt drift in the Communication agent's
public-alert generation pathway. Constitution V (Warnings — Australian Warning
System tiers + 10 warning principles) compliance is encoded in the existing
prompt text; any drift could weaken life-safety communications without an
operator noticing.

The invariant is asserted as a documented superset relationship:
- The MAF agent's instructions (loaded from communication.yaml) MUST contain
  every required AWS-tier and warning-principle keyword that the legacy
  ``apps/agents/communication/translator.py`` and ``templates.py`` exercise.
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMUNICATION_YAML = REPO_ROOT / "apps" / "agents" / "maf_runtime" / "agents" / "communication.yaml"


# Required tokens — AWS-tier alignment, 10-warning-principle alignment,
# vulnerable-population alignment. All MUST appear in the MAF prompt.
REQUIRED_TOKENS: tuple[str, ...] = (
    # AWS tiers (V-A)
    "Advice",
    "Watch and Act",
    "Emergency Warning",
    # AWS nested model
    "Warning Level",
    "Hazard",
    "Action",
    # Multi-language target set (existing translator default)
    "en-AU",
    # Vulnerability tier reference (V-C / VI-C)
    "Constitution",
    # HITL non-bypassability (NN-1)
    "approval",
    "publish",
    # Output schema reference
    "PublicAlert",
)


def test_communication_prompt_contains_constitution_v_tokens() -> None:
    assert COMMUNICATION_YAML.exists(), f"missing {COMMUNICATION_YAML}"
    definition = yaml.safe_load(COMMUNICATION_YAML.read_text(encoding="utf-8"))
    prompt = definition.get("prompt", "")
    missing = [tok for tok in REQUIRED_TOKENS if tok not in prompt]
    assert not missing, (
        "FR-024a / Constitution V violation: communication.yaml prompt is "
        "missing required Australian Warning System / warning-principle tokens: "
        + ", ".join(missing)
        + ". Prompt drift risks weakening life-safety communications. "
        "Restore the missing tokens or update REQUIRED_TOKENS with explicit reasoning."
    )


def test_communication_prompt_uses_pending_review_pattern() -> None:
    """The prompt must instruct the agent to NEVER set status to a published value."""
    definition = yaml.safe_load(COMMUNICATION_YAML.read_text(encoding="utf-8"))
    prompt = definition.get("prompt", "")
    assert "NEVER" in prompt or "never" in prompt
    assert "publish" in prompt.lower()
