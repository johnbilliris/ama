# Persona-Cluster Review of `001-arch-docs-refresh` Implementation

**Reviewed**: 2026-05-11 · **Branch**: `001-arch-docs-refresh` · **Scope**: cluster-level review per user's chosen Option 3 (one synthesis per persona family).

Each cluster review answers: *(1) does the delivered docs set address this cluster's primary architectural question?* *(2) are there material defects we should escalate as amendments?*

---

## 1. Operational cluster (10 AIIMS roles)

Personas: Incident Commander, Operations, Planning, Logistics, Public Information, Field Coordinator, Resilience Planner, Executive Leader, Observer/Auditor, Risk Manager.

**Coverage check**: OPS-01 (AIIMS system context), OPS-02 (escalation paths L1→L3), SEQ-01–06 (alert authoring, cross-agency recommendation, evacuation 5-stage, recovery transition, audit provenance, graceful degradation) all present. Index has dedicated Operational section.

**Findings**:
- ✅ Constitutional alignment — AIIMS roles, AWS, evacuation 5-stage, recovery transition, human-in-the-loop callouts all visible per FR-009/FR-013.
- ⚠️ **MERIT — Risk Manager perspective** has no dedicated hazard-classification or risk-register-flow diagram. The persona's primary deliverables (hazard taxonomy, risk register lifecycle, risk-informed decision support) are not visible from the index. Could be addressed by a small RISK-01 diagram or by adding an explicit "risk register" annotation to OPS-01.
- ⚠️ **MERIT — Resilience Planner** asked for a PPRR phase-overlay view (which agents activate in which phase). The analyzer flagged this in C1: PPRR coverage is implicit only. GOV-01 mentions WAF but not PPRR phasing.
- ⚪ Minor — SEQ-01 should explicitly tag the AWS three-tier label on the alert flow (analyzer C1).

## 2. Sector clusters (8 jurisdictions + Commonwealth + Cross-Sector — 58 personas)

**Coverage check**: SECTOR-01 (multi-jurisdiction tenancy), SECTOR-02 (CAP/EDXL/GeoJSON ingestion), SECTOR-03 (BoM/GA/NEMA integration map), SECTOR-04 (jurisdiction filter, spec-022).

**Findings**:
- ✅ All 8 jurisdictions + Commonwealth represented as tenant boundaries in SECTOR-01.
- ✅ Lead-agency designation, jurisdiction filter (spec-022), cross-state authority hand-off documented.
- ⚠️ **MERIT — Cross-Sector personas** (community-NGOs, health, transport, utility, volunteer) have no dedicated diagram showing their integration touch-points. They appear only as nodes in SECTOR-03. A SECTOR-05 ("Cross-sector touch-points and partner data exchange") would close this gap.
- ⚪ Minor — Commonwealth-only personas (ADF, NEMA, BoM, GA) appear in SECTOR-03 but their authority relationships are not modelled (e.g., NEMA NCM activation triggers).

## 3. Technical-Architecture cluster (Solution Arch, Azure Principal, API Architect, Principal Eng)

**Coverage check**: C4-L1, L2, four L3 component views (API/Web/Agents/Ingest), GOV-01 (WAF mapping), ADR navigation index present.

**Findings**:
- ✅ Full C4 L1–L3 coverage; L4 deferred per spec assumption.
- ✅ GOV-01 maps the 5 WAF pillars to platform components.
- ⚪ The C4-L3 component diagrams use generic placeholder boxes rather than real introspected components (DRAWIO-FALLBACK). The drawio source is editable and entity names are correct, but a future pass should expand each L3 to reflect the actual file/module structure.
- ⚪ ADR navigation index points at `docs/decisions/` — fine, but only spec-036's ADR set is populated there. Other specs lack ADRs (gap predates this feature).

## 4. Technical-Build cluster (Software Dev, Infra/DevOps, Data Eng, AI/ML, Docker)

**Coverage check**: DEPLOY-01 (CI/CD), DEPLOY-02 (rg-ama topology), DEPLOY-03 (Cosmos partitioning).

**Findings**:
- ✅ Azure resource topology covers ca-api/ca-agents/ca-ingest, cosmos-ama-zo6bb5, app-ama-zo6bb5, AI Search, Service Bus, Event Hubs, Application Insights, Key Vault.
- ⚠️ **MERIT — AI/ML Engineer** asked for an "agent runtime + LLM client + model gateway" view. This is not present as a standalone diagram; partial coverage in SEC-01 (model gateway) and C4-L3-Agents (agent runtime) but no integrated view. Recommend adding BUILD-01.
- ⚠️ **MERIT — Docker/Container Engineer** asked for a container image layering view. Not present (was not in the SC-007 inventory). Could be a deferral entry in known-gaps rather than a new diagram.
- ⚪ Bicep dependency graph is correctly tracked under BICEP-DEP-01 known-gap.

## 5. Technical-Quality cluster (QA-Test, Accessibility, Chaos, SRE, Compliance, Security)

**Coverage check**: SEC-01 (AU residency + Foundry carve-out), SEC-02 (RBAC), SEC-03 (trust boundary), SEC-04 (SLI/SLO), SEQ-05 (audit provenance), `accessibility/wcag-coverage.md` (text page).

**Findings**:
- ✅ AU residency + Foundry carve-out label is verbatim per FR-016. Compliance reviewers can use SEC-01 as the single-page proof per SC-003.
- ✅ Audit-trail provenance flow with human-gate (SEQ-05) covers FR-020.
- ⚠️ **MERIT — QA/Test Engineer** asked for a test-pyramid view (contract/integration/simulation/e2e). Not present and not in SC-007 — this is a real gap.
- ⚠️ **MERIT — Chaos Engineer** asked for a chaos-experiment blast-radius diagram. Not present and not in SC-007.
- ⚪ Accessibility view is text-only by design (not in the diagram count); WCAG-AUDIT-FULL captured as a known-gap.

## 6. Technical-Experience cluster (UX Designer, Product Owner/BA)

**Coverage check**: WCAG coverage page, spec-035 middleware narrative, capacity model, README index.

**Findings**:
- ⚠️ **MERIT — UX Designer** asked for user-journey diagrams for high-pressure ops dashboards. Not present.
- ⚠️ **MERIT — Product Owner/BA** asked for a success-criteria → architecture component traceability matrix. Not present.
- These two omissions match the analyzer's note that the Experience cluster was scoped narrowly to accessibility.

---

## Cross-cutting findings

- 🔴 **DRAWIO-FALLBACK applies to all 26 diagrams** because the Draw.io MCP server is not configured in `.mcp.json` (only Playwright is). The `.drawio` files are real, editable mxfile XML with correctly named entities; the PNGs are functional auto-renders. To replace placeholders, install the Draw.io MCP server (or open each `.drawio` in app.diagrams.net and re-export). Tracked via 26 known-gap entries — auditable but the user's original request was to use the MCP skill, so this is a real deviation.
- 🟢 CI gates (`docs-arch` job) are wired and locally green for: markdownlint, PNG↔drawio pairing, hash manifest verify, spec cross-ref check, known-gaps validation.
- 🟢 No runtime application code modified. Deployment is a no-op (T073).

---

## Amendments with merit (proposed Step 2–7 amendment cycle)

Six new diagrams + matched pages would close the merit-bearing gaps:

| ID | Diagram | Cluster | Spec FR mapping |
|----|---------|---------|-----------------|
| RISK-01 | Hazard taxonomy + risk-register lifecycle | Operational (Risk Manager) | FR-013 extension |
| OPS-03 | PPRR phase-overlay (which agents activate when) | Operational (Resilience Planner) | new FR (constitutional §PPRR) |
| SECTOR-05 | Cross-sector touch-points & partner data exchange | Sector (Cross-Sector) | FR-015 extension |
| BUILD-01 | Agent runtime + LLM client + model gateway integrated view | Technical-Build (AI/ML) | FR-014 extension |
| QUAL-01 | Test pyramid (contract / integration / simulation / e2e) | Technical-Quality (QA) | new FR |
| EXP-01 | High-pressure ops dashboard user-journey | Technical-Experience (UX) | new FR |

Plus one deferred-only entry: container image layering view (Docker engineer) → known-gaps `LAYER-MIG-01`.

---

## Recommendation

**Proceed with one amendment cycle** (Steps 2–7 abbreviated): add the 6 diagrams above, re-run docs-arch lint, then close. The DRAWIO-FALLBACK situation cannot be resolved without installing the MCP server; the editable `.drawio` sources mitigate the issue and are tracked under known-gaps for future replacement.

Step 9 (azd up) remains a no-op for this feature regardless.
