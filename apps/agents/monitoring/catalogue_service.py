"""AIDR catalogue lookup and indicator suggestion service.

Provides browse-by-domain, outcome detail, activity suggestions for lagging
indicators, and evaluation question lookup.

FRs: FR-015–024, FR-026
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SEED_ROOT = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "packages"
    / "domain"
    / "src"
    / "domain"
    / "seed"
    / "recovery-catalogue"
)

DOMAIN_FILES = ["overarching", "social", "economic", "built", "natural"]


class CatalogueService:
    """In-memory AIDR catalogue loaded from seed data."""

    def __init__(self):
        self._outcomes: dict[str, dict] = {}
        self._activities: dict[str, dict] = {}
        self._indicators: dict[str, dict] = {}
        self._evaluation_questions: dict[str, dict] = {}
        self._load_catalogue()

    def _load_catalogue(self):
        for domain in DOMAIN_FILES:
            path = SEED_ROOT / f"{domain}.json"
            if not path.exists():
                logger.warning("Catalogue file not found: %s", path)
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            for outcome in data.get("outcomes", []):
                oid = outcome["outcome_id"]
                self._outcomes[oid] = {
                    "outcome_id": oid,
                    "domain": data["domain"],
                    "objective_type": outcome["objective_type"],
                    "title": outcome["title"],
                    "description": outcome.get("description", ""),
                    "has_developed_activities": outcome.get("has_developed_activities", True),
                    "activity_ids": [a["activity_id"] for a in outcome.get("activities", [])],
                    "indicator_ids": [i["indicator_id"] for i in outcome.get("indicators", [])],
                }
                for act in outcome.get("activities", []):
                    self._activities[act["activity_id"]] = {**act, "outcome_id": oid, "domain": data["domain"]}
                for ind in outcome.get("indicators", []):
                    self._indicators[ind["indicator_id"]] = {**ind, "outcome_id": oid, "domain": data["domain"]}

        # Load evaluation questions
        eq_path = SEED_ROOT / "evaluation-questions.json"
        if eq_path.exists():
            eq_data = json.loads(eq_path.read_text(encoding="utf-8"))
            for domain_q in eq_data.get("evaluation_domains", []):
                self._evaluation_questions[domain_q["domain"]] = domain_q

    def list_outcomes(self, domain: str | None = None, objective_type: str | None = None) -> list[dict]:
        results = list(self._outcomes.values())
        if domain:
            results = [o for o in results if o["domain"] == domain]
        if objective_type:
            results = [o for o in results if o["objective_type"] == objective_type]
        return results

    def get_outcome(self, outcome_id: str) -> dict | None:
        return self._outcomes.get(outcome_id)

    def get_activities_for_outcome(self, outcome_id: str) -> list[dict]:
        outcome = self._outcomes.get(outcome_id)
        if not outcome:
            return []
        return [self._activities[aid] for aid in outcome.get("activity_ids", []) if aid in self._activities]

    def get_indicators_for_outcome(self, outcome_id: str) -> list[dict]:
        outcome = self._outcomes.get(outcome_id)
        if not outcome:
            return []
        return [self._indicators[iid] for iid in outcome.get("indicator_ids", []) if iid in self._indicators]

    def get_domain_summary(self, domain: str) -> dict:
        outcomes = [o for o in self._outcomes.values() if o["domain"] == domain]
        activities = [a for a in self._activities.values() if a["domain"] == domain]
        indicators = [i for i in self._indicators.values() if i["domain"] == domain]
        return {
            "domain": domain,
            "outcome_count": len(outcomes),
            "activity_count": len(activities),
            "indicator_count": len(indicators),
        }

    def suggest_activities(self, lagging_indicator_ids: list[str]) -> list[dict]:
        """Suggest activities from the catalogue that address lagging indicators."""
        suggestions = []
        for ind_id in lagging_indicator_ids:
            indicator = self._indicators.get(ind_id)
            if not indicator:
                continue
            outcome = self._outcomes.get(indicator["outcome_id"])
            if not outcome:
                continue
            activities = self.get_activities_for_outcome(outcome["outcome_id"])
            for act in activities:
                suggestions.append(
                    {
                        "activity": act,
                        "for_indicator": ind_id,
                        "outcome": outcome["title"],
                        "rationale": (
                            f"Activity addresses lagging indicator '{indicator.get('title', ind_id)}'"
                            f" under outcome '{outcome['title']}'"
                        ),
                    }
                )
        return suggestions

    def get_evaluation_questions(self, domain: str) -> dict | None:
        return self._evaluation_questions.get(domain)
