# Agent Catalogue Deep Critique

**Date**: 2026-03-25
**Scope**: All non-speckit agents in `.github/agents/` and subfolders (~91 agents)
**Method**: Each agent was executed with the instruction to provide a deep constructive critique and generate objections. Each objection was then assessed for merit.

---

## Table of Contents

- [Operational Agents (1–10)](#operational-agents)
- [Technical Agents (11–27)](#technical-agents)
- [Cross-Sector Agents (28–35)](#cross-sector-agents)
- [State/Territory Sector Agents (36–74)](#stateterritory-sector-agents)
- [Commonwealth Sector Agents (75–85)](#commonwealth-sector-agents)
- [Archived Sector Agents (86–91)](#archived-sector-agents)
- [Grand Summary & Meta-Assessment](#grand-summary--meta-assessment)

---

## Operational Agents

### Agent 1: `operational/incident-commander.agent.md`

**CRITIQUE FROM THE INCIDENT COMMANDER PERSPECTIVE:**

1. **No real-time operational tempo model.** The system treats incidents as database objects with status enums (`monitoring`, `active`, `stabilising`...) but doesn't model the operational tempo — the rate at which decisions must be made. During a fast-moving bushfire, the IC may need to approve 20+ decisions per hour. The current architecture's approval workflow (human-in-the-loop for all safety-critical actions) could become a bottleneck that costs lives. There is no escalation-by-timeout or auto-approve-with-notification pattern for when the IC is overwhelmed.

2. **Span-of-control is documented but not enforced.** The guidance says "flag warnings when task assignment density exceeds threshold" — but is this actually implemented? The data model doesn't include a span-of-control metric or threshold trigger. This is aspirational text in an agent file, not a system capability.

3. **Multi-jurisdiction command authority is underspecified.** The agent says "identify which jurisdiction's framework applies" but the system's `OperatingFramework` model has no conflict resolution for overlapping jurisdictions. When a bushfire crosses the NSW/VIC border, who has authority? The system needs a framework precedence model, not just "escalate to executive-leader."

4. **No deputy IC / succession model.** AIIMS includes provisions for deputy controllers and handover. The agent makes no mention of deputy appointment or handover protocols. If the IC goes offline during a critical incident, there's no defined fallback.

5. **The handoff to sector agents is vague.** The agent says "handoff to the relevant sector agent (e.g., fire-services, police, health)" — but these generic agents are now archived. The actual agents are jurisdiction-specific (e.g., `frnsw`, `nswpf`). The scope boundaries reference incorrect agent names.

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "The approval bottleneck at the IC level during high-tempo incidents will cause dangerous delays in safety-critical decisions." | **YES — Strong merit.** This is a legitimate operational risk. Real AIIMS operations use standing orders and delegated authority precisely to avoid this. The system needs pre-approved response templates or delegated authority levels. |
| O2 | "Span-of-control warnings are mentioned but not in the data model — this is vaporware guidance." | **YES — Merit.** The agent references a capability that doesn't exist in the spec or data model. It should either be added to the data model or removed from the agent guidance. |
| O3 | "Multi-jurisdiction conflict resolution needs explicit modelling, not just escalation." | **YES — Strong merit.** Australia's federal structure means multi-jurisdiction incidents are common (floods across LGA boundaries, bushfires crossing state lines). A simple "escalate" is insufficient. |
| O4 | "Missing deputy IC / succession protocols." | **PARTIAL merit.** This is important for operational completeness but is arguably a system feature concern, not an agent definition concern. The agent could mention it in Guidance Notes. |
| O5 | "Scope boundaries reference archived agent names." | **YES — Merit.** The scope boundary section references `fire-services`, `police`, `health` — but these are archived. Should reference the actual state/territory-specific agents or cross-sector agents. |

---

### Agent 2: `operational/operations-officer.agent.md`

**CRITIQUE FROM THE OPERATIONS OFFICER PERSPECTIVE:**

1. **No real-time resource tracking model.** My role requires tracking resource check-in/check-out, field team status, and staging area utilization in real time. The data model has `CoordinationTask` and `Organisation` but no `FieldResource`, `StagingArea`, or `DeploymentOrder` entity. I'm described as managing staging areas, but there's no data structure to actually represent them.

2. **Division/Sector/Taskforce structuring is mentioned but unsupported.** The guidance notes say I "organise field resources into divisions, sectors, or taskforces" — these are core AIIMS organizational units but don't appear anywhere in the data model. Without them, the hub can't model the actual operational structure of a response.

3. **The handoff chain is too narrow.** I only hand off to IC, field-coordinator, and logistics-officer. In practice, I'd frequently need direct communication with sector-specific operational leads — fire sector, police sector, ambulance. The handoff model forces me to go through the IC for cross-sector coordination, which doesn't reflect AIIMS operational reality where the Ops Officer directly manages sector commanders.

4. **No concept of operational periods.** AIIMS operates in defined operational periods (typically 12-hour shifts). The data model and this agent have no concept of shift handover, operational period planning, or crew rotation, which are critical for sustained operations.

5. **Field intelligence flow is one-directional.** The agent describes receiving situation assessments from Planning, but doesn't describe how field intelligence (from my teams observing conditions on the ground) flows back into the system. In real operations, ground truth often contradicts sensor data.

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "Missing data model entities for staging areas and field resources makes the operations function unusable." | **YES — Strong merit.** The current data model can't represent what this agent claims to manage. This is a real gap. |
| O2 | "AIIMS divisions/sectors/taskforces need first-class data model support." | **YES — Merit.** These are the core organizational building blocks of AIIMS operations and their absence means the system can't model real incident structures. |
| O3 | "Direct handoffs to sector agents needed, not routing through IC." | **YES — Merit.** AIIMS Ops Officer directly manages sector commanders. The current handoff structure is hierarchically correct but operationally wrong. |
| O4 | "No operational period / shift management." | **PARTIAL merit.** Important for sustained operations, but could be argued as a v2 feature. For an MVP, it's a nice-to-have. However, for any real deployment, this is essential. |
| O5 | "Field intelligence needs bidirectional flow modelling." | **YES — Merit.** Field reports are a critical signal source and the architecture already ingests signals — but the connection between field-coordinator reports and the signal pipeline is unclear. |

---

### Agent 3: `operational/planning-officer.agent.md`

**CRITIQUE FROM THE PLANNING OFFICER PERSPECTIVE:**

1. **Constitution reference error in Contextual References.** The agent references "III (Provenance & Transparency) and IV (Deterministic Coordination)" — but the actual constitution principles are "III. Data Trust, Provenance, and Freshness" and "IV. Privacy, Security, and Regional Policy Compliance." There is no principle called "Deterministic Coordination." This is a factual error that undermines trust in the agent's accuracy.

2. **No structured intelligence product model.** My primary output is situation reports, action plans, and intelligence assessments. The data model has `Signal` and `Recommendation` but no `SituationReport`, `IncidentActionPlan`, or `IntelligenceAssessment` entity. The Planning Officer's core deliverables have no data model representation.

3. **Signal correlation and contradiction detection is mentioned but unspecified.** The guidance says "flags contradictions, confidence gaps, and information voids" — but there's no mechanism in the spec for contradiction detection between signals. How does the system know when two signals contradict? This needs a formal model.

4. **No integration with the Risk Assessment agent.** The system has a dedicated Risk Assessment agent in the architecture (`apps/agents/risk_assessment/`), and this operational agent does risk analysis too, but the handoff originally only went to IC and logistics. The addition of `risk-manager` is good, but the relationship between the planning officer's intelligence analysis and the software agent's risk assessment is unclear — who does what?

5. **Predictive assessments mentioned without any ML/forecasting capability specified.** "Produces predictive assessments for resource demand, hazard progression, and impact areas" — but the system architecture doesn't describe any predictive modelling capability. This is aspirational text with no implementation path.

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "The constitution principle names are wrong — this erodes agent reliability." | **YES — Strong merit.** Incorrect references to the project's foundational document is a significant quality issue. Must be fixed. |
| O2 | "Core planning outputs (SitReps, action plans) need data model entities." | **YES — Merit.** These are fundamental AIIMS artifacts. Without them, the planning function is described in prose but can't be implemented in software. |
| O3 | "Signal contradiction detection needs a formal model." | **YES — Merit.** The constitution explicitly requires provenance and freshness tracking. Contradiction detection is implicit in this requirement but has no specification. |
| O4 | "Overlap between planning officer intelligence analysis and the software risk assessment agent is confusing." | **PARTIAL merit.** The operational agent (human role) and the software agent serve different purposes — one is a persona describing how a human planner uses the hub, the other is actual code. But the boundary should be clearer. |
| O5 | "Predictive assessment is aspirational without implementation support." | **PARTIAL merit.** The agent is a knowledge/persona agent, not code. It's reasonable for it to describe what planners do. But it shouldn't imply the system has capabilities it doesn't have. |

---

### Agent 4: `operational/logistics-officer.agent.md`

**CRITIQUE FROM THE LOGISTICS OFFICER PERSPECTIVE:**

1. **Same constitution reference error.** The agent references "IV (Deterministic Coordination)" — this principle doesn't exist. It's "IV. Privacy, Security, and Regional Policy Compliance." This error is present across multiple operational agents, indicating a systematic copy-paste issue.

2. **Scope boundary references archived agents.** References `ambulance-paramedic` — but this is now archived in `sectors/_archive/`. The actual agents are state-specific: `nsw-ambulance`, `qas`, `saas`, `at`, `av`, `sja-nt`, `sja-wa`, `sja-national`. The handoff would break.

3. **No mutual aid agreement model.** The guidance mentions "mutual aid agreements" as a key coordination mechanism, but the data model has no entity for mutual aid agreements, resource sharing arrangements, or pre-positioned resource pools. This is a critical gap for logistics operations.

4. **Cost tracking and financial accountability mentioned but unspecified.** Real disaster logistics involves financial delegation, cost centres, and reimbursement tracking (especially for NDRRA claims). The data model has nothing for financial tracking.

5. **Cold chain and pharmaceutical tracking are mentioned but incredibly complex in practice.** The guidance casually mentions cold chain integrity and pharmaceutical tracking — each of these is a regulated domain requiring specific data models, audit trails, and compliance frameworks. This feels like a wish list rather than a realistic scope for an MVP.

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "Constitution principle IV is incorrectly named across multiple agents — systematic error." | **YES — Strong merit.** This needs a bulk fix across all agents referencing this non-existent principle. |
| O2 | "Handoff to `ambulance-paramedic` references an archived, non-existent agent." | **YES — Strong merit.** Broken handoff reference. This should point to the cross-sector `health` agent or specific state ambulance agents. |
| O3 | "No mutual aid agreement data model — logistics can't function without it." | **YES — Merit.** Mutual aid is foundational to Australian disaster logistics. Without it, the system can't model how resources move between agencies. |
| O4 | "Financial tracking is essential for real operations." | **PARTIAL merit.** It's important for production, but reasonable to exclude from MVP. The agent guidance shouldn't imply it exists if it doesn't. |
| O5 | "Cold chain and pharma tracking are unrealistic scope items." | **YES — Merit.** These are legitimate domains but wildly out of scope for this system. Mentioning them sets unrealistic expectations. |

---

### Agent 5: `operational/public-information-officer.agent.md`

**CRITIQUE FROM THE PIO PERSPECTIVE:**

1. **Scope boundary references wrong agent name.** Handoff to `meteorology-bom` — this agent doesn't exist. The actual agent is `bom-national` (which is correctly referenced in the YAML handoffs but incorrectly named in the scope boundaries text). Inconsistency within the same file.

2. **Aboriginal and Torres Strait Islander language support is mentioned but practically unachievable at MVP.** The guidance says "must be considered where communities are directly affected" — this is a laudable but enormously complex requirement. There are 250+ Aboriginal languages. The spec should acknowledge the practical constraints: which languages, what level of support (full translation vs. community liaison), and how this is resourced.

3. **Social media monitoring scope is dangerously broad.** The agent describes monitoring social media for "misinformation, rumours, and community concerns" — this implies real-time NLP over social media streams, sentiment analysis, and misinformation detection. These are each major ML challenges. The system architecture mentions a Communication Agent but doesn't specify social media monitoring capabilities.

4. **No misinformation response framework.** The guidance says "issue corrections and clarifications" — but in real disaster communications, the misinformation response cycle is complex. There's no model for tracking misinformation instances, correction chains, or effectiveness measurement.

5. **Multi-channel distribution is mentioned but the `PublicAlert` data model is thin.** The data model's `PublicAlert` entity needs to support channel-specific formatting (SMS character limits, rich media for social, audio scripts for radio, accessible HTML). The current model doesn't appear to have channel-variant support.

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "Inconsistency between YAML handoffs (`bom-national`) and scope boundary text (`meteorology-bom`)." | **YES — Merit.** Internal inconsistency in the same file. Easy fix but indicates quality control gaps. |
| O2 | "Aboriginal and Torres Strait Islander language support needs practical scoping." | **YES — Strong merit.** The requirement is constitutionally mandated (Principle V) but practically unbounded. Needs narrowing to specific first-priority languages or a community-liaison model. |
| O3 | "Social media monitoring implies ML capabilities not in the architecture." | **YES — Merit.** The system doesn't have a social media ingestion pipeline or sentiment analysis capability specified. This is aspirational. |
| O4 | "Misinformation tracking needs its own model." | **PARTIAL merit.** Important for a mature system but over-engineering for MVP. The agent correctly describes what a PIO does — the system doesn't have to automate every aspect. |
| O5 | "PublicAlert needs channel-variant support." | **YES — Merit.** The constitution mandates multi-channel delivery, so the data model must support it. |

---

### Agent 6: `operational/field-coordinator.agent.md`

**CRITIQUE FROM THE FIELD COORDINATOR PERSPECTIVE:**

1. **Offline/degraded mode is my defining capability, but it's barely specified.** The constitution mentions degraded connectivity, and this agent leans heavily on it — but the system architecture doesn't describe an offline-capable client, local data caching, sync-on-reconnect protocols, or conflict resolution when cached local decisions conflict with commands issued while the field coordinator was offline. This is a core feature, not a footnote.

2. **Only two handoffs is unrealistically constrained.** I only hand off to operations-officer and logistics-officer. In reality, field coordinators interact with every sector agency on the ground — fire crews, police cordons, ambulance triage stations, SES volunteers. The handoff model doesn't reflect field reality.

3. **No model for field reports as signals.** The guidance says my reports "follow the same provenance requirements as other signals" — implying field reports should enter the Signal pipeline. But the `Signal` entity in the data model is designed for automated feeds (BoM, IoT, social media). There's no clear pathway for structured field reports to become first-class signals.

4. **GPS and timestamp tagging implies a mobile client that doesn't exist yet.** The guidance says "reports are tagged with GPS coordinates, timestamp, and confidence level" — this implies a mobile-capable reporting interface. The architecture specifies a "responsive web" client but not a dedicated mobile field app with GPS integration.

5. **"Coordinate with local community contacts" is undefined.** What community contacts? Through what channels? The system doesn't model community contact databases, local liaison networks, or field-to-community communication workflows.

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "Offline/degraded mode is essential for field ops but has no implementation spec." | **YES — Strong merit.** This is a showstopper for real field use. Australian disaster zones routinely lose connectivity. Without offline capability, the field coordinator role is theoretical. |
| O2 | "Two handoffs is too narrow for field reality." | **YES — Merit.** Should at minimum include direct handoffs to sector agents like fire, police, and ambulance since field coordinators work alongside them physically. |
| O3 | "Field reports need a defined pathway into the Signal pipeline." | **YES — Merit.** If field reports are signals (as the agent claims), the signal ingestion pipeline needs to support human-originated structured reports. |
| O4 | "GPS-tagged reports imply a mobile client not in the architecture." | **YES — Merit.** The architecture says "responsive web" but field GPS tagging needs native device APIs or a PWA with geolocation. This needs explicit architectural support. |
| O5 | "Community contacts are undefined." | **PARTIAL merit.** This is a nice-to-have for MVP. In real operations, community contacts exist in agency systems, not in the coordination hub. |

---

### Agent 7: `operational/resilience-planner.agent.md`

**CRITIQUE FROM THE RESILIENCE PLANNER PERSPECTIVE:**

1. **Same constitution reference error: "IV (Deterministic Coordination)" doesn't exist.** This is at least the third agent with this wrong reference. Systematic quality issue across the operational tier.

2. **`ScenarioRun` in the data model is an execution record, not a scenario design model.** The data model has `ScenarioRun` — but it's a record of a simulation execution, not a scenario design template. The Resilience Planner needs to *design* scenarios (hazard parameters, participating agencies, expected outcomes, evaluation criteria). There's no `ScenarioTemplate` or `ExerciseDesign` entity.

3. **User Story 3 dependency is well-identified but under-connected.** This agent correctly maps to US3 (preparedness rehearsal), which is good. But the relationship between my offline preparedness work and the live incident system is one-directional — I feed into the system, but there's no mechanism for live incidents to automatically generate preparedness recommendations (i.e., "this incident exposed gaps in X — schedule exercise Y").

4. **Gap analysis has no quantitative framework.** The guidance says "compare current capability against requirements" but there's no capability maturity model, scoring framework, or gap severity classification. Gap analysis without metrics produces subjective assessments.

5. **Framework version control is mentioned but operationally complex.** "Framework configurations are version-controlled and auditable" — but during a live incident, you can't version-control a running framework. What happens when a framework is updated while an incident is active? There's no transition model.

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "Constitution reference error is systemic." | **YES — Strong merit.** Needs a bulk fix. |
| O2 | "Need a ScenarioTemplate entity distinct from ScenarioRun." | **YES — Merit.** You can't run what you can't design. The data model needs a design-time entity. |
| O3 | "Live incidents should auto-generate preparedness recommendations." | **PARTIAL merit.** Nice feedback loop, but properly belongs in the observer-auditor's review output rather than being automated. |
| O4 | "Gap analysis needs quantitative metrics." | **YES — Merit.** Without a scoring model, gap analysis is subjective opinion, not structured assessment. |
| O5 | "Framework version transitions during active incidents need a model." | **PARTIAL merit.** Edge case, but a real one. Could be addressed by freezing the framework version at incident activation. |

---

### Agent 8: `operational/executive-leader.agent.md`

**CRITIQUE FROM THE EXECUTIVE LEADER PERSPECTIVE:**

1. **Financial delegation and authority thresholds are referenced but never defined.** The agent repeatedly mentions "above delegated thresholds" and "above jurisdictional limits" but these thresholds don't exist in the data model. The `Organisation` entity has no `financialDelegation` field, no `resourceCommitmentThreshold`, no `approvalLimits`. Without defined delegation levels, the system can't model when escalation to the executive is required vs. when the IC can decide autonomously.

2. **Emergency declaration workflows are missing.** The guidance mentions "emergency declarations and legislative triggers flow through the executive level" — but this is a legally significant process with specific triggers, notification requirements, and published gazette procedures per state legislation. The data model has no `EmergencyDeclaration` entity or state/territory-specific declaration workflow.

3. **The handoff to `nema` is correct, but the earlier agents reference `commonwealth-government` which is archived.** Good that this agent correctly points to `nema` (National Emergency Management Agency), but cross-referencing with other agents (e.g., logistics, planning) shows inconsistency in how Commonwealth coordination is addressed.

4. **No model for ministerial briefings or government reporting.** In real executive disaster management, a huge part of the job is briefing the minister, preparing cabinet submissions, and managing government reporting. The system doesn't model any of these workflows, which is the primary tool of an executive leader during a disaster.

5. **ADF assistance requests follow a specific legal pathway (DACC).** The guidance casually mentions "engagement of Australian Defence Force assets through formal request channels" — but Defence Aid to the Civil Community (DACC) categories 1-6 have specific approval authorities, timeframes, and cost-recovery implications. This needs more than a one-liner.

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "Financial delegation / authority thresholds need to be in the data model." | **YES — Strong merit.** Without these, the system can't determine when escalation is required. This is a foundational governance gap. |
| O2 | "Emergency declaration needs a formal workflow and data entity." | **YES — Strong merit.** Legal declarations enable specific powers (forced evacuations, road closures, resource requisition). They're not optional for a disaster response system. |
| O3 | "Cross-agent inconsistency in Commonwealth handoff references." | **YES — Merit.** Some agents reference `nema`, some `commonwealth-government` (archived). Needs consistency. |
| O4 | "Ministerial briefing workflows are realistically out of scope." | **NO — Low merit.** This is a coordination hub, not a government reporting tool. Ministerial briefings happen in separate government systems. |
| O5 | "DACC categories need more detail." | **PARTIAL merit.** Worth a Guidance Notes expansion, but the full DACC framework is Defence department domain knowledge, not something this system needs to model. |

---

### Agent 9: `operational/observer-auditor.agent.md`

**CRITIQUE FROM THE OBSERVER-AUDITOR PERSPECTIVE:**

1. **The constitution reference "III (Provenance & Transparency)" is slightly wrong.** The actual principle name is "III. Data Trust, Provenance, and Freshness." Not as egregious as "Deterministic Coordination" but still inaccurate. Pattern of loose referencing continues.

2. **`AuditEntry` is not in the data model.** The Contextual References cite "AuditEntry, TimelineEvent" — but the data model document lists `TimelineEvent` but not `AuditEntry`. The audit trail is constitutionally mandated but has no first-class data model entity. This is a critical gap: the append-only audit trail is referenced across multiple agents and the constitution, but there's no defined schema for it.

3. **Read-only enforcement is stated but not mechanistically modelled.** The agent says it has "no operational decision rights" and "read-only mode" — but the system's RBAC model doesn't appear to define an observer permission set. How is read-only enforced? Through the `Persona` entity's permissions? Through a separate RBAC rule? This needs specification.

4. **Post-incident review has no formal output model.** The guidance describes producing "post-incident review reports" but there's no `PostIncidentReport`, `LessonLearned`, or `AuditFinding` entity in the data model. The observer-auditor's core deliverables have no structured representation.

5. **Compliance verification scope is enormous.** The guidance lists verification across approval workflows, provenance, framework adherence, accessibility, and audit integrity — each of these is a significant verification domain. For an MVP, this should be scoped to what's mechanically verifiable vs. what requires human judgment.

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "Constitution principle names are loosely referenced." | **YES — Merit.** Minor but cumulative quality issue. |
| O2 | "`AuditEntry` is referenced but doesn't exist in the data model." | **YES — Strong merit.** The append-only audit trail is constitutionally mandated and referenced by multiple agents but not modelled. Must be added. |
| O3 | "Read-only role enforcement needs RBAC specification." | **YES — Merit.** Without RBAC modelling, "read-only" is a guideline, not an enforcement mechanism. |
| O4 | "Post-incident review outputs need data model entities." | **YES — Merit.** If the system's purpose includes continuous improvement, the outputs of that improvement cycle need structure. |
| O5 | "Compliance verification scope is too broad for MVP." | **PARTIAL merit.** The scope is appropriate for a mature system but should be phased. The audit against approval workflows is MVP-essential; accessibility auditing is later. |

---

### Agent 10: `operational/risk-manager.agent.md`

**CRITIQUE FROM THE RISK MANAGER PERSPECTIVE:**

1. **My role overlaps significantly with the software Risk Assessment Agent.** The architecture has an actual `RiskAssessmentAgent` in `apps/agents/risk_assessment/agent.py` that generates hazard maps, recommendations, and handoffs. My operational persona agent describes the human risk manager role — but the boundary between what the software agent does autonomously and what the human risk manager governs is undefined. The `HazardAssessment` and `Recommendation` entities are produced by the software agent, not by me.

2. **No risk register model.** Risk management fundamentally requires a risk register — a structured catalog of identified risks with likelihood, consequence, treatments, and residual risk. The data model has `HazardAssessment` (which is an incident-time artifact) but no standing risk register for ongoing risk management.

3. **ISO 31000 is referenced in the guidance but not in the data model.** If the risk manager follows ISO 31000 (as implied by Australian emergency management standards), the data model should include risk contexts, risk criteria, and treatment plans as first-class entities.

4. **Risk-informed decision support has no feedback loop.** The agent describes providing risk assessments to support IC decisions — but there's no mechanism for tracking whether IC decisions actually followed risk advice, what the outcomes were, and whether the risk assessment was accurate. Without a feedback loop, risk management can't improve.

5. **The agent was apparently added later** (it's the 10th operational agent, while the original spec called for 9). Its handoff relationships are well-integrated into other agents, which is good. But it doesn't appear in the original spec's FR-002 list of operational personas, suggesting it was an afterthought.

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "Overlap between risk-manager persona and RiskAssessmentAgent software is confusing." | **YES — Strong merit.** These serve different purposes (human governance vs. automated analysis) but the naming collision and unclear boundary is a real problem. |
| O2 | "No risk register data model entity." | **YES — Merit.** A risk register is the foundational artifact of risk management. Its absence means the risk manager role is aspirational. |
| O3 | "ISO 31000 alignment should be explicit in the data model." | **PARTIAL merit.** ISO 31000 provides a framework, but mapping every ISO concept to a data entity may be over-engineering. Key concepts (risk criteria, treatments) are worth adding. |
| O4 | "No feedback loop for risk assessment accuracy." | **YES — Merit.** This is how risk management matures. Without it, assessments remain uncalibrated guesses. |
| O5 | "Risk manager appears to be a late addition not in the original spec." | **PARTIAL merit.** Late additions aren't inherently bad if well-integrated, and this one is. But it should be added to the spec's FR-002 for completeness. |

---

## Technical Agents

### Agent 11: `technical/principal-engineer.agent.md`

**CRITIQUE FROM THE PRINCIPAL ENGINEER PERSPECTIVE:**

1. **The `copilot-instructions.md` file has duplicated, conflicting entries for the same feature.** The Active Technologies section lists `001-disaster-response-hub` entries multiple times with slightly different dependency lists (e.g., one mentions "Azure Service Bus or Event Hubs" and another mentions "Azure Event Hubs or Service Bus SDK"). This makes it unclear which is authoritative. The Project Structure section shows `backend/`, `frontend/`, `tests/` but the actual structure is `apps/`, `packages/`, `tests/`, `infra/`, `docs/`. This is actively misleading.

2. **The agent catalogue has scaled far beyond the original 31-agent specification.** The spec (FR-002, FR-003, FR-004) called for 9 operational + 14 sector + 8 technical = 31 agents. The current catalogue has ~90+ agents due to state/territory-specific expansion. The validation rules in the agent file contract (e.g., "every agent MUST have a corresponding entry in `AGENTS.md`") need to be verified — do all 90+ agents appear in the registry?

3. **No automated validation exists.** The spec describes structural validation rules (SC-002), the quickstart describes validation checks, but there's no actual validation script. For 90+ agents, manual validation is infeasible. There should be a CI check that validates YAML frontmatter, handoff references, required sections, and contextual reference paths.

4. **Technical debt in architecture documentation.** The architecture doc, constitution, and multiple specs reference the same system from different angles with varying levels of currency. There's no single source of truth for "what is actually built vs. what is planned." The principal engineer should own this distinction.

5. **The absence of ADRs (Architecture Decision Records).** Major decisions are embedded in spec research documents, plan documents, and agent guidance notes. There's no formal ADR log. For a system this complex, ADRs are essential for understanding why decisions were made.

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "`copilot-instructions.md` has duplicated, conflicting entries and wrong project structure." | **YES — Strong merit.** This file is auto-generated from plans and has accumulated contradictory entries. It's the primary dev guidance file and should be accurate. |
| O2 | "Agent count has tripled from spec without spec amendment." | **YES — Strong merit.** The spec says 31, reality is 90+. The spec, validation rules, and registry need updating to reflect actuality. |
| O3 | "No automated validation script for 90+ agents." | **YES — Strong merit.** Manual validation at this scale is unreliable. A CI check would catch broken handoffs, missing sections, and wrong references automatically. |
| O4 | "No clear distinction between built and planned features." | **YES — Merit.** Important for decision-making, but could be addressed through better doc hygiene rather than a new system. |
| O5 | "Missing ADRs." | **PARTIAL merit.** ADRs would be valuable, but the spec research documents serve a similar (if informal) purpose. Formal ADRs are nice-to-have. |

---

### Agent 12: `technical/solution-architect.agent.md`

**CRITIQUE FROM THE SOLUTION ARCHITECT PERSPECTIVE:**

1. **The CQRS-lite pattern is mentioned but not implemented in the codebase.** The architecture notes say "separate read models for dashboards (Redis-cached) from write models (Cosmos DB)" but the current API code uses direct repository access for both reads and writes. Either implement the pattern or remove the claim.

2. **"Maximum 3 runtime projects" is already violated.** The system has `apps/web`, `apps/api`, `apps/agents/` (with 5+ sub-agents), and upcoming ingestion pipelines. Whether agents are separate runtime deployments or in-process depends on the deployment model, but this guidance is already ambiguous.

3. **Azure Event Hubs vs. Service Bus is still "or" after multiple spec iterations.** The `copilot-instructions.md`, this agent, and the spec all say "Event Hubs or Service Bus." After 6 feature specifications, this decision should have been made. The ambiguity propagates through every agent that mentions messaging.

4. **Schema evolution strategy is mentioned but not specified.** "Govern API contracts and schema evolution" — but there's no versioning strategy, backward compatibility policy, or migration approach defined for OpenAPI or signal-envelope schema changes.

5. **The contextual references include paths that may not exist.** References `packages/schemas/openapi.yaml` and `infra/bicep/main.bicep` — do these actually exist in the repo? If not, these are aspirational references that violate the validation rule "contextReferences paths MUST point to files that exist."

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "CQRS-lite is documented but not implemented." | **YES — Merit.** Documentation should reflect reality, not aspirations. |
| O2 | "3 runtime projects limit is ambiguous or violated." | **PARTIAL merit.** It depends on how you count — agents can be in-process. Guidance should be clarified. |
| O3 | "Event Hubs vs. Service Bus needs a decision, not an 'or'." | **YES — Strong merit.** This has been deferred across 6 specs. Time to decide. |
| O4 | "Schema evolution strategy is unspecified." | **YES — Merit.** For a system that will evolve, breaking schema changes could be catastrophic. |
| O5 | "Contextual references may point to nonexistent files." | **YES — Merit.** Violates the project's own validation rules. |

---

### Agent 13: `technical/software-developer.agent.md`

**CRITIQUE FROM THE SOFTWARE DEVELOPER PERSPECTIVE:**

1. **The `copilot-instructions.md` says "cd src; pytest; ruff check ." but the project structure has no `src/` directory at root.** The actual commands would be different based on the monorepo structure. This is the primary developer onboarding document and it's wrong on basic commands.

2. **No code owner model.** The agent describes PR workflow and code review but there's no CODEOWNERS file, no defined ownership for the various modules (`apps/api/`, `apps/agents/`, `packages/domain/`), and no merge protection rules documented.

3. **Python/TypeScript boundary is well-defined but testing conventions differ.** The agent correctly identifies Python 3.12 + TypeScript 5.6 as the dual stack, but the testing guidance doesn't address how to test cross-stack contracts (e.g., the TypeScript frontend calling the Python API). Contract tests exist but the conventions for maintaining them aren't clear.

4. **Ruff configuration is referenced but may not actually exist.** The agent builds on the assumption that these configs exist. If they don't, the guidance is aspirational.

5. **No error handling conventions.** The agent doesn't address exception handling patterns, error response formats, or logging standards — which are critical for consistency in a multi-developer project.

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "Basic build/test commands in `copilot-instructions.md` are wrong." | **YES — Strong merit.** Developer friction from day one. |
| O2 | "No CODEOWNERS or ownership model." | **PARTIAL merit.** Important for a team project but may be premature for a one-person or small-team setup. |
| O3 | "Cross-stack contract testing conventions needed." | **YES — Merit.** The system has both stacks and they interact. |
| O4 | "Referenced config files may not exist." | **YES — Merit.** Same pattern as other agents — guidance referencing non-existent artifacts. |
| O5 | "Missing error handling conventions." | **YES — Merit.** Error patterns are among the most important conventions for consistency. |

---

### Agent 14: `technical/security-engineer.agent.md`

**CRITIQUE FROM THE SECURITY ENGINEER PERSPECTIVE:**

1. **Content safety is implemented but narrowly.** The `MonitoringAgent` has a simple one-word LLM response for misinformation detection ("credible" or "misinformation"). This is a content safety guardrail but it's trivially bypassable by adversarial inputs. A single-word response with no structured reasoning is not a defense against prompt/agent injection from social media signals.

2. **The `AuthenticatedPrincipal` model is a good start but fragile.** The auth module in `apps/api/app/core/auth.py` extracts claims from a dict with `.get()` defaults like `"anonymous"` and `"unknown-agency"`. This means unauthenticated requests could silently succeed with anonymous identity. There should be explicit validation and rejection of missing claims for protected endpoints.

3. **Tenant isolation is mentioned across multiple agents but no isolation test exists.** The constitution mandates jurisdiction-aware isolation, but there are no explicit tests verifying that one tenant can't access another tenant's data. This is a critical security gap.

4. **Encryption at rest and in transit is constitutionally mandated but not configured in Bicep.** Constitution Principle IV requires encryption. The Azure services default to encryption, but the Bicep templates should explicitly configure encryption settings to ensure compliance.

5. **No secrets management pattern.** The LLM client reads API keys from environment variables (`os.getenv("AZURE_OPENAI_API_KEY")`). While acceptable for local dev, there's no guidance on secrets management for production (Azure Key Vault, Managed Identity).

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "Content safety misinformation detection is trivially bypassable." | **YES — Strong merit.** A single-word LLM response is not a security boundary. Adversarial inputs from social media could bypass this easily. |
| O2 | "Auth defaults to anonymous — silent auth bypass risk." | **YES — Strong merit.** Safety-critical system must fail closed on missing auth, not default to anonymous. |
| O3 | "No tenant isolation tests." | **YES — Strong merit.** The absence of explicit multi-tenant isolation tests is a critical security gap for a system handling multiple agencies' data. |
| O4 | "Encryption configuration should be explicit in Bicep." | **PARTIAL merit.** Azure defaults are generally secure, but explicit configuration is defense-in-depth best practice. |
| O5 | "No secrets management pattern for production." | **YES — Merit.** Environment variables are fine for dev; production needs Key Vault or Managed Identity. |

---

### Agent 15: `technical/infrastructure-devops.agent.md`

**CRITIQUE FROM THE INFRASTRUCTURE/DEVOPS ENGINEER PERSPECTIVE:**

1. **Bicep templates are referenced but the infrastructure is incomplete.** The agent references `infra/bicep/main.bicep` and `infra/bicep/monitoring.bicep` — but the full infrastructure (Cosmos DB, Redis, Blob Storage, Container Apps, Event Hubs) needs to be defined. Without complete IaC, the "Azure AU-region only" constraint can't be enforced at deployment time.

2. **CI/CD pipeline is not defined.** The spec mentions GitHub Actions CI with a <10 minute target, but there's no `.github/workflows/` file described. The agent provides guidance but no pipeline exists to validate against.

3. **No blue-green or canary deployment strategy.** For a safety-critical system, zero-downtime deployment is essential. The agent doesn't address deployment strategies, rollback procedures, or feature flags.

4. **Monitoring is partially implemented but alerting is incomplete.** The spec mentions alert rules and action groups, but the actual monitoring Bicep is still being completed (FR-026, FR-027 from the rubric gap closure spec).

5. **Container security is mentioned but no container scanning.** Docker images are built but there's no Trivy, Snyk, or Azure Defender for Containers scanning in the pipeline.

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "Incomplete Bicep means AU-region constraint can't be enforced." | **YES — Strong merit.** IaC is how you enforce deployment constraints. |
| O2 | "No CI/CD pipeline definition." | **YES — Strong merit.** This should exist. |
| O3 | "No deployment strategy for a safety-critical system." | **YES — Merit.** Important but can be addressed later. |
| O4 | "Monitoring/alerting is incomplete." | **YES — Merit.** Being actively worked on per spec 003. |
| O5 | "No container scanning." | **YES — Merit.** Standard security practice. |

---

### Agent 16: `technical/data-engineer.agent.md`

**CRITIQUE FROM THE DATA ENGINEER PERSPECTIVE:**

1. **Cosmos DB partition strategy is not defined.** The agent references Cosmos DB for operational state but doesn't specify partition keys for any container. For a system with multi-jurisdiction data and high signal throughput (50,000/hour), partition design is critical for performance and cost.

2. **The signal ingestion pipeline (spec 006) is well-specified but the data model's `Signal` entity doesn't include deduplication fields.** The constitution requires freshness and provenance, but without dedup hashes on signals, the same BoM warning could be ingested multiple times.

3. **No data retention or lifecycle policy.** The system will accumulate signals, timeline events, and audit entries indefinitely. There's no TTL policy, archival strategy, or data lifecycle management for any entity.

4. **The choice of Cosmos DB for everything is questioned.** The `copilot-instructions.md` says "pending data-engineer review for polyglot alternatives." This review hasn't happened. For time-series signal data, a time-series database might be more appropriate. For the audit trail, immutable Blob Storage is already planned. Cosmos DB for operational state is reasonable.

5. **Ingestion from BoM, Geoscience Australia, and other sources needs resilience.** The spec 006 mentions FTP/HTTP polling and XML parsing, but what happens when BoM is down? The data engineer agent should define retry, backoff, circuit-breaker, and stale-data handling patterns.

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "Cosmos DB partition strategy undefined." | **YES — Strong merit.** This is foundational for performance and cost. Must be decided before writing any Cosmos code. |
| O2 | "No signal deduplication." | **YES — Strong merit.** 50,000 signals/hour with no dedup will create data quality issues. |
| O3 | "No data retention policy." | **YES — Merit.** Important for cost management and compliance, though not MVP-blocking. |
| O4 | "Polyglot data stores need evaluation." | **PARTIAL merit.** Cosmos DB is a reasonable default. The review should happen but isn't urgent. |
| O5 | "Source resilience patterns needed." | **YES — Merit.** BoM and GA going down during a disaster is a real scenario. |

---

### Agent 17: `technical/qa-test-engineer.agent.md`

**CRITIQUE FROM THE QA/TEST ENGINEER PERSPECTIVE:**

1. **Testing strategy has four tiers (contract, integration, simulation, e2e) but unclear which tests exist.** The tests directory structure shows these tiers, and some contract tests exist (e.g., `test_risk_assessment_llm.py`), but there's no test coverage report and no minimum coverage threshold defined.

2. **Simulation testing is the most novel and least specified tier.** The capstone mentions "scenario replay" and the spec references simulation tests, but the methodology for simulation testing — how scenarios are defined, what constitutes pass/fail, how to run them — isn't documented.

3. **Playwright e2e tests are referenced but the web app is still evolving.** E2e tests are fragile during active UI development. The agent should provide guidance on when to write e2e tests (stable screens only) vs. when to rely on component tests.

4. **Load testing target of 50,000 signals/hour is specific but untested.** The Locust load test suite is mentioned in spec 003, but it's unclear if it's actually implemented and what the current baseline is.

5. **No test data management strategy.** Testing a multi-agency disaster response system needs realistic test data — incidents, organisations, jurisdictions, signals. There's no test data seeding strategy or fixture library.

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "No coverage report or minimum threshold." | **YES — Merit.** TDD is constitutionally mandated but coverage isn't tracked. |
| O2 | "Simulation testing methodology is unspecified." | **YES — Strong merit.** This is the highest-value testing tier for a disaster response system and it's not documented. |
| O3 | "E2e test timing guidance needed." | **PARTIAL merit.** Reasonable guidance point but not a critical gap. |
| O4 | "Load test results unknown." | **YES — Merit.** Performance targets exist but baseline measurements don't. |
| O5 | "No test data management strategy." | **YES — Strong merit.** Realistic test data is essential for meaningful testing. |

---

### Agent 18: `technical/ux-designer.agent.md`

**CRITIQUE FROM THE UX DESIGNER PERSPECTIVE:**

1. **High-pressure operations context is well-identified.** The agent correctly notes that disaster response dashboards are used under extreme stress. This should drive every design decision: large touch targets, high contrast, minimal cognitive load.

2. **WCAG 2.1 AA is the minimum per constitution, but the dashboard's actual accessibility hasn't been tested.** There's no accessibility audit, no axe-core integration, no screen reader testing documented.

3. **Mobile responsiveness is mentioned but the needs of field coordinators aren't addressed.** The field coordinator operates on mobile in degraded conditions. The UX agent should define mobile-specific interaction patterns: offline indicators, sync status, fat-finger-friendly controls for gloved hands.

4. **Multi-language UI support isn't addressed.** Constitution Principle V mandates multilingual alerts, but the UI itself — navigation, labels, error messages — may need localization for diverse workforce deployments.

5. **Information density balance is unaddressed.** Incident commanders need dense information; field coordinators need minimal, actionable info. The role-based workspace concept (US2) needs UX guidance on information density by persona.

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "High-stress UX design is well-identified." | **N/A — Positive observation, not an objection.** |
| O2 | "No accessibility audit or automated testing." | **YES — Strong merit.** Constitution mandates WCAG AA. Must be tested, not just aspired to. |
| O3 | "Mobile UX for field coordinators not addressed." | **YES — Merit.** The field coordinator's environment (outdoors, gloves, sunlight, degraded connectivity) demands specific mobile UX patterns. |
| O4 | "UI localization not addressed." | **PARTIAL merit.** Alert content needs multi-language; the UI itself may not need full localization for MVP. |
| O5 | "Information density by persona not specified." | **YES — Merit.** Different personas have fundamentally different information needs. |

---

### Agent 19: `technical/product-owner-ba.agent.md`

**CRITIQUE FROM THE PRODUCT OWNER/BA PERSPECTIVE:**

1. **The success metrics in the capstone are aspirational without measurement capability.** "Save 1,000+ lives annually," "Reduce response time by 50%," "Evacuate 24 hours earlier" — these are marketing claims, not measurable product metrics. There's no baseline, no measurement methodology, no telemetry to track these outcomes.

2. **User stories are well-structured but too few.** The main spec has 3 user stories. For a system of this complexity, there should be significantly more granular stories, especially for the sector-specific interactions.

3. **Acceptance criteria are scenario-based, which is good, but lack negative cases.** The acceptance scenarios describe happy paths. Where are the failure scenarios? What happens when BoM is down? When an IC rejects a recommendation? When conflicting signals arrive?

4. **No stakeholder validation model.** The spec references multiple Australian emergency management agencies, but there's no evidence of stakeholder validation — has any actual emergency management professional reviewed these requirements?

5. **Feature prioritization rationale is unclear.** Why is live incident coordination (US1) MVP while preparedness (US3) is P3? In Australian disaster management, preparedness is often considered more impactful than response coordination (PPRR model: Prevention, Preparedness, Response, Recovery).

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "Success metrics are unmeasurable marketing claims." | **YES — Strong merit.** Metrics must be SMART (Specific, Measurable, Achievable, Relevant, Time-bound). These aren't. |
| O2 | "Too few user stories for this complexity." | **YES — Merit.** 3 stories for a system this complex is too coarse. |
| O3 | "No failure/negative acceptance scenarios." | **YES — Strong merit.** Safety-critical systems need negative test cases more than positive ones. |
| O4 | "No stakeholder validation." | **YES — Strong merit.** Building a disaster response system without EM professional input is risky. |
| O5 | "Prioritization of response over preparedness is questionable." | **PARTIAL merit.** Response is more visually demonstrable (MVP/capstone), but the PPRR argument has genuine merit in EM practice. |

---

### Agent 20: `technical/api-architect.agent.md`

**CRITIQUE FROM THE API ARCHITECT PERSPECTIVE:**

1. **The OpenAPI contract is referenced but its completeness is unknown.** The spec references `packages/schemas/openapi.yaml` but the actual API surface area — endpoints for incidents, signals, recommendations, approvals, alerts — may not all be defined.

2. **No API versioning strategy.** For a system that multiple agencies will integrate with, API versioning is critical. Breaking changes to the signal ingestion API could disrupt BoM, GA, and other feeds.

3. **Rate limiting / throttling not addressed.** 50,000 signals/hour from multiple sources needs admission control. What happens during signal flood? The API needs back-pressure messaging mechanisms.

4. **Multi-tenant API scoping is architecturally mandated but not detailed.** Every API call must be scoped to government and jurisdiction. How is this enforced? Through middleware? Through path parameters? Through claim-based authorization?

5. **No webhook or push API for external consumers.** The system ingests data from agencies, but do agencies receive events from the hub? The communication is currently one-directional for data flow (ingest signals) and one-directional for alerts (publish). But agencies may need real-time event subscriptions.

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "OpenAPI completeness unknown." | **YES — Merit.** Should be verified. |
| O2 | "No API versioning strategy." | **YES — Strong merit.** Essential for multi-agency integration. |
| O3 | "Rate limiting not addressed." | **YES — Strong merit.** Signal floods are a real scenario during major disasters. |
| O4 | "Multi-tenant scoping mechanism undefined." | **YES — Strong merit.** This is where security and architecture intersect critically. |
| O5 | "No push API for external consumers." | **PARTIAL merit.** Push notifications to agencies would be valuable but is realistically a phase 2 feature. |

---

### Agent 21: `technical/ai-ml-engineer.agent.md`

**CRITIQUE FROM THE AI/ML ENGINEER PERSPECTIVE:**

1. **LLM integration is currently minimal but presented as a core capability.** The actual LLM usage is: (a) misinformation detection with a one-word response, (b) risk assessment explanation generation, (c) multilingual alert drafting. These are reasonable starting points but are all simple prompt-response patterns, not agentic AI behavior.

2. **No model evaluation framework.** The system uses Azure OpenAI, but there's no evaluation suite, no benchmark set, no quality metrics for LLM outputs. How do you know the multilingual alert drafts are accurate? How do you measure explanation quality?

3. **Confidence scoring is hardcoded.** The risk assessment agent always returns `confidence_level="high"` and the handoff confidence is hardcoded to `0.9`. These should be dynamically computed based on signal quality and model uncertainty.

4. **No model versioning or deployment tracking.** The `ModelDeployment` entity exists in the domain models, but actual model deployment tracking (which model version produced which output) is partially implemented at best.

5. **Content safety is the right concern but implementation is surface-level.** The `CommunicationAgent` checks `content_safety_result` but the actual safety validation appears to be a passthrough. Toxic, misleading, or panic-inducing alert content could reach production.

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "LLM usage is simple prompt-response, not agentic." | **PARTIAL merit.** The spec is explicit about "deterministic orchestration" with LLM for augmentation, not autonomous AI. This is by design. |
| O2 | "No model evaluation framework." | **YES — Strong merit.** You can't deploy LLM outputs in a safety-critical system without evaluation. |
| O3 | "Confidence scoring is hardcoded." | **YES — Strong merit.** In a system where confidence drives decisions (handoffs, approvals), hardcoded values are dangerous. |
| O4 | "Model versioning is incomplete." | **YES — Merit.** The infrastructure exists (ModelDeployment entity) but implementation needs completion. |
| O5 | "Content safety validation is surface-level." | **YES — Strong merit.** For public alerts, content safety is safety-critical. Surface-level checks are insufficient. |

---

### Agent 22: `technical/azure-principal-architect.agent.md`

**CRITIQUE FROM THE AZURE PRINCIPAL ARCHITECT PERSPECTIVE:**

1. **Azure Well-Architected Framework (WAF) assessment is referenced but not documented.** The agent should guide WAF assessments across all 5 pillars (Reliability, Security, Cost Optimization, Operational Excellence, Performance Efficiency) but there's no assessment artifact.

2. **Azure Cosmos DB is used as a general-purpose database without considering alternatives.** For time-series signal data, Azure Data Explorer or Azure Table Storage might be more cost-effective. For the audit trail, immutable Blob Storage is already planned. The "pending data-engineer review" has never landed.

3. **Azure AU-region constraint is constitutionally mandated but specific region selection isn't documented.** Australia has 5 Azure regions (Australia East, Australia Southeast, Australia Central, Australia Central 2, Australia). Which are primary and DR? Are paired regions used for geographic redundancy?

4. **No disaster recovery plan for the disaster response system itself.** Ironic but critical: what happens when the Azure region hosting this system is itself affected by the disaster it's coordinating? There's no DR strategy, backup region, or failover documentation.

5. **Cost estimation is absent.** Azure Cosmos DB, Event Hubs, Redis, Container Apps, Blob Storage, Azure OpenAI — this is an expensive stack. No cost estimate exists for the projected workload (1,000 operators, 50,000 signals/hour, 100+ organisations).

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "No WAF assessment artifact." | **YES — Merit.** WAF assessment is a best practice for Azure solutions. |
| O2 | "Cosmos DB may not be optimal for all workloads." | **YES — Merit.** A valid technical evaluation that should happen. |
| O3 | "Specific Azure region selection not documented." | **YES — Merit.** Needs to be explicit for deployment and DR. |
| O4 | "No DR plan for the coordination hub itself." | **YES — Strong merit.** A disaster response system must be resilient to disasters. This is arguably the most critical gap. |
| O5 | "No cost estimation." | **YES — Merit.** Important for viability. |

---

### Agent 23: `technical/chaos-engineer.agent.md`

**CRITIQUE FROM THE CHAOS ENGINEER PERSPECTIVE:**

1. **Chaos engineering principles are relevant but the system is too immature for chaos testing.** You need stable, well-tested baseline behavior before injecting failures. The current system doesn't have comprehensive integration tests, load tests, or deployment pipelines. Chaos testing would be premature.

2. **However, failure mode analysis should happen NOW.** While active chaos testing is premature, FMEA (Failure Mode and Effects Analysis) should be done during design. What happens when each component fails? The degraded mode architecture is partially specified but not systematically covered.

3. **The agent should define specific chaos experiments for future implementation.** "What happens when BoM goes down?" "What happens when Cosmos DB is slow?" "What happens when the LLM service is unavailable?" These can be documented as planned experiments even if not yet executable.

4. **The agent correctly identifies degraded source handling as critical.** If a data source becomes unreliable during an active incident, the system must degrade gracefully. This is already in the constitution but needs concrete implementation.

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "Chaos testing is premature at current maturity." | **YES — Merit.** Can't break what isn't built and stable yet. |
| O2 | "Failure mode analysis should happen now." | **YES — Strong merit.** FMEA during design is a best practice. |
| O3 | "Plan chaos experiments for future implementation." | **YES — Merit.** Good engineering discipline to document expected failure scenarios. |
| O4 | "Degraded source handling is constitution-critical." | **YES — Strong merit.** The constitution mandates safe degradation. |

---

### Agent 24: `technical/compliance-auditor.agent.md`

**CRITIQUE FROM THE COMPLIANCE AUDITOR PERSPECTIVE:**

1. **Australian privacy legislation is correctly identified (Privacy Act 1988, APPs) but not mapped to system controls.** Each APP should map to a specific system capability or policy. What data does the system collect? Under which APP is it justified? How is consent managed?

2. **The intersection of multiple jurisdictions' privacy laws is unaddressed.** NSW, VIC, and QLD all have jurisdiction-specific privacy legislation that may impose additional requirements beyond the Commonwealth Privacy Act. The system needs a jurisdiction-privacy matrix.

3. **No privacy impact assessment.** For a system processing personal data (location data from IoT, community reports, field reports mentioning individuals), a PIA is likely legally required and is certainly best practice.

4. **Records management obligations differ by jurisdiction.** Each state has different records retention legislation (e.g., NSW State Records Act 1998, VIC Public Records Act 1973). The system's data retention must comply with the strictest applicable requirement.

5. **Emergency powers change privacy rules.** During declared emergencies, certain privacy constraints may be relaxed. The system should understand and model these emergency-specific privacy provisions.

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "Privacy Act APPs not mapped to system controls." | **YES — Strong merit.** Compliance requires specific control mappings. |
| O2 | "Multi-jurisdiction privacy matrix needed." | **YES — Merit.** Real gap for a multi-state system. |
| O3 | "PIA likely required." | **YES — Strong merit.** Should be done before handling real personal data. |
| O4 | "Records retention varies by jurisdiction." | **YES — Merit.** Affects data lifecycle policies. |
| O5 | "Emergency powers change privacy rules." | **YES — Merit.** Unique to emergency management context, important to model. |

---

### Agent 25: `technical/docker-container-engineer.agent.md`

**CRITIQUE FROM THE DOCKER/CONTAINER ENGINEER PERSPECTIVE:**

1. **Non-root container requirement is in the spec but needs verification.** The spec (003) mentions "non-root container images" but this needs to be enforced in Dockerfiles and validated in CI.

2. **Multi-stage builds should be standard.** For Python and Node.js applications, multi-stage builds reduce image size and attack surface. The agent should mandate this pattern.

3. **No container registry specified.** Azure Container Registry (ACR) is the obvious choice given the Azure stack, but it's not specified.

4. **Health checks are essential for Container Apps.** Container health probes (liveness, readiness, startup) need to be defined for each service.

5. **Image versioning and tagging strategy absent.** How are images tagged? Commit SHA? Semantic version? No convention is defined.

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "Non-root enforcement needs CI validation." | **YES — Merit.** |
| O2 | "Multi-stage builds should be standard." | **YES — Merit.** Best practice. |
| O3 | "No container registry specified." | **YES — Merit.** Needs to be ACR for AU-region compliance. |
| O4 | "Health probes not defined." | **YES — Merit.** Essential for Container Apps deployment. |
| O5 | "Image tagging strategy absent." | **YES — Merit.** Important for traceability. |

---

### Agent 26: `technical/sre-engineer.agent.md`

**CRITIQUE FROM THE SRE ENGINEER PERSPECTIVE:**

1. **No SLOs/SLAs defined.** The non-functional requirements have performance targets (dashboard <2s p95, API <500ms p95, signals 50K/hour) but these aren't formalized as SLOs with error budgets.

2. **No runbook library.** The architecture doc mentions "response runbooks" under `docs/disaster-response-hub/` but none exist. For a production system, runbooks for common failure scenarios are essential.

3. **No on-call rotation or escalation path.** For a 24/7 disaster response system, who gets paged when it's down? This is an SRE fundamental.

4. **Monitoring and observability are partially implemented.** Azure Monitor with Bicep alerts is a start, but structured logging, distributed tracing (Application Insights), and correlation IDs for multi-agent flows aren't defined.

5. **No capacity planning.** 1,000 concurrent operators and 50,000 signals/hour are targets, but the provisioning model to handle these loads isn't specified.

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "SLOs need formalization." | **YES — Merit.** Performance targets exist; SLOs with error budgets are the next step. |
| O2 | "No runbooks." | **YES — Strong merit.** Essential for operations. |
| O3 | "No on-call/escalation." | **YES — Merit but premature.** This matters when the system is in production. |
| O4 | "Observability is incomplete." | **YES — Merit.** Distributed tracing is critical for multi-agent debugging. |
| O5 | "No capacity planning." | **YES — Merit.** Need to know resource requirements before deployment. |

---

### Agent 27: `technical/accessibility-tester.agent.md`

**CRITIQUE FROM THE ACCESSIBILITY TESTER PERSPECTIVE:**

1. **WCAG 2.1 AA is correct but WCAG 2.2 has been published.** The constitution mandates "WCAG 2.1 AA minimum" — but WCAG 2.2 was published in October 2023. For a new system, targeting 2.2 is better practice.

2. **No automated accessibility testing in CI.** axe-core, Lighthouse, or Pa11y should run on every PR that touches frontend code. None of this exists.

3. **Disaster response UIs have unique accessibility needs.** Color-blind operators may miss red/orange severity indicators. Screen magnification users may not see map overlays. The agent should define disaster-specific accessibility test scenarios.

4. **Audio/voice interfaces aren't considered.** In field conditions, visual interfaces may be impractical. Voice-driven interaction (e.g., "Show me active tasks in my sector") could be critical for accessibility and operational effectiveness.

5. **The accessibility tester agent is a good addition beyond the original 8 technical agents.** It shows recognition that accessibility deserves a dedicated testing perspective.

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "Target WCAG 2.2, not 2.1." | **YES — Merit.** If building new, target the latest standard. |
| O2 | "No automated accessibility CI checks." | **YES — Strong merit.** Must be automated to maintain compliance. |
| O3 | "Disaster-specific accessibility scenarios needed." | **YES — Strong merit.** Color-blind operators and severity indicators is a critical real-world scenario. |
| O4 | "Voice interfaces for field conditions." | **PARTIAL merit.** Aspirational but out of scope for MVP. |
| O5 | "Good that this agent exists." | **N/A — Positive observation.** |

---

## Cross-Sector Agents

### Agent 28: `sectors/cross-sector/health.agent.md`

**CRITIQUE FROM THE HEALTH SECTOR PERSPECTIVE:**

1. **Scope boundaries reference archived agents.** The scope boundaries reference `ambulance-paramedic`, `commonwealth-government`, and `meteorology-bom` — all three are archived. The handoff YAML correctly references `nsw-ambulance` for one, but the scope boundaries text is inconsistent. This is a systemic issue.

2. **The health sector is arguably the most complex cross-sector agent and it tries to cover too much.** Hospital surge, environmental health, mental health, pandemic response, pharmaceutical distribution — each of these is a discipline unto itself. This agent is a mile wide and an inch deep. Compare with the fire sector which was split into state-specific agents.

3. **The jurisdictional variations table is excellent.** This is the kind of concrete, actionable domain knowledge that makes these agents valuable. Every cross-sector agent should have this level of specificity.

4. **Mental health response is included, which is forward-thinking.** Disaster mental health is often overlooked. Including it here — with temporal phases (immediate, short, medium, long-term) — is genuinely valuable.

5. **No mention of pandemic-specific data requirements.** The agent says health becomes "lead agency for pandemic and communicable disease emergencies" but doesn't address the unique data flows (case numbers, vaccination rates, contact tracing) that pandemics require. The data model has no pandemic-specific entities.

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "Scope boundaries reference archived agents." | **YES — Strong merit.** Systematic issue across many agents. |
| O2 | "Health agent is too broad — should be split like fire was." | **PARTIAL merit.** Health could be split into separate agents for hospital surge, public health, and mental health. But the jurisdictional split (by state) doesn't make as much sense for health as it does for fire services, since health departments operate similarly across states. |
| O3 | "Jurisdictional variations table is excellent." | **N/A — Positive observation.** |
| O4 | "Mental health inclusion is commendable." | **N/A — Positive observation.** |
| O5 | "Pandemic data requirements missing." | **PARTIAL merit.** Pandemics are a valid disaster type but very different from natural disasters. May warrant its own mini-spec rather than being crammed into this agent. |

---

### Agent 29: `sectors/cross-sector/transport.agent.md`

**CRITIQUE FROM THE TRANSPORT SECTOR PERSPECTIVE:**

1. **Transport is critical for evacuation but poorly connected to the Evacuation Agent.** The software `EvacuationAgent` does route pressure analysis, but the transport sector agent (which knows about actual road networks, rail services, and fleet assets) has no direct handoff to contribute to evacuation planning.

2. **No real-time traffic data integration.** Transport coordination during disasters requires knowledge of road closures, bridge conditions, and traffic management points. The signal pipeline doesn't include transport-specific data feeds (e.g., Transport for NSW LiveTraffic, VicRoads).

3. **Multi-modal transport isn't addressed.** Evacuation may require air (helicopters, RAAF), sea (boats for flood isolation), rail, and road. The agent should address intermodal coordination.

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "Transport agent disconnected from Evacuation software agent." | **YES — Strong merit.** Critical gap between domain knowledge and software capability. |
| O2 | "No transport-specific data feeds." | **YES — Merit.** Real-time road status is essential for evacuation routing. |
| O3 | "Multi-modal transport coordination needed." | **YES — Merit.** Single-mode (road only) is insufficient for Australian disasters. |

---

### Agent 30: `sectors/cross-sector/utility.agent.md`

**CRITIQUE FROM THE UTILITY SECTOR PERSPECTIVE:**

1. **Utility infrastructure failure cascades are unmodelled.** Power failure causes water pump failure which causes communication failure. These cascading dependencies are critical in disaster response but the data model has no infrastructure dependency graph.

2. **No integration with SCADA/OT systems.** Utility operations during disasters depend on operational technology monitoring (power grid SCADA, water system SCADA). The signal pipeline doesn't include OT data feeds.

3. **Essential services priority restoration is a key concept not modelled.** After a disaster, utilities prioritize restoring service to hospitals, evacuation centres, and critical infrastructure. This priority model doesn't exist in the data model.

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "Infrastructure cascade dependencies unmodelled." | **YES — Strong merit.** Critical for understanding real disaster impacts. |
| O2 | "No SCADA/OT integration." | **PARTIAL merit.** Important but extremely complex and security-sensitive. |
| O3 | "Service restoration prioritization not modelled." | **YES — Merit.** Important for recovery phase. |

---

### Agent 31: `sectors/cross-sector/local-government.agent.md`

**CRITIQUE FROM THE LOCAL GOVERNMENT PERSPECTIVE:**

1. **Local government is where disasters actually happen**, yet this agent is at the same level as other cross-sector agents. In Australian EM, local government is the first responder tier. The agent should have rich local context: evacuation centres, community halls, local hazard profiles.

2. **No model for local government capacity variation.** A Sydney metro council has very different disaster capacity than a remote rural shire. The agent should address this disparity.

3. **Evacuation centre management is correctly identified as a local government responsibility but has no supporting data model.**

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "Local government is under-emphasized relative to its EM importance." | **YES — Merit.** |
| O2 | "Capacity variation between urban and rural councils." | **YES — Merit.** |
| O3 | "Evacuation centres need data model support." | **YES — Strong merit.** |

---

### Agents 32–33: `sectors/cross-sector/state-government.agent.md` & `territory-government.agent.md`

**CRITIQUE:**

1. **These agents correctly describe the coordination role** of state/territory governments in Australian EM — they coordinate major incidents, manage emergency declarations, and interface between local and Commonwealth levels.

2. **The distinction between state and territory agents is appropriate** given legislative differences (states have sovereign emergency management acts; territories have self-governing arrangements with some Commonwealth oversight).

3. **Emergency declaration workflows are mentioned but unmodelled** (same issue as executive-leader agent).

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "Emergency declaration workflows missing from data model." | **YES — Merit.** (Previously identified) |
| O2 | "State/territory distinction is appropriate." | **N/A — Positive observation.** |

---

### Agents 34–35: `sectors/cross-sector/community-ngos.agent.md` & `volunteer.agent.md`

**CRITIQUE:**

1. **Community NGOs agent correctly identifies Red Cross, Salvation Army, and community recovery organizations.** These are critical partners in Australian EM.

2. **Volunteer management is a genuine complexity.** Spontaneous volunteers, credentialing, protection legislation — the agent addresses real challenges.

3. **The boundary between organized volunteering (NGOs) and spontaneous volunteers is well-drawn.** Community-ngos handles organized programs; volunteer handles spontaneous arrivals.

4. **No model for volunteer credentialing or skills matching.** The data model has no way to represent volunteer capabilities, credentials, or availability.

5. **Digital volunteer management (social media, crowdsourcing) is unaddressed.** Modern disaster response increasingly uses digital volunteering (crisis mapping, social media monitoring). The agent focuses on physical volunteers only.

**OBJECTIONS:**

| # | Objection | Has Merit? |
|---|-----------|-----------|
| O1 | "Volunteer credentialing needs data model support." | **YES — Merit.** |
| O2 | "Digital volunteering is unaddressed." | **PARTIAL merit.** Important but not MVP-critical. |
| O3 | "NGO/volunteer boundary is well-drawn." | **N/A — Positive observation.** |

---

## State/Territory Sector Agents

### Systemic Critique (All State/Territory Agents)

**These agents follow a cookie-cutter template with minimal differentiation. The systemic issues are:**

1. **Generic responsibilities.** "Bushfire detection, containment, and suppression" is true of *every* fire service. What's specific to each agency? What unique capabilities, legislative authorities, or operational constraints?

2. **Filler relationship descriptions.** Every key relationship says "Coordination within [State] emergency management arrangements" — meaningless boilerplate that adds no development guidance.

3. **Missing legislation.** The archived generic agents had comprehensive legislation tables. The state-specific agents removed this and replaced it with nothing. FRNSW should mention the Fire Brigades Act 1989 (NSW); CFA should mention the Country Fire Authority Act 1958 (VIC). None do.

4. **Generic scope boundaries.** Every fire agent: "Not flood → SES; not medical → ambulance; not law enforcement → police." Identical across all states. State-specific scope (e.g., CFA rural vs FRV urban in Victoria) is not captured.

5. **However, the handoff network is correctly wired.** Each state agent references the correct peer agencies within its jurisdiction. This is genuinely valuable for catalog navigation.

6. **Contextual references to seed data files are good.** References to `packages/domain/src/domain/seed/organisations_australia.json` ground the agents in actual system data.

---

### NSW Agents (36–41)

| # | Agent | Key Critique | Objection Merit |
|---|-------|-------------|-----------------|
| 36 | `nsw/frnsw.agent.md` | Missing urban/rural boundary with NSW RFS — the defining characteristic of NSW fire services | **YES** |
| 37 | `nsw/nsw-rfs.agent.md` | No mention of volunteer workforce model, world's largest volunteer fire service | **YES** |
| 38 | `nsw/ses-nsw.agent.md` | "Combat agency" designation has specific legislative meaning in NSW; not mentioned | **PARTIAL** |
| 39 | `nsw/nswpf.agent.md` | Police are lead combat agency for terrorism and SAR in NSW; not mentioned | **YES** |
| 40 | `nsw/nsw-ambulance.agent.md` | No mention of aeromedical capabilities (helicopters) | **PARTIAL** |
| 41 | `nsw/mrnsw.agent.md` | No mention of inland flood rescue role | **YES** |

---

### NT Agents (42–46)

| # | Agent | Key Critique | Objection Merit |
|---|-------|-------------|-----------------|
| 42 | `nt/bushfires-nt.agent.md` | NT's vast distances and remote Aboriginal communities not addressed | **YES** |
| 43 | `nt/ntes.agent.md` | Cyclone-prone Top End context missing | **YES** |
| 44 | `nt/ntfrs.agent.md` | Generic urban fire description; NT-specific context absent | **YES** |
| 45 | `nt/ntpf.agent.md` | NT Police carries broader responsibilities in remote areas; not captured | **YES** |
| 46 | `nt/sja-nt.agent.md` | SJA operates NT ambulance under contract — unique arrangement not mentioned | **YES** |

---

### QLD Agents (47–50)

| # | Agent | Key Critique | Objection Merit |
|---|-------|-------------|-----------------|
| 47 | `qld/qas.agent.md` | Generic ambulance description | **PARTIAL** |
| 48 | `qld/qfd.agent.md` | Recent restructure (QFES → QFD) may not be reflected | **YES** |
| 49 | `qld/qps.agent.md` | QPS is the primary disaster coordination agency in QLD (unique); District Disaster Coordinator is always police | **YES** |
| 50 | `qld/ses-qld.agent.md` | Cyclone exposure (most of any state) should be prominent | **YES** |

---

### SA Agents (51–55)

| # | Agent | Key Critique | Objection Merit |
|---|-------|-------------|-----------------|
| 51 | `sa/saas.agent.md` | Generic ambulance description | **PARTIAL** |
| 52 | `sa/sacfs.agent.md` | Dual fire service model boundary with SAMFS not captured | **PARTIAL** |
| 53 | `sa/samfs.agent.md` | Metropolitan boundary not specified | **PARTIAL** |
| 54 | `sa/sapol.agent.md` | SA Police acts as Hazard Leader for many disaster types; not mentioned | **YES** |
| 55 | `sa/ses-sa.agent.md` | Generic SES description | **PARTIAL** |

---

### TAS Agents (56–59)

| # | Agent | Key Critique | Objection Merit |
|---|-------|-------------|-----------------|
| 56 | `tas/at.agent.md` | Generic ambulance description | **PARTIAL** |
| 57 | `tas/ses-tas.agent.md` | Generic SES description | **PARTIAL** |
| 58 | `tas/taspol.agent.md` | Tasmania Police coordinates land-based SAR as combat agency; not mentioned | **YES** |
| 59 | `tas/tfs.agent.md` | Tasmania has a **unified** fire service (unlike dual NSW/VIC/SA models); this simplification is not noted | **YES** |

---

### VIC Agents (60–64)

| # | Agent | Key Critique | Objection Merit |
|---|-------|-------------|-----------------|
| 60 | `vic/av.agent.md` | Generic ambulance description | **PARTIAL** |
| 61 | `vic/cfa-vic.agent.md` | CFA/FRV boundary disputes and overlap zones not addressed — the most complex fire arrangement in Australia | **YES** |
| 62 | `vic/frv.agent.md` | Metropolitan boundary with CFA not specified | **YES** |
| 63 | `vic/ses-vic.agent.md` | Generic SES description | **PARTIAL** |
| 64 | `vic/vicpol.agent.md` | Victoria Police is control agency for SAR and counterterrorism; not mentioned | **YES** |

---

### WA Agents (65–67)

| # | Agent | Key Critique | Objection Merit |
|---|-------|-------------|-----------------|
| 65 | `wa/dfes-wa.agent.md` | DFES is a **unified** emergency service (fire + SES + EM combined); this unique model is not captured. WA covers 1/3 of Australia's land mass — geographic scale not addressed | **YES** |
| 66 | `wa/sja-wa.agent.md` | SJA operates WA ambulance service — non-government arrangement not mentioned | **YES** |
| 67 | `wa/wapol.agent.md` | Generic police description; WA Police has unique remote policing challenges | **PARTIAL** |

**Additional WA critique:** Only 3 agents while most states have 4-6. Missing WA SES (unless covered under DFES).

---

### ACT Agents (68–74)

| # | Agent | Key Critique | Objection Merit |
|---|-------|-------------|-----------------|
| 68 | `act/act-ambulance.agent.md` | Generic ambulance | **PARTIAL** |
| 69 | `act/act-esa.agent.md` | ESA is umbrella agency for ACT F&R, RFS, SES — redundant with sub-service agents | **YES** |
| 70 | `act/act-fr.agent.md` | Generic urban fire | **PARTIAL** |
| 71 | `act/act-policing.agent.md` | ACT Policing provided by AFP — correctly identified | **N/A** |
| 72 | `act/act-rfs.agent.md` | Generic rural fire; no mention of 2003 Canberra bushfires (formative event) | **YES** |
| 73 | `act/afp.agent.md` | Potential confusion with `commonwealth/afp.agent.md` | **YES** |
| 74 | `act/ses-act.agent.md` | Generic SES | **PARTIAL** |

**Additional ACT critique:** 7 agents is disproportionate for Australia's smallest jurisdiction (~460K people) compared to VIC (6.7M, 5 agents).

---

## Commonwealth Sector Agents

| # | Agent | Key Critique | Objection Merit |
|---|-------|-------------|-----------------|
| 75 | `commonwealth/nema.agent.md` | **Most important coordination body, least useful agent.** Scope boundary is circular ("does NOT cover: operations outside scope of NEMA"). Key relationships are boilerplate. Handoffs should go to state/territory EM agencies, not just Commonwealth agencies. | **YES — Strong** |
| 76 | `commonwealth/bom-national.agent.md` | Should be richest Commonwealth agent — constitutionally mandated authoritative source. Likely follows thin template. | **YES** |
| 77 | `commonwealth/ga-national.agent.md` | Earthquake, tsunami, geohazard. Also provides satellite imagery for disaster assessment — not mentioned. | **PARTIAL** |
| 78 | `commonwealth/adf.agent.md` | DACC categories of assistance (1-6) should be detailed. | **YES** |
| 79 | `commonwealth/afp.agent.md` | Appears in both ACT and Commonwealth folders — potential confusion/duplication. | **YES** |
| 80 | `commonwealth/abf.agent.md` | Border security during disasters. Narrow, legitimate scope. | **PARTIAL** |
| 81 | `commonwealth/arc.agent.md` | Red Cross is critical humanitarian partner. Good placement at Commonwealth level. | **N/A** |
| 82 | `commonwealth/asa.agent.md` | Airservices Australia — niche but relevant for aerial firefighting. | **PARTIAL** |
| 83 | `commonwealth/rfds.agent.md` | RFDS is medical transport, not traditional emergency service. Placement as EM service is awkward. | **PARTIAL** |
| 84 | `commonwealth/sja-national.agent.md` | National coordination for SJA state operations. Reasonable. | **N/A** |
| 85 | `commonwealth/surf-lifesaving.agent.md` | Very niche disaster role. Primary role is beach safety, not disaster response. | **PARTIAL** |

---

## Archived Sector Agents

| # | Agent | Key Critique | Objection Merit |
|---|-------|-------------|-----------------|
| 86 | `_archive/fire-services.agent.md` | **Significantly better than its replacements.** Contains comprehensive jurisdictional variation table, legislation references, FFDI, Total Fire Ban authority, AFAC mutual aid. This domain knowledge was NOT migrated to state-specific agents. | **YES — Strong** |
| 87 | `_archive/ambulance-paramedic.agent.md` | Multiple operational agents still reference this archived agent — broken references. | **YES — Strong** |
| 88 | `_archive/commonwealth-government.agent.md` | Replaced by specific agency agents (NEMA, ADF, etc.). Reasonable archival. | **N/A** |
| 89 | `_archive/meteorology-bom.agent.md` | Some agents still reference `meteorology-bom` in scope boundary text. Verify domain knowledge migration. | **YES** |
| 90 | `_archive/police.agent.md` | Jurisdiction comparison tables likely lost. Same pattern as fire-services. | **PARTIAL** |
| 91 | `_archive/ses.agent.md` | Jurisdiction comparison tables likely lost. | **PARTIAL** |

---

## Grand Summary & Meta-Assessment

### CRITICAL Issues (Must Fix)

| # | Finding | Affected Agents | Merit |
|---|---------|----------------|-------|
| 1 | **Constitution principle names are wrong** across multiple agents ("Deterministic Coordination", "Provenance & Transparency" instead of actual names). | logistics-officer, resilience-planner, planning-officer, + others | **Strong** |
| 2 | **Scope boundaries reference archived/non-existent agents** (`ambulance-paramedic`, `commonwealth-government`, `meteorology-bom`, `fire-services`, `police`). | logistics-officer, health, incident-commander, + many sector agents | **Strong** |
| 3 | **Agent count tripled (31 → 90+) without spec/registry update.** Validation rules designed for 31 agents haven't been updated. | All new agents | **Strong** |
| 4 | **Archived agents contained valuable domain knowledge (legislation tables, jurisdictional variations) that was not migrated** to replacement agents. | All state/territory sector agents | **Strong** |
| 5 | **`AuditEntry` entity is constitutionally mandated but missing from data model.** Referenced by observer-auditor and architecture. | observer-auditor + system-wide | **Strong** |

### HIGH Issues (Should Fix)

| # | Finding | Merit |
|---|---------|-------|
| 6 | State/territory agents are cookie-cutter templates with minimal differentiation — generic responsibilities, filler relationship descriptions ("Coordination within X arrangements"). | **Strong** |
| 7 | No automated validation script for agent catalogue despite 90+ agents. Manual validation is infeasible. | **Strong** |
| 8 | `copilot-instructions.md` has duplicated/conflicting entries and wrong project structure. | **Strong** |
| 9 | The Event Hubs/Service Bus decision has been deferred across 6 specs. | **Strong** |
| 10 | Missing data model entities for core operational concepts: StagingArea, FieldResource, SituationReport, IncidentActionPlan, MutualAidAgreement, EmergencyDeclaration, RiskRegister. | **Strong** |

### MEDIUM Issues (Consider Fixing)

| # | Finding | Merit |
|---|---------|-------|
| 11 | ACT is disproportionately represented (7 agents) vs VIC (5) despite being 1/15th the population. | **Partial** |
| 12 | WA is under-represented (3 agents, missing SES). | **Merit** |
| 13 | NEMA (apex coordination body) has the least useful agent content. | **Merit** |
| 14 | AFP appears in both ACT and Commonwealth sections — potential confusion. | **Merit** |
| 15 | Financial delegation/authority thresholds are referenced but unmodelled. | **Merit** |

### Objections Without Merit

| # | Finding | Why Not |
|---|---------|---------|
| 1 | "Ministerial briefing workflows should be in the system." | Out of scope — separate government systems handle this. |
| 2 | "Voice interfaces for field conditions." | Aspirational for a web-based MVP. |
| 3 | "LLM usage is too simple — needs agentic AI." | The spec deliberately chose deterministic orchestration with LLM augmentation. Simple is correct. |
| 4 | "Chaos testing should start now." | Premature — system isn't stable enough. FMEA yes, chaos testing no. |
| 5 | "Full DACC category documentation in ADF agent." | Defence domain knowledge, not this system's responsibility to replicate. |

### Overall Assessment

**The strongest overall finding:** The expansion from 14 to 60+ sector agents created breadth at the cost of depth. The archived generic agents with jurisdictional variation tables were more useful than 60 templated agents with generic descriptions. The recommended fix: either (a) restore the archived agents' domain knowledge into the state-specific agents, or (b) keep the generic agents as cross-sector references and use the state-specific agents only for handoff routing.
