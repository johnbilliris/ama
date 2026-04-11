"""Dynamic replanning — trigger evaluation, rate limiting, and incremental updates.

Implements six replan trigger conditions:
(a) new road closure
(b) hazard expansion >10%
(c) progress delay >30%
(d) higher-severity assessment
(e) manual trigger
(f) shelter-to-evacuation recovery

Supports multi-trigger merging, rate limiting (REPLAN_RATE_LIMIT_SECONDS),
and no-change detection to avoid unnecessary version creation.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from evacuation.config import EvacuationConfig
from evacuation.templates import generate_change_summary_template

logger = logging.getLogger(__name__)

# Severity ordering for comparison (higher index = more severe)
_SEVERITY_ORDER: dict[str, int] = {
    "low": 0,
    "moderate": 1,
    "high": 2,
    "critical": 3,
}

# Keys compared for material change detection
_MATERIAL_CHANGE_KEYS = (
    "routes",
    "zones",
    "transport_requirements",
    "shelter_in_place_zones",
    "total_population",
)


class DynamicReplanner:
    """Evaluates replan triggers, enforces rate limits, and detects material changes.

    Usage::

        replanner = DynamicReplanner(config)
        triggers = replanner.evaluate_triggers(incident_id, current_plan, ...)
        if triggers and not replanner.is_rate_limited(incident_id):
            # run pipeline to generate new_plan
            if replanner.detect_material_change(old_plan, new_plan):
                # persist new version
            replanner.record_replan(incident_id)
    """

    def __init__(self, config: EvacuationConfig | None = None) -> None:
        self._config = config or EvacuationConfig()
        self._last_replan_times: dict[str, float] = {}  # incident_id -> monotonic time

    # ------------------------------------------------------------------
    # Trigger evaluation
    # ------------------------------------------------------------------

    def evaluate_triggers(
        self,
        incident_id: str,
        current_plan: dict[str, Any] | None,
        new_road_closures: list[str] | None = None,
        hazard_area_change_pct: float | None = None,
        progress_delay_pct: float | None = None,
        new_severity: str | None = None,
        current_severity: str | None = None,
        manual_trigger: bool = False,
        shelter_zones_with_new_routes: list[int] | None = None,
    ) -> list[str]:
        """Evaluate all 6 trigger conditions and return list of active triggers.

        Returns an empty list if no triggers are active.  When multiple triggers
        fire simultaneously, all are included (multi-trigger merging).

        Args:
            incident_id: Incident identifier.
            current_plan: Current plan dict (may be ``None`` for first plan).
            new_road_closures: Edge IDs of newly closed roads.
            hazard_area_change_pct: Percentage change in hazard area size.
            progress_delay_pct: Percentage delay vs. planned progress.
            new_severity: New severity level from updated assessment.
            current_severity: Current severity level on the plan.
            manual_trigger: Whether an operator manually triggered a replan.
            shelter_zones_with_new_routes: Zone numbers that were shelter-in-place
                but now have viable evacuation routes.

        Returns:
            List of trigger description strings.
        """
        triggers: list[str] = []

        # (a) New road closure
        if new_road_closures:
            triggers.append(
                f"road_closure: {len(new_road_closures)} new closure(s) — "
                f"{', '.join(new_road_closures[:5])}"
                + (" ..." if len(new_road_closures) > 5 else "")
            )

        # (b) Hazard expansion > threshold %
        expansion_threshold = self._config.hazard_expansion_replan_pct
        if (
            hazard_area_change_pct is not None
            and hazard_area_change_pct > expansion_threshold
        ):
            triggers.append(
                f"hazard_expansion: area changed by {hazard_area_change_pct:.1f}% "
                f"(threshold: {expansion_threshold}%)"
            )

        # (c) Progress delay > threshold %
        delay_threshold = self._config.progress_delay_replan_pct
        if (
            progress_delay_pct is not None
            and progress_delay_pct > delay_threshold
        ):
            triggers.append(
                f"progress_delay: {progress_delay_pct:.1f}% behind schedule "
                f"(threshold: {delay_threshold}%)"
            )

        # (d) Higher-severity assessment
        if new_severity and current_severity:
            new_ord = _SEVERITY_ORDER.get(new_severity, -1)
            cur_ord = _SEVERITY_ORDER.get(current_severity, -1)
            if new_ord > cur_ord:
                triggers.append(
                    f"severity_escalation: {current_severity} → {new_severity}"
                )

        # (e) Manual trigger
        if manual_trigger:
            triggers.append("manual_trigger: operator-initiated replan")

        # (f) Shelter-to-evacuation recovery
        if shelter_zones_with_new_routes:
            zone_list = ", ".join(str(z) for z in shelter_zones_with_new_routes)
            triggers.append(
                f"shelter_recovery: zones [{zone_list}] now have viable evacuation routes"
            )

        if triggers:
            logger.info(
                "Replan triggers for incident %s: %s",
                incident_id,
                "; ".join(triggers),
            )

        return triggers

    # ------------------------------------------------------------------
    # Rate limiting
    # ------------------------------------------------------------------

    def is_rate_limited(self, incident_id: str) -> bool:
        """Check if replanning is rate-limited for this incident.

        Returns True if the minimum interval (``REPLAN_RATE_LIMIT_SECONDS``)
        has not elapsed since the last replan for this incident.
        """
        last = self._last_replan_times.get(incident_id)
        if last is None:
            return False

        elapsed = time.monotonic() - last
        limit = self._config.replan_rate_limit_seconds
        if elapsed < limit:
            logger.info(
                "Replan rate-limited for incident %s: %.1fs elapsed, limit %ds",
                incident_id,
                elapsed,
                limit,
            )
            return True
        return False

    def record_replan(self, incident_id: str) -> None:
        """Record that a replan was executed for rate-limiting purposes."""
        self._last_replan_times[incident_id] = time.monotonic()

    # ------------------------------------------------------------------
    # Material change detection
    # ------------------------------------------------------------------

    def detect_material_change(
        self,
        old_plan: dict[str, Any],
        new_plan: dict[str, Any],
    ) -> bool:
        """Return True if the new plan has material differences from the old.

        Compares routes, zones, transport requirements, shelter-in-place zones,
        total population, and confidence score.  Ignores metadata-only changes
        (timestamps, version numbers, summaries).
        """
        # Route count change
        old_routes = len(old_plan.get("routes", []))
        new_routes = len(new_plan.get("routes", []))
        if old_routes != new_routes:
            return True

        # Route IDs changed
        old_route_ids = sorted(
            r.get("route_id", "") for r in old_plan.get("routes", [])
        )
        new_route_ids = sorted(
            r.get("route_id", "") for r in new_plan.get("routes", [])
        )
        if old_route_ids != new_route_ids:
            return True

        # Zone count or population change
        old_zones = old_plan.get("zones", [])
        new_zones = new_plan.get("zones", [])
        if len(old_zones) != len(new_zones):
            return True

        old_pop = old_plan.get("total_population", 0)
        new_pop = new_plan.get("total_population", 0)
        if old_pop != new_pop:
            return True

        # Transport requirement count change
        old_transport = len(old_plan.get("transport_requirements", []))
        new_transport = len(new_plan.get("transport_requirements", []))
        if old_transport != new_transport:
            return True

        # Shelter-in-place zone changes
        old_sip = sorted(old_plan.get("shelter_in_place_zones", []))
        new_sip = sorted(new_plan.get("shelter_in_place_zones", []))
        if old_sip != new_sip:
            return True

        # Confidence score change (>1% absolute)
        old_conf = old_plan.get("confidence_score", 0.0)
        new_conf = new_plan.get("confidence_score", 0.0)
        if abs(old_conf - new_conf) > 0.01:
            return True

        return False

    # ------------------------------------------------------------------
    # Change summary
    # ------------------------------------------------------------------

    def generate_change_summary(
        self,
        old_plan: dict[str, Any] | None,
        new_plan: dict[str, Any],
        triggers: list[str] | None = None,
    ) -> str:
        """Generate a human-readable change summary.

        Delegates to the template module for consistent formatting.
        """
        return generate_change_summary_template(
            old_plan=old_plan,
            new_plan=new_plan,
            triggers=triggers,
        )

    # ------------------------------------------------------------------
    # Multi-trigger merging
    # ------------------------------------------------------------------

    def merge_triggers(self, trigger_lists: list[list[str]]) -> list[str]:
        """Merge multiple trigger lists, deduplicating by trigger type prefix.

        When multiple trigger evaluations occur between replans, this
        consolidates them into a single deduplicated list, keeping the
        most recent description for each trigger type.
        """
        seen_types: dict[str, str] = {}
        for triggers in trigger_lists:
            for trigger in triggers:
                # Extract trigger type prefix (before the first colon)
                prefix = trigger.split(":")[0].strip()
                seen_types[prefix] = trigger  # last one wins
        return list(seen_types.values())
