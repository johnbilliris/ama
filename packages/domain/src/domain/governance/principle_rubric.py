from __future__ import annotations

from typing import TypedDict

from packages.domain.src.domain.models.constitutional_assessment import ConstitutionalPrinciple

RUBRIC_VERSION = "1.2.0"
RUBRIC_SOURCE = ".specify/memory/constitution.md"


class PrincipleRubricEntry(TypedDict):
    principle_id: ConstitutionalPrinciple
    label: str
    constitutional_section: str
    constitutional_anchor: str
    fr_004a_criteria: list[str]


# Repository implementation policy only:
# this maps feature principle ids to constitution sections for consistent review.
RUBRIC_CHANGE_CONTROL = {
    "owner": "governance-lead",
    "status": "approved_for_repository_implementation",
    "external_certification": "not_a_legal_or_regulatory_certification",
    "change_process": "update in PR with governance-lead approval and version bump",
}


PRINCIPLE_RUBRIC: dict[ConstitutionalPrinciple, PrincipleRubricEntry] = {
    "life_safety_first": {
        "principle_id": "life_safety_first",
        "label": "I. Primacy of Life and Harm Reduction",
        "constitutional_section": "Core Principles",
        "constitutional_anchor": "I. Primacy of Life and Harm Reduction",
        "fr_004a_criteria": [
            "Does the source provide data used in safety-critical decisions (evacuation, alerts)?",
            "Is the source reliable enough for life-safety use?",
            "Are there failure modes that could endanger life if the source provides incorrect data?",
        ],
    },
    "multi_agent_coordination": {
        "principle_id": "multi_agent_coordination",
        "label": "II/II-A/III. National Principles, AIIMS Alignment, Multi-Agency Design",
        "constitutional_section": "Core Principles",
        "constitutional_anchor": "II. National Emergency Management Principles",
        "fr_004a_criteria": [
            "Which agents consume this source?",
            "Are handoff boundaries clear?",
            "Could ambiguous ownership cause gaps or duplicated processing?",
        ],
    },
    "data_trust_provenance_freshness": {
        "principle_id": "data_trust_provenance_freshness",
        "label": "IV. Transparency and Auditability",
        "constitutional_section": "Core Principles",
        "constitutional_anchor": "IV. Transparency and Auditability",
        "fr_004a_criteria": [
            "Does the source provide provenance metadata (origin, collection method, timestamp)?",
            "Is the source authoritative or unverified?",
            "What is the expected freshness and how is staleness detected?",
            "Can contradictory signals from this source be identified?",
        ],
    },
    "privacy_security_regional_policy": {
        "principle_id": "privacy_security_regional_policy",
        "label": "Non-Negotiables #2/#3 with constitutional transparency",
        "constitutional_section": "NON-NEGOTIABLE Requirements",
        "constitutional_anchor": "2. Data sovereignty",
        "fr_004a_criteria": [
            "Does the source contain or transmit PII or sensitive location data?",
            "Does the source require data-sharing agreements?",
            "Does it comply with Australian Privacy Principles?",
            "Are there jurisdictional data residency requirements?",
        ],
    },
    "multilingual_accessible_actionable": {
        "principle_id": "multilingual_accessible_actionable",
        "label": "V. Warning and Public Information",
        "constitutional_section": "Core Principles",
        "constitutional_anchor": "V. Warning and Public Information",
        "fr_004a_criteria": [
            "Does the source provide content that will be used in public alerts?",
            "If so, does the content support multilingual requirements or require translation?",
        ],
    },
    "cloud_platform": {
        "principle_id": "cloud_platform",
        "label": "VIII. Cloud Platform and Infrastructure",
        "constitutional_section": "Core Principles",
        "constitutional_anchor": "VIII. Cloud Platform and Infrastructure",
        "fr_004a_criteria": [
            "Does the source require connectivity to systems outside Australian Azure regions?",
            "Are there data residency constraints that affect ingestion architecture?",
        ],
    },
}

REQUIRED_PRINCIPLES = frozenset(PRINCIPLE_RUBRIC.keys())
