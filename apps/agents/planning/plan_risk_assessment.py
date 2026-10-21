"""Multi-environment risk analysis for emergency planning.

Supports cascading, concurrent, and catastrophic scenarios across
the four environments (social, built, economic, natural).

FRs: FR-003 | Research: R-001
"""

from typing import Literal, TypedDict

RiskEnvironment = Literal["social", "built", "economic", "natural"]
ScenarioType = Literal["cascading", "concurrent", "catastrophic", "single"]

RISK_ENVIRONMENTS: list[str] = ["social", "built", "economic", "natural"]


class EnvironmentRisk(TypedDict):
    environment: str
    risk_level: str
    hazard_exposure: list[str]
    cascading_risks: list[str]
    mitigation_strategies: list[str]


class RiskAssessment(TypedDict):
    region_id: str
    hazard_types: list[str]
    scenario_type: ScenarioType
    environments: dict[str, EnvironmentRisk]


def assess_risks(
    *,
    hazard_types: list[str],
    region_id: str,
    scenario_type: ScenarioType = "single",
) -> RiskAssessment:
    """Run a multi-environment risk assessment for the given hazards and region.

    Returns a structured risk assessment with per-environment analysis.
    """
    assessment: RiskAssessment = {
        "region_id": region_id,
        "hazard_types": hazard_types,
        "scenario_type": scenario_type,
        "environments": {},
    }
    for env in RISK_ENVIRONMENTS:
        assessment["environments"][env] = {
            "environment": env,
            "risk_level": "medium",  # Placeholder — would integrate with risk models
            "hazard_exposure": [h for h in hazard_types],
            "cascading_risks": (
                _identify_cascading_risks(env, hazard_types) if scenario_type in ("cascading", "catastrophic") else []
            ),
            "mitigation_strategies": [],
        }
    return assessment


def _identify_cascading_risks(environment: str, hazard_types: list[str]) -> list[str]:
    """Identify potential cascading risks from one environment to others."""
    cascading_map = {
        "built": ["Damaged infrastructure affects economic activity", "Infrastructure failure impacts social services"],
        "natural": [
            "Environmental damage affects water supply (built)",
            "Ecosystem disruption affects agriculture (economic)",
        ],
        "economic": [
            "Business closures affect employment (social)",
            "Supply chain disruption affects built repairs",
        ],
        "social": [
            "Population displacement affects economic recovery",
            "Health impacts delay infrastructure rebuilding",
        ],
    }
    return cascading_map.get(environment, [])
