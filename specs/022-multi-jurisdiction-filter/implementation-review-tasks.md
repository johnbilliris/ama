# Implementation Review: Multi-Jurisdiction Filter

## Scope and Evidence Rules

- **Review date**: 2026-09-11 (requested audit date).
- **Reviewed revision**: `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`; local HEAD matched this revision.
- **Boundary**: Fresh, isolated, static source and test-assertion review of specification 022. Only this report is authored. No branches, commits, index updates, original-document changes, source changes, other audit reports, or delegation.
- **Execution restriction**: No application imports, tests, builds, servers, browser sessions, cloud queries, deployments, or external approvals were performed. Read-only text searches, seed JSON projections, existing artifact inspection, and report-integrity checks are not application execution.
- **Contract**: The complete [Review Contract](../001-spec-implementation-audit/README.md#L11) was read. The applicable [code-review instructions](../../.github/instructions/code-review.instructions.md#L1) and Python fact-grounded coding skill were consulted. Python runtime conclusions remain unverified under the execution restriction.
- **Original tasks**: 27 separate IDs; all originally `[ ]`. Review dispositions: **13 IMPLEMENTED, 11 PARTIAL, 1 CONFLICT, 1 MISSING, 1 UNVERIFIED**. Original checkboxes are not completion evidence and are not changed.
- **Follow-ups**: **13 open tasks**, AUD-022-001 through AUD-022-013. Four P1 implementation findings precede nine P2 findings/evidence gaps. No follow-up is completed by this audit.

Evidence statuses retain the contract meanings:

| Status | Meaning in this report |
| --- | --- |
| IMPLEMENTED | Full scoped behavior or authored artifact is supported by inspected source; not a claim of successful execution. |
| PARTIAL | Some required behavior exists, but a specific obligation is absent or contradicted. |
| MISSING | Required behavior or artifact was not found after the stated scoped replacement search. |
| CONFLICT | Requirements, instructions, documentation, or current behavior disagree and need explicit resolution. |
| UNVERIFIED | Inspected evidence cannot establish execution, measured outcome, approval, or deployed state. |
| SUPERSEDED | Requires explicit replacement/retirement evidence. No original task is assigned this status merely because its code moved. |

### Inputs Read

All nine local input files were read in full, including the appended country requirement, personas, hypothesis, deferrals, both clarification sessions, task dependencies, and validation instructions:

| Input | Purpose |
| --- | --- |
| [spec.md](spec.md) | Requirements, 12 acceptance scenarios, seven edge cases, clarifications, assumptions, and amendments. |
| [tasks.md](tasks.md) | All 27 original task descriptions and original unchecked states. |
| [plan.md](plan.md) | Architecture, performance assumptions, and 15 constitution-gate claims. |
| [research.md](research.md) | R-001 through R-009 decisions, including tenant pass-through and URL conventions. |
| [data-model.md](data-model.md) | Four entities, seed assignment rules, selection/replay state transitions, and client interfaces. |
| [quickstart.md](quickstart.md) | Setup, future commands, and 13 manual validation steps. |
| [contracts/jurisdiction-filter-api.yaml](contracts/jurisdiction-filter-api.yaml) | Four operations and five named schemas. |
| [checklists/requirements.md](checklists/requirements.md) | 16 originally checked specification-quality statements. |
| [checklists/comprehensive-review.md](checklists/comprehensive-review.md) | 61 originally unchecked formal-review questions. |

Associated evidence inspected includes the [persona contract](../027-spec-hardening/contracts/persona-profile.md), [hypothesis-evidence contract](../028-capstone-alignment/contracts/evidence-stub.contract.md), full [rubric baseline](../028-capstone-alignment/evidence/rubric-baseline.md), full [post-feature rubric](../028-capstone-alignment/evidence/rubric-postfeature.md), the directly associated [028 task T029](../028-capstone-alignment/tasks.md#L184), and full [feature-value ledger](../shared/feature-value-ledger.md).

The full active [filter help article](../../apps/web/src/content/help/articles/screen-by-screen/multi-jurisdiction-filter.mdx), [architecture index](../../docs/architecture/README.md), [tenancy description](../../docs/architecture/data/multi-jurisdiction-tenancy.md), [filter description](../../docs/architecture/data/jurisdiction-filter.md), [cross-sector description](../../docs/architecture/data/cross-sector-touchpoints.md), [RISK-NEW-007](../../docs/risk-register/RISK-NEW-007.md), and [RISK-NEW-011](../../docs/risk-register/RISK-NEW-011.md) were also read. Diagram descriptions and authored risk treatments are not proof of working controls.

Backend unit, contract, integration, simulation, frontend route-smoke, page-object, test-discovery, and fixture source is cited below. Existing preparedness entries in [JUnit](../../tests/e2e/web-coverage/_artifacts/junit/web-coverage.xml#L131) and the associated [JSON run artifact](../../tests/e2e/web-coverage/_artifacts/web-coverage.json) were inspected without rerunning them.

## Prioritized Findings

P1 means a security or incorrect-result issue that blocks reliance on this feature as specified. P2 means an important capability, contract, test, documentation, or evidence gap. These are static findings, not reproduced runtime incidents.

| Priority / follow-up | Expected versus actual, impact, and exact evidence |
| --- | --- |
| P1 / AUD-022-001 | **Tenant isolation is not a data-query boundary.** FR-005 requires authenticated tenant-scoped queries. [Organisations](../../apps/api/app/api/routes/organisations.py#L21), [frameworks](../../apps/api/app/api/routes/frameworks.py#L19), and [jurisdictions](../../apps/api/app/api/routes/jurisdictions.py#L24) only log tenant identity; service calls omit it. The [seed cache](../../apps/api/app/services/seed_service.py#L8) is keyed only by path. [Anonymous defaults](../../apps/api/app/middleware/auth_middleware.py#L11), the [tenant resolver](../../apps/api/app/middleware/tenant_middleware.py#L47), and restricted [Entra](../../apps/api/app/middleware/entra_auth.py#L37)/[RBAC](../../apps/api/app/middleware/rbac_check.py#L32) prefix lists do not establish authenticated preparedness scoping. Shared public seeds do not demonstrate a private-data leak, but they also do not satisfy the promised isolation. [R-007](research.md#L124) conflicts with FR-005 and even its promised service pass-through is absent. |
| P1 / AUD-022-002 | **Catalogs retain the previous jurisdiction's records across selection changes.** [Selection changes](../../apps/web/src/components/preparedness/preparedness-client.tsx#L123) update IDs without clearing arrays or starting loading. [Loading starts](../../apps/web/src/components/preparedness/preparedness-client.tsx#L75) only after the [300ms timer](../../apps/web/src/components/preparedness/preparedness-client.tsx#L103); arrays are cleared only for the [empty fetch branch](../../apps/web/src/components/preparedness/preparedness-client.tsx#L67). A failed new request restores non-loading rendering of old records. Planners can see old-jurisdiction catalogs under the new selection. |
| P1 / AUD-022-003 | **Failure/loading state is shared, not per catalog.** One [loading/error pair](../../apps/web/src/components/preparedness/preparedness-client.tsx#L27) and [Promise.all](../../apps/web/src/components/preparedness/preparedness-client.tsx#L79) couple both requests. The [single error/retry banner](../../apps/web/src/components/preparedness/preparedness-client.tsx#L169) is outside both catalogs; the [analyzer props](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L16) have no per-catalog error/retry input. One failure discards the successful sibling response and can reveal stale arrays. This contradicts FR-012/FR-013 and the independent-section design. |
| P1 / AUD-022-004 | **Replay output is not gated by a successful, current selection snapshot.** [Every completion publishes its payload](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L77) without a request-generation check. Clearing depends on later [parent comparison](../../apps/web/src/components/preparedness/preparedness-client.tsx#L115) and [child effects/deferred rendering](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L52). Old output can be rendered before those effects clear it; no duration is asserted without execution. Separately, the [empty default](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L26) renders ["No blocking gaps detected"](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L337) before any successful replay and after stale clearing. That is a false assurance, not evidence of a completed assessment. |
| P2 / AUD-022-005 | **URL restoration is one-time, not ongoing reconciliation.** [initializedRef](../../apps/web/src/components/preparedness/preparedness-client.tsx#L43) prevents applying later URL inputs. [useSearchParams](../../apps/web/src/components/preparedness/preparedness-client.tsx#L20) is used when writing URLs, not to restore changed selection. Duplicate URL IDs remain duplicated; the [server prop](../../apps/web/src/app/preparedness/page.tsx#L5) assumes a single string. Same-route navigation/history can disagree with selected IDs; malformed repeated URL keys have no normalization path. |
| P2 / AUD-022-006 | **Jurisdiction-list failure cannot be retried through the offered Retry action.** [The loader catch](../../apps/web/src/components/preparedness/preparedness-client.tsx#L52) writes the shared catalog error; the subsequent [empty catalog fetch](../../apps/web/src/components/preparedness/preparedness-client.tsx#L67) clears it. [Retry](../../apps/web/src/components/preparedness/preparedness-client.tsx#L141) calls only catalog fetching. The loader effect also depends on the URL-derived prop, so selection navigation can refetch the supposedly mount-only list outside the catalog debounce. The selector can remain empty with no persistent explanation. |
| P2 / AUD-022-007 | **The required keyboard interaction contract is not implemented.** The [native-checkbox fieldsets](../../apps/web/src/components/preparedness/jurisdiction-selector.tsx#L79) provide labels and ordinary Tab/Space behavior, but no arrow-navigation, Enter-toggle, dropdown, or Escape handler required by [NFR-001](spec.md#L131), [T016](tasks.md#L73), and [R-005](research.md#L83). A fieldset is not inherently inaccessible; the finding is the explicit interaction mismatch and lack of WCAG evidence, not a claim that native checkboxes necessarily fail WCAG. |
| P2 / AUD-022-008 | **Country hierarchy/placeholders are absent from the actual filter path.** [FR-CAP-022-001](spec.md#L180) requires AU preservation plus PH/JP/BD placeholder nodes with preconditions. [The list route](../../apps/api/app/api/routes/jurisdictions.py#L23) always loads AU seeds, its [client type](../../apps/web/src/lib/api/jurisdictions.ts#L3) has no country/status/precondition metadata, and the [selector](../../apps/web/src/components/preparedness/jurisdiction-selector.tsx#L119) groups only by administrative level. The [shared shell](../../packages/ui/src/components/layout/app-shell.tsx#L17) supplies no replacement provider. A country-looking URL field is not a country-scoped query. Real non-AU operations remain deferred; that does not waive the required placeholder presentation. |
| P2 / AUD-022-009 | **Authored API contract and runtime validation disagree.** The contract's [jurisdiction enums](contracts/jurisdiction-filter-api.yaml#L90) and [required replay fields/hazard enum](contracts/jurisdiction-filter-api.yaml#L313) are not enforced by the [plain-string query](../../apps/api/app/api/routes/organisations.py#L19) or [replay input](../../apps/api/app/api/routes/scenarios.py#L8). Existing [invalid-ID tests](../../tests/contract/test_multi_jurisdiction_contract.py#L84) explicitly expect 200/empty. The new list operation returns generic dictionaries, not a declared JurisdictionSummary response model. Resolve permissive behavior versus the contract; do not confuse forgiving UI URL parsing with an agreed direct-API policy. |
| P2 / AUD-022-010 | **Tests do not discriminate the important failures, and the filter E2E workflow is missing.** [Union tests](../../tests/unit/test_multi_jurisdiction_filter.py#L37) compare counts, [framework tests](../../tests/unit/test_multi_jurisdiction_filter.py#L66) mostly check nonemptiness, and [API shape tests](../../tests/contract/test_multi_jurisdiction_contract.py#L32) do not validate the YAML schemas. [The only preparedness route smoke](../../tests/e2e/interface-coverage.spec.ts#L644) accepts a loading shell or heading. The [page object](../../tests/e2e/web-coverage/_support/pages/preparedness.po.ts#L6) has no filter/replay operations. Scoped searches found no replacement selection, URL, debounce, error, or replay-race workflow. |
| P2 / AUD-022-011 | **Performance, usability, manual rehearsal, and full-suite success are unverified.** [SC-001/SC-005/SC-006](spec.md#L147) have no scoped measurements. [T026/T027](tasks.md#L118) require execution. Existing [JUnit entries](../../tests/e2e/web-coverage/_artifacts/junit/web-coverage.xml#L131) are skipped, not passing. The [ledger's response-time(+0.05), zero-gap row](../shared/feature-value-ledger.md#L36) is an authored manual assertion, not the required measurements. |
| P2 / AUD-022-012 | **Operator and architecture documentation describes a different capability.** The [active help article](../../apps/web/src/content/help/articles/screen-by-screen/multi-jurisdiction-filter.mdx#L13) claims a global, claim-union, browser-persistent Apply filter. Actual [navigation links](../../packages/ui/src/components/layout/app-shell.tsx#L6) and [page-local state](../../apps/web/src/components/preparedness/preparedness-client.tsx#L24) do not implement it. [Authority enforcement](../../docs/architecture/data/jurisdiction-filter.md#L16), [jurisdiction-as-tenant isolation](../../docs/architecture/data/multi-jurisdiction-tenancy.md#L16), [Unified Command treatment](../../docs/risk-register/RISK-NEW-007.md#L9), and [activation-status treatment](../../docs/risk-register/RISK-NEW-011.md#L9) are not established by this filter. [R-001/T019](research.md#L5) also still prescribe server-side list fetching, whereas the current page forwards raw input to the client. |
| P2 / AUD-022-013 | **Formal review and amendment evidence is incomplete.** All [61 comprehensive questions](checklists/comprehensive-review.md#L16) remain unchecked, despite the earlier [16-item pass claim](checklists/requirements.md#L34) and [plan gate claims](plan.md#L24). [HYP-020](spec.md#L167) references a missing, malformed-name hypothesis stub; no renamed matching stub was found. The portfolio-wide [post-feature rubric](../028-capstone-alignment/evidence/rubric-postfeature.md#L24) does not establish per-022 uplift or consultation on every change. [PER-058/PER-059](spec.md#L159) labels are not named SME/practitioner validation records. |

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 022 only. Three parallel technical reviews examined frontend
selection races, backend tenant/auth scope, and API/accessibility contract drift. The source-completable stale-catalog
defect was corrected: selection changes now abort the prior request, invalidate its generation, clear both catalog
results and errors immediately, and show loading for the new non-empty selection before the existing 300 ms debounce.
Tenant scope, replay authorization, placeholder semantics, and browser evidence remain contract- or evidence-gated.

Validation: the touched React file has no editor diagnostics. The local web TypeScript check remains blocked by four
pre-existing Playwright return-type errors in
`tests/e2e/web-coverage/cross-cutting/accessibility-and-multilingual.spec.ts`.

## Controlling Paths and Scoped Searches

1. **URL to rendering**: [page](../../apps/web/src/app/preparedness/page.tsx#L9) awaits URL parameters and sends a raw string to [PreparednessClient](../../apps/web/src/components/preparedness/preparedness-client.tsx#L18). The client fetches jurisdictions, validates initial IDs, owns page-local selection, writes comma-separated URLs with `replace`, debounces catalog requests, and renders [JurisdictionSelector](../../apps/web/src/components/preparedness/jurisdiction-selector.tsx#L26) plus [OperatingModelAnalyzer](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L37).
2. **Selection to real queries**: [organisation client](../../apps/web/src/lib/api/organisations.ts#L22) and [framework client](../../apps/web/src/lib/api/frameworks.ts#L26) append repeated `jurisdictionId` values and pass AbortSignal. The [registered routes](../../apps/api/app/api/router.py#L64) call the [organisation intersection/seen-ID loop](../../apps/api/app/services/organisation_intelligence_service.py#L16) and [assignment-based framework filter](../../apps/api/app/services/preparedness_analysis_service.py#L30). This is real AU seed filtering, not selector-only behavior.
3. **Seed/provider semantics**: [bootstrap](../../packages/domain/src/domain/seed/bootstrap.py#L54) loads AU jurisdiction, organisation, framework, and assignment files. [SeedService](../../apps/api/app/services/seed_service.py#L8) caches by seed path, not tenant, country, or selection. The new list endpoint filters active jurisdictions and sorts by level/name. Seed deployment/restart can expose additions without UI code changes; live hot-reload/deactivation semantics are not defined and are not assumed to exist.
4. **Framework authority**: [FrameworkAssignment](../../packages/domain/src/domain/models/framework_assignment.py#L7) is actually used. The modern [OperatingFramework model](../../packages/domain/src/domain/models/operating_framework.py#L8) also has `applicable_jurisdiction_ids`, unlike the historic design description, but neither catalog filtering nor rehearsal uses that field as a replacement authority. Tests should deliberately distinguish it from assignments.
5. **Replay**: [client POST](../../apps/web/src/lib/api/scenarios.ts#L14) passes selected IDs to the [scenario route](../../apps/api/app/api/routes/scenarios.py#L15), [orchestrator](../../apps/api/app/services/rehearsal_orchestrator.py#L9), and [analysis](../../apps/api/app/services/preparedness_analysis_service.py#L42). Analysis filters actual organisations and current assignments. Findings are aggregate counts; gaps are pooled checks, and the called [legacy evacuation review](../../apps/agents/evacuation/agent.py#L261) supplies a generic recommendation. This is not the richer evacuation planner, a Unified Command action, or proof of country-specific operational analysis.
6. **Authorization**: [main registration](../../apps/api/app/main.py#L54) installs default auth/tenant middleware. Preparedness routes are outside production Entra/RBAC prefixes. [Principal extraction](../../apps/api/app/core/auth.py#L16) exposes agency/jurisdictions, but the feature does not consume them for query authorization. Deployment-side EasyAuth, gateway protection, and actual tenant-private access are unverified, not asserted absent in every environment.
7. **Persistence/cross-view**: The filter owns local React state plus one page's URL. There is no inspected provider or browser-storage persistence. Shell links navigate to bare paths, so returning via the bare Preparedness link intentionally reaches its empty default; global cross-view retention is not required by the base spec. The contradictory help claims need correction, not an unapproved global-state expansion.

### Negative-Search Boundaries

| Search | Scope and result | Disposition |
| --- | --- | --- |
| Missing historical unit/API files | Named-file inventory plus service/test-symbol searches in root unit, integration, and contract tests. Behaviour exists in [test_multi_jurisdiction_filter.py](../../tests/unit/test_multi_jurisdiction_filter.py#L1) and [test_multi_jurisdiction_contract.py](../../tests/contract/test_multi_jurisdiction_contract.py#L1). | Relocated partial test coverage, not missing implementation or SUPERSEDED tasks. |
| Missing filter E2E/component workflow | 179 JS/TS test-source files under root E2E and the web unit, integration, and accessibility test trees searched for the three component names, `/preparedness`, `jurisdictions=`, and replay button text. Eight matches were only interface smoke and the page object. Named-file search also found no T025 file. | MISSING workflow; AUD-022-010. |
| Replacement country/global-persistence behavior | 215 JS/TS implementation files in web src and shared UI src searched for country-provider/context/hooks, country-code/id fields, JurisdictionProvider, claim-union, and localStorage identifiers; zero matches. Direct page, shell, selector, clients, routes, bootstrap, and service reads confirmed AU-only paths. | MISSING hierarchy/provider in this flow; AUD-022-008. This is not a claim that all other features lack country data. |
| Hypothesis/review/measurement evidence | All nine local documents, matching 028 evidence filenames, and 832 supporting Markdown/YAML documents under specs/docs searched for exact spec slug, country FR, and HYP-020 variants, excluding all implementation audit reports. No matching HYP-020 stub or per-022 measurement/consultation record was found; ledger and two risk references were inspected. | MISSING stub and UNVERIFIED outcomes; AUD-022-011, AUD-022-013. |
| Claimed broader authority/activation behavior | Selection handler, four API clients/routes, services, replay helper, shell, and referenced architecture/risk prose. Selection dispatches list queries; no filter-triggered authority change or activation-status query is connected. | CONFLICT in feature attribution; AUD-022-012. No blanket absence claim about other incident workflows. |

`rg` was unavailable. Narrow workspace searches and read-only PowerShell source enumeration supplied the bounded searches above. No original report from another audit was used as evidence.

## Open Remediation Tasks

All following checkboxes must remain unchecked until future implementation and independent validation meet their acceptance criteria. Source owners are role/surface owners, not inferred individual assignees. Future command groups V1 through V6 are defined later and were not executed.

### AUD-022-001 - Authenticated Tenant Query Boundary

- [ ] **AUD-022-001 (P1): Resolve and enforce the authenticated tenant boundary.**

**Affected original obligations**: FR-005; T007, T008, T009, T010, T011, T018, T027; R-007; CHK005, CHK025, CHK055. Also review the replay query boundary under T021.

**Expected / actual / impact**: Trusted tenant context must reach each scoped data lookup. Current handlers log it, then use globally cached seeds without it; auth defaults and protected-prefix exclusions do not establish an authenticated boundary. Public reference data may legitimately be shared, but that exception needs explicit authority and separation from tenant-owned data. No private-record exfiltration was observed.

**Source owners**: API security and domain-data owners; [route](../../apps/api/app/api/routes/organisations.py#L21), [service](../../apps/api/app/services/organisation_intelligence_service.py#L16), [analysis service](../../apps/api/app/services/preparedness_analysis_service.py#L19), [auth](../../apps/api/app/middleware/auth_middleware.py#L22), [tenant middleware](../../apps/api/app/middleware/tenant_middleware.py#L47), and the four frontend API clients.

**Developer steps**:

1. Resolve FR-005 versus R-007 with the tenant/auth owners: distinguish authenticated organisation identity, live/simulation tenant, jurisdiction selection, and explicitly shared reference data. Do not equate an AU state with an Entra tenant by assumption.
2. Make the four feature operations obtain trusted server-resolved context; preserve validated principal information and reject missing/expired identity according to the agreed production policy. Do not trust caller-supplied X-Tenant-Id or anonymous fallbacks as authorization.
3. Pass context explicitly into services/repositories and scope tenant-owned reads/cache keys. Keep shared immutable reference data an explicit policy exception if approved. Wire the browser transport to the supported authenticated path without breaking repeated query parameters or AbortSignal.

**Tester - positive**: In [API contract tests](../../tests/contract/test_multi_jurisdiction_contract.py#L15), use two controlled authenticated principals and tenant-owned fixtures with identical jurisdiction IDs but distinguishable record IDs. Assert each permitted request returns only its allowed tenant data; permitted shared reference rows are identical only under the approved exception.

**Tester - negative**: Missing/expired identity, an untrusted tenant header, and a non-member simulation request must not expose tenant-owned catalog or replay results. Assert agreed 401/403 responses and no successful scoped service call; do not make real identity/cloud calls.

**Tester - edge**: Reuse a process/cache while changing principal and live/simulation context; identical jurisdiction selections must not reuse another tenant's result. Test jurisdiction visibility policy separately from tenant identity. Existing homes: [contract](../../tests/contract/test_multi_jurisdiction_contract.py), [unit](../../tests/unit/test_multi_jurisdiction_filter.py). Commands V1/V2 after approved identity fixtures exist.

**Dependencies / acceptance**: Resolve policy with AUD-022-013, align contracts with AUD-022-009, then add discrimination under AUD-022-010. Acceptance requires explicit context at every scoped read and passing allow/deny/cache-isolation assertions, not a tenant log line.

### AUD-022-002 - Immediate Catalog Invalidation

- [ ] **AUD-022-002 (P1): Make every selection transition invalidate old catalog presentation immediately.**

**Affected original obligations**: FR-002, FR-003, FR-013; NFR-002; T017, T018; edge cases 3/4; CHK003, CHK037, CHK047, CHK060.

**Expected / actual / impact**: Old records must disappear on selection change, including the debounce window. [The handler](../../apps/web/src/components/preparedness/preparedness-client.tsx#L123) leaves them intact until new data succeeds; a failed request exposes them again. Abort/request IDs do protect superseded catalog completions after dispatch, but do not clear already rendered data.

**Source owner**: Preparedness frontend owner; [selection and fetch lifecycle](../../apps/web/src/components/preparedness/preparedness-client.tsx#L58), [catalog render branches](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L91).

**Developer steps**:

1. Use the canonical selection snapshot as the catalog generation key. At both user- and URL-driven transitions, invalidate old arrays/errors and mark affected sections loading immediately; empty selection must show its own empty state immediately.
2. Abort/invalidate the previous generation independently of the 300ms dispatch timer. Accept success, failure, and completion-state writes only for the active generation.
3. Keep one final catalog refresh after rapid toggles. Ensure retries do not leave an extra pending debounce request or let an older completion reset loading for newer work.

**Tester - positive**: Use controlled deferred responses for NSW-only and VIC-only fixtures. After the VIC click and before advancing time, assert no NSW cards remain and both affected loading states are present; at 299ms no new catalog request, at 300ms one request per catalog.

**Tester - negative**: Resolve an aborted/older response and reject the current request; neither path may restore NSW data under VIC. Exercise a fake transport that ignores AbortSignal so the generation guard, not only browser cancellation, is tested.

**Tester - edge**: NSW -> VIC -> QLD, Select All, Clear All during in-flight work, retry during debounce, and unmount. Test homes: proposed `apps/web/__tests__/preparedness-client.test.tsx` within [Vitest discovery](../../apps/web/vitest.config.ts#L19), and proposed T025 E2E workflow. Commands V3/V4.

**Dependencies / acceptance**: Coordinate state shape with AUD-022-003 and URL transitions with AUD-022-005. Acceptance is zero out-of-selection cards from the first transition render onward and final-selection-only completion writes.

### AUD-022-003 - Independent Catalog Failure States

- [ ] **AUD-022-003 (P1): Give each catalog its own loading, error, data, and retry lifecycle.**

**Affected original obligations**: FR-012, FR-013; T017, T018; R-004; edge case 4; CHK001, CHK010, CHK024, CHK038, CHK043.

**Expected / actual / impact**: Each affected section needs an inline error and retry without stale/partial records in that section. [Promise.all](../../apps/web/src/components/preparedness/preparedness-client.tsx#L79) discards a successful sibling when one request fails, and [one external banner](../../apps/web/src/components/preparedness/preparedness-client.tsx#L169) cannot explain which catalog failed.

**Source owner**: Preparedness frontend owner; [client state](../../apps/web/src/components/preparedness/preparedness-client.tsx#L25) and [analyzer prop boundary](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L16).

**Developer steps**:

1. Maintain section-specific states and independently handle request settlement for the same active selection generation.
2. Pass section status and retry callbacks to the analyzer. Render the error and action inside the affected catalog, keeping the selector usable; never present old data as an error fallback.
3. Preserve a successful sibling's current-generation result while the other fails or retries. Agree and document this partial-failure interpretation without showing partial records inside the failed catalog.

**Tester - positive**: Organisation success plus delayed framework success must render each section as it settles. Retry a failed framework request and assert organisation records remain current and are not needlessly refetched.

**Tester - negative**: Independently reject each endpoint, then both; assert correctly named section errors, absence of stale cards, and a still-operable selector. JSON/transport failures must follow the same safe presentation.

**Tester - edge**: Failure after a selection change, repeated Retry clicks, collapsed catalog reopening, and error-to-success announcements. Homes: proposed frontend unit tests under [existing discovery](../../apps/web/vitest.config.ts#L19), proposed T025 E2E file. Commands V3/V4.

**Dependencies / acceptance**: Depends on AUD-022-002 generation handling; AUD-022-007 covers announcements/focus. Acceptance requires independent success/failure/retry assertions for both endpoint permutations.

### AUD-022-004 - Current and Truthful Replay Output

- [ ] **AUD-022-004 (P1): Gate replay output on a successful replay for the current selection.**

**Affected original obligations**: FR-004, FR-015; SC-003; T020, T021, T022; R-009; edge case 6; CHK014, CHK037, CHK038, CHK042, CHK047.

**Expected / actual / impact**: Findings must belong to the current selected jurisdiction set. [Completion](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L77) publishes before any current-request check; later effects may clear it, but are not a publication guard. [The no-gap branch](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L337) treats never-run/stale-cleared defaults as a successful clean assessment.

**Source owners**: Preparedness frontend and rehearsal-domain owners; [analyzer](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L49), [parent replay tracking](../../apps/web/src/components/preparedness/preparedness-client.tsx#L115), [scenario client](../../apps/web/src/lib/api/scenarios.ts#L14), [analysis](../../apps/api/app/services/preparedness_analysis_service.py#L42).

**Developer steps**:

1. Track explicit idle/running/succeeded/failed/stale state with the canonical jurisdiction snapshot and replay request generation. Invalidate on selection change before showing new-context content.
2. Publish only a completion whose captured/requested and returned jurisdiction sets match the active snapshot. Abort where supported and retain a generation guard; do not rely on the completion callback's later state update or deferred presentation to correct a stale publish.
3. Show the specified stale/re-run notice after invalidation. Render a clean-gap statement only after a successful current replay; idle, failure, and cleared output must say assessment is unavailable/not run, not that no blocking gaps were detected. Review aggregate finding accuracy with a planner rather than treating echoed IDs as proof.

**Tester - positive**: Bushfire with NSW+VIC and flood with SA must send those exact sets and render matching organisation/framework memberships. After a current successful response with no gaps, the clean-gap statement may appear.

**Tester - negative**: On first load, first replay failure, or stale clearing, assert the clean-gap statement is absent. Start replay A, change to B, resolve A; assert no A findings, counts, jurisdiction labels, or clean-gap result is committed under B.

**Tester - edge**: Complete A, change to B, start B, return to A before B resolves; reorder the same set; repeat a replay with an error after an earlier success; change scenario type while a request is pending. Backend homes: [contract replay test](../../tests/contract/test_multi_jurisdiction_contract.py#L119), [integration](../../tests/integration/test_preparedness_analysis.py#L11), [simulation](../../tests/simulation/test_preparedness_replays.py#L5). Frontend home is proposed under V3/V4. Commands V1/V2/V3/V4.

**Dependencies / acceptance**: AUD-022-005 supplies set normalization; AUD-022-009 defines invalid direct requests; AUD-022-010 adds deferred-response assertions. Acceptance requires no outdated output even transiently and no unearned clean-assessment language.

### AUD-022-005 - URL and Selection Reconciliation

- [ ] **AUD-022-005 (P2): Reconcile every relevant URL change with one canonical selection set.**

**Affected original obligations**: FR-014; T018, T019, T020; R-003; edge case 7; CHK004, CHK034, CHK044, CHK046, CHK050, CHK051, CHK054.

**Expected / actual / impact**: Shareable/restored URLs must describe the visible selection. [Initial-only validation](../../apps/web/src/components/preparedness/preparedness-client.tsx#L43) ignores later URL input, permits duplicate IDs, and does not normalize repeated query-key shapes from [page input](../../apps/web/src/app/preparedness/page.tsx#L5).

**Source owner**: Preparedness navigation/frontend owner; [page](../../apps/web/src/app/preparedness/page.tsx#L9), [URL writer](../../apps/web/src/components/preparedness/preparedness-client.tsx#L123), and selection/replay generation handlers.

**Developer steps**:

1. Define normalization for absent, empty, invalid, duplicate, and repeated URL values. Keep valid comma-separated IDs, deduplicate as a set, and silently drop invalid IDs without inventing a default jurisdiction.
2. Reconcile changes from navigation/history and refreshed valid-ID lists, not only first mount. Avoid replace/effect loops and preserve unrelated query parameters.
3. Retain page-local, URL-based scope unless an explicit decision changes it. `replace` need not create a history entry for every toggle; existing navigable entries must nevertheless restore consistently. Document plain-shell-link behavior and independent-tab semantics.

**Tester - positive**: NSW+QLD bookmark, reload, new tab, and same-route navigation to VIC all restore exact checkbox/catalog/replay context. Preserve an unrelated query parameter.

**Tester - negative**: Invalid-only URL yields empty selection; mixed valid/invalid yields only the valid set. Duplicate/repeated-key input must not inflate counts or fail with `.split` errors.

**Tester - edge**: Existing history Back/Forward entries, all-nine URL, two tabs with different selections, a deactivated bookmarked ID, and parameter updates before the jurisdiction list resolves. Homes: proposed client unit tests and T025 E2E; [existing page object](../../tests/e2e/web-coverage/_support/pages/preparedness.po.ts#L6) can gain scoped locators. Commands V3/V4.

**Dependencies / acceptance**: Apply AUD-022-002/AUD-022-004 invalidation on restored changes; coordinate country namespace with AUD-022-008. Acceptance is URL/UI/request set equality without loops, duplicate IDs, or cross-tab leakage.

### AUD-022-006 - Jurisdiction Provider Recovery

- [ ] **AUD-022-006 (P2): Separate jurisdiction-list loading/retry from catalog fetching.**

**Affected original obligations**: FR-007, FR-012; NFR-002; T009, T013, T018, T019; R-001/R-004; CHK007, CHK023, CHK046, CHK052.

**Expected / actual / impact**: A failed control data source needs a persistent explanation and working recovery path. [Loader failure](../../apps/web/src/components/preparedness/preparedness-client.tsx#L52) is overwritten by catalog state; [Retry](../../apps/web/src/components/preparedness/preparedness-client.tsx#L141) does not reload jurisdictions. The loader is also rerun for changed initial URL props rather than only an agreed mount/refresh event.

**Source owner**: Preparedness data-provider/frontend owner; [list client](../../apps/web/src/lib/api/jurisdictions.ts#L9), [loader](../../apps/web/src/components/preparedness/preparedness-client.tsx#L38), and [seed cache](../../apps/api/app/services/seed_service.py#L8).

**Developer steps**:

1. Introduce dedicated list loading/error/retry state. A list failure must not be mistaken for a legitimate zero-jurisdiction result, and catalog cleanup must not erase it.
2. Give retry an actual list-fetch path with cancellation/generation protection; initialize/validate URL state only against a successful current list. Stop accidental list refetches on every selection-derived URL update.
3. Define refresh, seed rollout, addition, and deactivation behavior. Preserve dynamic data sourcing; do not claim live hot reload for the current process-lifetime cache without implementing and testing it.

**Tester - positive**: Fail the first list request, then recover through its retry without page refresh; full names and restored valid URL IDs must appear.

**Tester - negative**: Persistent 500, malformed response, and authentication failure must retain a meaningful error and not clear to an unexplained empty selector after 300ms. Retry must call the jurisdictions endpoint, not only catalogs.

**Tester - edge**: Zero active jurisdictions, an additional valid seeded jurisdiction, fewer-than-nine controlled fixture, deactivation, rapid retry, and a late older list response. Homes: [API contract](../../tests/contract/test_multi_jurisdiction_contract.py#L20) plus proposed frontend tests. Commands V1/V3/V4.

**Dependencies / acceptance**: Resolve architecture in AUD-022-012 and schema evolution in AUD-022-009. Acceptance requires recoverable list failure, documented refresh semantics, and no selection-driven request storm.

### AUD-022-007 - Keyboard and Accessibility Contract

- [ ] **AUD-022-007 (P2): Meet or explicitly reconcile the selector's interaction contract and validate accessibility.**

**Affected original obligations**: FR-001, FR-008; NFR-001; T016, T024, T025, T026; R-005; CHK015, CHK030, CHK031, CHK032.

**Expected / actual / impact**: The specified dropdown/listbox and arrow/Enter/Escape interactions are absent from the [fieldset implementation](../../apps/web/src/components/preparedness/jurisdiction-selector.tsx#L79). Native labels and Space/Tab support are useful existing behavior, but not proof of the specified keyboard path or WCAG 2.1 AA conformance.

**Source owners**: UX/accessibility and preparedness frontend owners; [selector](../../apps/web/src/components/preparedness/jurisdiction-selector.tsx#L48), [catalog render branches](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L91), and [current dynamic status](../../apps/web/src/components/preparedness/jurisdiction-selector.tsx#L57).

**Developer steps**:

1. Obtain an explicit resolution for fieldsets versus R-005/T016's dropdown/listbox. Either implement the required interaction pattern or approve an equivalent accessible pattern and trace the changed obligations; do not mark the old design SUPERSEDED without a decision.
2. Implement all retained keyboard operations, full names, predictable focus, and named group/global actions. Avoid nesting incompatible interactive roles just to add ARIA attributes.
3. Announce catalog loading, error, empty, and result changes appropriately without stealing focus. Verify focus visibility, selected-state contrast, mobile layout, and touch targets against the applicable standard.

**Tester - positive**: Complete selection, Select All, Clear All, retry, and replay with keyboard only. Assert specified Tab/Shift-Tab, Enter/Space, ArrowUp/ArrowDown, and Escape behavior for the approved pattern; verify all nine full names and grouping.

**Tester - negative**: No keyboard trap, unnamed group action, stale announced count, missing focus indicator, or inaccessible error/retry region. Automated accessibility success alone is not a screen-reader sign-off.

**Tester - edge**: First/last option navigation, empty list, all-selected state, error recovery, zoom/narrow viewport, and returning focus after loading. Homes: proposed `apps/web/tests/a11y/jurisdiction-selector.test.tsx` in [a11y discovery](../../apps/web/vitest.config.ts#L23), plus proposed T025 workflow. Commands V3/V4 and manual V5.

**Dependencies / acceptance**: Coordinate independent catalog states with AUD-022-003. Acceptance needs automated assertions plus dated manual keyboard/screen-reader evidence and the explicit design resolution.

### AUD-022-008 - Country Hierarchy Without AU Fallback

- [ ] **AUD-022-008 (P2): Add the required country hierarchy and explicitly non-operational placeholders.**

**Affected original obligations**: FR-CAP-022-001; PER-060; SCP-064; FR-001, FR-007, FR-008; T009, T013, T016, T018, T019, T023, T024; associated 028:T029.

**Expected / actual / impact**: [The amendment](spec.md#L180) preserves all nine AU nodes and adds PH/JP/BD placeholders with named prerequisites. Current list/provider/selector/query paths are AU-only; rendering a country label or retaining an unknown URL field would not change that data scope.

**Source owners**: Jurisdiction domain, API, UX, and capstone-governance owners; [AU list route](../../apps/api/app/api/routes/jurisdictions.py#L23), [client projection](../../apps/web/src/lib/api/jurisdictions.ts#L3), [selector grouping](../../apps/web/src/components/preparedness/jurisdiction-selector.tsx#L119), and [bootstrap](../../packages/domain/src/domain/seed/bootstrap.py#L54).

**Developer steps**:

1. Represent country-parent identity, child jurisdictions, placeholder status, and preconditions in the agreed data/provider contract. Preserve every existing AU identifier, name, grouping, assignment, and Commonwealth membership rule.
2. Render AU -> nine jurisdictions and PH/JP/BD -> explicit placeholder content. Carry the namespace through URL/state/query boundaries when applicable; never present the AU dataset under a non-AU selection.
3. Keep real non-AU catalogs/replays disabled or explicitly unavailable until D-009, regulatory/data-sharing, and responsible-agent/SME gates are cleared. This task does not authorize overseas operations, data transfers, or constitutional changes.

**Tester - positive**: AU renders exactly its existing nine nodes and unchanged record memberships. PH/JP/BD each expose placeholder status and their specified prerequisites, including JMA/Cabinet Office and DDM/BWDB references where required.

**Tester - negative**: A PH/JP/BD placeholder or invalid country URL must not dispatch an operational AU replay or display AU catalogs as foreign-country results. Placeholder-only selection cannot silently become NSW/default AU selection.

**Tester - edge**: AU -> placeholder while catalog/replay work is in flight, reload a placeholder URL, return to AU, and add a future approved node via the provider. Homes: [API contracts](../../tests/contract/test_multi_jurisdiction_contract.py) and proposed frontend tests. Commands V1/V3/V4; no real foreign or Azure calls.

**Dependencies / acceptance**: AUD-022-009 contract evolution, AUD-022-005 canonical state, AUD-022-013 prerequisite governance. Acceptance requires actual hierarchy metadata and safe data-path behavior, not labels alone; AU regressions must remain absent.

### AUD-022-009 - Contract and Runtime Agreement

- [ ] **AUD-022-009 (P2): Reconcile input validation and publish verifiable response schemas.**

**Affected original obligations**: FR-004, FR-005, FR-007; T006, T009, T010, T011, T021, T027; all four API operations; CHK021, CHK022, CHK052.

**Expected / actual / impact**: Direct API behavior must agree with [the authored contract](contracts/jurisdiction-filter-api.yaml#L16). It currently declares finite jurisdiction/hazard enums and required replay jurisdictionIds, while routes accept arbitrary strings and default missing replay IDs to an empty list. Runtime list schemas are generic dictionaries and tests do not compare them to the contract.

**Source owners**: API/schema owners; [list route](../../apps/api/app/api/routes/jurisdictions.py#L23), [catalog query](../../apps/api/app/api/routes/frameworks.py#L18), [replay input](../../apps/api/app/api/routes/scenarios.py#L8), and the existing contract file.

**Developer steps**:

1. Decide the direct-API policy for unknown/mixed IDs and missing/invalid replay fields. Preserve single-value compatibility, empty catalog arrays, and forgiving UI URL behavior; explicitly reconcile the API's enum restriction with future dynamic jurisdiction additions.
2. Declare response projections/schemas for the list and catalog/replay payloads, preserving required fields and valid extra enrichment fields. Keep assignment-based framework filtering authoritative despite the newer applicability field.
3. Align authored contract, generated schema, route validation, and client types. Record intentional differences from older design instead of silently changing original requirement meanings.

**Tester - positive**: Validate all four operations' payloads against the agreed schemas; assert all required properties/types/enums, a single jurisdiction, repeated parameters, and empty catalogs.

**Tester - negative**: Unknown/mixed jurisdiction IDs, omitted replay fields, unsupported hazard, malformed parameter type, and schema-invalid response fixtures must produce the agreed documented outcomes. Tests must fail if contract enums or required fields drift.

**Tester - edge**: New active jurisdiction/administrative level, duplicate query IDs, two assignments referencing one framework, an ended assignment, and metadata/assignment disagreement. Homes: [multi-jurisdiction contract](../../tests/contract/test_multi_jurisdiction_contract.py#L20), [legacy contract](../../tests/contract/test_preparedness_contract.py#L5). Commands V1/V2 after schema assertions are authored.

**Dependencies / acceptance**: Coordinate AUD-022-001 and AUD-022-008. Acceptance requires one explicit policy and discriminating schema tests, not merely matching filenames or `hasattr` checks.

### AUD-022-010 - Discriminating Tests and Missing Workflow

- [ ] **AUD-022-010 (P2): Strengthen relocated backend tests and author the actual filter workflow tests.**

**Affected original obligations**: T003, T004, T005, T006, T025, T027; FR-001, FR-002, FR-003, FR-009, FR-012, FR-013, FR-014, FR-015; NFR-001, NFR-002; all user stories and seven edge cases.

**Expected / actual / impact**: Test assertions must reject wrong membership and stale/unauthorized views. Existing [count-only union assertions](../../tests/contract/test_multi_jurisdiction_contract.py#L68) could pass an over-broad catalog. [The no-duplicates test](../../tests/unit/test_multi_jurisdiction_filter.py#L43) selects NSW+Commonwealth, not the actual overlapping AFP ACT+Commonwealth membership. No corresponding interactive frontend workflow was found.

**Source owners**: Backend and web test owners, with feature owners supplying independent expected fixtures. Existing homes: [unit](../../tests/unit/test_multi_jurisdiction_filter.py), [contract](../../tests/contract/test_multi_jurisdiction_contract.py), [integration](../../tests/integration/test_preparedness_analysis.py), [simulation](../../tests/simulation/test_preparedness_replays.py), and [page object](../../tests/e2e/web-coverage/_support/pages/preparedness.po.ts).

**Developer steps**:

1. Reuse the consolidated tests rather than recreating files solely to match historical names. Add controlled seed fixtures with independent expected ID sets, overlapping membership, inactive/no-data jurisdictions, unassigned/ended assignments, and tenant distinctions.
2. Assert exact union equality and forbidden-record absence, not only nonempty/count inequalities; assert framework IDs through assignments, national coverage for each AU jurisdiction, and state-only exclusions. Add direct schema tests from AUD-022-009.
3. Author proposed `tests/e2e/multi-jurisdiction-filter.spec.ts` and focused frontend unit/a11y tests using current discovery. Cover all 13 quickstart actions, deferred-response ordering, URL reconciliation, failure permutations, and safe replay lifecycle. Keep deterministic transport tests distinct from separately labelled live-local-stack tests.

**Tester - positive**: Use the concrete seed fixture table below and controlled minimal equivalents. Verify exact visible IDs/names and captured request parameter sets, not just a heading, spinner, HTTP 200, or an echoed jurisdiction list.

**Tester - negative**: Demonstrate the new assertions reject intentionally over-broad union responses, state-framework leakage, duplicate AFP, stale completions, expired/missing identity, and a perpetual loading shell. Do not weaken assertions to accommodate current defects.

**Tester - edge**: Cover all seven edge cases and 12 acceptance scenarios below, including known-but-empty jurisdiction fixtures and all-nine selection. Commands V1/V2/V3/V4, after required code and fixtures exist.

**Dependencies / acceptance**: Behavioral fixes AUD-022-001, AUD-022-002, AUD-022-003, AUD-022-004, AUD-022-005, AUD-022-006, AUD-022-007, AUD-022-008, AUD-022-009. Tests can be authored first; do not claim historical red-before-green execution without records. Acceptance requires test discovery, exact assertions, and non-skipped execution evidence captured later.

### AUD-022-011 - Measured Outcomes and Execution Evidence

- [ ] **AUD-022-011 (P2): Produce genuine feature-specific validation and success-criterion evidence.**

**Affected original obligations**: SC-001, SC-003, SC-005, SC-006; T023, T024, T026, T027; CHK009, CHK039, CHK040, CHK041, CHK042, CHK049, CHK056; quickstart steps 1 through 13.

**Expected / actual / impact**: Latency, interaction reduction, first-time-user success, manual walkthrough, and full-suite success need recorded outcomes. Existing smoke artifacts are skipped, and the [ledger claim](../shared/feature-value-ledger.md#L36) does not measure the feature's SCs. Functional source presence alone cannot establish performance or user comprehension.

**Source owners**: Feature QA/performance/UX owners and the feature-value ledger custodian; [SC definitions](spec.md#L147), [quickstart](quickstart.md#L107), [test configuration](../../apps/web/playwright.config.cts#L17).

**Developer steps**:

1. Define measurement conditions: time from last selection interaction through debounce and final current catalog render; agreed network/device envelope; exact data volume; timeout/error treatment; and the old single-jurisdiction interaction baseline.
2. Provide observable selection/result identifiers and stable timing boundaries without collecting unnecessary identity or browsing history. Define planner-reviewed expected replay content rather than equating aggregate counts with complete coordination analysis.
3. Arrange dated, revision-bound manual and automated evidence. Update the ledger only through its owning publication/change-control flow when substantiated; do not retroactively convert skipped artifacts or original unchecked tasks to passes.

**Tester - positive**: Measure all-nine and representative combinations against the 2-second target, including 300ms debounce. Compare the same review task against the documented single-jurisdiction baseline for at least 50% fewer interactions. Run a predeclared first-time-user study with at least 90% unassisted success.

**Tester - negative**: Report misses, errors, exclusions, non-completion, and skipped tests explicitly. A stalled spinner, coached user, or cross-jurisdiction echo without correct catalog/findings membership is not success.

**Tester - edge**: Slow responses, complete current seed volume and agreed upper-volume fixture, empty result, retry, keyboard-only review, and narrow viewport. Future V1/V2/V4/V5/V6 require separate execution authorization and prerequisites. Record command, revision, environment, timestamps, fixture/version, raw results, and reviewer.

**Dependencies / acceptance**: Depends on AUD-022-010 and relevant behavioral fixes. Acceptance requires measured SC results, all manual steps with outcomes, and the requested full-suite record; future failures remain open rather than being hidden in an aggregate green status.

### AUD-022-012 - Documentation and Attribution Reconciliation

- [ ] **AUD-022-012 (P2): Align operator instructions, architecture attribution, and setup guidance with the actual approved feature.**

**Affected original obligations**: T016, T019, T026, T027; R-001, R-003, R-005, R-007; FR-005, FR-014, SCP-065, SCP-066; CHK018, CHK027, CHK029, CHK034, CHK045, CHK054; associated help/architecture/risk obligations.

**Expected / actual / impact**: Operators should not be told that a page-local UI filter is a global authorization control, a browser-persistent preference, or an operational activation trigger. The [help](../../apps/web/src/content/help/articles/screen-by-screen/multi-jurisdiction-filter.mdx#L13), [tenancy prose](../../docs/architecture/data/multi-jurisdiction-tenancy.md#L16), [authority prose](../../docs/architecture/data/jurisdiction-filter.md#L16), and risk treatments contradict the inspected path. Historical setup/test paths also no longer describe the relocated test homes.

**Source owners**: Product/BA and documentation owners with API, frontend, Incident Commander, and Executive Leader reviewers. [Current page](../../apps/web/src/app/preparedness/page.tsx#L9), [quickstart commands](quickstart.md#L90), [risk treatment 007](../../docs/risk-register/RISK-NEW-007.md#L9), and [risk treatment 011](../../docs/risk-register/RISK-NEW-011.md#L9) are the controlling references.

**Developer steps**:

1. Decide whether to restore R-001/T019's server-side jurisdiction initialization or formally record the client-side equivalent and its failure/performance trade-offs. Preserve the business requirements whichever architecture is approved.
2. Correct the help's default, IDs, persistence, interaction, keyboard, cross-view, persona-lock, and audit claims to the approved behavior. Attribute authority handoff, Unified Command, activation status, and cross-sector protocols to their actual owning capabilities or mark them unverified/deferred; do not expand spec 022 by inference.
3. Reconcile jurisdiction-versus-tenant terminology, the model's newer applicability metadata, and direct API policy. Correct quickstart working directories, consolidated test names, prerequisites, and auth setup. All such source/original-document edits belong to a later authorized implementation task, not this audit.

**Tester - positive**: Follow the corrected setup and each documented filter action against the approved feature, checking URL, visible results, keyboard behavior, and actual owning route for every claimed control.

**Tester - negative**: No unsupported claim-union default, localStorage/global persistence, automatic Unified Command, activation-status badge, or authority-enforcing filter claim remains presented as delivered without a connected implementation and evidence.

**Tester - edge**: Navigate away/return using bare shell links, independently bookmarked tabs, Commonwealth-only/ACT overlap, and placeholder countries. Homes: [existing interface smoke](../../tests/e2e/interface-coverage.spec.ts#L644), proposed filter workflow, and documentation review. Future V4/V5 plus source-link checks.

**Dependencies / acceptance**: Coordinate AUD-022-001, AUD-022-005, AUD-022-007, AUD-022-008, AUD-022-009 and governance AUD-022-013. Acceptance is approved, traceable documentation with executable future instructions, not silent rewriting of original requirements.

### AUD-022-013 - Formal Review and Amendment Evidence

- [ ] **AUD-022-013 (P2): Close the governance questions and supply correctly scoped amendment evidence.**

**Affected original obligations**: HYP-020; PER-058, PER-059, PER-060; SCP-064, SCP-065, SCP-066; FR-CAP-022-001; T026, T027; all 61 comprehensive questions and 16 specification-quality claims.

**Expected / actual / impact**: Formal readiness, persona validation, actor consultation, and hypothesis uplift require identified evidence. The [HYP reference](spec.md#L167) points to absent `specs/028-capstone-alignment/evidence/HYP-HYP-020.md`; its doubled prefix also conflicts with the [stub filename contract](../028-capstone-alignment/contracts/evidence-stub.contract.md#L46). Portfolio rubric prose and `status: validated` labels do not establish per-spec consultation, per-022 uplift, or named SME validation.

**Source owners**: Product-owner/BA, spec-027/spec-028 governance custodians, UX/security reviewers, and appropriate SME/practitioner reviewers; [comprehensive checklist](checklists/comprehensive-review.md#L16), [persona contract](../027-spec-hardening/contracts/persona-profile.md#L7), and [rubric snapshots](../028-capstone-alignment/evidence/rubric-postfeature.md#L24).

**Developer steps**:

1. Disposition every question in the coverage table with an owner, answer/decision, evidence, and any retained gap. Resolve shared-reference tenancy, state/history/error behavior, privacy/logging retention, accessibility, country preconditions, and measurement definitions without unilateral constitutional changes.
2. In the appropriate future owning-spec change, create or correctly link a contract-compliant HYP-020 stub, preserving `Not tested` until measured. Provide per-022 baseline/comparator provenance and consultation records if claiming the hypothesis's uplift; a portfolio mean is not a substitute.
3. Supply named SME/practitioner validation records for claimed AU personas, or accurately qualify the claims. Preserve PER-060 and real PH/JP/BD capabilities as placeholders/deferred until explicit regulatory/data-sharing and D-009 prerequisites clear. Do not invent approvals or commission delegation during this audit.

**Tester - positive**: Review the 61-question disposition and 16 quality statements against exact linked evidence; check all six hypothesis-stub headings, ID/location, two preconditions, quantified falsification, status, owning-spec links, and dated reviewer records.

**Tester - negative**: A missing/malformed stub, proxy-only persona sign-off, portfolio-only uplift, unchecked-question aggregate PASS, or unsupported prerequisite-clearance claim must leave the corresponding evidence status open.

**Tester - edge**: A criterion regression despite higher mean, missing consultation on one relevant change, conflicting spec authority, and placeholder promotion without one prerequisite. Future V5/manual contract review only after required artifacts and authorization exist.

**Dependencies / acceptance**: Policy decisions unblock AUD-022-001/AUD-022-008/AUD-022-012; final sign-off follows AUD-022-010/AUD-022-011. Acceptance is specific evidence or an explicit retained deferral for every item, never retrospective checkbox completion without proof.

## Original Task Coverage

Each ID below is a separate original task. `[ ]` reproduces its original checked state exactly. IMPLEMENTED is limited to the described source behavior/artifact; future run and review obligations remain separately visible. Relocation is not retirement.

| Original ID | Original state | Status | Concrete implementation/test evidence | Open follow-up |
| --- | --- | --- | --- | --- |
| T001 | [ ] | IMPLEMENTED | [Original](tasks.md#L29); [assignment seed](../../packages/domain/src/domain/seed/framework_assignments_australia.json#L1) has 123 explicit records, national AIIMS assignments for nine AU jurisdictions, and state-only mappings. | AUD-022-010 for stronger fixtures. |
| T002 | [ ] | IMPLEMENTED | [Original](tasks.md#L30); [bootstrap key](../../packages/domain/src/domain/seed/bootstrap.py#L60) loads framework assignments; [typed context](../../apps/api/app/services/preparedness_analysis_service.py#L19) consumes them. | None. |
| T003 | [ ] | PARTIAL | [Original](tasks.md#L44); consolidated [organisation unit tests](../../tests/unit/test_multi_jurisdiction_filter.py#L26) cover empty/invalid/some dedup cases, but union uses counts and no actual AFP-overlap/known-empty fixture. No test-first run proof. | AUD-022-010, AUD-022-011. |
| T004 | [ ] | PARTIAL | [Original](tasks.md#L45); [framework unit tests](../../tests/unit/test_multi_jurisdiction_filter.py#L66) and [assignment equality](../../tests/unit/test_multi_jurisdiction_filter.py#L122) exist, but national-per-state/state-only exclusion and ended/known-empty fixtures are incomplete. | AUD-022-010, AUD-022-011. |
| T005 | [ ] | PARTIAL | [Original](tasks.md#L46); relocated [TestClient coverage](../../tests/contract/test_multi_jurisdiction_contract.py#L20) exercises real routes, repeated/single/empty values and nine-ID subset; exact union and full ordering assertions are missing. | AUD-022-010. |
| T006 | [ ] | PARTIAL | [Original](tasks.md#L47); [new contract tests](../../tests/contract/test_multi_jurisdiction_contract.py#L32) check keys; [legacy test](../../tests/contract/test_preparedness_contract.py#L5) still checks single NSW. Neither validates the authored YAML schemas. | AUD-022-009, AUD-022-010. |
| T007 | [ ] | IMPLEMENTED | [Original](tasks.md#L51); [service](../../apps/api/app/services/organisation_intelligence_service.py#L16) accepts a list, returns empty for empty/None, applies OR membership and seen-ID deduplication. | AUD-022-001 for the shared tenant obligation; AUD-022-010 for tests. |
| T008 | [ ] | IMPLEMENTED | [Original](tasks.md#L52); [framework filter](../../apps/api/app/services/preparedness_analysis_service.py#L30) uses selected current assignments and a distinct framework-ID set; empty selection returns empty. | AUD-022-001, AUD-022-010. |
| T009 | [ ] | PARTIAL | [Original](tasks.md#L53); [route](../../apps/api/app/api/routes/jurisdictions.py#L23) returns active named rows sorted by level/name. Tenant is logged, not passed to the data provider; response schema is generic. | AUD-022-001, AUD-022-006, AUD-022-009. |
| T010 | [ ] | IMPLEMENTED | [Original](tasks.md#L54); [route parameter/service call](../../apps/api/app/api/routes/organisations.py#L18) accepts repeated values and empty goes through the service's empty branch. | AUD-022-001, AUD-022-009 for cross-cutting boundaries. |
| T011 | [ ] | IMPLEMENTED | [Original](tasks.md#L55); [framework route](../../apps/api/app/api/routes/frameworks.py#L18) returns empty without IDs and calls assignment filtering with the whole list; no NSW fallback. | AUD-022-001, AUD-022-009. |
| T012 | [ ] | IMPLEMENTED | [Original](tasks.md#L56); [router](../../apps/api/app/api/router.py#L66) registers jurisdictions. Prefix is owned by the child router, so the effective path is correct without duplicating `/jurisdictions`. | None. |
| T013 | [ ] | IMPLEMENTED | [Original](tasks.md#L70); [client](../../apps/web/src/lib/api/jurisdictions.ts#L3) defines the projection, fetches the endpoint with no-store, and rejects unsuccessful responses. | AUD-022-001, AUD-022-006, AUD-022-008 for integration/evolution. |
| T014 | [ ] | IMPLEMENTED | [Original](tasks.md#L71); [organisation client](../../apps/web/src/lib/api/organisations.ts#L22) appends each repeated ID and forwards AbortSignal. | AUD-022-001, AUD-022-010. |
| T015 | [ ] | IMPLEMENTED | [Original](tasks.md#L72); [framework client](../../apps/web/src/lib/api/frameworks.ts#L26) appends repeated IDs and forwards AbortSignal. | AUD-022-001, AUD-022-010. |
| T016 | [ ] | PARTIAL | [Original](tasks.md#L73); [selector](../../apps/web/src/components/preparedness/jurisdiction-selector.tsx#L48) has labelled native checkboxes, full names, group/global actions, but not specified dropdown/listbox/keyboard behavior. | AUD-022-007, AUD-022-008, AUD-022-012. |
| T017 | [ ] | PARTIAL | [Original](tasks.md#L74); [analyzer props/default](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L16) remove catalog fetching/NSW default and support empty/loading rendering; per-catalog error/retry states are absent and replay default is misleading. | AUD-022-002, AUD-022-003, AUD-022-004. |
| T018 | [ ] | PARTIAL | [Original](tasks.md#L75); [client](../../apps/web/src/components/preparedness/preparedness-client.tsx#L18) owns state, cancellation, a 300ms timer, and URL writes, but shares status, retains old arrays, cannot recover the list, and does not reconcile later URLs. | AUD-022-002, AUD-022-003, AUD-022-005, AUD-022-006. |
| T019 | [ ] | CONFLICT | [Original](tasks.md#L76); [page](../../apps/web/src/app/preparedness/page.tsx#L9) delegates raw URL text to the client, whereas the task/R-001 prescribe server fetching and validation. Initial behavior is partly relocated, not proven retired. | AUD-022-005, AUD-022-006, AUD-022-012. |
| T020 | [ ] | PARTIAL | [Original](tasks.md#L90); [sorted comparison/callback](../../apps/web/src/components/preparedness/preparedness-client.tsx#L115) exists, but comparison occurs after publication and has no replay-generation guard. | AUD-022-004, AUD-022-005. |
| T021 | [ ] | PARTIAL | [Original](tasks.md#L91); [replay request](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L77) uses selected IDs and the [notice](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L307) exists; deferred/effect clearing is not a current-result publication guarantee. | AUD-022-004. |
| T022 | [ ] | IMPLEMENTED | [Original](tasks.md#L92); [run button/message](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L292) and [retry](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L316) disable when selection is empty. | AUD-022-004 for truthful result presentation; AUD-022-010 for tests. |
| T023 | [ ] | IMPLEMENTED | [Original](tasks.md#L106); full [AU jurisdiction seed](../../packages/domain/src/domain/seed/jurisdictions_australia.json#L1) and static projection establish nine active full-name records: one Commonwealth, six states, two territories. No original execution/sign-off is inferred. | AUD-022-008 preserves AU; AUD-022-011 records future validation. |
| T024 | [ ] | IMPLEMENTED | [Original](tasks.md#L107); [API sort](../../apps/api/app/api/routes/jurisdictions.py#L32) supplies ordering; [grouping](../../apps/web/src/components/preparedness/jurisdiction-selector.tsx#L119) preserves it and [labels](../../apps/web/src/components/preparedness/jurisdiction-selector.tsx#L88) use full names. Actual browser verification remains unverified. | AUD-022-007, AUD-022-010, AUD-022-011. |
| T025 | [ ] | MISSING | [Original](tasks.md#L117); bounded frontend search found only [smoke](../../tests/e2e/interface-coverage.spec.ts#L644) and [page object](../../tests/e2e/web-coverage/_support/pages/preparedness.po.ts#L6), not the required filter workflow or a replacement. | AUD-022-010. |
| T026 | [ ] | UNVERIFIED | [Original](tasks.md#L118); [manual steps](quickstart.md#L107) are authored instructions; no complete execution record was found. Stored preparedness smoke cases are skipped. | AUD-022-011, AUD-022-012, AUD-022-013. |
| T027 | [ ] | PARTIAL | [Original](tasks.md#L119); source removes NSW query defaults and deduplicates, but tenant/schema boundaries are unresolved and no full-suite pass or final review approval was established. | AUD-022-001, AUD-022-009, AUD-022-010, AUD-022-011, AUD-022-013. |

## Requirement Coverage

The following 24 rows cover every FR, NFR, SC, and country-amendment FR. Cross-cutting PARTIAL statuses include the rendered lifecycle, not only successful service calls.

| ID | Status | Evidence / limitation | Follow-up |
| --- | --- | --- | --- |
| FR-001 | PARTIAL | [Requirement](spec.md#L106); nine named options and Select All/Clear All exist, but [selector](../../apps/web/src/components/preparedness/jurisdiction-selector.tsx#L79) lacks specified interaction behavior; WCAG not established. | AUD-022-007. |
| FR-002 | PARTIAL | [OR filter](../../apps/api/app/services/organisation_intelligence_service.py#L26) is correct; [state lifecycle](../../apps/web/src/components/preparedness/preparedness-client.tsx#L123) can render old selection's organisations. | AUD-022-002, AUD-022-003. |
| FR-003 | PARTIAL | [Assignment-based filter](../../apps/api/app/services/preparedness_analysis_service.py#L30) is connected; framework render lifecycle has the same stale/shared-state defect. | AUD-022-002, AUD-022-003. |
| FR-004 | IMPLEMENTED | [POST invocation](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L80) sends the selected IDs; [orchestrator](../../apps/api/app/services/rehearsal_orchestrator.py#L9) consumes them. | AUD-022-004 for result lifecycle; AUD-022-010 for assertions. |
| FR-005 | CONFLICT | [Requirement](spec.md#L110) requires tenant-scoped queries; [R-007](research.md#L124) permits shared seed pass-through; actual [service](../../apps/api/app/services/organisation_intelligence_service.py#L16) has no tenant parameter. Multi-value OR behavior itself exists. | AUD-022-001, AUD-022-009. |
| FR-006 | IMPLEMENTED | [No-selection rendering/button](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L299) supplies an explicit selection prompt and disables replay; catalogs are hidden for empty selection. | AUD-022-004, AUD-022-010. |
| FR-007 | IMPLEMENTED | [List route](../../apps/api/app/api/routes/jurisdictions.py#L23) sources active seed data and [client](../../apps/web/src/lib/api/jurisdictions.ts#L9) consumes it; no UI option hardcoding. Process-lifetime cache is not hot reload. | AUD-022-006, AUD-022-008, AUD-022-009 for recovery/evolution. |
| FR-008 | IMPLEMENTED | [Native option labels](../../apps/web/src/components/preparedness/jurisdiction-selector.tsx#L88) render names and use jurisdiction_id internally. | AUD-022-010. |
| FR-009 | IMPLEMENTED | [Organisation seen-ID set](../../apps/api/app/services/organisation_intelligence_service.py#L21) and [assignment framework-ID set](../../apps/api/app/services/preparedness_analysis_service.py#L35) avoid selected-jurisdiction overlap duplicates on current unique seed records. | AUD-022-010. |
| FR-010 | IMPLEMENTED | [State change and router.replace](../../apps/web/src/components/preparedness/preparedness-client.tsx#L123) drive client fetching without a full page reload. | AUD-022-005, AUD-022-006 for synchronization. |
| FR-011 | IMPLEMENTED | [Disabled button and visible message](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L297) match the empty-selection requirement. | AUD-022-010. |
| FR-012 | PARTIAL | [Global error/retry](../../apps/web/src/components/preparedness/preparedness-client.tsx#L169) exists, but not inside the affected catalog; failed new queries can expose stale arrays and lose sibling success. | AUD-022-002, AUD-022-003. |
| FR-013 | PARTIAL | [Two loading render branches](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L105) exist, but loading is shared/delayed and previous records are not cleared immediately. | AUD-022-002, AUD-022-003. |
| FR-014 | PARTIAL | [Initial valid-ID filter](../../apps/web/src/components/preparedness/preparedness-client.tsx#L45) and [URL writer](../../apps/web/src/components/preparedness/preparedness-client.tsx#L127) exist; later URL changes, duplicates, and repeated-key normalization remain incomplete. | AUD-022-005. |
| FR-015 | PARTIAL | [Notice](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L307) and [effect reset](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L54) exist, but outdated response publication and deferred old presentation are not guarded. | AUD-022-004. |
| NFR-001 | PARTIAL | [Keyboard requirement](spec.md#L131) exceeds [native checkbox implementation](../../apps/web/src/components/preparedness/jurisdiction-selector.tsx#L92); no scoped keyboard/screen-reader pass evidence. | AUD-022-007, AUD-022-011. |
| NFR-002 | PARTIAL | [300ms catalog timer](../../apps/web/src/components/preparedness/preparedness-client.tsx#L103) exists and cleanup cancels previous work; [list-loader dependency](../../apps/web/src/components/preparedness/preparedness-client.tsx#L54) can cause extra nondebounced list requests on URL selection changes. | AUD-022-002, AUD-022-006, AUD-022-010. |
| SC-001 | UNVERIFIED | [2-second target](spec.md#L147) has no scoped elapsed-time artifact including debounce, network, and current render. | AUD-022-011. |
| SC-002 | IMPLEMENTED | [Nine active seed records](../../packages/domain/src/domain/seed/jurisdictions_australia.json#L1), [active/sorted route](../../apps/api/app/api/routes/jurisdictions.py#L31), and [rendered iteration](../../apps/web/src/components/preparedness/jurisdiction-selector.tsx#L88) support availability in source. | AUD-022-010, AUD-022-011 for execution evidence. |
| SC-003 | PARTIAL | [Analysis](../../apps/api/app/services/preparedness_analysis_service.py#L42) uses the selected AU union, but findings are aggregate and [replay output lifecycle](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L77) can misrepresent current assessment. Planner accuracy is unverified. | AUD-022-004, AUD-022-010, AUD-022-011. |
| SC-004 | IMPLEMENTED | The same source dedup paths as FR-009 apply to combined selection; [AFP](../../packages/domain/src/domain/seed/organisations_australia.json#L153) supplies a real overlap fixture. | AUD-022-010. |
| SC-005 | UNVERIFIED | [50% interaction-reduction target](spec.md#L151) lacks a defined measured baseline and comparable completed workflow record. | AUD-022-011. |
| SC-006 | UNVERIFIED | [90% first-time-user target](spec.md#L152) lacks a participant protocol and unassisted completion evidence. | AUD-022-011. |
| FR-CAP-022-001 | PARTIAL | [Amendment](spec.md#L180): AU nine preserved; country-parent metadata and PH/JP/BD placeholder presentation/preconditions are missing from the actual flow. | AUD-022-008, AUD-022-013. |

### Acceptance Scenarios

Aliases below are review-local labels for the original numbered scenarios, not new original IDs. A source-supported happy path is not a recorded test run.

| Scenario | Status | Required result and inspected coverage | Follow-up |
| --- | --- | --- | --- |
| US1-AS1 | PARTIAL | [VIC-only scenario](spec.md#L21): services filter VIC correctly, but stale selection/error lifecycle can show another catalog. | AUD-022-002, AUD-022-003, AUD-022-010. |
| US1-AS2 | PARTIAL | [NSW+QLD union](spec.md#L22): service OR/dedup exists; rendered transitions and exact combined membership are not covered. | AUD-022-002, AUD-022-003, AUD-022-010. |
| US1-AS3 | IMPLEMENTED | [Commonwealth plus states](spec.md#L23): explicit commonwealth memberships join the selected state memberships; no automatic NSW fallback. AFP overlaps ACT/Commonwealth. | AUD-022-010 for discriminating combined UI assertion. |
| US1-AS4 | IMPLEMENTED | [No-selection prompt](spec.md#L24): selector reports none; analyzer shows selection instruction and hides catalogs. | AUD-022-010. |
| US2-AS1 | PARTIAL | [NSW+VIC bushfire](spec.md#L37): request and analysis consume both; current-result publication and substantive cross-state finding assertions are incomplete. | AUD-022-004, AUD-022-010, AUD-022-011. |
| US2-AS2 | PARTIAL | [SA-only replay](spec.md#L38): analysis scopes to SA, but specific finding quality and displayed current-context lifecycle are not established. | AUD-022-004, AUD-022-010, AUD-022-011. |
| US2-AS3 | IMPLEMENTED | [No-selection replay](spec.md#L39): run and error Retry are disabled with the specified visible instruction. | AUD-022-010. |
| US3-AS1 | IMPLEMENTED | [All-nine availability](spec.md#L53): active AU seeds flow through sorted list route and selector iteration. | AUD-022-007, AUD-022-010 for interaction verification. |
| US3-AS2 | IMPLEMENTED | [Names/individual toggles](spec.md#L54): native labels and controlled checkbox onChange use each supplied ID. | AUD-022-007, AUD-022-010. |
| US4-AS1 | IMPLEMENTED | [NSW+QLD organisation OR](spec.md#L68): [service membership predicate](../../apps/api/app/services/organisation_intelligence_service.py#L26) and seen-ID guard. | AUD-022-001 for tenant boundary; AUD-022-010 for exact assertions. |
| US4-AS2 | IMPLEMENTED | [TAS+ACT frameworks](spec.md#L69): [current assignment filter](../../apps/api/app/services/preparedness_analysis_service.py#L37) returns referenced union, not all frameworks. | AUD-022-001, AUD-022-010. |
| US4-AS3 | IMPLEMENTED | [No-ID data requests](spec.md#L70): both routes/services return empty arrays; no hardcoded NSW fallback. | AUD-022-010. |

### Edge Cases

EC aliases follow the seven bullets in [the original edge-case section](spec.md#L74).

| Edge | Status | Evidence / remaining boundary | Follow-up |
| --- | --- | --- | --- |
| EC-01 | UNVERIFIED | All-nine selection and union are authored; no measured full-dataset performance/display pass. Current volume is 49 organisations and 27 frameworks, not a measured capacity guarantee. | AUD-022-010, AUD-022-011. |
| EC-02 | IMPLEMENTED | Analyzer has separate organisation/framework no-match text versus empty selection. A controlled valid-but-empty jurisdiction is missing from tests; all current nine have data. | AUD-022-010. |
| EC-03 | PARTIAL | 300ms timer, AbortController, and request ID checks exist; immediate presentation invalidation and extra list requests are unresolved. | AUD-022-002, AUD-022-006, AUD-022-010. |
| EC-04 | PARTIAL | A retry exists but is global, not per affected catalog, and stale/independent-success handling is wrong. | AUD-022-003, AUD-022-006. |
| EC-05 | IMPLEMENTED | Options come from active seed rows without UI option constants; restart/refresh/deactivation semantics and contract enum evolution need explicit decisions. | AUD-022-006, AUD-022-009, AUD-022-010. |
| EC-06 | PARTIAL | Completed replay changes produce a notice/reset, but current-generation publication and truthful cleared-result rendering are missing. | AUD-022-004. |
| EC-07 | PARTIAL | First-load mixed/invalid IDs are filtered; ongoing navigation, duplicate values, and malformed repeated keys are not reconciled. | AUD-022-005. |

### Clarifications and Assumptions

CL-01 through CL-10 follow the two [2026-04-18 clarification sessions](spec.md#L86). AS-01 through AS-06 follow [the assumptions](spec.md#L134).

| Obligation | Status | Coverage / decision | Follow-up |
| --- | --- | --- | --- |
| CL-01 - WCAG 2.1 AA | PARTIAL | Native semantics exist; required keyboard operations and manual evidence are incomplete. | AUD-022-007, AUD-022-011. |
| CL-02 - Entra-derived tenant in every query | CONFLICT | FR-005, R-007, and service signatures disagree. | AUD-022-001. |
| CL-03 - 300ms debounce | PARTIAL | Catalog timer exists; selection-related list refetch bypasses it. | AUD-022-006, AUD-022-010. |
| CL-04 - independent loading/no old results | PARTIAL | Shared flag and retained arrays violate immediate independent-section behavior. | AUD-022-002, AUD-022-003. |
| CL-05 - inline section error/retry | PARTIAL | Global error loses endpoint specificity and recovery independence. | AUD-022-003. |
| CL-06 - FrameworkAssignment linkage | IMPLEMENTED | [Catalog](../../apps/api/app/services/preparedness_analysis_service.py#L30) and [replay](../../apps/api/app/services/preparedness_analysis_service.py#L50) both use current assignments. | AUD-022-010. |
| CL-07 - URL share/bookmark | PARTIAL | First-load restoration and writes exist, ongoing reconciliation does not. | AUD-022-005. |
| CL-08 - Select All/Clear All | IMPLEMENTED | [Single onChange actions](../../apps/web/src/components/preparedness/jurisdiction-selector.tsx#L39) pass the whole set or empty set. | AUD-022-007, AUD-022-010. |
| CL-09 - clear stale replay/notice | PARTIAL | Notice/effects exist; publication and default-result semantics remain unsafe. | AUD-022-004. |
| CL-10 - ignore invalid IDs | PARTIAL | Initial validation exists; later URL normalization and list-refresh behavior need completion. | AUD-022-005, AUD-022-006. |
| AS-01 - initial nine/dynamic additions | IMPLEMENTED | Nine active AU records; dynamic list route. Country placeholders remain a separate amendment. | AUD-022-006, AUD-022-008, AUD-022-009. |
| AS-02 - OR, not AND | IMPLEMENTED | Explicit overlapping-membership predicate and assignment-ID union. | AUD-022-010. |
| AS-03 - no saved user preference; URL state | PARTIAL | Source uses page-local URL state, not browser preference storage; restoration incomplete and help contradicts it. | AUD-022-005, AUD-022-012. |
| AS-04 - no default jurisdiction | IMPLEMENTED | Empty initial IDs and no NSW catalog fallback. | AUD-022-010. |
| AS-05 - current volume/no pagination | UNVERIFIED | Static counts are 49/27; adequacy and a future pagination threshold are not measured or approved. | AUD-022-011, AUD-022-013. |
| AS-06 - explicit Commonwealth inclusion | IMPLEMENTED | Commonwealth-only agencies require that membership to be selected; AFP's explicit ACT membership is a valid overlap, not automatic national expansion. | AUD-022-010. |

### Amendment Coverage

| ID | Status | Evidence / interpretation | Follow-up |
| --- | --- | --- | --- |
| PER-058 | UNVERIFIED | [AU persona cross-reference](spec.md#L159) is authored; no named, dated validation record is attached to this feature as required by the persona contract. | AUD-022-013. |
| PER-059 | UNVERIFIED | [Technical actor cross-reference](spec.md#L160) is authored; the validated label alone does not establish reviewer/SME validation or consultation. | AUD-022-013. |
| PER-060 | IMPLEMENTED | [PH/JP/BD personas](spec.md#L161) are explicitly placeholders with D-009/SME prerequisites. Their promotion is not claimed. | AUD-022-008, AUD-022-013 preserve the boundary. |
| HYP-020 | PARTIAL | [Hypothesis/falsification text](spec.md#L167) exists; the named stub and per-spec consultation/uplift proof are absent/unverified. The portfolio rubric is not a substitute. | AUD-022-013. |
| SCP-064 | IMPLEMENTED | [Real non-AU variants](spec.md#L173) are explicitly deferred behind three prerequisite classes. This does not defer the placeholder UI requirement. | AUD-022-008, AUD-022-013. |
| SCP-065 | PARTIAL | [Constitutional boundary](spec.md#L174) is stated, but tenancy/privacy/audit tensions are not resolved by specific approved risk decisions. No constitutional changes are made here. | AUD-022-001, AUD-022-012, AUD-022-013. |
| SCP-066 | PARTIAL | [Authority/deferral statement](spec.md#L175) is authored; help/architecture/risk attribution exceeds the page-local capability and needs owning-spec resolution. | AUD-022-012, AUD-022-013. |

## Design and Contract Coverage

### Research Decisions

| Decision | Status | Evidence / disposition | Follow-up |
| --- | --- | --- | --- |
| R-001 | CONFLICT | [Server/client decision](research.md#L5) says server list fetch/validation; [page](../../apps/web/src/app/preparedness/page.tsx#L9) delegates both to the client. No explicit retirement found. | AUD-022-006, AUD-022-012. |
| R-002 | IMPLEMENTED | [Repeated API parameters](research.md#L24) are used by both clients and both list routes. | AUD-022-009, AUD-022-010 for policy/schema assertions. |
| R-003 | PARTIAL | [Comma-separated URL state](research.md#L43) exists for initial restoration/writes but not ongoing reconciliation. | AUD-022-005. |
| R-004 | PARTIAL | [Debounce/abort strategy](research.md#L63) exists without independent catalog states or immediate clearing. A timer instead of a named hook is not itself a defect. | AUD-022-002, AUD-022-003, AUD-022-006. |
| R-005 | CONFLICT | [Dropdown/listbox decision](research.md#L83) differs from fieldsets, with missing specified keyboard operations and no replacement approval. | AUD-022-007, AUD-022-012. |
| R-006 | IMPLEMENTED | [Seed assignment decision](research.md#L104) is used by the actual catalog and analysis services rather than synthetic Cartesian assignments. | AUD-022-010. |
| R-007 | CONFLICT | [Shared-seed pass-through](research.md#L124) conflicts with FR-005; even the documented service argument is not passed. | AUD-022-001, AUD-022-013. |
| R-008 | IMPLEMENTED | [Single/repeated/empty behavior](research.md#L145) exists; no-query now returns empty as intentionally specified. | AUD-022-009, AUD-022-010. |
| R-009 | PARTIAL | [Snapshot comparison](research.md#L163) exists; later effect-based clearing is not a replay-publication boundary. | AUD-022-004. |

### Data and API Obligations

| Obligation | Status | Source evidence / limitation | Follow-up |
| --- | --- | --- | --- |
| Jurisdiction entity and active/name/level ordering | IMPLEMENTED | [Full seed](../../packages/domain/src/domain/seed/jurisdictions_australia.json#L1) and [route](../../apps/api/app/api/routes/jurisdictions.py#L31) supply the required AU projection and grouping order. | AUD-022-008, AUD-022-009 for hierarchy/evolution. |
| Organisation entity and union membership | IMPLEMENTED | [Service](../../apps/api/app/services/organisation_intelligence_service.py#L16) tests the actual jurisdiction_ids list and deduplicates IDs; current seed records are unique. | AUD-022-001, AUD-022-010. |
| OperatingFramework applicability | IMPLEMENTED | [Filter](../../apps/api/app/services/preparedness_analysis_service.py#L30) uses FrameworkAssignment, even though the newer [model](../../packages/domain/src/domain/models/operating_framework.py#L14) also exposes applicability metadata. | AUD-022-009, AUD-022-012. |
| FrameworkAssignment seed/current linkage | IMPLEMENTED | [Assignment model](../../packages/domain/src/domain/models/framework_assignment.py#L7), [bootstrap](../../packages/domain/src/domain/seed/bootstrap.py#L60), and [effective_to check](../../apps/api/app/services/preparedness_analysis_service.py#L37). Current assignments follow the specified null-end convention. | AUD-022-010. |
| Selection state machine | PARTIAL | EMPTY and fetched data exist, but immediate LOADING and independent ERROR transitions do not match [data-model.md](data-model.md). | AUD-022-002, AUD-022-003, AUD-022-006. |
| Replay state machine | PARTIAL | Stale notice exists; idle/stale defaults can render a clean result and old responses are not guarded before publication. | AUD-022-004. |
| GET /jurisdictions | PARTIAL | [Operation](contracts/jurisdiction-filter-api.yaml#L16): active/sorted response exists; promised once-per-load server call and tenant/provider contract are not fulfilled. | AUD-022-001, AUD-022-006, AUD-022-009, AUD-022-012. |
| GET /organisations | PARTIAL | [Operation](contracts/jurisdiction-filter-api.yaml#L65): OR/repeated/empty behavior exists; direct enum validation and authenticated query scoping disagree with contract obligations. | AUD-022-001, AUD-022-009. |
| GET /frameworks | PARTIAL | [Operation](contracts/jurisdiction-filter-api.yaml#L122): assignment union/repeated/empty behavior exists; schema/tenant boundary remains unresolved. | AUD-022-001, AUD-022-009. |
| POST /scenarios/replay | PARTIAL | [Operation](contracts/jurisdiction-filter-api.yaml#L168): selected IDs reach real analysis; input enum/required-field policy and current-result display are incomplete. | AUD-022-001, AUD-022-004, AUD-022-009. |
| JurisdictionSummary schema | PARTIAL | Required fields are returned, but [generic route schema](../../apps/api/app/api/routes/jurisdictions.py#L23) does not establish parity with [the named schema](contracts/jurisdiction-filter-api.yaml#L194). | AUD-022-009, AUD-022-010. |
| Organisation schema | PARTIAL | Current model_dump payload contains the contract fields and enrichment, but [tests](../../tests/contract/test_multi_jurisdiction_contract.py#L53) do not assert complete [schema](contracts/jurisdiction-filter-api.yaml#L215) agreement. | AUD-022-009, AUD-022-010. |
| OperatingFramework schema | PARTIAL | Current payload has required fields; no complete agreement test for [schema](contracts/jurisdiction-filter-api.yaml#L274), future applicability metadata, or types. | AUD-022-009, AUD-022-010. |
| ScenarioReplayRequest schema | CONFLICT | [Required IDs/hazard enum](contracts/jurisdiction-filter-api.yaml#L313) differ from optional-default IDs and unbounded scenarioType in the input model. | AUD-022-009. |
| ScenarioRunPayload schema | PARTIAL | [Orchestrator fields](../../apps/api/app/services/rehearsal_orchestrator.py#L19) cover [required payload](contracts/jurisdiction-filter-api.yaml#L334); no full schema assertion, and jurisdiction echo alone cannot establish content accuracy. | AUD-022-009, AUD-022-010, AUD-022-011. |

## Review and Checklist Evidence

These tables assess authored completeness and inspected implementation. They do not check off the original review or claim a reviewer actually approved it. All non-IMPLEMENTED rows retain explicit open follow-ups.

### Specification Quality Checklist

QA aliases identify the 16 original unnumbered items in their existing order. Every original state is `[x]`; those authored checks are not accepted as execution evidence.

| Item | Original state | Status | Assessment | Follow-up |
| --- | --- | --- | --- | --- |
| QA-01 | [x] | CONFLICT | [No implementation details](checklists/requirements.md#L9) is stronger than current FR-005/FR-014's explicit claims/URL details and appended technical hierarchy. Re-review the intended boundary rather than trusting the blanket pass. | AUD-022-013. |
| QA-02 | [x] | IMPLEMENTED | User value is expressed in planner/commander stories and scope. | None. |
| QA-03 | [x] | PARTIAL | User stories are readable; tenant/assignment/API terminology needs stakeholder interpretation and conflict resolution. | AUD-022-012, AUD-022-013. |
| QA-04 | [x] | IMPLEMENTED | Mandatory stories, requirements, assumptions, and measurable-outcome sections are populated. | None. |
| QA-05 | [x] | IMPLEMENTED | No NEEDS CLARIFICATION marker remains in the original spec; separate formal questions nevertheless remain. | AUD-022-013 for those questions. |
| QA-06 | [x] | PARTIAL | Tenant policy, partial failure, history, and keyboard-pattern conflicts prevent full unambiguity. | AUD-022-001, AUD-022-003, AUD-022-005, AUD-022-007, AUD-022-013. |
| QA-07 | [x] | PARTIAL | Numeric thresholds exist; timing origin, baseline, and first-time-user study protocol lack agreed measurement detail. | AUD-022-011. |
| QA-08 | [x] | IMPLEMENTED | SCs describe user-visible availability, duplication, accuracy, time, interactions, and usability rather than framework internals. | None. |
| QA-09 | [x] | PARTIAL | Twelve base scenarios exist; recovery/race/country-amendment scenarios require the additional coverage identified here. | AUD-022-008, AUD-022-010. |
| QA-10 | [x] | IMPLEMENTED | Seven explicit edge cases are present. Their implementation is assessed separately above. | None. |
| QA-11 | [x] | CONFLICT | Base scope and country deferrals are explicit, but associated help/architecture/risk material attributes wider capabilities to the filter. | AUD-022-012, AUD-022-013. |
| QA-12 | [x] | PARTIAL | Dependencies and assumptions are named; tenancy/sign-off/precondition validity is not established. | AUD-022-001, AUD-022-013. |
| QA-13 | [x] | PARTIAL | Country placeholders, per-section failures, and ongoing URL state lack complete accepted validation cases. | AUD-022-008, AUD-022-010, AUD-022-013. |
| QA-14 | [x] | IMPLEMENTED | Primary AU selection/catalog/replay/list flows are covered by the four stories. This does not prove their execution. | None. |
| QA-15 | [x] | UNVERIFIED | [Meets measured outcomes](checklists/requirements.md#L29) has no corresponding SC-001/SC-005/SC-006 measurements. | AUD-022-011. |
| QA-16 | [x] | CONFLICT | The repeated no-implementation-details claim needs the same current-spec review as QA-01. | AUD-022-013. |

### Comprehensive Review Questions

Every CHK ID is represented separately with its unchanged original state. Source references and the corresponding remediation task provide the evidence/decision path. IMPLEMENTED here means the question has a concrete authored/source answer, not that the original formal review was signed.

| ID | Original state | Status | Evidence / answer or unresolved obligation | Follow-up |
| --- | --- | --- | --- | --- |
| CHK001 | [ ] | PARTIAL | [FR-013](spec.md#L118) specifies independent catalog loading; replay has running text, but client status is shared and replay result lifecycle ambiguous. | AUD-022-003, AUD-022-004. |
| CHK002 | [ ] | IMPLEMENTED | [Empty selection](spec.md#L111), edge 2, and analyzer no-match branches distinguish the two cases in source. | AUD-022-010 for fixtures. |
| CHK003 | [ ] | PARTIAL | [R-004](research.md#L63) names AbortController; request IDs exist, but presentation and replay generations need completion. | AUD-022-002, AUD-022-004. |
| CHK004 | [ ] | CONFLICT | [R-001](research.md#L5) defines a server-first order; current page forwards raw params and client initializes once. | AUD-022-005, AUD-022-006, AUD-022-012. |
| CHK005 | [ ] | CONFLICT | [T009/R-007](tasks.md#L53) include list-route pass-through, but it is only logged and FR-005 still requires scoped reads. | AUD-022-001. |
| CHK006 | [ ] | PARTIAL | [Select All/Clear All](../../apps/web/src/components/preparedness/jurisdiction-selector.tsx#L39) each emit one set; catalog timer is shared, but extra list refetch and temporal assertions remain. | AUD-022-006, AUD-022-010. |
| CHK007 | [ ] | PARTIAL | List loader has a catch message but no working list retry or stable independent error. | AUD-022-006, AUD-022-013. |
| CHK008 | [ ] | IMPLEMENTED | [FR-009](spec.md#L114) names both organisations and frameworks; both dedup paths are connected. | AUD-022-010. |
| CHK009 | [ ] | PARTIAL | [SC-001](spec.md#L147) says from selection change; no agreed instrumentation origin/budget breakdown or actual measurement. | AUD-022-011. |
| CHK010 | [ ] | PARTIAL | [FR-012](spec.md#L117) names affected section/retry; rendered error is global and cannot isolate its cause. | AUD-022-003. |
| CHK011 | [ ] | IMPLEMENTED | [Data model](data-model.md) and service define association through Organisation.jurisdiction_ids OR overlap. | None. |
| CHK012 | [ ] | IMPLEMENTED | [T022](tasks.md#L92) supplies exact message text, which the analyzer renders. | AUD-022-010 for interaction assertion. |
| CHK013 | [ ] | IMPLEMENTED | Separate no-match and no-selection text exists in analyzer branches; valid empty-data test fixture remains needed. | AUD-022-010. |
| CHK014 | [ ] | PARTIAL | [T021](tasks.md#L91) supplies notice copy and UI uses role=status, but reset/dismissal/publication semantics are not safe. | AUD-022-004. |
| CHK015 | [ ] | PARTIAL | [FR-008](spec.md#L113) and AU seed names establish canonical names, not a verified narrow-layout/localization policy for future country nodes. | AUD-022-007, AUD-022-008, AUD-022-013. |
| CHK016 | [ ] | IMPLEMENTED | [Plan](plan.md#L24) declares advisory/read-only scope; traced rehearsal constructs an in-memory ScenarioRun and does not execute an irreversible command. | None. |
| CHK017 | [ ] | UNVERIFIED | [Plan region constraint](plan.md#L20) is authored; deployed endpoint regions were not queried or established by this audit. | AUD-022-011, AUD-022-013. |
| CHK018 | [ ] | CONFLICT | Clients use no-store and source uses page-local state; [help](../../apps/web/src/content/help/articles/screen-by-screen/multi-jurisdiction-filter.mdx#L85) claims localStorage persistence. Browser history/share privacy policy is not a resolved storage-governance record. | AUD-022-012, AUD-022-013. |
| CHK019 | [ ] | UNVERIFIED | Query jurisdiction/tenant values are logged; no feature-specific privacy assessment establishes profiling/telemetry treatment. | AUD-022-013. |
| CHK020 | [ ] | PARTIAL | [Route log](../../apps/api/app/api/routes/organisations.py#L22) exists, but selection-log retention/access rules are not specified by the feature. | AUD-022-013. |
| CHK021 | [ ] | PARTIAL | Authored OpenAPI and framework-generated docs exist; generic output schemas and direct input policy disagree. | AUD-022-009, AUD-022-010. |
| CHK022 | [ ] | IMPLEMENTED | [R-002](research.md#L24) versus [R-003](research.md#L43) deliberately separates repeated API params from comma-separated user URL state. | None. |
| CHK023 | [ ] | PARTIAL | Unavailable jurisdiction source has neither useful fallback nor actual offered retry; it can collapse to unexplained emptiness. | AUD-022-006, AUD-022-013. |
| CHK024 | [ ] | PARTIAL | [FR-012](spec.md#L117) identifies the affected catalog, but Promise.all/shared status suppress independent success. | AUD-022-003. |
| CHK025 | [ ] | CONFLICT | Missing/expired claims need an agreed failure policy; anonymous defaults and the protected-prefix gap do not implement FR-005. | AUD-022-001, AUD-022-013. |
| CHK026 | [ ] | IMPLEMENTED | [Plan](plan.md#L8) requires no new cloud resources; current cache is in-process, not a newly provisioned service. Deployment outcome is not implied. | None. |
| CHK027 | [ ] | PARTIAL | Route logs are not a complete filter-change audit policy; help says changes are not independently logged while broader provenance claims persist. | AUD-022-012, AUD-022-013. |
| CHK028 | [ ] | PARTIAL | [FR-014](spec.md#L119) defines silent UI dropping; no explicit security/privacy decision defines whether sanitized rejected IDs are audited. These are separable concerns, not inherently contradictory. | AUD-022-013. |
| CHK029 | [ ] | CONFLICT | Preparedness scope is explicit; [authority-handoff documentation](../../docs/architecture/data/jurisdiction-filter.md#L16) attributes Response/Recovery control to this filter without a connected call path. | AUD-022-012, AUD-022-013. |
| CHK030 | [ ] | UNVERIFIED | WCAG AA is named but feature-specific contrast/focus/target-size results were not supplied or executed. | AUD-022-007, AUD-022-011. |
| CHK031 | [ ] | PARTIAL | Selector count and stale notice have live/status semantics; catalog loading/results are plain paragraphs without a resolved announcement contract. | AUD-022-007. |
| CHK032 | [ ] | PARTIAL | No explicit feature focus policy for retry/loading transitions is documented or tested. | AUD-022-007, AUD-022-013. |
| CHK033 | [ ] | IMPLEMENTED | Empty selection text and replay-disabled message both direct the user to select jurisdictions. | AUD-022-010 for assertions. |
| CHK034 | [ ] | PARTIAL | [R-003](research.md#L43) identifies the spec-020 URL pattern; ongoing history restoration and contradictory global-persistence prose remain unresolved. | AUD-022-005, AUD-022-012. |
| CHK035 | [ ] | IMPLEMENTED | [Data model](data-model.md) distinguishes organisation membership from framework junction membership while applying OR logic to both. | None. |
| CHK036 | [ ] | IMPLEMENTED | Edge case 3 and [NFR-002](spec.md#L132) both specify 300ms; no contradictory interval appears in those requirements. | AUD-022-006 for the extra-request implementation issue. |
| CHK037 | [ ] | PARTIAL | Both requirements demand old-context clearing, but arrays, delayed loading, deferred replay, and effects do not enforce one consistent presentation boundary. | AUD-022-002, AUD-022-004. |
| CHK038 | [ ] | PARTIAL | No-stale rules are stated consistently but not applied uniformly to catalog failure and replay output. | AUD-022-002, AUD-022-003, AUD-022-004. |
| CHK039 | [ ] | PARTIAL | Total 2 seconds and 300ms are known; transport/render budget, workload envelope, and instrumentation are absent. | AUD-022-011. |
| CHK040 | [ ] | MISSING | No feature-local measurement protocol defines the old single-jurisdiction interaction count used by SC-005. Scoped evidence search found no replacement baseline. | AUD-022-011. |
| CHK041 | [ ] | MISSING | No first-time-user sampling/measurement protocol for SC-006 was found in scoped inputs/evidence. | AUD-022-011. |
| CHK042 | [ ] | PARTIAL | Request/union counts are inspectable, but no planner-reviewed expected findings or substantive accuracy criteria establish SC-003. | AUD-022-004, AUD-022-010, AUD-022-011. |
| CHK043 | [ ] | PARTIAL | One-endpoint-success/other-failure behavior is not independently represented or asserted. | AUD-022-003, AUD-022-010. |
| CHK044 | [ ] | PARTIAL | `replace` is specified; reconciling navigated URLs/Back/Forward is not implemented by initializedRef-only restoration. No requirement for one history entry per toggle is invented here. | AUD-022-005, AUD-022-013. |
| CHK045 | [ ] | IMPLEMENTED | [R-008](research.md#L145) explicitly documents the intentional change from all/default NSW to empty without IDs. | AUD-022-012 for updated operator/setup material. |
| CHK046 | [ ] | PARTIAL | Fresh list validation rejects absent/inactive IDs, but process-cache/active-session removal and refetched-list revalidation rules are unspecified. | AUD-022-005, AUD-022-006, AUD-022-013. |
| CHK047 | [ ] | PARTIAL | Catalog AbortController/request IDs exist; old rendered arrays and unguarded replay completions remain. | AUD-022-002, AUD-022-004, AUD-022-010. |
| CHK048 | [ ] | PARTIAL | Commonwealth-only source works; US1's explicit paired scenario does not test the standalone case or ACT overlap. | AUD-022-010. |
| CHK049 | [ ] | UNVERIFIED | Static volume is known and SC-001 supplies a target, but no all-nine time/display measurement proves performance. | AUD-022-011. |
| CHK050 | [ ] | PARTIAL | Nine short AU IDs are bounded; unrelated state preservation, canonical duplicates, future nodes, and a practical supported URL policy are not validated. | AUD-022-005, AUD-022-013. |
| CHK051 | [ ] | PARTIAL | Source-local state naturally avoids a shared preference store, but two-tab/cross-navigation acceptance and help consistency are not established. | AUD-022-005, AUD-022-012. |
| CHK052 | [ ] | PARTIAL | Dynamic active list and string levels permit changing counts, but payload validation, no-active recovery, new-level contract compatibility, and placeholder behavior need definition. | AUD-022-006, AUD-022-008, AUD-022-009. |
| CHK053 | [ ] | IMPLEMENTED | [Typed junction model](../../packages/domain/src/domain/models/framework_assignment.py#L7), populated seed, and actual catalog/replay consumers establish the dependency in source. | AUD-022-010 for stronger assertions. |
| CHK054 | [ ] | PARTIAL | [R-003](research.md#L43) documents adaptation, but no shared provider exists and same-route restoration is incomplete. | AUD-022-005, AUD-022-012. |
| CHK055 | [ ] | CONFLICT | Inspected auth/tenant middleware and service signatures do not establish the claimed Entra-derived scoped-query dependency. | AUD-022-001. |
| CHK056 | [ ] | PARTIAL | 49 organisations satisfy the approximate assumption; frameworks number 27. Capacity/pagination threshold is not defined by a measurement. | AUD-022-011, AUD-022-013. |
| CHK057 | [ ] | IMPLEMENTED | [Assumption](spec.md#L137) explicitly chooses OR; services implement it. No AND capability is required by this spec. | None. |
| CHK058 | [ ] | PARTIAL | Jurisdictions are sorted; combined catalogs currently follow seed order. An intended stable catalog ordering rule is not explicitly specified. | AUD-022-013. |
| CHK059 | [ ] | PARTIAL | Silent invalid-URL presentation does not decide whether/how to record sanitized rejection telemetry. Privacy/audit owners must disposition it. | AUD-022-013. |
| CHK060 | [ ] | PARTIAL | The immediate-clear requirement is not satisfied during the debounce interval; exact generation/last-selection semantics need assertions. | AUD-022-002, AUD-022-004, AUD-022-010. |
| CHK061 | [ ] | PARTIAL | FR/NFR/SC/task IDs exist; scenarios are numbered within stories only. This report adds traceable local aliases but does not edit the original scheme. | AUD-022-013. |

### Plan Gate Claims

The 15 original [plan gates](plan.md#L28) and its post-design all-PASS statement are authored review assertions. They are not deployed-state attestations or a substitute for unresolved checklist items.

| Gate | Status | Assessment | Follow-up |
| --- | --- | --- | --- |
| Gate 1 - Primacy of Life | PARTIAL | Cross-boundary planning value exists, but stale catalogs and unearned clean replay output undermine the claimed protection. | AUD-022-002, AUD-022-004. |
| Gate 2 - National EM Principles | PARTIAL | AU union supports collaboration; current-state correctness, graceful failure, and shareable restoration remain incomplete. | AUD-022-003, AUD-022-005. |
| Gate 3 - Multi-Hazard | IMPLEMENTED | UI has flood/bushfire/cyclone and replay receives hazard/jurisdictions. The generic legacy review is not proof of richer evacuation planning. | AUD-022-009, AUD-022-011. |
| Gate 4 - Transparency/Auditability | PARTIAL | URL and logs exist; tenant query provenance and selection/audit policy are not established. | AUD-022-001, AUD-022-013. |
| Gate 5 - Warning Compliance | IMPLEMENTED | Inspected path does not publish public warnings; this is a scoped non-actuation conclusion, not global warning compliance. | None. |
| Gate 6 - Evacuation | IMPLEMENTED | Feature consumes a legacy advisory review, not an evacuation activation operation. | None. |
| Gate 7 - Recovery | CONFLICT | Base scope does not change recovery, but associated filter architecture claims authority-dependent recovery transitions. | AUD-022-012. |
| Gate 8 - Cloud Platform | UNVERIFIED | No new resource is requested by the plan; deployed platform/location and CI outcomes were not inspected through cloud operations. | AUD-022-011, AUD-022-013. |
| Gate 9 - PPRR | IMPLEMENTED | Preparedness page is the scoped entry point. Actual lifecycle transitions belong to other features. | AUD-022-012 for attribution. |
| Gate 10 - Governance/Quality | PARTIAL | Backend tests are authored; workflow tests, non-skipped runs, and formal approvals are missing/unverified. | AUD-022-010, AUD-022-011, AUD-022-013. |
| Non-Negotiable 1 - Human Authorization | IMPLEMENTED | Explicit run action generates an advisory result without traced irreversible actuation. | None. |
| Non-Negotiable 2 - Sovereignty | UNVERIFIED | AU-only seed references and plan region prose do not attest actual deployed data residency. Foreign operations remain deferred. | AUD-022-008, AUD-022-013. |
| Non-Negotiable 3 - Privacy | PARTIAL | Shared seeds are reference data, but authenticated tenant boundaries and selection-log privacy decisions are unresolved. | AUD-022-001, AUD-022-013. |
| Non-Negotiable 4 - Interoperability | PARTIAL | Repeated/single query compatibility exists, but schemas/input policy disagree. | AUD-022-009. |
| Non-Negotiable 5 - Graceful Degradation | PARTIAL | Catalog and control-source failure handling do not match the per-section/recoverable design. | AUD-022-003, AUD-022-006. |

### Associated Review/Evidence Assessment

| Artifact or assertion | Status | What it proves and does not prove | Follow-up |
| --- | --- | --- | --- |
| Backend test files | IMPLEMENTED | Authored tests exercise services and in-process routes. They are not observed runs, and their assertion gaps are explicit in T003/T004/T005/T006. | AUD-022-010, AUD-022-011. |
| Stored Playwright artifacts | UNVERIFIED | JUnit timestamp is 2026-05-06T07:06:36.537Z; root totals are 76 tests, 76 skipped, 0 failures. Four preparedness cases are skipped. JSON reports expected=0, skipped=76. Neither establishes feature success at the reviewed revision. | AUD-022-011. |
| Rubric baseline/comparator | UNVERIFIED | Authored portfolio baseline 1.8 and comparator 3.8 exist under relocated comparator spelling. They do not supply per-022 HYP-020 scores, every-change consultation, or operational measurements. | AUD-022-013. |
| Hypothesis stub | MISSING | Named HYP-HYP-020 artifact and normalized HYP-020 replacement were not found in scoped evidence search; [contract](../028-capstone-alignment/contracts/evidence-stub.contract.md#L46) requires a normal HYP-NNN filename. | AUD-022-013. |
| Feature-value ledger | UNVERIFIED | [Manual-row ratio/sign-off label](../shared/feature-value-ledger.md#L6) and response-time(+0.05)/zero-gap row are published prose, not raw SC evidence or independent current-review sign-off. | AUD-022-011, AUD-022-013. |
| Active help, sections 1-4/7/9/11 | CONFLICT | Claims top-bar placement, claim-limited/default selections, Apply, browser persistence, persona locks, shortcuts, and mid-session claim handling that the inspected page-local control does not implement. | AUD-022-012. |
| Active help, sections 5-6/10/11.4 | CONFLICT | Claims global read/action scoping, cross-jurisdiction effect dialogs, and audit witnesses/KPI scoping not connected to the preparedness filter. Section 8/12's navigation guidance is consequently not a reliable recovery recipe. | AUD-022-012, AUD-022-013. |
| Tenancy/filter/cross-sector architecture | CONFLICT | Full descriptions name jurisdiction-as-tenant partitioning, lead-agency handoff, and protocols. The actual spec-022 path is an AU reference-data union, not those enforcement mechanisms. | AUD-022-001, AUD-022-012. |
| RISK-NEW-007 / RISK-NEW-011 treatments | UNVERIFIED | Authored residual risk scores and past next-review dates do not establish filter-triggered Unified Command or activation-status mitigation. No such connected selection action is present. | AUD-022-012, AUD-022-013. |

## Future Validation Instructions

**None of the commands or manual executions in this section ran during this audit.** Obtain separate execution authorization first. Proposed new paths are not linked as existing evidence.

### Fixtures and Existing Test Homes

Static projections of the inspected AU seed files establish these useful fixtures. Counts describe authored seed membership, not HTTP/browser observations.

| Fixture | Exact expected membership/use |
| --- | --- |
| AU full baseline | 9 active jurisdictions; 49 unique organisations; 27 unique frameworks; 123 current assignment records. Jurisdiction order: commonwealth, nsw, qld, sa, tas, vic, wa, act, nt. |
| NSW | Six organisations: frnsw, nsw-rfs, ses-nsw, nswpf, nsw-ambulance, mrnsw; 15 applicable frameworks. |
| VIC | Five organisations: frv, cfa-vic, ses-vic, vicpol, av; 14 applicable frameworks. |
| QLD | Four organisations: qfd, ses-qld, qps, qas; 14 applicable frameworks. NSW+QLD therefore has exactly ten organisation IDs, not an arbitrary larger count. |
| SA | Five organisations: samfs, sacfs, ses-sa, sapol, saas; 13 applicable frameworks. Use for the single-SA replay scenario. |
| ACT/Commonwealth overlap | ACT has seven organisations; Commonwealth has eleven. AFP is explicitly in both ([seed](../../packages/domain/src/domain/seed/organisations_australia.json#L153)); combined output must have seventeen unique organisations with AFP once. |
| State-only framework | [nsw-emplan](../../packages/domain/src/domain/seed/frameworks_australia.json#L396) and nsw-flood-communications must not appear for VIC-only selection. National aiims-national must appear once for any selected AU jurisdiction or union. |
| Controlled additional fixtures (proposed) | Active jurisdiction with no orgs/assignments; inactive jurisdiction; overlapping org; unassigned framework; ended assignment; assignment-versus-applicability disagreement; two tenants with distinguishable records; dynamic country placeholders. Expected sets must be independent of the service under test. |
| Controlled async fixtures (proposed) | Deferred A/B responses with independent org/framework settlement, explicit rejected requests, abort-ignoring transport, duplicate/repeated/mixed URL input, and selected-ID mismatched replay response. |

Reuse [unit tests](../../tests/unit/test_multi_jurisdiction_filter.py), [multi-jurisdiction contract tests](../../tests/contract/test_multi_jurisdiction_contract.py), [legacy contract](../../tests/contract/test_preparedness_contract.py), [analysis integration tests](../../tests/integration/test_preparedness_analysis.py), and [replay simulation tests](../../tests/simulation/test_preparedness_replays.py). Proposed frontend homes are `apps/web/__tests__/preparedness-client.test.tsx`, `apps/web/__tests__/operating-model-analyzer.test.tsx`, `apps/web/tests/a11y/jurisdiction-selector.test.tsx`, and the originally requested `tests/e2e/multi-jurisdiction-filter.spec.ts`. The existing preparedness page object may be extended; its readiness/lessons locators do not currently test this feature.

### Commands, Prerequisites, and Assertions

| Group | Future command and working directory | Prerequisites / expected result |
| --- | --- | --- |
| V1 | From repository root: `python -m pytest tests/unit/test_multi_jurisdiction_filter.py tests/contract/test_multi_jurisdiction_contract.py tests/contract/test_preparedness_contract.py -v` | Use the chosen Python >=3.12 project/dev environment and API dependencies, configured later. [Root conftest](../../tests/conftest.py#L10) resolves monorepo imports. Keep cloud credentials/telemetry inactive, replace identity/agent external work with approved deterministic fixtures, and isolate/clear seed cache when fixture roots are reused. Expect exact membership, schema, identity-denial, and empty/unknown-policy assertions, not skipped cases or count-only passes. |
| V2 | From repository root: `python -m pytest tests/integration/test_preparedness_analysis.py tests/simulation/test_preparedness_replays.py -v` | Same environment and network-isolated deterministic agent fixture; assert exact selected memberships, real assignment use, valid replay content, and no invalid-context success. In-process tests do not prove deployed authentication. |
| V3 | From repository root, after proposed files exist: `pnpm --filter @ama/web exec vitest run __tests__/preparedness-client.test.tsx __tests__/operating-model-analyzer.test.tsx tests/a11y/jurisdiction-selector.test.tsx` | Installed workspace dependencies and existing [Vitest/jsdom setup](../../apps/web/vitest.config.ts#L17). Fake timers/deferred transports must cover 299/300ms, immediate clearing, independent errors, URL reconciliation, replay generations, placeholder safety, and keyboard assertions. Never accept "no tests found" as a pass. |
| V4 | From repository root, after T025 file exists: `pnpm --filter @ama/web exec playwright test multi-jurisdiction-filter.spec.ts --project=chromium --project=mobile` | Separate permission to start servers/browser and write test artifacts. [Playwright config](../../apps/web/playwright.config.cts#L17) launches/reuses API and web servers and writes shared reporters. Ensure those services are isolated local instances with correct auth fixtures, no cloud integrations, known seed versions, and no unrelated service on the reused ports. Expect exact controls, requests, and rendered data across desktop/mobile, all scenarios/edges, and no skipped filter cases. |
| V5 | Manual quickstart, keyboard/screen-reader, planner, privacy, persona, hypothesis, and checklist review | Approved local environment and named reviewers; measure real actions/outcomes, not source labels. Record every step below, the SC timing/study protocol, explicit policy decisions, evidence locations, actual revision, and timestamps. No script can substitute for human validation or regulatory approval. |
| V6 | From repository root: `python -m pytest tests/ -v` | Separately approved full-suite environment with required optional/test dependencies and external-service isolation. T027 explicitly asks for the full suite; record real failures/skips and prerequisites. Do not claim completion from a narrower run, and do not execute cloud-marked tests without separate approved staging prerequisites. |

Python/environment setup, dependency installation, tests, servers, and browsers above are future work, not actions authorized by this review-only request. Full pytest and Playwright can execute imports or integrations and create outputs; their isolation must be reviewed before execution.

### Quickstart Validation Coverage

QS aliases correspond to the 13 original manual steps. All manual outcomes remain UNVERIFIED until future V5 evidence exists.

| Step | Status | Required future assertion | Follow-up |
| --- | --- | --- | --- |
| QS-01 | UNVERIFIED | Bare /preparedness has no preselected IDs, communicates selection, and does not report an assessment as completed. | AUD-022-004, AUD-022-011. |
| QS-02 | UNVERIFIED | NSW selection shows only its exact organisation/assigned-framework sets. | AUD-022-010, AUD-022-011. |
| QS-03 | UNVERIFIED | NSW+VIC shows exact union with no duplicate cards or excluded-state leakage. | AUD-022-010, AUD-022-011. |
| QS-04 | UNVERIFIED | Select All selects all nine AU nodes in one action and renders full current baseline within target. | AUD-022-008, AUD-022-010, AUD-022-011. |
| QS-05 | UNVERIFIED | Clear All immediately empties current catalogs, disables replay, and clears old-context output. | AUD-022-002, AUD-022-004, AUD-022-011. |
| QS-06 | UNVERIFIED | NSW+QLD URL restores on reload/new tab and reconciles same-route history/navigation. | AUD-022-005, AUD-022-011. |
| QS-07 | UNVERIFIED | Mixed/invalid URL IDs are safely normalized; invalid-only means empty, never NSW. | AUD-022-005, AUD-022-011. |
| QS-08 | UNVERIFIED | Replay sends exact IDs, displays current findings, and clears them with notice on change. | AUD-022-004, AUD-022-011. |
| QS-09 | UNVERIFIED | Both run and replay Retry remain disabled when no jurisdiction is selected. | AUD-022-010, AUD-022-011. |
| QS-10 | UNVERIFIED | Each affected catalog immediately shows loading without previous records. | AUD-022-002, AUD-022-003, AUD-022-011. |
| QS-11 | UNVERIFIED | Fail each endpoint independently; inline section retry recovers without stale data. List-source failure also has a working retry. | AUD-022-003, AUD-022-006, AUD-022-011. |
| QS-12 | UNVERIFIED | Approved Tab/Enter/Arrow/Space/Escape path, screen-reader names, and focus behavior work. | AUD-022-007, AUD-022-011. |
| QS-13 | UNVERIFIED | Rapid toggles cause one final request per catalog after 300ms, no extra selection-driven list fetch, and no outdated completion writes. | AUD-022-002, AUD-022-006, AUD-022-011. |

## Completion Boundary

This report establishes source traceability and an open remediation plan, not feature acceptance. Original task and checklist states remain untouched. Real non-AU operations, tenant-private safety, deployed residency/authentication, runtime races, WCAG conformance, performance/usability metrics, full-suite success, and human/governance approvals must not be inferred from authored source or this report.

Audit-text verification is limited to exact original task IDs/states, required coverage aliases, existing linked files and 1-based line bounds, valid evidence statuses, uniquely defined unchecked follow-ups, and editor diagnostics for this report. These checks do not execute the future validation commands or prove application correctness.
