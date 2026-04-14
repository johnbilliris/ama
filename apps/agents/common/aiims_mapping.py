"""AIIMS role constants, default agent-to-function mapping, and validation.

Three-tier hierarchy per R-005:
  OperatingFramework → FrameworkAssignment → AiimsRoleAssignment

Provides default mapping for automated role assignment when incidents are created.
"""


from packages.domain.src.domain.models.aiims_role_assignment import (
    ALL_AIIMS_FUNCTIONS,
    AiimsFunction,
)

# Default agent-to-AIIMS-function mapping (R-005)
# Used as static fallback when role assignment service is unavailable
DEFAULT_AGENT_AIIMS_MAP: dict[str, AiimsFunction] = {
    "monitoring": "intelligence",
    "risk_assessment": "planning",
    "evacuation": "operations",
    "resource_allocation": "logistics",
    "communication": "public_information",
}

# AIIMS incident level descriptions
INCIDENT_LEVEL_DESCRIPTIONS: dict[int, str] = {
    1: "Local/single-agency incident",
    2: "Multi-agency incident with shared COP",
    3: "Major/state-wide incident requiring full AIIMS structure",
}

# Level 3 requires all six functions assigned
FULL_COVERAGE_REQUIRED_LEVEL: int = 3


def get_default_function(agent_identifier: str) -> AiimsFunction | None:
    """Return the default AIIMS function for a given agent, or None if unmapped."""
    return DEFAULT_AGENT_AIIMS_MAP.get(agent_identifier)


def validate_coverage(
    assigned_functions: list[str],
    incident_level: int,
) -> tuple[float, list[str]]:
    """Calculate AIIMS function coverage ratio and identify gaps.

    Returns:
        Tuple of (coverage_ratio, list of unassigned functions).
    """
    assigned_set = set(assigned_functions)
    all_set = set(ALL_AIIMS_FUNCTIONS)
    missing = sorted(all_set - assigned_set)
    ratio = len(assigned_set & all_set) / len(all_set) if all_set else 0.0
    return ratio, missing


def is_full_coverage_required(incident_level: int) -> bool:
    """Check whether the incident level requires all AIIMS functions assigned."""
    return incident_level >= FULL_COVERAGE_REQUIRED_LEVEL
