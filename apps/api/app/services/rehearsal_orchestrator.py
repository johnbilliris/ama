from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.repositories.cosmos_scope import simulation_scope
from app.services.preparedness_analysis_service import PreparednessAnalysisService
from app.services.seed_service import SeedService

from packages.domain.src.domain.models.framework_assignment import FrameworkAssignment, is_effective
from packages.domain.src.domain.models.scenario_run import ScenarioEvent, ScenarioRun

_RUNS: dict[str, ScenarioRun] = {}


class RehearsalOrchestrator:
    def __init__(self) -> None:
        self._analysis_service = PreparednessAnalysisService()

    def run(self, scenario_name: str, scenario_type: str, jurisdiction_ids: list[str]) -> ScenarioRun:
        if scenario_type not in {"bushfire", "flood", "cyclone", "severe_storm"}:
            raise ValueError(f"Unsupported scenario type '{scenario_type}'")

        if not jurisdiction_ids:
            raise ValueError("At least one jurisdiction is required")

        analysis = self._analysis_service.analyse(scenario_type, jurisdiction_ids)
        template = self._resolve_template(scenario_type, jurisdiction_ids)

        started_at = datetime.now(UTC)
        trace = self._build_trace(template, started_at)
        findings = self._derive_findings(analysis, trace)

        scenario_run_id = str(uuid4())
        run = ScenarioRun(
            scenario_run_id=scenario_run_id,
            scenario_name=scenario_name,
            scenario_type=scenario_type,
            jurisdiction_ids=jurisdiction_ids,
            organisation_ids=[organisation["organisation_id"] for organisation in analysis["organisations"]],
            framework_ids=[framework["framework_id"] for framework in analysis["frameworks"]],
            coordination_gap_summary=list(analysis["coordinationGaps"]),
            generated_findings=findings,
            mode="rehearsal",
            status="completed",
            model_version="deterministic-replay-v1",
            event_trace=trace,
            started_at=started_at,
            completed_at=trace[-1].decided_at if trace else started_at,
            preflight_catalogue={
                "templateId": template.get("template_id") or template.get("id"),
                "organisationCount": len(analysis["organisations"]),
                "frameworkCount": len(analysis["frameworks"]),
                "policyCount": len(analysis.get("policies", [])),
            },
            tenant_id=simulation_scope(scenario_run_id),
        )
        _RUNS[run.scenario_run_id] = run
        return run

    def cancel(self, scenario_run_id: str) -> ScenarioRun:
        run = _RUNS.get(scenario_run_id)
        if run is None:
            raise ValueError("Scenario run not found")
        run.status = "cancelled"
        run.completed_at = datetime.now(UTC)
        return run

    def restart(self, scenario_run_id: str) -> ScenarioRun:
        existing = _RUNS.get(scenario_run_id)
        if existing is None:
            raise ValueError("Scenario run not found")
        return self.run(existing.scenario_name, existing.scenario_type, existing.jurisdiction_ids)

    def get(self, scenario_run_id: str) -> ScenarioRun | None:
        return _RUNS.get(scenario_run_id)

    @staticmethod
    def _build_trace(template: dict[str, object], started_at: datetime) -> list[ScenarioEvent]:
        timeline = list(template.get("signal_timeline", []))
        trace: list[ScenarioEvent] = []
        for index, entry in enumerate(timeline[:12]):
            if not isinstance(entry, dict):
                continue
            envelope = entry.get("signal_envelope", {})
            if not isinstance(envelope, dict):
                continue
            source_id = str(envelope.get("data_source_id", "unknown-source"))
            offset_seconds = int(entry.get("offset_seconds", index * 900))
            actor = "monitoring-agent"
            category = str(envelope.get("category", ""))
            if category in {"infrastructure", "resource_status"}:
                actor = "resource-allocation-agent"
            elif category in {"community_report", "social_report"}:
                actor = "communication-agent"
            trace.append(
                ScenarioEvent(
                    event_id=f"evt-{index + 1:03d}",
                    offset_seconds=offset_seconds,
                    actor=actor,
                    decided_at=started_at + timedelta(seconds=offset_seconds),
                    source=source_id,
                )
            )
        return trace

    def _derive_findings(self, analysis: dict[str, object], trace: list[ScenarioEvent]) -> list[str]:
        findings: list[str] = []
        gaps = list(analysis.get("coordinationGaps", []))
        if gaps:
            findings.append("finding-missing-owner")

        assignments = [FrameworkAssignment(**item) for item in list(analysis.get("assignments", []))]
        now = datetime.now(UTC)
        duplicate_scope = {
            (assignment.framework_id, assignment.organisation_id or assignment.jurisdiction_id)
            for assignment in assignments
            if is_effective(assignment, now)
        }
        if len(duplicate_scope) < len(assignments):
            findings.append("finding-duplicate-owner")

        for left, right in zip(trace, trace[1:]):
            if (right.offset_seconds - left.offset_seconds) > 1800:
                findings.append("finding-delayed-handoff")
                break

        if not findings:
            findings.append("finding-no-critical-gaps")
        return sorted(set(findings))

    def _resolve_template(self, scenario_type: str, jurisdiction_ids: list[str]) -> dict[str, object]:
        context = self._analysis_service.get_context()
        seed_root = self._analysis_service.seed_root
        templates = SeedService().load(seed_root).get("scenario_templates", [])
        for template in templates:
            if not isinstance(template, dict):
                continue
            if str(template.get("scenario_type", "")).strip().lower() != scenario_type:
                continue
            seed_jurisdictions = set(template.get("seed_jurisdictions", []))
            if seed_jurisdictions.intersection(jurisdiction_ids):
                return template

        # Fallback deterministic template when no exact match exists.
        return {
            "template_id": f"fallback-{scenario_type}",
            "signal_timeline": [
                {
                    "offset_seconds": 0,
                    "signal_envelope": {
                        "data_source_id": "fallback-source",
                        "category": "weather",
                    },
                },
                {
                    "offset_seconds": 2100,
                    "signal_envelope": {
                        "data_source_id": "fallback-handoff",
                        "category": "community_report",
                    },
                },
            ],
            "seed_jurisdictions": jurisdiction_ids,
            "organisations": context.get("organisations", []),
        }
