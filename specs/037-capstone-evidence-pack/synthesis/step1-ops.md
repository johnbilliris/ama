# Step 1 — Operational Cohort Synthesis (10 personas)

> Source: synthetic canvas of `.github/agents/operational/*.agent.md` files.
> Captured: 2026-05-11. Citations are file:line into the agent definition files.

## Risk Register inputs
- **Incident Commander** (`operational/incident-commander.agent.md:32-45,77-95`) — needs a live, decision-grade register that supports approval/reject/escalate workflows, multi-jurisdiction handling, and span-of-control warnings; risk views must map to incident command decisions and preserve human override for evacuations/alerts.
- **Operations Officer** (`operational/operations-officer.agent.md:20-33,61-77`) — wants tactical risk tied to field deployment, staging-area safety, resource scarcity, and life-safety prioritisation; register should surface when resource demand exceeds supply and trigger IC escalation.
- **Planning Officer** (`operational/planning-officer.agent.md:24-37,65-84`) — needs dynamic risk inputs for situation assessment, forecasting, and action plans; register must carry provenance/confidence, contradictions, and evolving threat trends.
- **Logistics Officer** (`operational/logistics-officer.agent.md:24-37,66-83`) — needs risk treatment coverage for supply-chain shortages, procurement duplication, cold-chain integrity, and resource accountability; register should distinguish critical shortages vs managed shortages.
- **Executive Leader** (`operational/executive-leader.agent.md:27-41,76-88`) — needs strategic/systemic risks and policy implications, especially cross-jurisdiction, mutual-aid, and resource-commitment risks requiring executive approval.
- **Observer-Auditor** (`operational/observer-auditor.agent.md:24-39,67-89`) — needs an auditable, append-only risk trail with completeness, provenance, approval evidence, and post-incident reviewability.
- **Risk Manager** (`operational/risk-manager.agent.md:40-65,83-152`) — explicitly asks for a dynamic, schema-bound register with likelihood/consequence matrix, risk treatments, ownership, residual risk, and archiveability; also wants audience-specific outputs and treatment thresholds.

## Adoption Roadmap inputs
- **Incident Commander** (`operational/incident-commander.agent.md:34-45,84-95`) — needs jurisdiction-aware onboarding and unified-command logic when incidents cross borders.
- **Executive Leader** (`operational/executive-leader.agent.md:30-41,69-88`) — requires an inter-government adoption sequence tied to policy authority, mutual-aid agreements, emergency declarations, and resource commitments above delegated thresholds.
- **Resilience Planner** (`operational/resilience-planner.agent.md:24-37,65-84`) — wants phased preparedness rollout, scenario rehearsal, gap closure, and version-controlled framework adoption; roadmap should sequence pilots, exercises, and readiness gates.
- **Operations Officer** (`operational/operations-officer.agent.md:22-33,61-77`) — needs staged rollout that proves tactical coordination, staging-area operations, and span-of-control compliance before wider adoption.
- **Field Coordinator** (`operational/field-coordinator.agent.md:16-29,56-74`) — needs connectivity-degraded onboarding and "conservative life-safety" fallback as part of pilot criteria before field deployment.
- **Logistics Officer** (`operational/logistics-officer.agent.md:24-37,66-83`) — needs onboarding that validates procurement, tracking, and resource accountability workflows before scaling.
- **Public Information Officer** (`operational/public-information-officer.agent.md:20-33,62-82`) — needs phased adoption that proves multilingual/accessibility alert workflows and IC approval before public release.
- **Observer-Auditor** (`operational/observer-auditor.agent.md:24-39,75-89`) — needs decommission/rollback criteria backed by audit evidence, so pilot exit is justified by traceable compliance findings.

## Executive KPI Surface inputs
- **Incident Commander** (`operational/incident-commander.agent.md:34-45,90-95`) — KPI surface must support live approval decisions, span-of-control monitoring, and cross-agency coordination.
- **Operations Officer** (`operational/operations-officer.agent.md:24-33,67-77`) — wants KPIs for deployment speed, staging effectiveness, field safety, and resource allocation efficiency.
- **Planning Officer** (`operational/planning-officer.agent.md:26-37,65-84`) — needs leading indicators from signal ingestion, forecast quality, and plan volatility, plus lagging measures of incident outcome.
- **Logistics Officer** (`operational/logistics-officer.agent.md:26-37,66-83`) — needs leading/lagging logistics KPIs for inventory accuracy, fill rate, cold-chain integrity, and shortfall avoidance.
- **Public Information Officer** (`operational/public-information-officer.agent.md:22-33,70-82`) — wants public-alert KPIs such as approval latency, multilingual coverage, accessibility compliance, and message reach/effectiveness.
- **Executive Leader** (`operational/executive-leader.agent.md:32-41,76-88`) — needs an executive roll-up mapping outcomes to policy/resource commitments and cross-jurisdiction performance.
- **Observer-Auditor** (`operational/observer-auditor.agent.md:26-39,67-89`) — requires KPI evidence that is auditable, provenance-backed, and reviewable post-incident.
- **Risk Manager** (`operational/risk-manager.agent.md:67-91,124-152`) — needs KPI linkage to risk thresholds and residual risk, with target/trigger levels for escalation and stand-down.

## Responsible AI Register inputs
- **Incident Commander** (`operational/incident-commander.agent.md:34-45,90-95`) — needs human override preserved for all safety-critical outputs.
- **Planning Officer** (`operational/planning-officer.agent.md:65-84`) — needs provenance and confidence handling for mixed-authority data; register should capture transparency of signal fusion and uncertainty.
- **Public Information Officer** (`operational/public-information-officer.agent.md:22-33,62-82`) — needs explicit controls for multilingual accessibility, plain language, misinformation monitoring, and human approval of alerts.
- **Executive Leader** (`operational/executive-leader.agent.md:34-41,83-88`) — wants governance alignment, legislative compliance, and executive accountability for AI-enabled decisions.
- **Observer-Auditor** (`operational/observer-auditor.agent.md:30-39,67-89`) — needs evidence of approval workflows, provenance, and audit integrity for AI outputs.
- **Risk Manager** (`operational/risk-manager.agent.md:40-75,83-91`) — needs risk communication that distinguishes confirmed vs assessed risks; a RAI register should cover safety, reliability, transparency, and decision-support uncertainty.
- **Resilience Planner** (`operational/resilience-planner.agent.md:24-37,65-84`) — needs preparedness modelling that is auditable and version-controlled, supporting responsible use of AI in scenario design.
- **Field Coordinator** (`operational/field-coordinator.agent.md:16-29,56-74`) — needs conservative defaults in degraded connectivity and local logging for later audit.

## Feature-Value Ledger / Tradeoff Log inputs
- **Incident Commander** (`operational/incident-commander.agent.md:37-45,84-95`) — wants tradeoffs explicit between speed, safety, and authority.
- **Operations Officer** (`operational/operations-officer.agent.md:26-33,67-77`) — needs feature contribution to deployment efficiency and resource allocation; tradeoffs around automation vs span-of-control.
- **Planning Officer** (`operational/planning-officer.agent.md:30-37,72-84`) — wants feature-to-metric traceability for forecasts, plans, and assessments.
- **Logistics Officer** (`operational/logistics-officer.agent.md:30-37,72-83`) — needs feature-to-metric linkage for tracking, procurement, and cold-chain reliability.
- **Public Information Officer** (`operational/public-information-officer.agent.md:26-33,62-82`) — needs ledger entries for alert drafting, multilingual delivery, accessibility, and misinformation monitoring.
- **Executive Leader** (`operational/executive-leader.agent.md:34-41,76-88`) — needs tradeoffs explicit for policy authority, resource commitments, and inter-government alignment.
- **Observer-Auditor** (`operational/observer-auditor.agent.md:26-39,67-89`) — wants a decision log with rationale and auditability for each tradeoff.
- **Risk Manager** (`operational/risk-manager.agent.md:59-65,83-91,144-152`) — explicitly needs treatment-level tradeoffs (accepted/mitigated/transferred/avoided) and residual risk after treatment.

## Cross-cutting concerns / additional asks
- **Field Coordinator** — strong demand for degraded-connectivity support.
- **Public Information Officer** — emphasis on multilingual, accessible, multi-channel public communications.
- **Observer-Auditor** — insists on append-only audit integrity and provenance metadata as non-negotiable system properties.
- **Risk Manager** — provides the clearest schema clues for severity/likelihood matrices and treatment thresholds; useful as the baseline taxonomy for the new artifacts.

