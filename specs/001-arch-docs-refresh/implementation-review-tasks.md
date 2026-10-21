# Static Implementation Audit: Architecture Documentation Refresh

## Scope and Verdict

- Review date: **2026-09-11**.
- Reviewed source revision: **5b44c249f00e0e4a13ea2579c8c33d06e2471d7a**; the checkout's HEAD matched it. Scoped working-tree comparisons showed no modifications to the reviewed feature artifacts or cited controlling entry points before this report was written.
- Feature: [spec.md](spec.md#L1), including all clarification sessions and Amendment 1; [tasks.md](tasks.md#L1), including T074 through T086. **86 original task IDs are assessed individually; all originally carry `[X]`.**
- Requirement denominator: **34 identified requirements/outcomes: FR-001 through FR-026 and SC-001 through SC-008**. The specification declares no numbered NFRs. Unnumbered constraints are assessed separately, without inventing original NFR IDs.
- Scenario denominator: **27 numbered acceptance scenarios**, plus all **7 independent tests** and **5 stated edge cases**.
- Authority: [Review Contract](../001-spec-implementation-audit/README.md#L9), [review instructions](../../.github/instructions/code-review.instructions.md#L1), [commenting guidance](../../.github/instructions/code-commenting.instructions.md#L1), and [constitution](../../.specify/memory/constitution.md#L1).
- Additional complete inputs: [plan.md](plan.md#L1), [research.md](research.md#L1), [data-model.md](data-model.md#L1), [quickstart.md](quickstart.md#L1), [manifest contract](contracts/diagram-manifest-format.md#L1), [gap schema](contracts/known-gaps-schema.md#L1), [lint contract](contracts/lint-scripts.md#L1), [requirements checklist](checklists/requirements.md#L1), [architecture checklist](checklists/architecture-review.md#L1), and the feature's pre-existing [persona review](review/persona-review.md#L1). No concurrent review findings from other folders were read.

**Verdict: substantial authored documentation exists, but acceptance is not established.** Several pages describe a materially different security, ingestion, storage, or deployment design from the reachable source. Mechanical checks can accept incomplete evidence. All remediation below is future work, not authorization to change the product during this audit.

This audit created only this report. It did not run application tests, builds, documentation lint scripts, CI jobs, deployments, cloud queries, diagram exports, or remediation. It did not delegate, create branches, stage files, or commit. Source/test assertions, XML graphs, existing PNGs, configuration, and local filesystem relationships were inspected read-only. Runtime success, cloud state, effective environment protection, timed usability, and human sign-off remain **UNVERIFIED** unless supported by trustworthy checked-in evidence; the local completion narrative is not such evidence.

### Evidence Conventions

Paths below are relative to this report. Text evidence uses 1-based `#L` links; compact, single-line Draw.io files necessarily use `#L1`. PNGs are linked without fictitious line numbers. Proposed paths are explicitly marked **proposed** and are not existing evidence. `IMPLEMENTED` describes a supported task-local artifact or static behavior, not an executed test, actual deployment, or approved release. Shared requirements can still require follow-up for an otherwise authored page.

Statuses follow the contract: `IMPLEMENTED`, `PARTIAL`, `MISSING`, `CONFLICT`, `UNVERIFIED`, and `SUPERSEDED`. A documented deferral is not silently converted to implementation. Priority P1 means an acceptance blocker with safety, security, correctness, or audit-reliability impact; P2 means an important completeness or maintainability gap.

## Static Observations

1. All **32 named diagram basenames** have both source and PNG artifacts. The directory currently contains **34 Draw.io files, 34 PNGs, and 34 manifest entries**, because two adoption-roadmap pairs were added. These additions are not a missing-diagram defect and must not be deleted to recover the historical count.
2. Every current manifest digest matches its current source bytes when its repository-root-relative path is resolved from the repository root. This is **not** proof of valid XML, faithful PNG export, or export-time provenance. The invalid recovery XML also has a matching digest.
3. All **40 architecture Markdown pages** were read; all 32 named PNGs were visually inspected and their source graphs examined. A read-only inline-link inventory examined **202 local link occurrences**, found **one nonexistent target**, and found every architecture page reachable from the index within two Markdown navigation hops. This inspection did not execute lychee or validate external URLs or every Markdown fragment.
4. The nonexistent target is the [known-gaps quickstart link](../../docs/architecture/known-gaps.md#L4): its three parent traversals resolve outside the repository. The intended [quickstart.md](quickstart.md#L1) exists in this feature folder.
5. No Azure stencil references were found in the named diagram sources examined. Named sources identify themselves as fallback artifacts, including [container.drawio](../../docs/architecture/c4/container.drawio#L1) and [azure-resource-topology.drawio](../../docs/architecture/deployment/azure-resource-topology.drawio#L1). A scoped source/style search did not find a renamed Azure-stencil implementation of these views.
6. None of the **34 PNGs records a `pHYs` density chunk**. An image decoder reports its default 96 DPI; that is not evidence that an author chose 96 DPI. The requested 150-DPI export is **UNVERIFIED**. Transparent backgrounds are directly observable on several original exports, including [system.png](../../docs/architecture/c4/system.png) and [alert-approval-publication.png](../../docs/architecture/sequence/alert-approval-publication.png), contrary to their task instructions.
7. A scoped Python-source search across the workspace found the two architecture linter definitions but **no tests referencing either linter, the diagram manifest, or the docs-arch job**. Relevant existing adjacent tests are assessed below; they must not be represented as architecture acceptance tests.
8. Renames were accounted for: planned `audit-trail-provenance`, `rbac-role-permission-matrix`, `hazard-risk-register`, and `agent-llm-gateway` are implemented under `audit-provenance`, `rbac-matrix`, `risk-register-lifecycle`, and `agent-runtime-llm-gateway`. The ADR index is at [adr/README.md](../../docs/architecture/adr/README.md#L1), not the plan's alternate governance subpath. None is classified missing merely because its historical filename changed.

## Prioritized Findings

| ID | Priority | Finding and Existing Evidence | Impact |
| --- | --- | --- | --- |
| AUD-001 | P1 | The approval-only publication claim is contradicted by the mounted [alert route](../../apps/api/app/api/routes/alerts.py#L37), [publication service](../../apps/api/app/services/public_alert_service.py#L48), and the audit diagram's [approve-or-reject edge into actuation](../../docs/architecture/sequence/audit-provenance.drawio#L16). | A reader can mistake a visual human gate for enforced approval and rejection handling. This is also a shared-code risk; actual external delivery is not established. |
| AUD-002 | P1 | Tenancy/partition diagrams claim jurisdiction tenants using `/tenant_id`, while [signals IaC](../../infra/main.bicep#L609), [repository filtering](../../apps/api/app/repositories/signal_repository.py#L51), and [tenant resolution](../../apps/api/app/middleware/tenant_middleware.py#L47) implement different concepts. | Misstates isolation, document routing, and agency authority to auditors and developers. |
| AUD-003 | P1 | BUILD-01 says every prompt is redacted, but [gateway execution](../../apps/agents/common/model_gateway.py#L179) bypasses AU regions and the [actual client](../../apps/agents/common/foundry_chat_client.py#L362) has further bypass paths. | Overstates the data-minimisation guarantee, including cases not covered by the diagram. |
| AUD-004 | P1 | The RBAC diagram gives IC admin privileges and omits Operations audit access, unlike the [role registry](../../apps/api/app/auth/rbac_registry.py#L19) and [enforcement middleware](../../apps/api/app/middleware/rbac_check.py#L95). | Incorrect permissions may be used as an access-control specification or approval basis. |
| AUD-005 | P1 | The [trust diagram](../../docs/architecture/security/trust-boundary.drawio#L52) labels browser-to-API as Managed Identity and invents a uniform authenticated ingestion gateway path. | Trust-boundary and credential guidance does not follow the actual browser, API, or polling implementations. |
| AUD-006 | P1 | [Integration-point-map](../../docs/architecture/data/integration-point-map.drawio#L1) names noncanonical consuming agents; [worker wiring](../../apps/ingestion/worker.py#L208) does not inject the persistence dependency required by [pipeline processing](../../apps/api/app/services/ingestion/pipeline_base.py#L266). | Broker-to-Cosmos-to-agent delivery is presented as implemented without a controlling end-to-end path. |
| AUD-007 | P1 | [C4 container source](../../docs/architecture/c4/container.drawio#L1) omits App Insights and names no five individual agents; L3 API/Web/Ingest views cannot trace the required cross-container round trip. [main.py](../../apps/api/app/main.py#L46) also contradicts the middleware ordering narrative. | New joiners cannot reliably determine what runs where or which code handles a request. |
| AUD-008 | P1 | [Recovery source](../../docs/architecture/sequence/recovery-transition.drawio#L16) is invalid XML; [its PNG](../../docs/architecture/sequence/recovery-transition.png) omits the roles and edges present in the text. Multiple other exports obscure labels; the test pyramid renders without pyramid geometry. | Editable-source and one-page comprehension obligations are not met, despite valid source hashes. |
| AUD-010 | P1 | The [hash step](../../.github/workflows/ci.yml#L515) checks only listed entries; it enforces neither complete manifest membership nor the named inventory. The [manifest](../../docs/architecture/.diagram-hashes#L1) also differs from the contributor contract's path/sort conventions. | An omitted source, omitted named pair, or independently stale PNG can escape the advertised integrity gate. |
| AUD-011 | P1 | [Link-check configuration](../../.github/workflows/ci.yml#L478) restricts target URLs with `--include 'docs/architecture'`, while a [broken spec link](../../docs/architecture/known-gaps.md#L4) already exists. | A green job need not mean all internal links from architecture pages resolve. |
| AUD-012 | P1 | [Citation collection](../../tools/lint/check_spec_cross_refs.py#L61) counts comments, examples, and the gap registry; the [index manifest](../../docs/architecture/README.md#L84) supplies blanket tokens unrelated to substantive coverage. | False-positive coverage masks missing or misattributed architecture explanations. |
| AUD-014 | P1 | [Evacuation prose](../../docs/architecture/sequence/evacuation-five-stage.md#L27) replaces Decision/Withdrawal with different stages; [the domain transition model](../../packages/domain/src/domain/models/evacuation_stage.py#L27) and constitution disagree. Recovery overlap is also absent. | Life-safety orientation teaches a different lifecycle from the implemented and constitutional one. |
| AUD-015 | P1 | [Deployment stages](../../docs/architecture/deployment/cicd-pipeline.md#L21) and static `rg-ama` topology disagree with the current [branch-driven CD workflow](../../.github/workflows/cd.yml#L19) and [service hosting declarations](../../azure.yaml#L28). | Operators may assume nonexistent what-if/promotion gates or target the wrong resource group. |
| AUD-009 | P2 | Azure services are generic boxes, including the task's mandatory-stencil [resource topology](../../docs/architecture/deployment/azure-resource-topology.drawio#L7). | FR-008 is not delivered; documented fallback did not waive stencil requirements. |
| AUD-013 | P2 | [Known gaps](../../docs/architecture/known-gaps.md#L10) use issue-creation forms and nonexistent task fragments, omit fallback records, and retain batched citation gaps. [Validation](../../tools/lint/check_known_gaps.py#L40) checks little beyond raw emptiness/TBD. | Deferred work is not reliably actionable, and malformed/empty registries can be accepted. |
| AUD-016 | P2 | [SEC-04](../../docs/architecture/security/sli-slo-model.md#L24) omits four catalogue objectives and changes burn thresholds from [the SLO catalogue](../../docs/observability/slo.md#L119); capacity numbers are labelled production baseline without measurement evidence. | SREs receive conflicting alerting and capacity guidance. |
| AUD-017 | P2 | Most page citations are unlinked tokens, C4 pages contain [feature-local MD041 suppression](../../docs/architecture/c4/system.md#L19), and text-only/legacy policies conflict with universal page/Draw.io requirements. | The documented authoring contract is internally inconsistent and not uniformly met. |
| AUD-018 | P2 | [PPRR source](../../docs/architecture/operational/pprr-phase-overlay.drawio#L8) contains agent bars but no AIIMS-role labels and no labelled overlap regions. | FR-024's agent-and-role phase mapping is incomplete on the diagram itself. |
| AUD-019 | P2 | [Cross-sector source](../../docs/architecture/data/cross-sector-touchpoints.drawio#L1) labels protocols but omits fire/SES boundaries and per-crossing lead-agency rules. | The amendment's operational hand-off question is not answered by the diagram. |
| AUD-020 | P2 | [Test-pyramid source](../../docs/architecture/quality/test-pyramid.drawio#L12) uses an unrelated shape, reports ungrounded test counts, and omits pytest backend E2E/simulation tooling. | QA readers cannot use the picture or numbers as an accurate taxonomy. |
| AUD-021 | P2 | [Journey page](../../docs/architecture/accessibility/ops-dashboard-user-journey.md#L23) omits publication confirmation/audit receipt and claims `aria-pressed` absent from the [approval control](../../apps/web/src/app/workspaces/%5BpersonaId%5D/_panels/ic-approval-card.tsx#L149). [WCAG coverage](../../docs/architecture/accessibility/wcag-coverage.md#L18) asserts universal verification without evidence. | Experience traceability and accessibility assurance are overstated. |
| AUD-022 | P2 | All original tasks are checked, but the [architecture checklist](checklists/architecture-review.md#L13) is entirely open and [persona-review success claims](review/persona-review.md#L76) lack reproducible run/sign-off records. | Completion, human acceptance, and historical command success cannot be attested. |

## Detailed Remediation Tasks

### Checkbox Semantics After the 2026-09-15 Pass

A top-level AUD checkbox is marked `[x]` **only** when every automatable implementation and test criterion in its own *Objective acceptance* paragraph is now satisfied and was verified by an executed command in this
environment. A checkbox stays `[ ]` when any remaining criterion depends on one of the following, none of which this pass could produce:

1. **A PNG export.** The draw.io desktop CLI is not installed, so `.github/skills/drawio-mcp-diagramming/scripts/render_drawio.py` fails with `Error: 'drawio' not found on PATH`. Every diagram whose acceptance
   depends on a faithful, legible, 150-DPI, white-background render therefore stays open, even where the **source** is now fully correct. Those items are recorded as `SOURCE-COMPLETE` in the 2026-09-15 status table
   above; the checked-in PNGs were deliberately left untouched rather than faked.
2. **Human or external evidence.** Qualified architect, AIIMS, SRE, auditor or accessibility sign-off; topic-correctness review of citations; GitHub Environment protection settings; CI run URLs; Azure inventory.
3. **Test execution that this environment cannot perform.** `pytest` and `pydantic` are both absent (`ModuleNotFoundError`), so route-level, gateway, ingestion and domain suites could not be run. The validator tests
   in `tests/contract/test_architecture_docs.py` were instead exercised directly against temporary directories and all 46 passed.

Therefore an unchecked box in this pass does **not** mean "no work was done" — consult the 2026-09-15 status table for the exact source-level state of each finding. Conversely, no diagram that was left unchanged has
been described as remediated.

The following tasks are all **unchecked**. They are instructions for later authorized developers and testers. For shared-code findings, the documentation owner must distinguish verified behavior from intended controls and coordinate any product fix with its owning feature; this audit does not silently expand a documentation feature into security or runtime remediation.

### 2026-09-14 Remediation Status Update (Implementation Pass)

| AUD ID | Status | Evidence Summary |
| --- | --- | --- |
| AUD-001 | PARTIAL | Product fix implemented: publication now requires `approved` status + recorded approved decision + authenticated actor claim. Focused pytest execution is blocked in this environment (dependency bootstrap/TLS failure). |
| AUD-002 | PARTIAL | Tenant/partition narratives were updated to hierarchical partition semantics (`scope/jurisdictionId/dataSourceId`) and scope-vs-jurisdiction separation; diagram-source parity and broader page sweep remain open. |
| AUD-003 | PARTIAL | Product fix implemented: model-gateway path now fails closed outside explicit AU bypass and inspects supported text-bearing message content comprehensively. Full test execution blocked by environment. |
| AUD-004 | PARTIAL | Product fix implemented: alert routes are now under RBAC protected prefixes and role allowlists. Full route-matrix verification remains pending test execution. |
| AUD-005 | PARTIAL | Trust-boundary prose corrected to protocol-specific ingestion auth assumptions; diagram-level and full source parity review remains open. |
| AUD-006 | PARTIAL | Product fix implemented: ingestion worker now injects and uses `SignalRepository`; repository persistence now writes partition metadata (`scope/jurisdictionId/dataSourceId`). Full end-to-end ingestion tests blocked by environment. |
| AUD-007 | PARTIAL | C4 system/container narratives were corrected for conditional carve-out behavior and scope/jurisdiction boundaries, and markdownlint suppression was removed; diagram-source parity and full middleware-order reconciliation remain open. |
| AUD-008 | PARTIAL | `recovery-transition.drawio` XML validity repaired and parse-validated; PNG fidelity/export provenance remains open (no fabricated export performed). |
| AUD-009 | OPEN | Azure stencil replacement across diagrams not completed in this pass. |
| AUD-010 | PARTIAL | CI hash-manifest step hardened for completeness/duplication checks; full docs-arch execution and PNG provenance enforcement remain open. |
| AUD-011 | PARTIAL | Broken known-gaps quickstart link fixed and CI link-check scope corrected (removed restrictive include, enabled fragments/offline). Full CI run remains pending. |
| AUD-012 | PARTIAL | Spec cross-ref checker hardened (missing roots, code/comment noise removal, bounded inventory, explicit deferral support via known gaps). Full substantive citation migration remains open. |
| AUD-013 | PARTIAL | Known-gaps checker hardened (table shape/date/status/placeholder validation); known-gaps registry updated with actionable refs and explicit per-spec deferrals. |
| AUD-014 | PARTIAL | Evacuation and recovery pages now use canonical lifecycle wording and explicit response/recovery overlap semantics; diagram-level role/edge fidelity remains open. |
| AUD-015 | PARTIAL | Deployment pages now distinguish historical versus branch-environment naming and branch-driven CD behavior; external environment-protection/approval evidence remains open. |
| AUD-016 | PARTIAL | SEC-04 page now maps SLO-1 through SLO-10 with explicit evidence-status labeling guidance; alert-policy/code-level parity validation remains open. |
| AUD-017 | PARTIAL | C4 page-level markdownlint suppressions were removed and lint now passes across architecture docs; remaining authoring-contract conflicts (legacy/text-only exceptions) remain open. |
| AUD-018 | PARTIAL | OPS-03 page now documents expected phase-overlap semantics and role-label synchronization requirements; drawio source still needs explicit overlap/role labels per finding. |
| AUD-019 | PARTIAL | SECTOR-05 page now contains per-sector-pair lead-agency rules and spec alignment markers; drawio-source authority-boundary rendering remains open. |
| AUD-020 | PARTIAL | QUAL-01 page now carries repository-grounded tier inventory and tooling notes, including backend E2E and simulation distinctions; diagram geometry and visual fidelity remain open. |
| AUD-021 | PARTIAL | EXP-01 and WCAG pages now include publication-confirmation/audit-receipt steps and explicit UNVERIFIED evidence qualifiers; component-level accessibility verification receipts remain open. |
| AUD-022 | PARTIAL | This pass adds command-grounded evidence tracking and status deltas, but external/human/CI/deployment proofs remain open by design. |

### 2026-09-15 Remediation Status Update (Diagram-Source and Validator Closure Pass)

Scope of this pass: diagram **sources**, validator hardening, and direct fixture/mutation tests. PNG exports were **not** produced — the draw.io desktop CLI is absent from this environment, so the checked-in renderer
(`.github/skills/drawio-mcp-diagramming/scripts/render_drawio.py`) exits 1 with `Error: 'drawio' not found on PATH`. Existing PNGs were preserved untouched; every changed source now declares
`agent="remediation-source-updated; export=pending-drawio"`, and `docs/architecture/.diagram-hashes` was regenerated from the new source bytes.

Status vocabulary for this table: **SOURCE-COMPLETE** means every automatable source-level criterion is satisfied and verified by token/style assertions, but the rendered-artefact criterion (faithful PNG, legibility,
150 DPI, white background, human visual review) cannot be met until an export tool is available. **CLOSED** means every automatable implementation and test criterion is met.

| AUD ID | Status | Evidence Summary (2026-09-15) |
| --- | --- | --- |
| AUD-001 | SOURCE-COMPLETE | `sequence/audit-provenance.drawio` now routes APPROVED-only to the actuation orchestrator and adds a REJECTED terminal node with its own audit and evidence edges plus an explicit "no execution arrow" label. Channel envelopes are labelled INTENDED with external delivery UNVERIFIED. Route-level test execution is still blocked (no `pytest`, no `pydantic`). |
| AUD-002 | SOURCE-COMPLETE | `data/multi-jurisdiction-tenancy.drawio` rewritten to the exact hierarchical keys `/scope`, `/jurisdictionId`, `/dataSourceId` with three separately labelled concepts (SCOPE / JURISDICTION / AUTHORITY). `deployment/cosmos-partitioning.drawio` corrected the same way. `grep` proves **zero** `/tenant_id` occurrences across all 34 architecture diagram sources. |
| AUD-003 | SOURCE-COMPLETE | `c4/agent-runtime-llm-gateway.drawio` now labels the Foundry endpoint as AU-deployments-only against `foundry-carveout.yaml` and adds the deployment registry and workload-identity nodes. Client bypass behaviour remains a prose-level statement; no test execution possible. |
| AUD-004 | CLOSED (source) / OPEN (render) | `security/rbac-matrix.drawio` regenerated directly from `APP_ROLES`: all 11 roles present, each row carries its AIIMS-function scope, its exact route-family allowlist, and a separate INTENDED-ONLY column. `system-administrator` is visually separated from incident command, and enforcement conditions / protected prefixes / alias normalisation are stated. 15/15 token assertions pass. |
| AUD-005 | SOURCE-COMPLETE | `security/trust-boundary.drawio` now shows browser Entra ID/OAuth 2.0 sign-in (explicitly "NOT managed identity"), BoM anonymous FTP versus partner OAuth 2.0/API key as separate edges, the real five-stage middleware chain, workload managed identity, and the five canonical consuming agents. |
| AUD-006 | SOURCE-COMPLETE | `c4/component-ingest.drawio` regenerated with an explicit SUCCESS persistence path (pipeline → SignalRepository → Cosmos signals → canonical consumers) alongside the dead-letter FAILURE path, plus a note that persistence is conditional on repository injection. `data/ingestion-data-flow.drawio` now names the canonical five consumers. |
| AUD-007 | SOURCE-COMPLETE | `c4/container.drawio` adds Application Insights with telemetry edges from API/agents/ingest, names all five canonical agents individually, adds the API↔agents and API→web return edges, and carries an explicit L3 round-trip/navigation note. `c4/component-api.drawio`, `component-web.drawio` and `component-ingest.drawio` regenerated; `spec-035-middleware-and-offline.md` mermaid and rationale table corrected to the actual registration-reversed order with a retained historical note. |
| AUD-008 | OPEN (render) | All 34 sources parse as XML. `recovery-transition.drawio` remains valid and now carries overlap, managed handover, four recovery environments and six national principles. PNG fidelity, 150 DPI, white background and human visual review are **not** addressable here: no export tool. Gap `DRAWIO-EXPORT-01` records this. |
| AUD-009 | SOURCE-COMPLETE | Confirmed offline Azure2 image styles added to all ten named Azure-bearing sources (55 references in those files; 64 across 13 files). All 20 distinct icon paths were verified against `.github/skills/drawio-mcp-diagramming/references/azure2-complete-catalog.txt` — 0 unconfirmed. Visible labels retained via `verticalLabelPosition=bottom`. Icon rendering itself is unverified (gap `AZURE2-ICON-RENDER`). |
| AUD-010 | PARTIAL | `tools/lint/check_diagram_manifest.py` enforces bijection, uniqueness, sort order, digest validity, XML validity, provenance attributes, both pairing directions and the named inventory. 13 new direct fixture/mutation tests exercise every named negative case and the complete-inventory positive case; all pass. Manifest regenerated (34 entries) and validated. **Remaining**: PNG-to-source export provenance is still not bound, so a source+digest update without a re-export still passes. |
| AUD-011 | PARTIAL | No further change in this pass; the broken quickstart link and CI include-scope fix from the previous pass stand. Demonstrating that a missing spec/ADR target fails the gate still requires a lychee run that is not available here. |
| AUD-012 | PARTIAL | `check_spec_cross_refs.py --root .` passes (36 specs cited). 11 new direct fixture tests cover missing specs root, missing architecture root, code-fence examples, gap-registry-only mentions, generic `Resolved` exclusions, valid archive/superseded exclusions, unresolvable exclusion references, untracked 038–040, absent 002, duplicate 036 prefixes and blanket comment tokens. **Remaining**: topic-correctness of each citation is a human review, and 23 `SPEC-*` deferral rows remain open. |
| AUD-013 | CLOSED | `check_known_gaps.py --root .` passes over the real registry (25 rows). An explicit no-gap marker state is now accepted while arbitrary empty files are still rejected. 15 new direct fixture tests cover missing file, empty file, missing header, truncated row, empty ref, plain/backticked/bold `TBD` plus `todo`/`n/a`/`pending`, issue-creation URLs, unresolvable refs, bad dates, bad statuses, duplicate IDs, lowercase IDs, CRLF, inline-code refs, multi-table validation and resolved-row traceability. Fallback and export-pending outcomes are recorded as `DRAWIO-EXPORT-01`, `DRAWIO-FALLBACK-01`, `AZURE2-ICON-RENDER`; no batched `SPEC-RANGE-*` row remains. |
| AUD-014 | SOURCE-COMPLETE | `sequence/evacuation-five-stage.drawio` regenerated with the exact canonical stages Decision, Warning, Withdrawal, Shelter, Return; Preparation is drawn as a labelled PRECONDITION outside the lifecycle; warning-publication and movement authorisation are separate human gates; shelter-in-place and re-entry-to-Decision alternatives are present. `sequence/recovery-transition.drawio` adds the overlap window, managed handover, four environments and six national principles and remains valid XML. |
| AUD-015 | SOURCE-COMPLETE | `deployment/cicd-pipeline.drawio` rewritten to the branch-driven `workflow_run` model with `rg-drh-dev`/`rg-drh-staging`/`rg-drh-production`, explicit "no PR deploy path", no what-if/promotion chain, and manual approval labelled UNVERIFIED. `deployment/azure-resource-topology.drawio` now shows `rg-drh-<env>` with `rg-ama` marked historical, web on App Service and the other three services on Container Apps — matching the already-corrected prose. |
| AUD-016 | SOURCE-COMPLETE | `security/sli-slo-model.drawio` regenerated to carry SLO-1 through SLO-10 with each objective, SLI name, error budget and paging rule taken verbatim from `docs/observability/slo.md`, plus the authoritative fast-burn (1 h / 5 m / >14.4) and slow-burn (6 h / 30 m / >6) policy and an explicit statement that zero-budget objectives are not burn-governed. Alert-configuration parity remains UNVERIFIED on the page. |
| AUD-017 | PARTIAL | markdownlint passes across all 40 architecture pages with **zero** `markdownlint-disable`/`markdownlint-capture` directives anywhere under `docs/architecture/`. Remaining authoring-contract conflicts (text-only/legacy exceptions, SC-007 four-level versus optional L4) are specification conflicts requiring an owner decision. |
| AUD-018 | SOURCE-COMPLETE | `operational/pprr-phase-overlay.drawio` now carries per-phase AIIMS role labels, per-phase key events, two labelled OVERLAP regions, a labelled RECURRENCE loop from Recovery back to Prevention, and all five canonical agent bars. |
| AUD-019 | SOURCE-COMPLETE | `data/cross-sector-touchpoints.drawio` adds a Fire sector node (NSW RFS, FRNSW, VIC CFA/FRV, QFD, CFS, DFES, TFS, ACT RFS, NTFRS) and a Flood/Storm SES sector node, hazard-dependent lead-agency edge labels, a mutual-aid bidirectional edge, an explicit AUTHORITY BOUNDARY rule, and bidirectional arrows on the crossings that are genuinely two-way. |
| AUD-020 | SOURCE-COMPLETE | `quality/test-pyramid.drawio` rebuilt with real `shape=trapezoid` geometry stacked so each tier's top width equals the next tier's bottom width, Unit as the visibly widest 800 px base. Counts are dated 2026-09-15 test-file counts measured from the working tree: Unit 173, Contract 158, Integration 137, Simulation 25, E2E 15 (5 pytest + 10 Playwright specs), plus devops 10 and security 1 called out as adjacent suites. Complete tooling inventory (pytest, Playwright incl. axe/web-coverage, Vitest, simulation replay harness) is stated. |
| AUD-021 | SOURCE-COMPLETE | `accessibility/ops-dashboard-user-journey.drawio` adds steps 6 Publication Confirmation and 7 Audit Receipt, a PERCEPTION/COMPREHENSION/ACTION tag per step, a component-and-endpoint mapping row per step (including `ic-approval-card.tsx` exposing `aria-pressed`), a nine-criterion SC coverage list, and an explicit UNVERIFIED conformance qualifier. |
| AUD-022 | PARTIAL | This pass adds executed-command evidence for XML parsing, three linters, markdownlint, 46 direct validator tests, and token/style assertions. CI run URLs, human architecture/auditor/accessibility sign-off, deployment evidence and PNG exports remain open by design. |

For automated document regression coverage, reuse the repository's pytest conventions and **proposed** `tests/contract/test_architecture_docs.py` for shared document/fixture helpers, rather than creating a separate test file for every finding. Content correctness still requires a qualified human reviewer; XML token checks alone are not sufficient. Commands below were **not executed**. Run them only after the named prerequisites and future changes exist.

### AUD-001: Separate Required Human Approval from Proven Enforcement

- [ ] AUD-001 Correct approval, rejection, actuation, and audit guarantees in the affected views and track the reachable publication enforcement discrepancy.

**Affected:** FR-009, FR-010(a/b/e), FR-020; SC-006; US1.3, US2.1, US5.2; T011, T012, T016, T017, T048, T054, T079, T085, and cross-container actuation views.

**Expected versus observed:** [SEQ-01 prose](../../docs/architecture/sequence/alert-approval-publication.md#L17) says publication can only follow explicit approval. [Router registration](../../apps/api/app/api/router.py#L61) mounts the publish route, which passes a body-supplied persona ID to [PublicAlertService.publish](../../apps/api/app/services/public_alert_service.py#L66). `_validate_publishable` permits `pending_approval`; the method changes state without consulting a recorded approval. The production [RBAC prefix list](../../apps/api/app/middleware/rbac_check.py#L32) is not a global permission matrix for these routes. [Audit graph edge 11](../../docs/architecture/sequence/audit-provenance.drawio#L16) sends both approval and rejection to the actuation orchestrator. Conversely, channel adapters in [the service](../../apps/api/app/services/public_alert_service.py#L29) return dictionaries; this audit does not establish real SMS/email dispatch or exploitation.

**Developer instructions:** Own the sequence pages/sources and BUILD/experience callouts. Show proposal, authenticated decision, approved-only actuation, rejection termination, and both decision/outcome audit paths distinctly. Name which mounted path implements each state. Mark the public-alert approval check as an unresolved owning-service discrepancy until its separately authorized fix exists; do not imply the standalone approval helper is called by publication. Distinguish in-process channel envelopes from external delivery acknowledgements.

**Tester instructions:** Trace the mounted route, not only the workflow helper. Use synthetic draft/approved/rejected alerts and a recording channel adapter; test future source changes separately from document review.

**Positive tests:** An approved proposal reaches actuation and a correlated result record; diagram and endpoint names agree. **Negative tests:** Pending/rejected proposals and a spoofed body persona do not count as proof of approval; rejection must not have an execution arrow. **Edge-case tests:** Duplicate decisions, approved-with-edits payloads, offline decisions, and acknowledgement failure must be distinguished from successful external delivery.

**Existing test locations:** [State-machine tests](../../tests/integration/test_approval_workflow_state_machine.py#L26) check terminal transitions but not the publish route. [Human-approval tests](../../tests/integration/test_human_approval_preserved.py#L71) manually add approval dictionaries; they do not prove gate enforcement. These are extension/reference locations, not passing evidence.

**Future commands/prerequisites:** In an authorized isolated Python test environment with API/agents installed, run `python -m pytest tests/integration/test_approval_workflow_state_machine.py tests/integration/test_human_approval_preserved.py -q`; add route-level cases under the existing integration suite and run their selected file. Require a human review of the re-exported actuation diagrams.

**Objective acceptance:** Every depicted real-world actuation has a visible approved-only path and a non-actuating rejection path; no page claims an enforced approval or delivered notification without a reachable implementation and assertion/evidence reference. The shared discrepancy is either fixed and independently verified or explicitly retained as an open blocker.

### AUD-002: Document the Real Tenant and Partition Boundaries

- [ ] AUD-002 Reconcile SECTOR-01, SECTOR-04, DEPLOY-03, and legacy partition narratives with actual tenant scope, jurisdiction filtering, and agency routing.

**Affected:** FR-004, FR-015; US3.1/4, US6.3; T021, T024, T025, T028, T057, T060, T068.

**Expected versus observed:** [SECTOR-01](../../docs/architecture/data/multi-jurisdiction-tenancy.md#L16) treats each jurisdiction as a `/tenant_id` partition. [Signals IaC](../../infra/main.bicep#L609) declares hierarchical paths `/scope`, `/jurisdictionId`, `/dataSourceId`; [SignalRepository](../../apps/api/app/repositories/signal_repository.py#L51) writes/filters `scope`. [TenantMiddleware](../../apps/api/app/middleware/tenant_middleware.py#L47) resolves `live` or simulation tenants, not NSW/VIC tenant values. [Routing](../../apps/api/app/services/simulation/jurisdiction_routing.py#L68) uses jurisdiction plus hazard and optional agency hint, not a universal fixed lead per state. SECTOR-04's RFS/SES/local-government example also does not identify two distinct state jurisdictions.

**Developer instructions:** Own the data and partition diagrams/pages. Show tenant/environment scope separately from jurisdiction and agency authorization. Identify per-container physical partition paths and application predicates. Label illustrative lead-agency examples as hazard-dependent and distinguish read filtering from field-level hand-over authority. Preserve the explicitly redirected legacy file until a separately approved migration.

**Tester instructions:** Reconcile diagrams against both IaC and repository predicates; use a live NSW record, live VIC record, two simulation scopes, and multiple NSW hazards. Do not treat different strings from a helper as an end-to-end database-isolation test.

**Positive tests:** A document's fields and physical partition path can be traced accurately; each of eight jurisdictions plus Commonwealth is represented. **Negative tests:** A tenant-only diagram must not claim cross-jurisdiction authorization it does not demonstrate. **Edge-case tests:** A common tenant spanning jurisdictions, unknown hazard, advisory agency hint, and cross-state hand-off retain distinct boundaries.

**Existing test locations:** [Tenant tests](../../tests/integration/test_tenant_isolation.py#L9) include a scope-helper comparison and in-memory simulation visibility tests. [Routing tests](../../apps/api/tests/test_jurisdiction_routing.py#L108) exercise jurisdiction/agency outcomes, not the illustrated field-redaction policy.

**Future commands/prerequisites:** With Python/API dependencies installed and cloud endpoints unset, run `python -m pytest tests/integration/test_tenant_isolation.py apps/api/tests/test_jurisdiction_routing.py -q`; inspect the provisioned-schema path separately only when later authorized. No schema migration is implied by this documentation task.

**Objective acceptance:** The diagrams use the exact configured key names, separately label scope/jurisdiction/agency controls, and cite the controlling definitions. No jurisdiction is described as a separate physical tenant solely because it appears in the UI filter.

### AUD-003: Correct Model-Gateway and Residency Guarantees

- [ ] AUD-003 Replace universal-redaction claims with a source-grounded AU/non-AU decision path and explicit unresolved bypass risks.

**Affected:** FR-014 extension, FR-016, SC-003; T029, T030, T041, T042, T044, T050, T077, T083.

**Expected versus observed:** [BUILD-01](../../docs/architecture/c4/agent-runtime-llm-gateway.md#L30) says no prompt reaches Foundry without redaction. [Model gateway](../../apps/agents/common/model_gateway.py#L193) returns AU content unchanged. [Live client gateway application](../../apps/agents/common/foundry_chat_client.py#L368) also bypasses an empty region, returns messages on gateway import failure, and applies the gateway to string-valued user messages rather than all roles/tools. [The registry](../../infra/parameters/foundry-carveout.yaml#L21) contains three AU deployments and zero non-AU entries, correctly reflected by SEC-01's exact mechanism-zone label. Older [C4 text](../../docs/architecture/c4/system.md#L53) still depicts non-AU Phi as a concrete path.

**Developer instructions:** Own SEC-01, BUILD-01, and contradictory C4 text. Preserve the accurate registry-driven label without hard-coding a permitted non-AU region. Draw current AU inference separately from conditional non-AU inference, including deny/redact/allow and response/audit handling. Document unverified bypass handling explicitly and obtain the owning security feature's resolution before claiming fail-closed coverage. Do not change the registry or widen permission as a documentation shortcut.

**Tester instructions:** Compare annotations against the registry and the actual client dispatch path, not just the gateway helper. Use synthetic nonpersonal text and dummy endpoint identifiers.

**Positive tests:** AU traffic is described according to implemented bypass behavior; non-AU user-message redaction/denial is represented. **Negative tests:** An empty region, absent gateway import, system-message content, or tool content cannot be presented as universally redacted without corresponding enforcement. **Edge-case tests:** Case-normalized regions, zero active non-AU deployments, multi-message prompts, and a newly approved registry entry update the explanation without hard-coded region names.

**Existing test locations:** [Data-minimisation tests](../../tests/integration/test_data_minimisation_gateway.py#L61) explicitly assert the AU bypass; they do not prove every `LiveFoundryChatClient` bypass fails closed. [Client contract tests](../../tests/contract/test_foundry_chat_client.py#L93) are the appropriate adjacent client-test surface.

**Future commands/prerequisites:** With agents dependencies and fake clients available, run `python -m pytest tests/integration/test_data_minimisation_gateway.py tests/contract/test_foundry_chat_client.py -q`; add future client-boundary regression cases under that existing contract test. No live inference is required.

**Objective acceptance:** A reviewer can distinguish current AU behavior, permitted non-AU mechanism, actual enforcement points, and unresolved bypass risks on the page/diagram. No universal PII-removal or fail-closed claim exceeds the inspected caller and test coverage.

### AUD-004: Ground the RBAC Matrix in Enforced Permissions

- [ ] AUD-004 Correct per-role permissions and add resolvable authority references for every permission boundary.

**Affected:** FR-017, US5.2; T045, T051.

**Expected versus observed:** [RBAC source](../../docs/architecture/security/rbac-matrix.drawio#L55) grants IC `Admin`, while [enforcement](../../apps/api/app/middleware/rbac_check.py#L118) reserves the admin branch for `system-administrator`. The diagram leaves [Operations audit access blank](../../docs/architecture/security/rbac-matrix.drawio#L76), whereas [common route access](../../apps/api/app/auth/rbac_registry.py#L57) includes audit-list for every operational role. The eight diagram permission columns have no per-row spec citations, and [page citations](../../docs/architecture/security/rbac-matrix.md#L28) refer generally to CD/AIDR specs rather than the implemented authorization registry.

**Developer instructions:** Own the RBAC source and page. Build the matrix from the closed AppRole set, protected route families, authentication activation conditions, and separate administrator behavior. Explain role-label aliases. Distinguish a role's intended business rights from an actually protected endpoint; do not make the product grant extra privileges to match the picture.

**Tester instructions:** Compare each of the ten role rows and the separate system-administrator explanation against allowed and denied route families. Use the existing test-principal mechanism only in isolated tests and never as production evidence.

**Positive tests:** A permitted audit-list/outcome route matches the matrix. **Negative tests:** IC impersonation/admin claims and an unknown role are not shown as allowed. **Edge-case tests:** Multiple role claims, persona-function mismatch, administrator impersonation, and production-auth disabled state are documented separately.

**Existing test locations:** [Impersonation tests](../../apps/api/tests/contract/spec_035/test_impersonation_pairing.py#L115) assert non-admin 403 and paired admin audit writes. [Whoami tests](../../apps/api/tests/contract/spec_035/test_whoami.py#L50) assert principal shape with injected test identity, not all matrix cells.

**Future commands/prerequisites:** With API test dependencies, run `python -m pytest apps/api/tests/contract/spec_035/test_impersonation_pairing.py apps/api/tests/contract/spec_035/test_whoami.py -q`; extend document parity coverage in the proposed shared architecture test file.

**Objective acceptance:** Every permission cell has an implementation/requirement source, all ten named roles remain visible, administration is not conflated with command authority, and diagram/prose agree with route-specific enforcement.

### AUD-005: Correct Trust-Boundary Authentication and Data Flow

- [ ] AUD-005 Replace unsupported authentication edges with the actual browser, API, ingestion, service, and agent boundaries.

**Affected:** FR-018, US5.3; T046, T052.

**Expected versus observed:** [SEC-03 edge 17](../../docs/architecture/security/trust-boundary.drawio#L52) assigns Managed Identity to browser-to-API traffic, although [the page](../../docs/architecture/security/trust-boundary.md#L30) says Entra/OAuth. The source diagram's uniform external OAuth-plus-key gateway is not the [BoM anonymous FTP poller](../../apps/ingestion/pipelines/bom_warnings.py#L33). No consuming agent is shown at the end of the trust path. [API middleware](../../apps/api/app/main.py#L46) includes distinct EasyAuth, Entra, RBAC, and tenant mechanisms rather than the single generic boundary drawn.

**Developer instructions:** Own the trust diagram/page and trace each edge to its actual client/server protocol. Separate operator identity from workload identity and source acquisition from downstream broker access. Include the agent consumer, trust decisions, and relevant threat/mitigation references; label design-intent controls not wired in the inspected entry point.

**Tester instructions:** Walk one authenticated operator request and one real configured feed through every crossing; compare code and deployment configuration without assuming cloud enforcement from local middleware alone.

**Positive tests:** Browser and workload credentials are distinct and named; every depicted crossing has a supported mechanism. **Negative tests:** Do not label anonymous polling as OAuth-protected or a user browser as a managed-identity workload. **Edge-case tests:** Local/test identity defaults, protected-prefix boundaries, private versus public endpoints, and sources with different protocols are explicitly distinguished.

**Existing test locations:** [Whoami contract](../../apps/api/tests/contract/spec_035/test_whoami.py#L34) installs only selected middleware with a test principal. [RBAC denial tests](../../tests/integration/test_rbac_enforcement_036.py#L94) exercise simulation routes, not an external ingestion gateway.

**Future commands/prerequisites:** In the isolated API environment, run `python -m pytest apps/api/tests/contract/spec_035/test_whoami.py tests/integration/test_rbac_enforcement_036.py -q`; obtain a source-to-edge review for uncovered feed protocols. External integration and cloud access are not prerequisites to a truthful current-state diagram.

**Objective acceptance:** No edge has a credential or authorization label contradicted by its caller, and the external-feed-to-consumer path and operator-to-API path are separately traceable on one readable diagram.

### AUD-006: Replace the Illustrative Ingestion Map with a Wired Path

- [ ] AUD-006 Reconcile source acquisition, normalization, persistence, brokers, and named consumers; expose disconnected persistence rather than claiming success.

**Affected:** FR-004, FR-014; US3.2/3, US4.3; T022, T023, T026, T027, T034, T039.

**Expected versus observed:** SECTOR-02 draws brokers before ingest and Cosmos before unnamed `alerting, impact, coordination` consumers. [SECTOR-03](../../docs/architecture/data/integration-point-map.drawio#L1) instead uses Alerting/Impact/Coordination/Operations/Recovery agents, without canonical runtime mapping. [The configured ingestion entry point](../../apps/ingestion/Dockerfile#L35) starts the worker, whose [factory](../../apps/ingestion/worker.py#L208) passes blob storage and deduplication only. [Pipeline construction](../../apps/ingestion/pipeline_factory.py#L63) does not supply a signal repository; [the controlling persistence branch](../../apps/api/app/services/ingestion/pipeline_base.py#L266) executes only if one was injected. The [BoM pipeline](../../apps/ingestion/pipelines/bom_warnings.py#L14) polls FTP XML. The L3-Ingest drawing ends at dead-letter handling without a successful persistence/consumer path.

**Developer instructions:** Own the three ingestion/integration views. Inventory actual configured pipeline IDs, formats, source endpoints, stores, and canonical agent consumers, with clear labels for implemented, optional, and proposed paths. Trace BoM, GA, NEMA, and named agency coverage separately. Document the worker dependency-wiring gap and route any product fix to its owner; do not invent a broker or consumer to satisfy a label.

**Tester instructions:** Use a recording repository, mocked source payload, mock broker, and named consumer in a later isolated fixture. Distinguish normalization/poll metrics from persisted records and consumed messages.

**Positive tests:** A normal signal's acquisition, persistence, routing, and consuming agent agree with the diagram and named configuration. **Negative tests:** Missing repository injection, unavailable broker/consumer, and invalid format cannot be reported as successful end-to-end ingestion. **Edge-case tests:** Duplicate source IDs, dead letters, disabled pipelines, simulation scope, and feeds without a supported adapter get explicit outcomes/gap entries.

**Existing test locations:** [Pipeline integration tests](../../tests/integration/test_ingestion_pipeline.py#L40) use `MockPipeline`; `signals_ingested >= 0` and `dedup_hits >= 0` are non-discriminating assertions and no production factory persistence is exercised. [BoM normalizer tests](../../tests/contract/test_bom_normaliser.py#L1) are format-level evidence only.

**Future commands/prerequisites:** With ingestion/API dependencies and recording fakes, run `python -m pytest tests/integration/test_ingestion_pipeline.py tests/contract/test_bom_normaliser.py -q`; strengthen the existing integration file to assert exact repository and consumer calls before claiming the path works.

**Objective acceptance:** Every system-format-endpoint-consumer row names existing implementations or an explicit tracked proposal. The documents accurately state the worker's persistence configuration, and an end-to-end success claim requires assertions beyond nonnegative counters.

### AUD-007: Make the C4 Model Trace Real Components

- [ ] AUD-007 Reconcile L1/L2/L3 views and the legacy middleware narrative with actual applications, optional services, and request/response relationships.

**Affected:** FR-004, FR-005; US1.3, US4.1/2/3; T029, T030, T031, T032, T033, T034, T036, T037, T038, T039, T041, T042, T066, T069.

**Expected versus observed:** [L2 XML](../../docs/architecture/c4/container.drawio#L1) has ten nodes, omits App Insights, and labels only `Agents Runtime / 5 agents`. [L3 API](../../docs/architecture/c4/component-api.drawio#L1) stops at generic handlers; [L3 Web](../../docs/architecture/c4/component-web.drawio#L1) and [L3 Ingest](../../docs/architecture/c4/component-ingest.drawio#L1) do not complete the required Web/API/agent response path. [L2 Mermaid](../../docs/architecture/c4/container.md#L33) adds Eval Runner and Dependency Notifier without matching L3 navigation/deferral explanations. The [legacy middleware diagram](../../docs/architecture/spec-035-middleware-and-offline.md#L29) orders authentication before audit, while [registration and documented request order](../../apps/api/app/main.py#L57) place audit outside classifier/Entra/RBAC.

**Developer instructions:** Own C4 sources/pages and the retained middleware narrative. Identify real modules and boundaries, distinguish deployed application containers from backing services and optional tools, add all required L2 services and five named agents, and label request and return paths. Link L2 directly to each application L3 page. Reconcile rather than silently retain conflicting Mermaid and Draw.io representations. Preserve existing file locations and explicit historical notes.

**Tester instructions:** Follow one browser request through the mounted router into a handler/service and back; separately inspect the ingest success path and agent model call. A conceptual component is acceptable only when its implementation mapping is supplied.

**Positive tests:** Every application in L2 has a corresponding L3 link or explicit justified deferral; all required external actors and backing services appear. **Negative tests:** An added container or changed middleware order without documentation mapping fails review. **Edge-case tests:** Optional Eval Runner/ingest-runner, nonbusiness Dependency Notifier, disabled feature registrations, and L4 deferral remain visible without implying they are the five business agents.

**Existing test locations:** [Production-reach contracts](../../apps/api/tests/contract/spec_035/test_production_reach.py#L1) are the relevant registration-test location. [API application factory](../../apps/api/app/main.py#L25) and [router](../../apps/api/app/api/router.py#L56) are the controlling static sources, not evidence of a running service.

**Future commands/prerequisites:** In a future API test environment, run `python -m pytest apps/api/tests/contract/spec_035/test_production_reach.py -q`; then use the feature's US4 navigation review and a human source-to-diagram walkthrough. Do not deploy applications to validate their documentation.

**Objective acceptance:** L1/L2/L3 agree, every required application/service is represented at the appropriate level, and a reader can trace an accurately labelled Web/API/agent round trip and ingest success path without consulting source code.

### AUD-008: Restore Valid and Faithful Diagram Exports

- [ ] AUD-008 Repair malformed sources and regenerate readable, faithful PNGs with recorded export settings.

**Affected:** FR-006, FR-007, FR-009, FR-010, SC-007; all original diagram-pair tasks, especially T007, T044, T048, T056, T078.

**Expected versus observed:** The XML parser rejects [recovery-transition.drawio](../../docs/architecture/sequence/recovery-transition.drawio#L16) because literal `<br>` appears inside an attribute. Its [PNG](../../docs/architecture/sequence/recovery-transition.png) shows only three disconnected phase boxes, not the additional source roles/transition edges. [Audit provenance](../../docs/architecture/sequence/audit-provenance.png), [AU residency](../../docs/architecture/security/au-residency-data-classification.png), and [resource topology](../../docs/architecture/deployment/azure-resource-topology.png) have edge labels crossing node/boundary labels; `rg-ama` is obscured. [QUAL-01](../../docs/architecture/quality/test-pyramid.png) displays text but no visible pyramid. Several original PNGs have transparent backgrounds and no recorded density/export provenance.

**Developer instructions:** Own each source/PNG pair as an atomic artifact. Correct XML with a real XML-aware authoring/export tool, render from the same source revision, keep all labels inside their intended bounds, and use the stipulated white background and 150-DPI setting or obtain an explicit requirement resolution. Preserve the extra roadmap diagrams. Update the manifest only after the export is checked; do not use a separately hand-drawn raster as proof of source fidelity.

**Tester instructions:** Parse every named source, open it in Draw.io, and compare the resulting diagram to the committed PNG at normal GitHub reading scale. Review all labels, not just image nonemptiness.

**Positive tests:** Valid source reopens, all actors/edges render, and the PNG visually matches. **Negative tests:** Invalid XML, unsupported shapes, omitted edges, clipped approval labels, and stale independent PNGs are rejected. **Edge-case tests:** Long labels, embedded HTML, transparent exports, one-line XML, Windows/LF bytes, and multiple diagram pages retain fidelity.

**Existing test locations:** There is no architecture export assertion in the inspected source. The current [pairing loop](../../.github/workflows/ci.yml#L489) only checks filenames and [hash step](../../.github/workflows/ci.yml#L515) only checks source bytes. Use the proposed shared architecture test file for structural checks, not semantic image approval.

**Future commands/prerequisites:** With Draw.io desktop/export support installed, perform source exports and human visual review; from repository root run `npx --yes markdownlint-cli2 "docs/architecture/**/*.md"` and, after AUD-010 resolves format, the documented manifest verifier. XML-only future checks must not launch application tests.

**Objective acceptance:** All 32 named sources parse and reopen; PNGs are faithful, legible, white-background exports with recorded settings; no actor, human gate, phase, boundary, or resource name is obscured or omitted.

### AUD-009: Use Azure Service Stencils

- [ ] AUD-009 Replace generic Azure-service boxes with supported Azure Draw.io stencils while preserving semantics and editability.

**Affected:** FR-008; T021, T022, T029, T030, T033, T034, T044, T046, T055, T056, T057, T074, T077 and other diagrams depicting Azure services.

**Expected versus observed:** Mandatory Azure services in [DEPLOY-02](../../docs/architecture/deployment/azure-resource-topology.drawio#L7), [SEC-01](../../docs/architecture/security/au-residency-data-classification.drawio#L8), and [BUILD-01](../../docs/architecture/c4/agent-runtime-llm-gateway.drawio#L1) use generic shapes. The inspected named sources have no Azure stencil styles. Fallback authoring is recorded in source metadata, but no specification amendment waives FR-008.

**Developer instructions:** Own service-node styles and exports, use available supported Azure libraries, retain plain shapes for domain actors, and keep the actual resource type discernible. Do not introduce an external image URL that prevents offline editing or export.

**Tester instructions:** Review every Azure-service node in the named inventory, especially all ten named DEPLOY-02 resources, and check rendering with the documented tool version.

**Positive tests:** Cosmos, messaging, identity, hosting, telemetry, and Foundry nodes render with the correct Azure symbol and text. **Negative tests:** A generic box with an Azure label, broken external icon link, or wrong service symbol is rejected. **Edge-case tests:** Services grouped inside a boundary still use identifiable symbols; domain actors remain semantically distinct.

**Existing test locations:** No stencil tests exist for this feature. [Diagram model contract](data-model.md#L89) defines the source/style obligation; [architecture checklist](checklists/architecture-review.md#L29) is the existing manual-review home.

**Future commands/prerequisites:** Enable the Azure shape library in the documented Draw.io authoring environment, re-export affected sources, and run future `python -m pytest tests/contract/test_architecture_docs.py -k azure_stencils -q` after the proposed structural test exists. Human icon correctness review remains required.

**Objective acceptance:** Every depicted Azure service uses a supported Azure stencil, all icons render offline, and generic-box fallback is not counted as compliance with FR-008.

### AUD-010: Enforce Manifest, Pair, and Inventory Completeness

- [ ] AUD-010 Make the diagram validation contract reject omitted sources/pairs and stale exports, and reconcile its path and ordering convention.

**Affected:** FR-007, FR-021(a/d), SC-007; T002, T005, T063, T070, T072, T086.

**Expected versus observed:** [The manifest contract](contracts/diagram-manifest-format.md#L24) requires architecture-relative paths sorted by path. [Current entries](../../docs/architecture/.diagram-hashes#L1) are repository-root-relative and ordered by digest; [current CI](../../.github/workflows/ci.yml#L515) appropriately runs from root, so this is a contract conflict, not a claim that current hashes fail. `sha256sum --check` reads listed entries only: removing one entry leaves that source unchecked. Removing both halves of a named pair can satisfy both existing loops. No named-inventory/count gate exists in the complete docs-arch job. Updating source plus digest without updating PNG also does not prove an export occurred.

**Developer instructions:** Own the CI diagram checks, manifest format, and contributor instructions. Agree one path convention; enforce bijection between discovered sources and manifest entries, unique paths, valid digests, source validity, both pairing directions, and all named inventory IDs or approved deferrals. Bind exported PNGs to source versions with export-time provenance rather than claiming source checksums alone prove rendering. Accommodate the two later roadmap pairs without weakening the 32 named obligations.

**Tester instructions:** Use temporary document trees in the proposed shared test file, not the real architecture directory, for mutation cases.

**Positive tests:** A complete named inventory plus extra valid pairs passes under the agreed convention. **Negative tests:** Missing source, missing PNG, omitted manifest line, duplicate entry, missing named pair, malformed XML, and source/digest-only updates fail. **Edge-case tests:** Empty manifest, digest/path ordering, spaces in paths, Windows newlines, duplicate basenames in different directories, and valid documented deferrals have explicit results.

**Existing test locations:** [Pair loops](../../.github/workflows/ci.yml#L489) are static executable definitions, not tests. [Adjacent repository lint contracts](../../tests/contract/test_rag_optout_lint.py#L99) demonstrate repository-scoped invariant testing but do not exercise this manifest.

**Future commands/prerequisites:** After adding the proposed regression tests, run `python -m pytest tests/contract/test_architecture_docs.py -k diagram_manifest -q`. The current-compatible diagnostic command is `sha256sum --check docs/architecture/.diagram-hashes` from repository root; it must not be confused with the contributor guide's architecture-directory command until conventions are reconciled.

**Objective acceptance:** Every existing source is checked exactly once, every named target is present or explicitly deferred, both pairing directions fail on absence, and export provenance cannot be satisfied by editing only source and digest. The 34 current artifacts remain intact unless an independent approved change retires one.

### AUD-011: Check All Internal Link Targets

- [ ] AUD-011 Repair the broken quickstart link and remove target filtering that hides links to specs, ADRs, contracts, or source.

**Affected:** FR-001, FR-021(b), SC-004; US1.1, US7.2; T010, T063, T071, T072, T086.

**Expected versus observed:** The [known-gaps link](../../docs/architecture/known-gaps.md#L4) resolves outside the repository. [CI](../../.github/workflows/ci.yml#L480) sets both a base and an include expression matching only `docs/architecture`. Pinned [lychee v0.15.1 filter implementation](https://raw.githubusercontent.com/lycheeverse/lychee/v0.15.1/lychee-lib/src/filter/mod.rs) and its `test_include_regex` show that with includes and no excludes, unmatched target URLs are excluded. Thus valid or broken targets under `specs/` or `docs/decisions/` can escape checking. No lychee configuration file was found by scoped filename search. Fragment checking is not enabled in the current command.

**Developer instructions:** Own the link-check step and broken page link. Scope input documents to architecture while validating all repository-local targets, resolve relative paths from each source document, and use offline checking where possible. Treat fragments and deliberate exceptions explicitly; do not solve bad relative links by excluding all specification targets.

**Tester instructions:** Use fixture pages at root and nested architecture levels with targets in specs, decisions, source, and sibling diagrams. Confirm extracted targets, not only the exit code of a scan that may check zero links.

**Positive tests:** Existing sibling and cross-directory targets are checked and pass. **Negative tests:** A missing specification target, bad parent traversal, missing PNG, and broken required fragment fail. **Edge-case tests:** Encoded spaces, reference-style links, HTML links, self-fragments, absolute external URLs, and deliberate ignored external sites do not suppress local validation.

**Existing test locations:** No feature link-check assertions exist. [The lint contract](contracts/lint-scripts.md#L145) copies the problematic configuration; it needs the same correction as CI. Proposed document regression tests should cover the command's target scope.

**Future commands/prerequisites:** With the pinned checker installed, inspect `lychee --offline --dump "docs/architecture/**/*.md"`, then run `lychee --offline --no-progress "docs/architecture/**/*.md"` under the agreed fragment policy. Run `python -m pytest tests/contract/test_architecture_docs.py -k internal_links -q` once proposed tests exist. Expected result: actual repository-local targets are checked and zero are broken.

**Objective acceptance:** The bad quickstart target is fixed, all 40 pages' local targets are checked independently of target directory, and a missing spec/ADR target demonstrably fails the future docs-arch gate.

### AUD-012: Make Spec Coverage Substantive and Fail Closed

- [ ] AUD-012 Replace blanket citation tokens with traceable page/spec mappings and harden inventory/exclusion validation.

**Affected:** FR-011, FR-012, FR-021(c), SC-005; T010, T025, T026, T027, T039, T040, T051, T053, T061, T064, T071, T082, T084.

**Expected versus observed:** [README's comment manifest](../../docs/architecture/README.md#L84) lists every number through 040. [Collector logic](../../tools/lint/check_spec_cross_refs.py#L61) accepts those tokens, code samples, and the gap registry itself. [Inventory](../../tools/lint/check_spec_cross_refs.py#L23) silently returns empty for a missing specs directory and is not bounded to 001-037. Static inventory is 39 prefixes, namely 001 and 003-040; 002 is absent without an individual confirmed archive record. [Exclusions](../../tools/lint/check_spec_cross_refs.py#L38) treat lowercase `spec-NNN` plus `Resolved` as sufficient, without proving archive/supersession. Page examples incorrectly cite spec-015 performance work for tenancy/health protocols and spec-035 web closure for ingest components. T010/T071 explicitly encourage blanket comments, conflicting with substantive traceability and the no-spurious-citation edge case.

**Developer instructions:** Own the citation checker, index mapping, and affected citations. Resolve the explicit 001-037 versus current-directory inventory contract. Require existing input roots and a documented inventory; require a meaningful linked architecture home or a genuine individual archival/deferral record with status semantics. Do not count a known-gap description as completed documentation coverage. Keep duplicate 036 prefixes deduplicated but expose both actual feature identities where relevant.

**Tester instructions:** Add temporary specs/pages/registry fixtures exercising the checker functions and CLI. Review at least one actual architecture explanation per required specification; matching tokens alone are insufficient.

**Positive tests:** A linked, topic-correct page mapping covers its spec; an explicitly approved archive is reported separately. **Negative tests:** Empty roots, blanket index comments, code-fence examples, gap-only mentions, and generic Resolved rows must not fabricate coverage. **Edge-case tests:** Two 036 folders, two 001 features, absent 002, newer 038-040 features, uppercase registry IDs, and resolved-but-not-archived gaps follow documented rules.

**Existing test locations:** No tests exercise `build_spec_inventory`, `build_exclusion_set`, or `build_cited_set`. [RAG opt-out lint tests](../../tests/contract/test_rag_optout_lint.py#L105) demonstrate bidirectional source-to-document checks that can inform the proposed architecture fixture tests.

**Future commands/prerequisites:** After contract resolution and fixture additions, run `python -m pytest tests/contract/test_architecture_docs.py -k spec_cross_refs -q`, then `python tools/lint/check_spec_cross_refs.py --root .`. Expected reporting separates required, meaningfully cited, archived, deferred, and missing IDs.

**Objective acceptance:** No required spec is considered covered solely by a boilerplate token or gap mention. Every exclusion has an explicit reason/reference, wrong roots fail, and page citations lead to topic-correct existing feature documents.

### AUD-013: Make Known Gaps Actionable and Validate Their Shape

- [x] AUD-013 Replace placeholder tracking references, restore missing fallback records, and reject malformed/empty gap registries.

**Affected:** FR-005, FR-023, SC-008; T004, T062, T065, T067, T068, T069, T074, T075, T076, T077, T078, T079, T086.

**Expected versus observed:** The [registry](../../docs/architecture/known-gaps.md#L10) has eleven seed rows. The Bicep graph reference is an issue-creation URL, not an issue. Backticked `tasks.md#T061` and similar references neither resolve relative to the registry nor identify actual heading anchors in [tasks.md](tasks.md#L196); many point to already-checked tasks that do not perform the deferred migration. `SPEC-RANGE-VERIFY` still batches unmapped specs. All six amendment sources identify fallback authoring, but no required `DRAWIO-FALLBACK-*` records exist. [Parser logic](../../tools/lint/check_known_gaps.py#L40) returns success for a document with no recognized data rows and treats formatting-wrapped placeholders such as backticked `TBD` as nonempty valid text.

**Developer instructions:** Own the registry and checker. Add stable, resolvable open follow-up references with a real owner/outcome; maintain historical resolutions without pretending a task fragment is an open issue. Reconcile all fallback metadata with authoring evidence, and keep unproven fallback resolutions open. Validate headers, required cells, statuses, dates, identifiers, and recognizable placeholder forms; use an explicit empty-state representation instead of accepting arbitrary empty files.

**Tester instructions:** Use temporary Markdown tables; never mutate the checked-in registry to exercise negative cases. Verify references against actual task headings/work items.

**Positive tests:** Valid Open/In Progress/Resolved rows and a legitimate explicit no-gap state pass. **Negative tests:** Empty file, missing header, truncated row, empty ref, plain/backticked/bold TBD, issue-creation form, and nonexistent fragment fail according to the clarified schema. **Edge-case tests:** Multiple tables, duplicate IDs, escaped table separators, CRLF, inline-code refs, and a resolved gap retain traceability.

**Existing test locations:** [check_known_gaps.py](../../tools/lint/check_known_gaps.py#L20) is the current implementation; no adjacent tests reference it. Use the proposed shared architecture test file and existing [known-gaps schema](contracts/known-gaps-schema.md#L28).

**Future commands/prerequisites:** After adding fixtures, run `python -m pytest tests/contract/test_architecture_docs.py -k known_gaps -q`, then `python tools/lint/check_known_gaps.py --root .`. Actual remote issue existence may be confirmed later by an authorized reviewer; no cloud access is required.

**Objective acceptance:** Every deferred area has an actionable reference, all six amendment fallback outcomes are documented truthfully, no spec is hidden in a batched unresolved range, and malformed/placeholder registries do not pass.

### AUD-014: Correct Evacuation and Recovery Semantics

- [ ] AUD-014 Restore the constitutional five-stage evacuation model and a managed, overlapping recovery transition.

**Affected:** FR-009, FR-010(c/d), SC-006; T006, T007, T008, T009; CHK074, CHK075, CHK086, CHK087.

**Expected versus observed:** [Evacuation prose](../../docs/architecture/sequence/evacuation-five-stage.md#L27) names Preparation, Alert/Warning, Evacuation, Shelter, Return/Recovery. [The constitutional model](../../.specify/memory/constitution.md#L134) and [domain transitions](../../packages/domain/src/domain/models/evacuation_stage.py#L27) require Decision, Warning, Withdrawal, Shelter, Return, with additional alternative/terminal states. [Recovery PNG](../../docs/architecture/sequence/recovery-transition.png) reduces the view to three disconnected boxes, omitting managed handover and response/recovery overlap. The local checklist additionally demands explicit recovery principles and environments, an obligation not satisfied by those boxes.

**Developer instructions:** Own SEQ-03/04 sources/pages. Label the five canonical stages explicitly; put preparation outside the lifecycle rather than substituting it for Decision. Distinguish warning publication authorization from movement authorization, shelter-in-place/re-entry alternatives, and return safety certification. Show response/recovery overlap, transition owners, criteria, and the four recovery environments; resolve/check the checklist's six-principle scope explicitly.

**Tester instructions:** Walk canonical and alternative lifecycle paths against the domain state machine and constitution. Treat lifecycle review separately from export validity in AUD-008.

**Positive tests:** The normal five-stage path and managed recovery handover are traceable. **Negative tests:** Warning without Decision, rejected movement authorization, skipped stages, and abrupt response-to-recovery shutdown are not represented as valid defaults. **Edge-case tests:** Shelter-in-place, re-entry to Decision, immediate evacuation, phased return, and concurrent response/recovery are intelligible.

**Existing test locations:** [Evacuation stage tests](../../tests/unit/test_evacuation_stages.py#L20) assert valid/invalid transitions and [full lifecycle](../../tests/unit/test_evacuation_stages.py#L215). [Controlling stage transition code](../../apps/agents/evacuation/stages.py#L37) consumes the domain transition table.

**Future commands/prerequisites:** With domain/agents dependencies, run `python -m pytest tests/unit/test_evacuation_stages.py -q`, then obtain an AIIMS-qualified source/diagram review. This task corrects documentation, not evacuation runtime behavior.

**Objective acceptance:** Canonical stage names/order agree with the constitution and source; alternatives and human gates are visible; recovery is explicitly overlapping and managed, and all applicable recovery checklist claims have evidence or an approved scope resolution.

### AUD-015: Reconcile Deployment Guidance with Current Delivery Configuration

- [ ] AUD-015 Update deployment/topology views to separate historical named resources, current IaC naming, and verified release gates.

**Affected:** FR-004, US6.1/2/4; T055, T056, T058, T059; SC-007 Bicep deferral.

**Expected versus observed:** [DEPLOY-01](../../docs/architecture/deployment/cicd-pipeline.md#L23) shows PR quality, what-if, one manual approval, then sequential dev/staging/prod promotion. [Current CD](../../.github/workflows/cd.yml#L19) runs after successful CI push events for three separate branches, selects a GitHub environment, resolves `rg-drh-${TARGET_ENV}`, and directly provisions/deploys. [The service declaration](../../azure.yaml#L58) hosts Web on App Service. The architecture task's fixed `rg-ama` names conflict with the current environment-based design. Environment protection settings are not established by the YAML environment name. Bicep graph generation remains explicitly deferred, not delivered under a renamed graph found in the architecture inventory.

**Developer instructions:** Own DEPLOY-01/02 and linked C4 topology text. Label the `rg-ama` snapshot as historical/example unless deployment evidence supports it; show current naming templates and branch/environment mapping. Represent actual checked-in gates and separately identify required-but-unproven what-if/manual controls. Resolve outdated specification expectations explicitly without modifying CD just to match an obsolete picture. Give BICEP-DEP-01 a real follow-up rather than claiming generation occurred.

**Tester instructions:** Derive triggers, conditions, environment selection, service hosts, and resource-name formulas from source; distinguish repository configuration from remote environment protection.

**Positive tests:** A dev/staging/production push maps to its named environment and services; main/PR behavior is clear. **Negative tests:** No picture implies a PR deploys, a single run promotes all environments, or an environment label proves a human approval. **Edge-case tests:** Failed CI, rollback differences, optional services, and an older `rg-ama` deployment have explicit labels.

**Existing test locations:** [CD workflow tests](../../tests/devops/test_cd_workflow.py#L49) still expect main-triggered deployment, OIDC, and separate deploy-staging jobs; they are conflicting historical assertions, not proof of the current diagram. [CD source](../../.github/workflows/cd.yml#L224) is the controlling current path.

**Future commands/prerequisites:** Reconcile old workflow assertions before running `python -m pytest tests/devops/test_cd_workflow.py -q` in a future Python/PyYAML environment. Inspect GitHub protection evidence only with later authorization. No `azd up`, provisioning, or cloud discovery is required for document correction.

**Objective acceptance:** Diagram and workflow agree on branch triggers, actual gates, service hosts, and naming; historical resources and unknown external approval settings are labelled; Bicep-graph deferral has a concrete tracked disposition.

### AUD-016: Reconcile SLOs and Qualify Capacity Evidence

- [ ] AUD-016 Align SEC-04 and capacity claims with explicit metric definitions, alert configuration, and evidence status.

**Affected:** FR-019, US5.4; T047, T053, T067; quality/capacity views under FR-004.

**Expected versus observed:** [SEC-04's six services](../../docs/architecture/security/sli-slo-model.md#L24) omit audit integrity, kill-switch propagation, evaluation-baseline adherence, and public-network refusal from [the SLO catalogue](../../docs/observability/slo.md#L59). It substitutes 1x/2x/4x windows for [catalogue fast/slow burns](../../docs/observability/slo.md#L125), and its cost target has no numeric budget. [Capacity baseline](../../docs/architecture/capacity-model.md#L20) claims measured/provisioned-looking throughput, replica limits, and failover behavior without a benchmark/run/configuration evidence reference. The observed [simulation SLI configuration](../../infra/observability/sli-kql.json#L6) is a separate concrete metric set, not evidence for those capacity figures.

**Developer instructions:** Own SEC-04/capacity pages. Reconcile conflicting catalogues and identify each service's metric name, numerator/denominator or latency population, target, window, error-budget calculation, and alert policy. Link the controlling configuration or label the threshold as a proposal. Mark unmeasured capacity figures as estimates and distinguish desired from provisioned failover capacity; do not fabricate benchmark receipts.

**Tester instructions:** Review metric-to-alert mapping with SRE ownership; inspect assertions and configurations, and schedule measurements separately when authorized.

**Positive tests:** Every key service has an objective and a traceable threshold/window. **Negative tests:** Missing audit-integrity/kill-switch objectives, unexplained alternative burn rates, and estimates labelled verified fail review. **Edge-case tests:** Zero-budget gates, percentile versus availability SLIs, no samples, short windows, and cost guardrails have distinct definitions.

**Existing test locations:** [Observability Bicep tests](../../tests/devops/test_observability_alerts_bicep.py#L55) assert specific simulation thresholds; they do not measure the architecture page's SLIs or capacity. [SLO catalogue](../../docs/observability/slo.md#L119) is a conflicting document that needs explicit reconciliation, not unquestioned replacement authority.

**Future commands/prerequisites:** With pytest and checked-in IaC, run `python -m pytest tests/devops/test_observability_alerts_bicep.py -q` after any related assertion changes; a qualified SRE must review the reconciled definitions. Any future load/availability measurements require separate approval and recorded environment/sample details.

**Objective acceptance:** All key services are covered or explicitly scoped out, conflicting thresholds are resolved with an owner and reason, and every capacity/availability assertion is labelled configured, estimated, measured, or unverified with supporting evidence.

### AUD-017: Reconcile Page Standards and Markdown Exceptions

- [ ] AUD-017 Apply a consistent, approved architecture page standard without feature-specific markdownlint suppression.

**Affected:** FR-003, FR-005, FR-006, FR-012, FR-022; US4.5; T003, T035, T040, T041, T042, T049, T066, T067, T068, T069, T071, T072 and page tasks listed below.

**Expected versus observed:** Most diagram pages carry YAML spec-number tokens but no link to their motivating specification/ADR, for example [component-api.md](../../docs/architecture/c4/component-api.md#L7). [WAF mapping](../../docs/architecture/governance/waf-pillar-mapping.md#L22) lists components/specs but provides no per-pillar navigation to them. [C4 system](../../docs/architecture/c4/system.md#L19) and [container](../../docs/architecture/c4/container.md#L20) disable MD041 despite FR-022's prohibition on feature exceptions. Universal diagram requirements conflict with [RQ-10's text-only WCAG decision](research.md#L210), legacy Mermaid retention, and diagram-free capacity/registry/index pages. SC-007 says four C4 levels while FR-004 and the assumptions make L4 optional. These are explicit contract conflicts, not permission to invent diagrams or mark everything complete.

**Developer instructions:** Own page headers/citations, index redirect notes, authoring template, and local standards. Obtain an explicit scope interpretation for navigation/registry/text-only/legacy pages and optional L4. Preserve old URLs. Add meaningful linked motivations and per-pillar links; remove local markdownlint disables by fixing structure, not weakening root rules. Preserve honest canonical ADR metadata, including the existing stub status, rather than fabricating acceptance.

**Tester instructions:** Review every new/retained page against the resolved template and the unchanged [root rules](../../.markdownlint.jsonc#L4). Verify redirects and that no imported standard claims were silently waived.

**Positive tests:** A diagram page has a visible purpose/audience, image, index link, and meaningful spec/ADR links. **Negative tests:** Bare boilerplate citations, missing required metadata, local lint disables, and an unapproved diagram exemption fail. **Edge-case tests:** Text-only WCAG, ADR index, known-gaps registry, retained Mermaid pages, and optional L4 use explicitly approved classifications.

**Existing test locations:** [Architecture checklist](checklists/architecture-review.md#L116) is the manual page-standard review surface; no automated page-schema assertions were found. Use proposed shared document tests for structural checks only.

**Future commands/prerequisites:** With Node/npx available, run `npx --yes markdownlint-cli2 "docs/architecture/**/*.md"`; after adding tests run `python -m pytest tests/contract/test_architecture_docs.py -k page_contract -q`. Confirm the linter used the root rules and that no per-file disable hides a failure.

**Objective acceptance:** Every page meets a resolved applicable standard, all required citations are navigable/topic-correct, WAF pillars link to their evidence, old locations remain valid, and no feature-specific lint suppression remains.

### AUD-018: Complete the PPRR Agent and Role Overlay

- [ ] AUD-018 Add per-phase AIIMS roles, events, and labelled overlap regions to OPS-03.

**Affected:** FR-024; T075, T081; SC-002, SC-007.

**Expected versus observed:** [OPS-03 source](../../docs/architecture/operational/pprr-phase-overlay.drawio#L8) uses four adjacent vertical phase areas and five agent bars. It contains no AIIMS-role labels or phase event labels. [The page table](../../docs/architecture/operational/pprr-phase-overlay.md#L26) supplies some roles, including the nonspecific `All AIIMS roles`, but the diagram does not meet the single-view role obligation. Boundary markers are not labelled as overlap regions; the [constitution](../../.specify/memory/constitution.md#L207) says phases overlap and recur.

**Developer instructions:** Own OPS-03 source/page. Map each named agent and appropriate named role to every applicable phase, label recurrence/overlap explicitly, and explain whether this is operational guidance or runtime activation policy. Resolve the task's horizontal-lane requirement without obscuring the normative overlap semantics.

**Tester instructions:** Review Prevention, Preparedness, Response, and Recovery individually, then verify an incident with concurrent response/recovery and continuing monitoring. Use an AIIMS-qualified reviewer.

**Positive tests:** Each phase shows agents, named roles, capabilities, and events. **Negative tests:** Role names only in companion prose, an implied sequential-only lifecycle, or an unlabeled overlap fails review. **Edge-case tests:** Agents active in multiple phases, recurring preparedness during recovery, and capability unavailable in one phase retain readable distinctions.

**Existing test locations:** [OPS-03 page table](../../docs/architecture/operational/pprr-phase-overlay.md#L26) is existing authoring evidence; [architecture checklist](checklists/architecture-review.md#L130) includes constitutional review but lacks a completed amendment-specific review. No automated semantic phase-overlay test exists.

**Future commands/prerequisites:** After authorized Draw.io editing/export, run `npx --yes markdownlint-cli2 docs/architecture/operational/pprr-phase-overlay.md` and the reconciled pair/manifest checks; complete the manual FR-024 review. No agent execution is necessary to label operational intent accurately.

**Objective acceptance:** The diagram alone names the agents and AIIMS roles active in each phase and explicitly shows overlap/recurrence, with a constitution reference and no unsupported runtime activation claim.

### AUD-019: Add Cross-Sector Authority Boundaries

- [ ] AUD-019 Complete SECTOR-05 with named emergency sectors and lead-agency rules at the actual exchanges.

**Affected:** FR-015 extension; T076, T082; US3.4 and SC-007.

**Expected versus observed:** [SECTOR-05](../../docs/architecture/data/cross-sector-touchpoints.drawio#L1) connects government/community/health/transport/utility/volunteer nodes to a hub with format labels only. Fire and flood/SES are not explicit nodes, and no lead-agency rule appears on any crossing. [The companion table](../../docs/architecture/data/cross-sector-touchpoints.md#L25) supplies generic designation phrases, not source-grounded boundary rules for the task's NSW RFS/VIC CFA/SES scenario.

**Developer instructions:** Own this diagram/page. Retain relevant partner sectors but explicitly show fire, flood/SES, health, transport, and utilities, source/recipient direction, data format, jurisdiction, and authority rule. Cite the actual hazard/jurisdiction routing source; label any merely proposed partner integration as such.

**Tester instructions:** Walk an RFS/CFA/SES/health coordination example and inspect who authorizes each exchange. Reuse the agency-routing fixtures rather than treating spec-number strings as authority evidence.

**Positive tests:** Each required sector and boundary has a protocol and concrete lead/authorization rule. **Negative tests:** Generic `state designated` text without a referenced rule, missing fire/flood sectors, and an unimplemented partner endpoint claimed active fail. **Edge-case tests:** Multi-agency candidates, advisory hints, Commonwealth support, and cross-state versus within-state coordination remain distinct.

**Existing test locations:** [Routing tests](../../apps/api/tests/test_jurisdiction_routing.py#L97) verify agency brands/candidates; [routing service](../../apps/api/app/services/simulation/jurisdiction_routing.py#L68) controls tuple selection. They do not prove the hub-and-spoke partner exchange drawn here.

**Future commands/prerequisites:** With isolated API dependencies run `python -m pytest apps/api/tests/test_jurisdiction_routing.py -q`, then complete a human diagram-to-routing review and the reconciled export checks.

**Objective acceptance:** Fire, flood/SES, health, transport, and utilities are present; each depicted crossing identifies direction, protocol, and a supported authority rule; unsupported connections have explicit tracked status.

### AUD-020: Make the Test Pyramid Accurate and Visible

- [ ] AUD-020 Correct QUAL-01 geometry, count units/provenance, and complete primary tooling coverage.

**Affected:** FR-025; T078, T084; SC-007.

**Expected versus observed:** [Source tiers](../../docs/architecture/quality/test-pyramid.drawio#L12) use `mxgraph.lean_mapping.electronic_info_flow_edge`; [the PNG](../../docs/architecture/quality/test-pyramid.png) shows no pyramid geometry. [Page counts](../../docs/architecture/quality/test-pyramid.md#L25) call approximately 159/50/80/30/20 items tests without a dated count method. Read-only source inventory at the reviewed checkout counted 173 unit, 156 contract, 134 integration, 25 simulation, and 5 backend-E2E `test*.py` files; these are files, not executed or collected tests, and exclude app-local/web tests. Simulation omits pytest and E2E omits the backend pytest variant, contrary to the amended FR-025.

**Developer instructions:** Own QUAL-01 source/page. Use actual pyramid-compatible geometry with Unit as the widest base. State whether volume means files, collected test cases, or an illustrative investment proportion and include date/scope/method. Show pytest for unit/contract/integration/simulation/backend-E2E, simulation harness where used, and Playwright for web E2E. Do not repeat unproven mandatory testcontainers/Pact tooling as universal fact.

**Tester instructions:** Compare labels to test entry points and an agreed reproducible inventory; visual review must verify widths, ordering, and readability rather than counting tier strings.

**Positive tests:** Five visible ordered tiers, largest Unit base, and both E2E variants appear. **Negative tests:** Unsupported geometry, file/test conflation, missing pytest lanes, and arbitrary percentages fail. **Edge-case tests:** Parametrized tests, app-local suites, supplementary tiers, and future volume changes are represented with the chosen scope and units.

**Existing test locations:** [Test-tier README](../../tests/README.md#L8), [simulation suite example](../../tests/simulation/test_bushfire_evacuation_scenario.py#L1), and [backend E2E tier description](../../tests/README.md#L19) establish tooling/locations, not measured passing counts. The README's canonical unit-inclusive CI description also differs from [actual CI selection](../../.github/workflows/ci.yml#L133).

**Future commands/prerequisites:** After agreeing the count unit, a source-file inventory requires only filesystem reads. If collected-case counts are desired later, use an authorized `python -m pytest --collect-only -q tests/unit tests/contract tests/integration tests/simulation tests/e2e` environment; collection was not run in this audit. Re-export and visually review the pyramid.

**Objective acceptance:** The PNG visibly forms a five-tier pyramid, all required tooling appears, numbers have a dated reproducible definition, and neither inventory nor assertions are represented as evidence of executed test success.

### AUD-021: Complete Experience Traceability without Invented WCAG Assurance

- [ ] AUD-021 Add the missing publication/audit journey and source-grounded success-criteria/component mapping; qualify accessibility statuses.

**Affected:** FR-002, FR-003, FR-026; T049, T079, T085; SC-002 and SC-007.

**Expected versus observed:** [EXP-01](../../docs/architecture/accessibility/ops-dashboard-user-journey.drawio#L1) has five generic steps ending in Monitor Outcome, omitting task-required publication confirmation and audit receipt. No perception/comprehension/action labels or feature-success-criterion-to-component mapping is supplied. The [page](../../docs/architecture/accessibility/ops-dashboard-user-journey.md#L28) claims `aria-pressed`; the [approval button](../../apps/web/src/app/workspaces/%5BpersonaId%5D/_panels/ic-approval-card.tsx#L149) uses a disabled submit action instead. [WCAG table](../../docs/architecture/accessibility/wcag-coverage.md#L22) says all UI contrast was verified; the [existing baseline](../../docs/accessibility/spec-036-citation-card-baseline.md#L3) is warn-only and qualified, and the axe test does not assert zero violations.

**Developer instructions:** Own EXP-01/WCAG pages and source. Map actual screens/controls to perception, comprehension, action, publication confirmation, and correlated audit evidence. Separate WCAG criterion IDs from feature SC IDs. Scope conformance claims to reviewed components/states and label manual/runtime outcomes unverified absent receipts; do not add incorrect ARIA semantics to make source match a mistaken documentation statement.

**Tester instructions:** Prepare a canonical IC journey with successful and rejected publication and an audit-fetch failure. Use keyboard, assistive-technology, and contrast review later as separately recorded checks, not as assumptions from component names.

**Positive tests:** Each step has actual component/endpoint and feature-SC links; successful approval leads to explicit publication status and audit receipt. **Negative tests:** Warn-only axe results, missing audit, failed publication, and claims about nonexistent attributes cannot be labelled conformant/successful. **Edge-case tests:** Offline queued action, narrow viewport, zoom, keyboard focus, live status, and low/high confidence preserve the human gate and truthful state.

**Existing test locations:** [Citation axe tests](../../apps/web/tests/web/src/components/citation/citation-card.axe.test.tsx#L39) assert only `Array.isArray(results.violations)`. [Approval control](../../apps/web/src/app/workspaces/%5BpersonaId%5D/_panels/ic-approval-card.tsx#L51) fetches an evaluation and audit list, not evidence of a complete external publication journey. [Component tests](../../apps/web/tests/web/src/components/citation/citation-card.test.tsx#L1) are an existing adjacent test home.

**Future commands/prerequisites:** After installing the existing web workspace dependencies, run `pnpm --filter ./apps/web exec vitest run tests/web/src/components/citation`; obtain separately authorized browser/assistive-technology evidence for conformance claims. Authoring the corrected documentation itself needs no running app.

**Objective acceptance:** EXP-01 explicitly covers publication confirmation and audit receipt plus cognitive and feature-SC traceability. WCAG statuses cite scoped assertions/measurements, remain unverified where appropriate, and do not treat a warn-only test as universal conformance.

### AUD-022: Reconcile Completion Claims with Review Evidence

- [ ] AUD-022 Record an honest completion/evidence ledger and resolve contradictory historical gate expectations before obtaining final sign-off.

**Affected:** SC-001, SC-003, SC-004, SC-005, SC-006; T003, T005, T064, T065, T070, T071, T072, T073, T086; all review/acceptance gates.

**Expected versus observed:** The [persona review](review/persona-review.md#L76) asserts locally green checks without commands, exit records, source SHA, or a CI run reference. [All architecture checklist items](checklists/architecture-review.md#L13) remain unchecked, including roll-up human/CI gates. The [requirements checklist](checklists/requirements.md#L32) still counts 23 FRs and predates amendment coverage. [T005](tasks.md#L49) asks an empty manifest to make `sha256sum --check` exit zero, although an input with no valid checksum records does not establish a successful verification. T063 describes seven steps while listing more; historical 26/32 count and working-directory instructions also disagree with current 34-entry root-relative configuration. These are not trustworthy historical execution receipts.

**Developer instructions:** Own the feature's future evidence ledger/review records, not retrospective checkbox manipulation. Record actual final SHA, artifact inventory, unresolved items, exact checks, prerequisites, exit status, and linked outputs when later performed. Resolve obsolete count/path/empty-baseline instructions explicitly. Keep original historical claims distinguishable from current verification. Scope documentation fixes to docs/lint/CI and do not trigger `azd up` to manufacture evidence.

**Tester instructions:** After substantive remediation, perform the authorized document gates and persona acceptance reviews. Record reviewer qualification, timing and answers for the four-question orientation exercise, compliance-page walkthrough, and actuation marker/denial review.

**Positive tests:** A reproducible docs-arch run and dated reviewer record correspond to the exact reviewed artifact SHA. **Negative tests:** A checked task, unverifiable prose, stale run, helper-only test, or unrelated passing suite cannot close an execution/human gate. **Edge-case tests:** A later artifact change invalidates relevant sign-off; valid deferrals remain visible; parallel reviewers' unrelated work is not included in the evidence scope.

**Existing test locations:** [Architecture review checklist](checklists/architecture-review.md#L194), [original independent tests](spec.md#L18), and [CI definition](../../.github/workflows/ci.yml#L446) are the existing future review/execution surfaces. They are not current run receipts. No matching execution artifacts were found in this feature's records or scoped attestations/testing/CI documentation searches.

**Future commands/prerequisites:** After all document corrections, with Node/npx, Python 3.12, the agreed hash tool, and pinned lychee available, run the corrected six docs-arch checks and new document regression tests. Human acceptance needs actual AIIMS/Azure-familiar participants; record outcomes rather than inferring them. All product/cloud/deployment commands require separate authorization and are unnecessary here.

**Objective acceptance:** Every execution or human-acceptance claim has trustworthy SHA-bound evidence; unresolved items remain explicitly open; all applicable 26-FR/8-SC/amendment review gates have a truthful disposition and the 60-minute orientation outcome is measured, not assumed.

## Requirement Coverage

Each row assesses the complete requirement, including its subclauses. Evidence of a static definition does not establish its execution. There are **26 FR rows and 8 SC rows**.

| Requirement | Status | Existing Evidence and Assessment | Follow-up IDs |
| --- | --- | --- | --- |
| [FR-001](spec.md#L146) | IMPLEMENTED | [Index](../../docs/architecture/README.md#L1) reaches all 40 architecture pages within two local Markdown hops in the read-only inventory. Broken outgoing links are separately covered by FR-021(b). | AUD-011 |
| [FR-002](spec.md#L147) | IMPLEMENTED | [Six persona sections](../../docs/architecture/README.md#L11) include EXP-01; its [related link](../../docs/architecture/accessibility/ops-dashboard-user-journey.md#L41) reaches WCAG within two hops. Content adequacy is assessed below. | AUD-021 |
| [FR-003](spec.md#L148) | CONFLICT | [Typical page metadata](../../docs/architecture/c4/component-api.md#L1) exists, but motivating specs are not linked; text-only WCAG/registry/capacity and legacy Mermaid treatment conflict with the universal wording and [RQ-10](research.md#L210). | AUD-017 |
| [FR-004](spec.md#L149) | PARTIAL | [C4 pages](../../docs/architecture/README.md#L36) and auxiliary views exist, but component relationships, current topology, and capacity/governance evidence are incomplete. L4 is explicitly deferred. | AUD-007, AUD-015, AUD-016, AUD-017 |
| [FR-005](spec.md#L150) | PARTIAL | All six old files remain with index links; [legacy Cosmos redirect](../../docs/architecture/cosmos-partitioning.md#L16) is explicit. [Index legacy entries](../../docs/architecture/README.md#L73) are not a complete consistent redirect policy, and migration refs are not actionable. | AUD-013, AUD-017 |
| [FR-006](spec.md#L154) | PARTIAL | All named source files exist, but [recovery XML](../../docs/architecture/sequence/recovery-transition.drawio#L16) is invalid; retained [Mermaid sequences](../../docs/architecture/sequence/monitoring-risk-comms.md#L17) need a resolved exception/transition policy. | AUD-008, AUD-017 |
| [FR-007](spec.md#L155) | IMPLEMENTED | All 34 source files have same-directory/base-name PNG siblings; [manifest](../../docs/architecture/.diagram-hashes#L1) records their sources. This status is pairing presence, not export fidelity or DPI proof. | AUD-008, AUD-010 |
| [FR-008](spec.md#L156) | MISSING | Scoped named-source style inspection finds generic service boxes, including [DEPLOY-02](../../docs/architecture/deployment/azure-resource-topology.drawio#L7); no Azure-stencil replacement was found. | AUD-009 |
| [FR-009](spec.md#L157) | PARTIAL | [SEQ-01](../../docs/architecture/sequence/alert-approval-publication.drawio#L1) and [EXP-01](../../docs/architecture/accessibility/ops-dashboard-user-journey.drawio#L1) show distinct gates; [SEQ-05](../../docs/architecture/sequence/audit-provenance.drawio#L16) conflates rejection/actuation and other public-output views lack a complete gate path. | AUD-001, AUD-007, AUD-014 |
| [FR-010](spec.md#L158) | PARTIAL | All six sequence basenames exist. Author/approve/publish and cross-agency shapes exist; evacuation names, recovery flow, audit rejection, and fidelity are defective. [Graceful-degradation table](../../docs/architecture/sequence/graceful-degradation.md#L21) is authored guidance, not tested outage evidence. | AUD-001, AUD-008, AUD-014 |
| [FR-011](spec.md#L162) | PARTIAL | [Blanket comments](../../docs/architecture/README.md#L84) create lexical coverage, not substantive spec homes; [inventory](../../tools/lint/check_spec_cross_refs.py#L23) does not require missing 002 or bound newer prefixes. | AUD-012 |
| [FR-012](spec.md#L163) | PARTIAL | Page-level spec tokens are widespread but several are topic-wrong, such as [ingest citing 035](../../docs/architecture/c4/component-ingest.md#L7) and [tenancy citing 015](../../docs/architecture/data/multi-jurisdiction-tenancy.md#L7). | AUD-012, AUD-017 |
| [FR-013](spec.md#L164) | IMPLEMENTED | [OPS-01 source](../../docs/architecture/operational/aiims-system-context.drawio#L1) and [role list](../../docs/architecture/operational/aiims-system-context.md#L19) contain all ten named actors; PNG interaction lines are visible. Authority correctness is separate. | AUD-004, AUD-008 |
| [FR-014](spec.md#L165) | PARTIAL | [SECTOR-03](../../docs/architecture/data/integration-point-map.drawio#L1) includes BoM/GA/NEMA and generic state sources but wrong/generic consumers and endpoints; [worker](../../apps/ingestion/worker.py#L208) does not establish depicted persistence. | AUD-006, AUD-003 |
| [FR-015](spec.md#L166) | CONFLICT | [Nine jurisdiction labels](../../docs/architecture/data/multi-jurisdiction-tenancy.drawio#L1) exist, but fixed tenant/lead semantics conflict with [scope resolution](../../apps/api/app/middleware/tenant_middleware.py#L47) and [hazard routing](../../apps/api/app/services/simulation/jurisdiction_routing.py#L68). | AUD-002, AUD-019 |
| [FR-016](spec.md#L170) | PARTIAL | [SEC-01 source](../../docs/architecture/security/au-residency-data-classification.drawio#L7) has the AU boundary, required resources, redaction node, and exact zero-entry mechanism label matching [registry](../../infra/parameters/foundry-carveout.yaml#L21). Export overlap and universal gateway claims prevent full assurance. | AUD-003, AUD-008, AUD-009 |
| [FR-017](spec.md#L171) | CONFLICT | [Matrix](../../docs/architecture/security/rbac-matrix.drawio#L55) conflicts with [registry](../../apps/api/app/auth/rbac_registry.py#L57); no per-role spec citation column exists. | AUD-004 |
| [FR-018](spec.md#L172) | CONFLICT | [Trust edge labels](../../docs/architecture/security/trust-boundary.drawio#L52) include an incorrect browser Managed Identity path and omit a consuming agent. | AUD-005 |
| [FR-019](spec.md#L173) | PARTIAL | [Six objective rows](../../docs/architecture/security/sli-slo-model.md#L24) omit four catalogue services and conflict with [burn thresholds](../../docs/observability/slo.md#L125). | AUD-016 |
| [FR-020](spec.md#L174) | PARTIAL | [Evidence/audience table](../../docs/architecture/sequence/audit-provenance.md#L27) exists; rejection flow, mounted publication logging, and downstream acknowledgements are not established by the [helper-shaped test](../../tests/integration/test_human_approval_preserved.py#L71). | AUD-001, AUD-008 |
| [FR-021](spec.md#L178) | PARTIAL | [docs-arch](../../.github/workflows/ci.yml#L446) defines pairing, links, hashes, citations, and gaps; (a) pairing is wired, (b) target filtering is incomplete, (c) citation collection is bypassable, (d) manifest membership/export integrity is incomplete. | AUD-010, AUD-011, AUD-012, AUD-013 |
| [FR-022](spec.md#L179) | CONFLICT | [npx invocation](../../.github/workflows/ci.yml#L474) is correct, but [C4 file-local disable](../../docs/architecture/c4/system.md#L19) violates no-feature-exception wording. A clean lint run is unverified. | AUD-017, AUD-022 |
| [FR-023](spec.md#L180) | PARTIAL | [Registry headers/eleven rows](../../docs/architecture/known-gaps.md#L8) exist, but references are not reliably resolvable and [parser](../../tools/lint/check_known_gaps.py#L40) accepts empty/unrecognized content and formatted placeholders. | AUD-013 |
| [FR-024](spec.md#L184) | PARTIAL | [Agent phase bars](../../docs/architecture/operational/pprr-phase-overlay.drawio#L8) exist; AIIMS roles and labelled overlaps are missing on the diagram. | AUD-018 |
| [FR-025](spec.md#L185) | PARTIAL | [Five tier labels](../../docs/architecture/quality/test-pyramid.drawio#L12) exist, but geometry does not render as a pyramid and tooling/count semantics are incomplete. | AUD-008, AUD-020 |
| [FR-026](spec.md#L186) | PARTIAL | [Five-step journey](../../docs/architecture/accessibility/ops-dashboard-user-journey.drawio#L1) has a gate and WCAG notes, but no cognitive/feature-SC component mapping or publication/audit completion. | AUD-021 |
| [SC-001](spec.md#L203) | UNVERIFIED | [Index](../../docs/architecture/README.md#L1) is navigable; no timed participant answers/source-SHA receipt supports the 60-minute outcome. | AUD-007, AUD-022 |
| [SC-002](spec.md#L204) | PARTIAL | All six clusters reach diagrams within two hops, but [tenancy](../../docs/architecture/data/multi-jurisdiction-tenancy.md#L16), security, build, and experience answers are incomplete/contradicted. | AUD-002, AUD-004, AUD-007, AUD-015, AUD-021 |
| [SC-003](spec.md#L205) | UNVERIFIED | [SEC-01](../../docs/architecture/security/au-residency-data-classification.drawio#L7) contains the three requested concepts; no trusted compliance-review record establishes single-page success, and export labels overlap. | AUD-003, AUD-008, AUD-022 |
| [SC-004](spec.md#L206) | UNVERIFIED | [CI definition](../../.github/workflows/ci.yml#L446) is not a run receipt; one [broken link](../../docs/architecture/known-gaps.md#L4) and incomplete checks contradict blanket green assertions. | AUD-010, AUD-011, AUD-012, AUD-022 |
| [SC-005](spec.md#L207) | PARTIAL | [Citation tokens](../../docs/architecture/README.md#L84) cover all numbers lexically but lack meaningful/verified homes; no trustworthy CI execution receipt establishes 100% substantive coverage. | AUD-012, AUD-022 |
| [SC-006](spec.md#L208) | UNVERIFIED | Distinct markers exist on several named actuation images, but [manual roll-up](checklists/architecture-review.md#L199) is not signed off and rejection/other action-path defects remain. | AUD-001, AUD-014, AUD-022 |
| [SC-007](spec.md#L209) | PARTIAL | All 32 named pairs plus two later roadmap pairs exist. [No inventory gate](../../.github/workflows/ci.yml#L489), malformed/export defects, and optional-L4 versus four-level wording prevent full satisfaction. | AUD-008, AUD-010, AUD-017, AUD-020 |
| [SC-008](spec.md#L249) | PARTIAL | Eleven seed gaps have nonempty raw text refs, but [tracking](../../docs/architecture/known-gaps.md#L10) is not actionable and missing fallback/individual spec gaps remain. | AUD-013 |

### Unnumbered Constraints

These are not added to the 34-requirement denominator.

| Constraint | Status | Evidence and Disposition | Follow-up IDs |
| --- | --- | --- | --- |
| CI completes within 10 minutes | UNVERIFIED | [Job timeout](../../.github/workflows/ci.yml#L448) is configured; no execution duration receipt was found. | AUD-022 |
| Stdlib Python 3.12 linters with `--root` | IMPLEMENTED | [Cross-ref CLI](../../tools/lint/check_spec_cross_refs.py#L74), [gap CLI](../../tools/lint/check_known_gaps.py#L20), and [Python setup](../../.github/workflows/ci.yml#L452) exist; no third-party imports in either linter. | AUD-012, AUD-013 |
| Same push/PR triggers, no path filter, no quality dependency | IMPLEMENTED | [Workflow triggers](../../.github/workflows/ci.yml#L3) and [standalone docs-arch job](../../.github/workflows/ci.yml#L446) implement these static constraints. External required-check configuration is unverified. | AUD-022 |
| PNG 150 DPI and white background | PARTIAL | Every PNG lacks recorded density metadata; several are transparent. [Export instructions](quickstart.md#L79) cannot substitute for provenance. | AUD-008 |
| View-type layout; original file locations retained | IMPLEMENTED | [Index paths](../../docs/architecture/README.md#L15) and [legacy redirect](../../docs/architecture/cosmos-partitioning.md#L16) preserve the observed layout/old files. | AUD-017 |
| Documentation-only; no redeployment needed | UNVERIFIED | [T073](tasks.md#L219) is a historical claim without its diff/receipt; no deployment was performed in this audit, and none is needed to fix documentation. | AUD-022 |

## Acceptance Scenario Coverage

### Numbered Scenarios

| Scenario | Status | Existing Evidence and Assessment | Follow-up IDs |
| --- | --- | --- | --- |
| [US1.1](spec.md#L22) | PARTIAL | All pairs exist; [known-gaps](../../docs/architecture/known-gaps.md#L4) has a broken outgoing link and [recovery source](../../docs/architecture/sequence/recovery-transition.drawio#L16) is invalid. Fresh-clone execution was not performed. | AUD-008, AUD-011 |
| [US1.2](spec.md#L23) | PARTIAL | [Six cluster sections](../../docs/architecture/README.md#L11) satisfy two-hop navigation; question-answer adequacy is limited by inaccurate sector/security/build views. | AUD-002, AUD-007, AUD-015, AUD-021 |
| [US1.3](spec.md#L24) | PARTIAL | [System diagram](../../docs/architecture/c4/system.drawio#L1) has no complete human-gate trace; [SEQ-05](../../docs/architecture/sequence/audit-provenance.drawio#L16) sends rejection toward execution. | AUD-001, AUD-007 |
| [US2.1](spec.md#L38) | PARTIAL | [SEQ-01](../../docs/architecture/sequence/alert-approval-publication.drawio#L1) orders author/approve/publish correctly as a drawing; [mounted service](../../apps/api/app/services/public_alert_service.py#L48) contradicts its enforcement implication. | AUD-001, AUD-008 |
| [US2.2](spec.md#L39) | IMPLEMENTED | [Escalation drawing](../../docs/architecture/operational/escalation-paths.drawio#L1) and [summary](../../docs/architecture/operational/escalation-paths.md#L21) label triggers, roles, and actions for L1/L2/L3. No runtime transition success is implied. | AUD-008 |
| [US2.3](spec.md#L40) | IMPLEMENTED | [Six-subsystem table](../../docs/architecture/sequence/graceful-degradation.md#L21) and [drawing](../../docs/architecture/sequence/graceful-degradation.drawio#L1) explicitly state degrades/remains/fallback for each named subsystem; actual outage behavior remains unverified. | AUD-008, AUD-022 |
| [US2.4](spec.md#L41) | IMPLEMENTED | [OPS-01](../../docs/architecture/operational/aiims-system-context.drawio#L1) includes all seven requested actors and the additional three, with visible interactions in the PNG. | AUD-004, AUD-008 |
| [US3.1](spec.md#L55) | CONFLICT | [NSW/VIC boundaries](../../docs/architecture/data/multi-jurisdiction-tenancy.drawio#L1) exist but disagree with [physical signals keys](../../infra/main.bicep#L616) and [tenant semantics](../../apps/api/app/middleware/tenant_middleware.py#L47). | AUD-002 |
| [US3.2](spec.md#L56) | PARTIAL | [SECTOR-02](../../docs/architecture/data/ingestion-data-flow.drawio#L1) draws the broad path, but not an actual named consumer or reachable worker persistence. | AUD-006 |
| [US3.3](spec.md#L57) | PARTIAL | [Integration map](../../docs/architecture/data/integration-point-map.drawio#L1) labels BoM/GA/NEMA formats but uses generic intake endpoints and noncanonical agent names. | AUD-006 |
| [US3.4](spec.md#L58) | CONFLICT | [RFS/SES/welfare drawing](../../docs/architecture/data/jurisdiction-filter.drawio#L1) offers field-subset authority claims without controlling rule references and does not identify two state jurisdictions. | AUD-002, AUD-019 |
| [US4.1](spec.md#L72) | IMPLEMENTED | [C4-L1](../../docs/architecture/c4/system.drawio#L1) names BoM, GA, NEMA, state CAP/EDXL sources, and browser/mobile client. | AUD-008, AUD-009 |
| [US4.2](spec.md#L73) | PARTIAL | [L2](../../docs/architecture/c4/container.drawio#L1) lacks App Insights and names only an aggregate five-agent runtime, with inconsistent Mermaid additions. | AUD-007 |
| [US4.3](spec.md#L74) | PARTIAL | [API L3](../../docs/architecture/c4/component-api.drawio#L1), [Web L3](../../docs/architecture/c4/component-web.drawio#L1), and [Agents L3](../../docs/architecture/c4/component-agents.drawio#L1) do not trace the required request/return path across containers. | AUD-007 |
| [US4.4](spec.md#L75) | IMPLEMENTED | [ADR index](../../docs/architecture/adr/README.md#L7) lists all 18 currently existing canonical ADR files with number/title/status/date/spec/path; status text includes an honest stub. It is not proof of human acceptance. | AUD-017, AUD-022 |
| [US4.5](spec.md#L76) | PARTIAL | [WAF table](../../docs/architecture/governance/waf-pillar-mapping.md#L22) covers five pillars but has no per-pillar links to specs/diagrams, and the drawing maps every pillar to one undifferentiated component box. | AUD-012, AUD-017 |
| [US5.1](spec.md#L90) | PARTIAL | [SEC-01](../../docs/architecture/security/au-residency-data-classification.drawio#L7) shows AU/carve-out/gateway, but current AU inference versus conditional egress and actual client bypasses are not accurately distinguished. | AUD-003, AUD-008 |
| [US5.2](spec.md#L91) | CONFLICT | [RBAC cells](../../docs/architecture/security/rbac-matrix.drawio#L55) disagree with [enforcement](../../apps/api/app/auth/rbac_registry.py#L57) and lack per-role spec links. | AUD-004 |
| [US5.3](spec.md#L92) | CONFLICT | [Trust diagram](../../docs/architecture/security/trust-boundary.drawio#L52) has unsupported authentication labels and stops short of an agent consumer. | AUD-005, AUD-006 |
| [US5.4](spec.md#L93) | PARTIAL | [SEC-04](../../docs/architecture/security/sli-slo-model.md#L24) has partial objectives and windows, but omitted catalogue services and conflicting thresholds prevent per-key-service coverage. | AUD-016 |
| [US6.1](spec.md#L107) | CONFLICT | [What-if/manual/promotion drawing](../../docs/architecture/deployment/cicd-pipeline.drawio#L1) differs from [current CD](../../.github/workflows/cd.yml#L19). Remote environment approvals are unverified. | AUD-015 |
| [US6.2](spec.md#L108) | CONFLICT | [DEPLOY-02 source](../../docs/architecture/deployment/azure-resource-topology.drawio#L7) lists all task names, but the PNG obscures the group label and current CD selects different environment-derived groups/names. | AUD-008, AUD-015 |
| [US6.3](spec.md#L109) | CONFLICT | [Forward-authoritative partition table](../../docs/architecture/deployment/cosmos-partitioning.md#L25) disagrees with [signals IaC](../../infra/main.bicep#L616). | AUD-002 |
| [US6.4](spec.md#L110) | PARTIAL | Bicep dependency graph is explicitly deferred in [known gaps](../../docs/architecture/known-gaps.md#L10); no equivalent delivered graph was found. The issue-creation form is not a resolved follow-up. | AUD-013, AUD-015 |
| [US7.1](spec.md#L124) | IMPLEMENTED | [Two explicit pairing loops](../../.github/workflows/ci.yml#L489) fail on missing siblings and are wired in docs-arch. This is source-defined behavior, not an executed CI result. | AUD-010, AUD-022 |
| [US7.2](spec.md#L125) | PARTIAL | [Target filter](../../.github/workflows/ci.yml#L482) can omit repository-local targets and [known-gaps link](../../docs/architecture/known-gaps.md#L4) is broken. | AUD-011 |
| [US7.3](spec.md#L126) | PARTIAL | [Checker](../../tools/lint/check_spec_cross_refs.py#L23) deduplicates prefixes but accepts spurious citations and ambiguous exclusions. | AUD-012, AUD-013 |

### Independent Tests

| Independent Test | Status | Evidence Assessment | Follow-up IDs |
| --- | --- | --- | --- |
| [US1 orientation](spec.md#L18) | UNVERIFIED | No timed new-joiner answer sheet; index/source inspection is not a 60-minute participant exercise. | AUD-022 |
| [US2 one-page alert flow](spec.md#L34) | UNVERIFIED | Existing [PNG](../../docs/architecture/sequence/alert-approval-publication.png) is viewable; no qualified reviewer receipt proves acceptance of its safety semantics. | AUD-001, AUD-022 |
| [US3 tenancy and signal path](spec.md#L51) | UNVERIFIED | Existing data pages are authored, but no trustworthy reviewer record establishes correctness against actual isolation/persistence. | AUD-002, AUD-006, AUD-022 |
| [US4 C4 navigation](spec.md#L68) | UNVERIFIED | Static two-hop reachability exists via the index; no complete application-by-application L1/L2/L3 review result is checked in. | AUD-007, AUD-022 |
| [US5 auditor page](spec.md#L86) | UNVERIFIED | The local persona synthesis asserts success but does not identify an auditor/source SHA or completed checklist. | AUD-003, AUD-022 |
| [US6 release/topology questions](spec.md#L103) | UNVERIFIED | Historical labels and current workflow disagree; no reviewer question/answer record resolves them. | AUD-015, AUD-022 |
| [US7 docs-arch run](spec.md#L120) | UNVERIFIED | Job code and unsourced green claims are present; no exact-run/exit/output receipt for this revision was found or generated. | AUD-010, AUD-011, AUD-012, AUD-022 |

### Edge Cases

| Edge Case | Status | Existing Evidence and Assessment | Follow-up IDs |
| --- | --- | --- | --- |
| [Archived/duplicate numbers](spec.md#L132) | PARTIAL | [DUPE-036 row](../../docs/architecture/known-gaps.md#L11) and prefix set handle duplication mechanically; 002 absence and actual archive semantics are not explicitly resolved. | AUD-012, AUD-013 |
| [Source/PNG mismatch](spec.md#L133) | PARTIAL | [Source hashes](../../docs/architecture/.diagram-hashes#L1) match current bytes but do not bind the rendered PNG; recovery demonstrates divergence, and omitted entries are not discovered. | AUD-008, AUD-010 |
| [Pre-existing sparse documents](spec.md#L134) | PARTIAL | Six original files remain and link back; [Cosmos root copy](../../docs/architecture/cosmos-partitioning.md#L16) is explicitly superseded by the deployment page. Remaining stale diagrams/contracts and unresolvable migration refs persist. | AUD-002, AUD-007, AUD-013, AUD-017 |
| [Spec without a natural home](spec.md#L135) | CONFLICT | [SPEC-037 and batched range gaps](../../docs/architecture/known-gaps.md#L16) remain open, while [blanket comments](../../docs/architecture/README.md#L84) satisfy the checker without a substantive home. | AUD-012, AUD-013 |
| [Foundry carve-out accuracy](spec.md#L136) | PARTIAL | Zero active non-AU entries match [registry](../../infra/parameters/foundry-carveout.yaml#L21); [C4 Phi text](../../docs/architecture/c4/system.md#L53) and gateway guarantees need reconciliation. | AUD-003 |

## Original Task Coverage

Each original task has exactly one row; no ID ranges are used. Every state below is the original `[X]`, not an audit checkbox. Diagram-pair rows assess content/source/export obligations, not merely sibling existence. Page rows marked IMPLEMENTED mean the requested task-local authored page/metadata exists; shared link, accuracy, visual, and review obligations are explicitly retained in the follow-up column and requirement tables. Executed gates remain UNVERIFIED without a receipt.

| Original Task | Original State | Status | Concrete Existing Source/Test Evidence and Static Disposition | Follow-up IDs |
| --- | --- | --- | --- | --- |
| [T001](tasks.md#L21) | [X] | IMPLEMENTED | Required view directories contain delivered files, e.g. [operational page](../../docs/architecture/operational/aiims-system-context.md#L1), [ADR index](../../docs/architecture/adr/README.md#L1), and [linter](../../tools/lint/check_known_gaps.py#L1); empty-directory tracking is no longer needed. | None |
| [T002](tasks.md#L22) | [X] | CONFLICT | [Manifest](../../docs/architecture/.diagram-hashes#L1) exists but has no format header and now uses root-relative, digest-sorted entries rather than the contracted initial convention; historical empty initialization is unverified. | AUD-010, AUD-022 |
| [T003](tasks.md#L32) | [X] | UNVERIFIED | [Local green narrative](review/persona-review.md#L76) has no pre-flight output; [C4 suppression](../../docs/architecture/c4/system.md#L19) prevents inferring unexcepted baseline compliance. | AUD-017, AUD-022 |
| [T004](tasks.md#L33) | [X] | PARTIAL | [Eleven seed rows](../../docs/architecture/known-gaps.md#L10) exist with nonempty raw refs, but the issue form/fragments do not reliably track actionable future work. | AUD-013 |
| [T005](tasks.md#L49) | [X] | CONFLICT | [Current nonempty manifest](../../docs/architecture/.diagram-hashes#L1) cannot prove an empty-baseline check; the requested zero-entry success criterion is not a valid verification receipt. | AUD-010, AUD-022 |
| [T006](tasks.md#L63) | [X] | CONFLICT | [SEQ-03 source](../../docs/architecture/sequence/evacuation-five-stage.drawio#L1) and PNG exist with a visible gate, but [canonical stage assertions](../../tests/unit/test_evacuation_stages.py#L20) disagree with its substituted stages. | AUD-008, AUD-014 |
| [T007](tasks.md#L64) | [X] | PARTIAL | [Recovery source](../../docs/architecture/sequence/recovery-transition.drawio#L16) is malformed; PNG exists but lacks transition arrows and roles. | AUD-008, AUD-014 |
| [T008](tasks.md#L65) | [X] | CONFLICT | [Page](../../docs/architecture/sequence/evacuation-five-stage.md#L1) has purpose/persona/spec tokens/image/banner, but [stage list](../../docs/architecture/sequence/evacuation-five-stage.md#L27) contradicts the domain lifecycle. | AUD-014, AUD-017 |
| [T009](tasks.md#L66) | [X] | PARTIAL | [Page](../../docs/architecture/sequence/recovery-transition.md#L1) is authored; its promised transition is not supported by the embedded three-box export. | AUD-008, AUD-014, AUD-017 |
| [T010](tasks.md#L67) | [X] | PARTIAL | [Six-section index](../../docs/architecture/README.md#L11) links all diagram pages, but [forthcoming note](../../docs/architecture/README.md#L9) remains and blanket tokens mask coverage gaps. | AUD-011, AUD-012, AUD-017 |
| [T011](tasks.md#L81) | [X] | PARTIAL | [SEQ-01 source](../../docs/architecture/sequence/alert-approval-publication.drawio#L1) has ordered author/gate/publish; export is transparent, 150-DPI provenance is absent, and [publish service](../../apps/api/app/services/public_alert_service.py#L48) contradicts the guarantee. | AUD-001, AUD-008 |
| [T012](tasks.md#L82) | [X] | PARTIAL | [SEQ-02 source](../../docs/architecture/sequence/cross-agency-recommendation.drawio#L1) and PNG show approved-only execution; authoring/export provenance and actual actuation enforcement are not established. | AUD-001, AUD-008, AUD-022 |
| [T013](tasks.md#L83) | [X] | PARTIAL | [Six subsystem/fallback nodes](../../docs/architecture/sequence/graceful-degradation.drawio#L1) exist; PNG connector paths cross labels and export settings are unverified. | AUD-008 |
| [T014](tasks.md#L84) | [X] | PARTIAL | [Ten-role source](../../docs/architecture/operational/aiims-system-context.drawio#L1) and PNG interactions exist; export background/provenance requirements are incomplete and authority correctness is separate. | AUD-004, AUD-008 |
| [T015](tasks.md#L85) | [X] | PARTIAL | [Escalation source](../../docs/architecture/operational/escalation-paths.drawio#L1) shows L1/L2/L3 triggers/roles/actions and acceptance note; export/tooling provenance is unverified. | AUD-008, AUD-022 |
| [T016](tasks.md#L86) | [X] | PARTIAL | [Page metadata and gate notes](../../docs/architecture/sequence/alert-approval-publication.md#L1) exist; approved-only prose conflicts with [reachable publication](../../apps/api/app/services/public_alert_service.py#L48). | AUD-001, AUD-017 |
| [T017](tasks.md#L87) | [X] | IMPLEMENTED | [Page](../../docs/architecture/sequence/cross-agency-recommendation.md#L1) has requested audience, spec tokens, embed, FR notes, and index banner. Execution assurance remains separate. | AUD-001, AUD-017, AUD-022 |
| [T018](tasks.md#L88) | [X] | IMPLEMENTED | [Page](../../docs/architecture/sequence/graceful-degradation.md#L1) includes requested metadata, image, index, and concrete degrades/remains/fallback table. No outage execution is established. | AUD-008, AUD-017, AUD-022 |
| [T019](tasks.md#L89) | [X] | IMPLEMENTED | [Key Elements](../../docs/architecture/operational/aiims-system-context.md#L19) names all ten roles with audience/spec/image/banner present. | AUD-004, AUD-017 |
| [T020](tasks.md#L90) | [X] | IMPLEMENTED | [Escalation page](../../docs/architecture/operational/escalation-paths.md#L1) includes the requested metadata and level/trigger/role/action table. | AUD-008, AUD-017 |
| [T021](tasks.md#L104) | [X] | CONFLICT | [SECTOR-01 source](../../docs/architecture/data/multi-jurisdiction-tenancy.drawio#L1) labels 8+1 jurisdictions but wrong uniform `/tenant_id` semantics and fixed leads; no Cosmos Azure stencil. | AUD-002, AUD-008, AUD-009 |
| [T022](tasks.md#L105) | [X] | PARTIAL | [SECTOR-02 source](../../docs/architecture/data/ingestion-data-flow.drawio#L1) shows a broker/store/runtime chain but lacks canonical consumers and matches neither polling/persistence wiring nor stencil requirements. | AUD-006, AUD-008, AUD-009 |
| [T023](tasks.md#L106) | [X] | PARTIAL | [SECTOR-03 source](../../docs/architecture/data/integration-point-map.drawio#L1) labels formats/endpoints but uses noncanonical agents and generic state sources. | AUD-006, AUD-008 |
| [T024](tasks.md#L107) | [X] | CONFLICT | [Filter source](../../docs/architecture/data/jurisdiction-filter.drawio#L1) cites 022 and names RFS/SES/welfare, but unsupported field-authority claims are not a trace of actual cross-state policy. | AUD-002, AUD-008, AUD-019 |
| [T025](tasks.md#L108) | [X] | CONFLICT | [Page](../../docs/architecture/data/multi-jurisdiction-tenancy.md#L16) meets metadata shape but asserts partition semantics contradicted by [signals IaC](../../infra/main.bicep#L616). | AUD-002, AUD-012, AUD-017 |
| [T026](tasks.md#L109) | [X] | PARTIAL | [Page](../../docs/architecture/data/ingestion-data-flow.md#L21) claims normalization/persistence/consumption without [worker repository injection](../../apps/ingestion/worker.py#L208). | AUD-006, AUD-012, AUD-017 |
| [T027](tasks.md#L110) | [X] | PARTIAL | [Page](../../docs/architecture/data/integration-point-map.md#L19) claims all systems and consuming ownership but supplies no actual endpoint/agent mapping. | AUD-006, AUD-012, AUD-017 |
| [T028](tasks.md#L111) | [X] | PARTIAL | [Page](../../docs/architecture/data/jurisdiction-filter.md#L11) contains the requested annotation and image, but actual filter/authority rules and two-state scope are unsupported. | AUD-002, AUD-017, AUD-019 |
| [T029](tasks.md#L125) | [X] | PARTIAL | [L1 source](../../docs/architecture/c4/system.drawio#L1) contains required external actors; Azure nodes are generic and export background/provenance incomplete. | AUD-007, AUD-008, AUD-009 |
| [T030](tasks.md#L126) | [X] | PARTIAL | [L2 source](../../docs/architecture/c4/container.drawio#L1) lacks App Insights and individual five-agent names; generic Azure shapes and conflicting Mermaid topology remain. | AUD-007, AUD-008, AUD-009 |
| [T031](tasks.md#L127) | [X] | PARTIAL | [API L3](../../docs/architecture/c4/component-api.drawio#L1) labels router/middleware/handlers but not boundary/service/agent round-trip or current middleware order. | AUD-007, AUD-008 |
| [T032](tasks.md#L128) | [X] | PARTIAL | [Web L3](../../docs/architecture/c4/component-web.drawio#L1) labels pages/components but generic API/state nodes and crossed labels do not supply source-grounded request/response relationships. | AUD-007, AUD-008 |
| [T033](tasks.md#L129) | [X] | PARTIAL | [Agents L3](../../docs/architecture/c4/component-agents.drawio#L1) names five business agents plus Dependency Notifier and services; actual gateway/return path and Azure stencils are absent. | AUD-003, AUD-007, AUD-008, AUD-009 |
| [T034](tasks.md#L130) | [X] | PARTIAL | [Ingest L3](../../docs/architecture/c4/component-ingest.drawio#L1) names three formats but its only terminal path is dead-letter handling, not configured success persistence/routing. | AUD-006, AUD-007, AUD-008, AUD-009 |
| [T035](tasks.md#L131) | [X] | PARTIAL | [WAF source](../../docs/architecture/governance/waf-pillar-mapping.drawio#L1) names all five pillars but maps them to one generic components/specs pair rather than distinct supported mappings. | AUD-008, AUD-012, AUD-017 |
| [T036](tasks.md#L132) | [X] | IMPLEMENTED | [API component page](../../docs/architecture/c4/component-api.md#L1) contains required metadata, image, index, and L1/L2 related links; content/source-link obligations remain. | AUD-007, AUD-017 |
| [T037](tasks.md#L133) | [X] | IMPLEMENTED | [Web component page](../../docs/architecture/c4/component-web.md#L1) contains both personas, spec-020 token, embed, and index banner. | AUD-007, AUD-017 |
| [T038](tasks.md#L134) | [X] | IMPLEMENTED | [Agents component page](../../docs/architecture/c4/component-agents.md#L1) contains requested spec tokens, image, and index link. | AUD-003, AUD-007, AUD-017 |
| [T039](tasks.md#L135) | [X] | PARTIAL | [Ingest component page](../../docs/architecture/c4/component-ingest.md#L1) exists but repeats mismapped spec-035 and embeds an incomplete ingest path. | AUD-006, AUD-007, AUD-012, AUD-017 |
| [T040](tasks.md#L136) | [X] | PARTIAL | [WAF page](../../docs/architecture/governance/waf-pillar-mapping.md#L20) has five rows but repeats generic spec-015/028 refs without navigable pillar-specific evidence. | AUD-012, AUD-017 |
| [T041](tasks.md#L137) | [X] | PARTIAL | [Retained system page](../../docs/architecture/c4/system.md#L1) has new metadata/embed/banner, but local MD041 disable and contradictory old topology remain. | AUD-003, AUD-007, AUD-017 |
| [T042](tasks.md#L138) | [X] | PARTIAL | [Retained container page](../../docs/architecture/c4/container.md#L1) has required additions but local lint disable, old networking/hosting claims, and no direct application-L3 navigation. | AUD-007, AUD-015, AUD-017 |
| [T043](tasks.md#L139) | [X] | IMPLEMENTED | [ADR index](../../docs/architecture/adr/README.md#L7) includes all 18 canonical files and metadata; [ADR-20](../../docs/decisions/036-foundry-rag-grounding/20-hard-cutover-foundry-foundation.md#L7) preserves supersession semantics. No ADR relocation found. | AUD-017, AUD-022 |
| [T044](tasks.md#L153) | [X] | PARTIAL | [SEC-01 source](../../docs/architecture/security/au-residency-data-classification.drawio#L7) contains required resources and exact zero-non-AU zone; source/PNG overlap, missing stencils, and gateway accuracy remain. | AUD-003, AUD-008, AUD-009 |
| [T045](tasks.md#L154) | [X] | CONFLICT | [RBAC matrix](../../docs/architecture/security/rbac-matrix.drawio#L55) has ten roles but false admin/audit cells and no citation column. | AUD-004, AUD-008 |
| [T046](tasks.md#L155) | [X] | CONFLICT | [Trust source](../../docs/architecture/security/trust-boundary.drawio#L52) names mechanisms but wrongly labels browser identity and omits actual feed-to-agent path and stencils. | AUD-005, AUD-008, AUD-009 |
| [T047](tasks.md#L156) | [X] | PARTIAL | [SLI diagram](../../docs/architecture/security/sli-slo-model.drawio#L7) has six service summaries but lacks four key catalogue controls and supported window/threshold mappings. | AUD-008, AUD-016 |
| [T048](tasks.md#L157) | [X] | PARTIAL | [Audit source](../../docs/architecture/sequence/audit-provenance.drawio#L16) has gate/log/evidence/reviewers, but reject-to-actuation and overlapping export labels contradict intended provenance. | AUD-001, AUD-008 |
| [T049](tasks.md#L158) | [X] | PARTIAL | [WCAG page](../../docs/architecture/accessibility/wcag-coverage.md#L18) is the requested text-only table and defers full audit, yet labels unproven whole-UI contrast/keyboard claims Implemented. | AUD-017, AUD-021 |
| [T050](tasks.md#L159) | [X] | IMPLEMENTED | [Residency page](../../docs/architecture/security/au-residency-data-classification.md#L1) has persona/spec annotation/embed and Security pillar notes; runtime/visual qualifications remain separate. | AUD-003, AUD-008, AUD-017 |
| [T051](tasks.md#L160) | [X] | PARTIAL | [RBAC page](../../docs/architecture/security/rbac-matrix.md#L25) has requested metadata but misattributes permission authority and does not reconcile inaccurate cells. | AUD-004, AUD-012, AUD-017 |
| [T052](tasks.md#L161) | [X] | PARTIAL | [Trust page](../../docs/architecture/security/trust-boundary.md#L25) is authored but disagrees with its own browser edge and actual polling source. | AUD-005, AUD-017 |
| [T053](tasks.md#L162) | [X] | PARTIAL | [SLO page](../../docs/architecture/security/sli-slo-model.md#L24) defines terms/rows but omits services and introduces conflicting/unnumeric objectives. | AUD-012, AUD-016, AUD-017 |
| [T054](tasks.md#L163) | [X] | PARTIAL | [Audit page](../../docs/architecture/sequence/audit-provenance.md#L27) supplies evidence/audience table but cannot establish every-actuation capture or correct rejection behavior. | AUD-001, AUD-017, AUD-022 |
| [T055](tasks.md#L177) | [X] | CONFLICT | [CD drawing](../../docs/architecture/deployment/cicd-pipeline.drawio#L1) contains requested gate labels but contradicts [current workflow](../../.github/workflows/cd.yml#L19); no Azure stencils. | AUD-008, AUD-009, AUD-015 |
| [T056](tasks.md#L178) | [X] | CONFLICT | [Topology source](../../docs/architecture/deployment/azure-resource-topology.drawio#L7) contains all historical task resource names; current naming differs, group label is obscured, and mandatory stencils are absent. | AUD-008, AUD-009, AUD-015 |
| [T057](tasks.md#L179) | [X] | CONFLICT | [Partition source](../../docs/architecture/deployment/cosmos-partitioning.drawio#L1) routes to wrong signals key and uses generic Cosmos shapes. | AUD-002, AUD-008, AUD-009 |
| [T058](tasks.md#L180) | [X] | CONFLICT | [CD page stages](../../docs/architecture/deployment/cicd-pipeline.md#L23) repeat obsolete promotion/gate behavior as current. | AUD-015, AUD-017 |
| [T059](tasks.md#L181) | [X] | CONFLICT | [Topology page](../../docs/architecture/deployment/azure-resource-topology.md#L21) lists required names but calls them deployed without a trustworthy current snapshot and contrary to environment-derived naming. | AUD-015, AUD-017, AUD-022 |
| [T060](tasks.md#L182) | [X] | CONFLICT | [Explicit forward-authority note](../../docs/architecture/deployment/cosmos-partitioning.md#L14) exists, but the [partition table](../../docs/architecture/deployment/cosmos-partitioning.md#L25) disagrees with IaC. | AUD-002, AUD-017 |
| [T061](tasks.md#L196) | [X] | PARTIAL | [Stdlib linter](../../tools/lint/check_spec_cross_refs.py#L23) implements CLI/prefix dedup/Resolved parsing, but empty roots, unbounded inventory, and spurious/gap citations yield false assurance; no linter assertions found. | AUD-012 |
| [T062](tasks.md#L197) | [X] | PARTIAL | [Gap linter](../../tools/lint/check_known_gaps.py#L40) validates raw empty/TBD values and CLI exits, but accepts no-row files and formatted placeholders; no feature tests found. | AUD-013 |
| [T063](tasks.md#L198) | [X] | PARTIAL | [docs-arch](../../.github/workflows/ci.yml#L446) has correct triggers/no needs/10-minute timeout/tool setup and all basic checks, but link scope, inventory checks, and root-relative manifest convention differ from advertised guarantees. | AUD-010, AUD-011, AUD-012, AUD-013 |
| [T064](tasks.md#L199) | [X] | UNVERIFIED | [Claimed green review](review/persona-review.md#L76) has no local command receipt; [index tokens](../../docs/architecture/README.md#L84) mean an exit-zero prediction would not establish real homes. | AUD-012, AUD-022 |
| [T065](tasks.md#L200) | [X] | UNVERIFIED | [Eleven rows](../../docs/architecture/known-gaps.md#L10) can satisfy the weak raw-text checker; no trustworthy execution output exists. | AUD-013, AUD-022 |
| [T066](tasks.md#L212) | [X] | PARTIAL | [Retained sequence](../../docs/architecture/sequence/monitoring-risk-comms.md#L1) has audience/spec/banner, but local lint execution and old runtime sequence claims remain unverified/inconsistent. | AUD-007, AUD-017, AUD-022 |
| [T067](tasks.md#L213) | [X] | IMPLEMENTED | [Capacity header](../../docs/architecture/capacity-model.md#L14) adds the requested index/migration note without moving the file; baseline measurement claims and follow-up actionability remain separate. | AUD-013, AUD-016, AUD-017 |
| [T068](tasks.md#L214) | [X] | IMPLEMENTED | [Legacy Cosmos banner](../../docs/architecture/cosmos-partitioning.md#L14) links the index and explicitly redirects to the new authoritative page. That page's accuracy is separately defective. | AUD-002, AUD-013, AUD-017 |
| [T069](tasks.md#L215) | [X] | PARTIAL | [Middleware/offline page](../../docs/architecture/spec-035-middleware-and-offline.md#L14) has requested banner/migration/annotation, but its claimed production ordering contradicts [application registration](../../apps/api/app/main.py#L57). | AUD-007, AUD-013, AUD-017 |
| [T070](tasks.md#L216) | [X] | PARTIAL | [Manifest](../../docs/architecture/.diagram-hashes#L1) contains matching source digests for all current 34 sources, but uses a different path/sort convention; historical 26-entry command success is unverified. | AUD-010, AUD-022 |
| [T071](tasks.md#L217) | [X] | PARTIAL | [Index](../../docs/architecture/README.md#L15) has real links to all named pages; [forthcoming note](../../docs/architecture/README.md#L9), blanket citations, and unverified lint remain. | AUD-011, AUD-012, AUD-017, AUD-022 |
| [T072](tasks.md#L218) | [X] | UNVERIFIED | [Post-flight success prose](review/persona-review.md#L76) is not a five-command receipt; current manifest conventions differ and a local link is broken. No feature checks were executed by this audit. | AUD-010, AUD-011, AUD-017, AUD-022 |
| [T073](tasks.md#L219) | [X] | UNVERIFIED | [No-deployment assertion](review/persona-review.md#L77) exists without the feature's historical scoped diff/commit evidence. The original no-op/no-redeploy boundary is respected by this audit. | AUD-022 |
| [T074](tasks.md#L233) | [X] | PARTIAL | [Risk lifecycle source](../../docs/architecture/operational/risk-register-lifecycle.drawio#L1) names hazards, lifecycle, Risk Manager, IC escalation; Cosmos is generic and the required fallback record/export provenance is absent. | AUD-008, AUD-009, AUD-013 |
| [T075](tasks.md#L234) | [X] | PARTIAL | [PPRR source](../../docs/architecture/operational/pprr-phase-overlay.drawio#L8) has four phases/five agents/footer but lacks named roles, events, explicit overlaps, and fallback record. | AUD-008, AUD-013, AUD-018 |
| [T076](tasks.md#L235) | [X] | PARTIAL | [Cross-sector source](../../docs/architecture/data/cross-sector-touchpoints.drawio#L1) shows protocols but not required fire/SES nodes or per-crossing authority rules; fallback record absent. | AUD-008, AUD-013, AUD-019 |
| [T077](tasks.md#L236) | [X] | PARTIAL | [BUILD-01 source](../../docs/architecture/c4/agent-runtime-llm-gateway.drawio#L1) contains five agents, LLM client, redaction/rate/breaker nodes; actual AU/bypass conditions, Azure stencil, and fallback record are missing. | AUD-003, AUD-008, AUD-009, AUD-013 |
| [T078](tasks.md#L237) | [X] | PARTIAL | [Quality page](../../docs/architecture/quality/test-pyramid.md#L1) establishes the directory and [source](../../docs/architecture/quality/test-pyramid.drawio#L12) has five labels, but its PNG lacks geometry and tooling/count claims/fallback record are incomplete. | AUD-008, AUD-013, AUD-020 |
| [T079](tasks.md#L238) | [X] | PARTIAL | [EXP-01 source](../../docs/architecture/accessibility/ops-dashboard-user-journey.drawio#L1) shows a human gate and WCAG notes, but publication confirmation/audit receipt/cognitive traceability and fallback record are absent. | AUD-008, AUD-013, AUD-021 |
| [T080](tasks.md#L242) | [X] | IMPLEMENTED | [Risk lifecycle page](../../docs/architecture/operational/risk-register-lifecycle.md#L1) has the requested purpose/persona/spec annotation/embed/index and stage/role Key Elements. Runtime risk-register behavior is not established. | AUD-008, AUD-017, AUD-022 |
| [T081](tasks.md#L243) | [X] | PARTIAL | [Page table](../../docs/architecture/operational/pprr-phase-overlay.md#L26) supplies four phases and constitution note, but does not cure the missing role/overlap content on the diagram. | AUD-017, AUD-018 |
| [T082](tasks.md#L244) | [X] | PARTIAL | [Touchpoint table](../../docs/architecture/data/cross-sector-touchpoints.md#L25) exists but generic government leads/incorrect topic citations do not satisfy requested emergency-sector boundaries. | AUD-012, AUD-017, AUD-019 |
| [T083](tasks.md#L245) | [X] | CONFLICT | [Page](../../docs/architecture/c4/agent-runtime-llm-gateway.md#L30) makes universal-redaction and output-HITL-callout claims absent/contradicted in the graph/client; required metadata and related links exist. | AUD-003, AUD-017 |
| [T084](tasks.md#L246) | [X] | PARTIAL | [Test tiers](../../docs/architecture/quality/test-pyramid.md#L25) have five rows but unsupported test counts/tooling, wrong quality-spec attribution, and an invisible pyramid. | AUD-008, AUD-012, AUD-017, AUD-020 |
| [T085](tasks.md#L247) | [X] | PARTIAL | [Journey table](../../docs/architecture/accessibility/ops-dashboard-user-journey.md#L23) has metadata/WCAG/related link, but lacks required completion/SC traceability and falsely states `aria-pressed`. | AUD-017, AUD-021 |
| [T086](tasks.md#L251) | [X] | PARTIAL | [Index amendment links](../../docs/architecture/README.md#L23) and all source hashes are present; [registry](../../docs/architecture/known-gaps.md#L10) lacks all amendment fallback records, format differs, and no five-check execution receipt exists. | AUD-010, AUD-013, AUD-022 |

## Checklist and Review Claims

These assessments concern the historical records themselves, separately from artifact implementation. The review did not alter any original checkbox.

| Record or Claim | Original State | Assessment | Follow-up IDs |
| --- | --- | --- | --- |
| [Specification quality checklist](checklists/requirements.md#L8) | All 16 items checked | Authored spec review, not implementation proof. Its 23-FR count is obsolete after Amendment 1; claims of no implementation details and unambiguous requirements conflict with pinned tool/path requirements and the documented contract conflicts. | AUD-017, AUD-022 |
| [CHK001 to CHK008: navigation/ADR](checklists/architecture-review.md#L13) | All unchecked | Source supports the six sections, all-page two-hop reachability, and 18-file ADR index. The broken outgoing link and incomplete redirect conventions prevent treating the group as signed off. | AUD-011, AUD-017, AUD-022 |
| [CHK009 to CHK015: diagram integrity](checklists/architecture-review.md#L26) | All unchecked | Pair presence and source hashes are supported; valid XML, faithful PNGs, Azure stencils, and count enforcement are not. The checklist still uses 26 rather than the amended named inventory. | AUD-008, AUD-009, AUD-010, AUD-022 |
| [CHK016 to CHK023: C4](checklists/architecture-review.md#L38) | All unchecked | L1 labels and four main L3 pages exist; L2 completeness and cross-container traceability remain partial. L4 is explicitly deferred, not missing by silence. | AUD-007, AUD-017 |
| [CHK024 to CHK031: persona coverage](checklists/architecture-review.md#L51) | All unchecked | Persona navigation and ten actor names are authored; sector/security/experience meaning is not proven by that navigation. | AUD-002, AUD-004, AUD-006, AUD-021 |
| [CHK032 to CHK040: security](checklists/architecture-review.md#L64) | All unchecked | The exact carve-out label is present; RBAC, trust, SLO, and actuation/audit claims are contradicted or incomplete. | AUD-001, AUD-003, AUD-004, AUD-005, AUD-016 |
| [CHK041 to CHK046: citations](checklists/architecture-review.md#L78) | All unchecked | Lexical comments do not satisfy topic-correct bidirectional traceability; archive/no-home semantics are weak. | AUD-012, AUD-013 |
| [CHK047 to CHK055: CI](checklists/architecture-review.md#L89) | All unchecked | Job wiring exists, but neither reliable gate completeness nor execution/human approval is established. | AUD-010, AUD-011, AUD-012, AUD-013, AUD-017, AUD-022 |
| [CHK056 to CHK063: gaps](checklists/architecture-review.md#L103) | All unchecked | Correct table headers/seed rows exist; actionable references and fallback/amendment records are incomplete. | AUD-013 |
| [CHK064 to CHK070: page standard](checklists/architecture-review.md#L116) | All unchecked | Frontmatter is widespread; linked motivations, universal diagram obligations, and truthful canonical status need explicit reconciliation. | AUD-017 |
| [CHK071 to CHK077: constitution](checklists/architecture-review.md#L128) | All unchecked | Ten role names do not prove authorization; evacuation model, recovery principles/environments/overlap, and WAF links remain deficient. | AUD-004, AUD-014, AUD-017, AUD-018 |
| [CHK078 to CHK103: base inventory](checklists/architecture-review.md#L142) | All unchecked | All 26 base pairs exist but semantic/visual defects remain. The checklist has no individual inventory rows for the six amendment diagrams. | AUD-008, AUD-018, AUD-019, AUD-020, AUD-021, AUD-022 |
| [CHK104 to CHK115: per-page checks](checklists/architecture-review.md#L175) | All unchecked | Authored pages are present; no executed Markdown validation receipt or completed page-by-page review exists. | AUD-017, AUD-022 |
| [CHK116 to CHK121: roll-up gates](checklists/architecture-review.md#L194) | All unchecked | CI success, timed orientation, auditor walkthrough, and human actuation review remain UNVERIFIED. Count language is outdated. | AUD-022 |
| [Persona review's base coverage](review/persona-review.md#L9) | Narrative approval/merit findings | It predates final amendment acceptance. Its assertion of editable/valid fallback sources is contradicted by recovery XML, and its broad content confirmations are not matched by the inspected diagrams. | AUD-007, AUD-008, AUD-022 |
| [Persona review's fallback tracking](review/persona-review.md#L75) | Claims 26 tracked fallback gaps | No such rows appear in the current registry. Named source fallback metadata remains. No trustworthy evidence establishes successful later re-rendering of the six amendment artifacts. | AUD-013, AUD-022 |
| [Persona review's local green/deployment claims](review/persona-review.md#L76) | Narrative assertions | No source-SHA-bound command outputs, CI run ID, or feature-scoped historical diff is supplied. Do not infer executed success from current static digest matches. | AUD-022 |
| [Plan constitution gate table](plan.md#L34) | PASS claims | Documentation-only scope avoids new infrastructure, but does not prove accurate safety/security diagrams or passing mechanical checks. | AUD-001, AUD-003, AUD-017, AUD-022 |

The checklist has **121 unchecked items**. Range labels in this separate checklist assessment are summaries of review claims only; the Original Task Coverage table above retains one explicit row per original task ID as required.

## Existing Assertions and Their Limits

| Existing Surface | What Its Assertions Establish Statically | What It Does Not Establish |
| --- | --- | --- |
| [Evacuation stages](../../tests/unit/test_evacuation_stages.py#L20) | Canonical transition table, invalid transitions, re-entry and shelter-in-place cases. | Correctness of the documentation's substituted stage labels or actual execution success. |
| [Approval workflow](../../tests/integration/test_approval_workflow_state_machine.py#L26) | In-process start/approve/reject transitions and terminal-state rules. | Mounted publication endpoint enforcement or downstream delivery. |
| [Grounded approval](../../tests/integration/test_human_approval_preserved.py#L71) | Manually extended record dictionaries retain assigned approval/citation fields. | That publication calls a human approval gate or writes a durable audit result. |
| [Tenant isolation](../../tests/integration/test_tenant_isolation.py#L9) | Different helper scope strings and in-memory live/simulation visibility. | Deployed physical partition schema or cross-state field-level authority. |
| [Ingestion pipeline](../../tests/integration/test_ingestion_pipeline.py#L40) | Mock polling/circuit-breaker behavior, with some non-discriminating nonnegative counters. | Production factory repository injection, durable Cosmos writes, or actual agent consumption. |
| [Model gateway](../../tests/integration/test_data_minimisation_gateway.py#L61) | The gateway helper deliberately permits unchanged AU text. | Universal prompt-role coverage or fail-closed behavior in every client dispatch branch. |
| [RBAC impersonation](../../apps/api/tests/contract/spec_035/test_impersonation_pairing.py#L115) | Test-principal non-admin rejection and recording-repository admin audit pairing. | All documented permission cells or remote Entra/EasyAuth configuration. |
| [CD workflow tests](../../tests/devops/test_cd_workflow.py#L49) | Historical asserted expectations are visible. | Current workflow correctness: main/OIDC/separate-job expectations conflict with current YAML. |
| [Observability tests](../../tests/devops/test_observability_alerts_bicep.py#L55) | String-level presence of selected simulation alert thresholds. | SEC-04 catalogue completeness, SLO attainment, or capacity measurements. |
| [Citation axe test](../../apps/web/tests/web/src/components/citation/citation-card.axe.test.tsx#L39) | The test expects a violations array and logs warnings. | Zero violations, all-UI contrast, full keyboard accessibility, or human conformance sign-off. |
| [RAG opt-out lint test](../../tests/contract/test_rag_optout_lint.py#L99) | Adjacent bidirectional marker/ADR invariants. | Any coverage of the architecture citation/gap/hash/link validators. |

## Future Validation Order and Prerequisites

1. Resolve safety/current-state contradictions and explicit requirement conflicts first. Do not retrofit runtime code or cloud policy merely to make a diagram look true.
2. Repair sources/exports and meaningful spec/ADR references, retain legacy redirects and later roadmap pairs, and create actionable gap records.
3. In a future authorized environment, use Python 3.12 and the repository's pytest conventions for the proposed shared document tests; use Node/npx with unchanged markdownlint rules; use pinned lychee in offline mode and an agreed cross-platform manifest verifier. Do not run the whole product suite as a substitute for document checks.
4. Demonstrate positive, negative, and edge cases for pair/inventory completeness, malformed XML, stale exports, missing references, wrong roots, archive semantics, formatted placeholders, and local links outside the architecture directory. Store outputs bound to the exact final source revision.
5. Obtain the human source-to-diagram, AIIMS, security, SRE, accessibility, and timed new-joiner reviews applicable to the requirements. Keep absent review/measurement evidence UNVERIFIED. Do not backdate or infer sign-off from task checkboxes.

### Audit Document Validation

Post-write validation for this report is restricted to original-task ID/state coverage, requirement/scenario coverage, remediation IDs and unchecked state, required per-task instruction fields, existence/line bounds and input/review-record anchors of local evidence links, final newline, and editor diagnostics. No application test, build, deployment, or future remediation command is part of this validation.

**Document validation receipt:** Task ID/state coverage 86/86; requirement coverage 34/34; numbered-scenario coverage 27/27; independent-test rows 7/7; edge-case rows 5/5; 22 remediation IDs with unchecked boxes and all ten required instruction fields per task; 610 local link occurrences resolving to 147 existing targets, with cited text lines within file bounds. The initial check identified a missing final newline (MD047), which was corrected. Input-ID and review-record anchors were checked and corrected where necessary. Final document validation and editor diagnostics were rerun after these report-only corrections; no application tests or CI jobs were executed.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 001 only. Three parallel technical reviews were used to identify source-completable remediation; no other specification report was used. The pass did not change product runtime behavior, infrastructure, PNG exports, or external approval state.

| Area | Implementation result | Validation |
| --- | --- | --- |
| AUD-010 / AUD-011 | `check_diagram_manifest.py` is now the CI authority for diagram inventory, XML/provenance, pairing, and source hashes; source-relative architecture links and fragments are validated; docs CI invokes the checker directly. | `python tools/lint/check_diagram_manifest.py --root .`; XML parse of 34 sources; `48 passed` architecture contract tests |
| AUD-012 | HTML comments and code fences are excluded from spec citation evidence; architecture-page citations cannot fall back to repository-root paths or nonexistent line/heading fragments. | `python tools/lint/check_spec_cross_refs.py --root .`; negative fixture coverage in `tests/contract/test_architecture_docs.py` |
| AUD-013 | Existing known-gap validation remains passing; no-gap and follow-up semantics were not broadened because the current registry contains actionable rows requiring separate content-owner review. | `python tools/lint/check_known_gaps.py --root .` |
| AUD-002 / AUD-006 / AUD-007 | Cosmos partition prose, C4 Mermaid/source views, integration-point wording, and canonical runtime boundary descriptions were reconciled. Unsupported optional tooling is labelled as tooling rather than a business agent. | `npx --yes markdownlint-cli2 "docs/architecture/**/*.md"`; 34 Draw.io sources parse |
| AUD-003 / AUD-015 / AUD-016 / AUD-019 / AUD-020 / AUD-021 | Gateway residency claims, branch-driven deployment wording, SLO evidence status, cross-sector implementation qualifiers, test inventory counts, and seven-step accessibility mapping were corrected. | Markdownlint passed; source manifest regenerated and validated |

Remaining open evidence is deliberate: Draw.io PNG re-export/fidelity/150-DPI/white-background review, Azure stencil rendering, human AIIMS/security/SRE/accessibility review, live CI/environment protection evidence, and runtime route/gateway integration tests remain UNVERIFIED or OPEN. The implementation pass therefore improves source truth and validator enforcement but does not mark the feature fully remediated.
