# Implementation Review Tasks: Disaster Mapper UI

**Review date:** 2026-09-11  
**Reviewed revision:** `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`  
**Specification:** 020-disaster-mapper-ui  
**Method:** Fresh, isolated, static implementation and test-source audit.  
**Disposition:** Remediation required; not a release approval.

## Scope and Evidence Rules

This report applies the complete [Review Contract](../001-spec-implementation-audit/README.md#L12).
The checkout matched the requested revision on `main`. Existing audit reports and the audit index were
left untouched. This report is the only authored file. No branch, commit, product source, original
task checkbox, specification, evidence record, or other audit was changed. No delegation, application
imports, product tests, builds, browser sessions, servers, cloud queries, or deployments were performed.
PowerShell was used only for read-only Git metadata and text inspection/validation.

The audit read all eight local inputs in full, including both clarification sessions and the appended
personas, hypothesis, and scope amendments. Implementation was followed from the actual entry route
through rendered components, filter and loading controllers, API registration, middleware, storage,
workspace navigation, infrastructure configuration, and test assertions. Applicable code-review,
Bicep/security instructions and the Python fact-grounded and Cosmos DB review skills were consulted.
No interpreter, SDK runtime, cloud policy, resource availability, or deployed topology is inferred
from source. Library/platform behavior requiring execution or authoritative platform verification
remains unverified.

| Evidence status | Meaning in this report |
| --- | --- |
| IMPLEMENTED | Inspected source supports the scoped behavior or authored artifact; not runtime success. |
| PARTIAL | Some required behavior exists, but a specific obligation is absent or contradicted. |
| MISSING | The required behavior/artifact was not found after the stated scoped search. |
| CONFLICT | Requirement, task, supporting document, or implementation disagree. |
| UNVERIFIED | Source cannot establish execution, measurement, approval, or deployed state. |
| SUPERSEDED | Explicit repository evidence identifies a replacement; remaining obligations still apply. |

There are **36 original tasks**, all originally `[x]`; **39 FRs** including FR-003a; **3 NFRs**;
**9 SCs**; **27 acceptance scenarios**; **7 edge cases**; and **130 original checklist questions**,
all originally `[ ]`. All receive individual rows below. There are **29 unchecked remediation tasks**.
USn-ASn, EC-nn, A-nn, CL-nn, and PG-nn are this report's positional labels for otherwise unnumbered
source obligations, not amendments to the original identifier scheme.

### Inputs and Associated Records

| Input | Extent and evidentiary use |
| --- | --- |
| [spec.md](spec.md#L1) | Entire specification, FR/NFR/SC, five stories, seven edges, ten assumptions, twelve clarifications, PER-052/PER-053/PER-054, HYP-018, SCP-058/SCP-059/SCP-060. |
| [tasks.md](tasks.md#L1) | Entire T001 through T036 list, dependencies, checkpoints, execution strategy, and notes. Original states preserved. |
| [plan.md](plan.md#L1) | Entire plan, structure, performance targets, and ten self-authored constitution-gate PASS claims. |
| [research.md](research.md#L1) | Entire R-001 through R-008 decisions, alternatives, authentication, clustering, contrast, filtering, and telemetry assertions. |
| [data-model.md](data-model.md#L1) | Entire entity model, GeoJSON response schema, domain mapping, predicates, pagination, unmapped counts, and indexing recommendations. |
| [contracts/incidents-map-api.md](contracts/incidents-map-api.md#L1) | Entire request/response/error contract and progressive loading strategy. |
| [quickstart.md](quickstart.md#L1) | Entire prerequisite, configuration, validation, and path guide. Instructions are not an execution record. |
| [checklists/requirements.md](checklists/requirements.md#L1) | All CHK001 through CHK130 questions and notes. No reviewer completion is implied. |
| [constitution](../../.specify/memory/constitution.md#L1) | Entire constitution, including human review, AU residency, privacy, interoperability, graceful degradation, and the model-hosting-only carve-out. That carve-out does not authorize non-AU map/incident services. |
| [persona profile contract](../027-spec-hardening/contracts/persona-profile.md#L1) | Entire required identity, authority, accessibility, scenarios, and named SME/practitioner validation structure. |
| [hypothesis evidence contract](../028-capstone-alignment/contracts/evidence-stub.contract.md#L1) | Entire six-section stub contract and controlled status transitions. |
| [rubric baseline](../028-capstone-alignment/evidence/rubric-baseline.md#L1) | Entire frozen portfolio baseline; not a mapper-specific usability or validation result. |
| [rubric postfeature](../028-capstone-alignment/evidence/rubric-postfeature.md#L1) | Entire portfolio structural self-assessment; does not measure HYP-018 specifically. |
| [decision record](../028-capstone-alignment/evidence/decision-record.md#L1) | Entire linked decision record; D-009 remains deferred and does not expand this map's country scope. |
| [mapper help article](../../apps/web/src/content/help/articles/screen-by-screen/disaster-mapper.mdx#L1) | Entire associated screen reference; many advertised controls are not present in the connected mapper. Not accepted as evidence of implementation. |
| [last-run record](../../apps/web/test-results/.last-run.json#L1) | Tracked file says `failed` and lists 13 opaque test IDs, without a run date, source SHA, or mapper attribution. Not 13 proven mapper failures. |

The following six local error records were also read in full. Git's tracked-path listing does not
include these error-context files; they are local historical evidence, not reproducible artifacts
at the reviewed commit. Their statements and embedded snapshots are not instructions for this audit.
They establish that prior failures were recorded, not the current pass/fail state or any successful
SC measurement.

| Historical record | Recorded observation | Current-revision result |
| --- | --- | --- |
| [heading/loading error](../../apps/web/test-results/test_disaster_mapper-Disas-9d0cc-e-heading-and-loading-state-chromium/error-context.md#L7) | Disaster heading not found; snapshot includes a count and map application. | UNVERIFIED |
| [heading hierarchy error](../../apps/web/test-results/test_disaster_mapper-Disas-b6d1c-as-proper-heading-hierarchy-chromium/error-context.md#L7) | No level-one heading found. | UNVERIFIED |
| [no-results test error](../../apps/web/test-results/test_disaster_mapper-Disas-bd2e0--filters-exclude-everything-chromium/error-context.md#L7) | Test fails on a heading assertion despite a snapshot showing the no-results notice. | UNVERIFIED |
| [mobile filter error](../../apps/web/test-results/test_disaster_mapper-Disas-d7a68-s-to-bottom-sheet-on-mobile-chromium/error-context.md#L7) | Test expects type controls after the click that hides an initially open filter sheet. | UNVERIFIED |
| [unmapped-notice error](../../apps/web/test-results/test_disaster_mapper-Disas-f222c-en-unmapped-incidents-exist-chromium/error-context.md#L7) | `/unmapped/i` does not match the displayed "could not be mapped" wording. | UNVERIFIED |
| [mobile page-load error](../../apps/web/test-results/test_disaster_mapper-Disas-f8365-ge-loads-on-mobile-viewport-chromium/error-context.md#L7) | Heading assertion fails on a mobile snapshot with filter controls and map application. | UNVERIFIED |

## Connected Implementation and Scoped Searches

1. [Legacy route](../../apps/web/src/app/disasters/page.tsx#L1) redirects to `/` without reading query
   parameters. The [home page](../../apps/web/src/app/page.tsx#L4) explicitly documents the move and
   dynamically renders DisasterMap, FilterPanel, and IncidentSidebar. The [root layout](../../apps/web/src/app/layout.tsx#L17)
   wraps it in the [application shell](../../packages/ui/src/components/layout/app-shell.tsx#L6).
   This is a moved experience, not a missing page implementation. Losing bookmarked filters remains a defect.
2. The [filter hook](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L95)
   produces URL-derived parameters. The [home-page load controller](../../apps/web/src/app/page.tsx#L91)
   calls the [progressive client](../../apps/web/src/lib/api/incidents-map.ts#L111). The default browser
   request is `/api/incidents/map`; the [rewrite](../../apps/web/next.config.ts#L28) and
   [API prefix](../../apps/api/app/core/settings.py#L10) do not add `/v1`.
3. [Router registration](../../apps/api/app/api/router.py#L56) reaches the
   [map handler](../../apps/api/app/api/routes/incidents_map.py#L111) and
   [repository](../../apps/api/app/repositories/incident_map_repository.py#L20). Storage has moved to
   `seed`, `kind = 'disaster'`. The [workspace lookup](../../apps/api/app/services/dashboard_service.py#L10)
   reads the same historical disaster source; the old `incidents` container name alone is not a missing-implementation finding.
4. [Map lifecycle](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L63) reaches
   [marker layers](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L132), not the filter's
   decorative [severity icons](../../packages/ui/src/components/disaster-map/severity-icon.tsx#L22).
   The separate [fallback table](../../packages/ui/src/components/disaster-map/list-view-fallback.tsx#L50)
   and [SearchBar](../../packages/ui/src/components/disaster-map/search-bar.tsx#L20) exist. The former
   is disconnected; the latter has a live inline equivalent at [home search](../../apps/web/src/app/page.tsx#L160).
5. [Repository unit tests](../../tests/unit/test_incident_map_repository.py#L95) contain 22 test declarations;
   [API contract tests](../../tests/contract/test_incidents_map_contract.py#L47) contain 25; the renamed
   [mapper E2E file](../../tests/e2e/test_disaster_mapper.spec.ts#L81) contains 15. These are source counts,
   not executed/pass counts. [Playwright's replacement config](../../apps/web/playwright.config.cts#L1)
   discovers the file in the general chromium/mobile projects. Its `.ts` predecessor is not required
   for discovery. [Vitest](../../apps/web/vitest.config.ts#L17) provides existing unit/a11y test homes.

| Search | Scope and terms | Result used, with controlling evidence |
| --- | --- | --- |
| S01 | Entire target feature directory; spec/task/plan/research/data-model/contracts/checklists and nested files. | Eight inputs, no local amendment/review/evidence file beyond these; appended amendments were read within [spec](spec.md#L248). |
| S02 | `apps/web/src` and `packages/ui/src`: DisasterMap, FilterPanel, IncidentSidebar, ListViewFallback, SearchBar, incidents-map. | Live root replacement found; fallback only definition/export, no mounted caller. [Root rendering](../../apps/web/src/app/page.tsx#L211). |
| S03 | All disaster-map source components plus live root page: tabIndex, onKeyDown, keyboard, aria, touch/swipe/pointer handlers, timeout and selection. | Keyboard activation only in the disconnected table's rows; no per-marker focus controller or sheet swipe/outside-close implementation. [Map markup](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L223), [table rows](../../packages/ui/src/components/disaster-map/list-view-fallback.tsx#L145). |
| S04 | Map route/repository, API factory/router/settings, auth/tenant/Entra/RBAC middleware, next config, shell/layout, and web middleware filename search. | Global middleware exists, but its verified-protected prefixes omit the map and its repository ignores request scope. No web middleware file was found at the conventional searched paths. [Entra prefixes](../../apps/api/app/middleware/entra_auth.py#L37), [RBAC prefixes](../../apps/api/app/middleware/rbac_check.py#L32). |
| S05 | `apps/web/src`, `packages/ui/src`, `infra` source files, scripts and workflow declarations: Maps settings, CORS, authSettings, Azure Maps roles/outputs, API upstream, disaster_mapper metrics. | Global Maps location, key-only browser, empty CORS default, no connected browser metric instruments. Generated bundles and local secret files are not accepted as implementation or configuration proof. [Maps binding](../../infra/main.bicep#L439). |
| S06 | Mapper test filenames; `tests/unit`, `tests/contract`, `tests/e2e`, web unit/a11y tests; mapper/controller names and callers; all workflow pytest/Playwright selectors. | Existing tests found, not missing by historical name. Other simulation-map tests concern another caller. The [Disasters page object](../../tests/e2e/web-coverage/_support/pages/disasters.po.ts#L11) looks for declarations/headings and is not replacement coverage of this read-only map. |
| S07 | Exact `HYP-HYP-018.md` and `HYP-018.md` filename search under specs; HYP-018/PER-052/PER-053/PER-054 references in target and linked evidence; mapper references under docs. | No matching HYP-018 stub found. [Spec's target](spec.md#L260), portfolio baseline/postfeature and D-009 record inspected; no mapper-specific named operator/SME approval supplied. |
| S08 | Local mapper test-results/error-context files and tracked-path listing, not other audit reports. | Six historical failure contexts, no matching date/SHA/pass attestation; [last-run](../../apps/web/test-results/.last-run.json#L2) records a non-attributed failed run. |

Search-based negatives are bounded to these scopes. No absence of a deployed control is asserted
from a local source search, and no absent historical filename is used as proof of absent behavior.

## Prioritized Findings

P1 findings block acceptance of the affected security, safety, or operational behavior. P2 findings
are important correctness, verification, or contractual gaps. Shared surfaces below are reviewed
only for this mapper's obligations, not as an audit of their other callers.

| Follow-up | Priority | Finding and status | Exact controlling evidence |
| --- | --- | --- | --- |
| AUD-020-001 | P1 | PARTIAL: incident read access is not authenticated/authorized or jurisdiction-scoped by the connected path. Deployment protection is UNVERIFIED. | [map handler](../../apps/api/app/api/routes/incidents_map.py#L111), [default claims](../../apps/api/app/middleware/auth_middleware.py#L11), [Entra scope](../../apps/api/app/middleware/entra_auth.py#L37), [query](../../apps/api/app/repositories/incident_map_repository.py#L79) |
| AUD-020-002 | P1 | CONFLICT: Maps is explicitly global, contradicting Australia East-only requirements; tile residency and policy/approval evidence are UNVERIFIED. | [binding](../../infra/main.bicep#L439), [allowed locations](../../infra/modules/azure-maps.bicep#L5), [NFR-001](spec.md#L180) |
| AUD-020-003 | P1 | PARTIAL: production disables local auth while the browser only uses a key; CORS, account outputs, and deployment configuration are not connected. | [auth policy](../../infra/modules/azure-maps.bicep#L35), [browser auth](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L79), [web settings](../../infra/main.bicep#L1300), [upstream config](../../apps/web/next.config.ts#L7) |
| AUD-020-004 | P1 | CONFLICT: severity is not encoded by marker colour/shape; all individual markers use type-specific teardrops. | [pin generator](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L115), [incidentType expression](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L193) |
| AUD-020-005 | P1 | MISSING: the five-second sortable fallback is not connected; a 15-second initialization overlay replaces it. | [timeout](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L133), [always-map branch](../../apps/web/src/app/page.tsx#L242) |
| AUD-020-006 | P1 | PARTIAL: an obsolete in-flight response can overwrite a newer filter's incidents, counts, timestamp, and loading state. | [fetch without signal](../../apps/web/src/lib/api/incidents-map.ts#L86), [post-await publication](../../apps/web/src/lib/api/incidents-map.ts#L124), [state callback](../../apps/web/src/app/page.tsx#L103) |
| AUD-020-007 | P1 | PARTIAL: missing/failed production storage initialization can return successful empty in-memory data instead of an availability error. | [constructor fallback](../../apps/api/app/repositories/incident_map_repository.py#L36), [query fallback](../../apps/api/app/repositories/incident_map_repository.py#L152) |
| AUD-020-008 | P1 | PARTIAL: malformed locations may be plotted at a fabricated origin, escape bounds validation, or fail a whole response; unmapped counts disagree by backend. | [geometry conversion](../../apps/api/app/api/routes/incidents_map.py#L84), [Point model](../../apps/api/app/models/geojson.py#L22), [unmapped predicate](../../apps/api/app/repositories/incident_map_repository.py#L87) |
| AUD-020-009 | P1 | PARTIAL: unknown severities are silently downgraded to Advice; response domain fields are unconstrained strings/integers. | [severity fallback](../../apps/api/app/api/routes/incidents_map.py#L101), [properties model](../../apps/api/app/models/geojson.py#L37) |
| AUD-020-010 | P1 | MISSING: marker-by-marker Tab/Enter/Space selection and focus management are absent from the connected canvas experience. | [layer event handlers](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L242), [map markup](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L223) |
| AUD-020-011 | P2 | PARTIAL: co-located incidents can remain hidden after clustering stops; expansion failure and SDK event-shape handling lack assertions. | [cluster max zoom](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L148), [overlap policy](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L211), [expansion handler](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L220) |
| AUD-020-012 | P2 | PARTIAL: moving the page to `/` discards filters from legacy `/disasters?...` bookmarks. | [redirect](../../apps/web/src/app/disasters/page.tsx#L3), [moved implementation](../../apps/web/src/app/page.tsx#L4) |
| AUD-020-013 | P2 | CONFLICT: default endpoint/version and validation statuses differ from the local API contract. | [prefix](../../apps/api/app/core/settings.py#L10), [binding validation](../../apps/api/app/api/routes/incidents_map.py#L117), [422 assertions](../../tests/contract/test_incidents_map_contract.py#L241) |
| AUD-020-014 | P2 | PARTIAL: unstable filter objects trigger pre-debounce loads; pending keyword callbacks can undo reset/navigation or overwrite newer filters. | [filter object](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L101), [reset/debounce](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L146), [load dependency](../../apps/web/src/app/page.tsx#L127) |
| AUD-020-015 | P2 | PARTIAL: hard-coded year boundaries, no severity All/Clear, and partial-tier URL state prevent full filter fidelity. All nine required types do exist within a 19-type superset. | [year options](../../packages/ui/src/components/disaster-map/filter-panel.tsx#L125), [severity group](../../packages/ui/src/components/disaster-map/filter-panel.tsx#L261), [API year limits](../../apps/api/app/api/routes/incidents_map.py#L118) |
| AUD-020-016 | P2 | PARTIAL: mobile sheets can cover each other; swipe dismissal, outside close, and exit transitions are absent. Viewport usability is UNVERIFIED. | [initial open state](../../apps/web/src/app/page.tsx#L87), [sheet stacking](../../apps/web/src/app/globals.css#L1014), [detail overlay](../../apps/web/src/app/globals.css#L1057) |
| AUD-020-017 | P2 | PARTIAL: a valid null PPRR phase disappears from the required detail sheet; selected detail is not reconciled with refreshed/filter-excluded data. | [conditional field](../../packages/ui/src/components/disaster-map/incident-sidebar.tsx#L112), [selection snapshot](../../apps/web/src/app/page.tsx#L132) |
| AUD-020-018 | P2 | PARTIAL: the fallback artifact has incorrect hemisphere formatting and mouse-only column sorting; restoration alone would not deliver accessible fallback semantics. | [coordinate formatter](../../packages/ui/src/components/disaster-map/list-view-fallback.tsx#L46), [sort headers](../../packages/ui/src/components/disaster-map/list-view-fallback.tsx#L124) |
| AUD-020-019 | P2 | CONFLICT: initial 500 versus 200-page instructions disagree; pagination/failure state does not establish a consistent complete dataset. | [FR-035](spec.md#L168), [progressive loop](../../apps/web/src/lib/api/incidents-map.ts#L111), [ordering](../../apps/api/app/repositories/incident_map_repository.py#L125) |
| AUD-020-020 | P2 | PARTIAL: console messages and log extras are not the five correctly timed, exported metrics; filter_apply_ms is absent. | [browser logging](../../apps/web/src/app/page.tsx#L139), [Node-only exporter](../../apps/web/src/instrumentation.ts#L1), [backend error logging](../../apps/api/app/api/routes/incidents_map.py#L155) |
| AUD-020-021 | P2 | PARTIAL: synchronous cross-partition Cosmos queries inside async handlers, repeated counts, and full marker rebuilds leave scale risks unresolved. Performance failure is not claimed as measured. | [blocking queries](../../apps/api/app/repositories/incident_map_repository.py#L177), [seed partition](../../infra/main.bicep#L670), [marker rebuild](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L156) |
| AUD-020-022 | P2 | PARTIAL: backend tests omit authorization, storage failure, real query-result parity, and malformed/domain-edge assertions. | [unit fixtures](../../tests/unit/test_incident_map_repository.py#L16), [contract assertions](../../tests/contract/test_incidents_map_contract.py#L74), [test environment](../../tests/conftest.py#L1) |
| AUD-020-023 | P2 | PARTIAL: E2E assertions are conditional/stale and do not prove connected map, filter, sidebar, mobile, or fallback behavior; mapper tests are not selected by the inspected CI lanes. | [conditional filter](../../tests/e2e/test_disaster_mapper.spec.ts#L117), [conditional fallback](../../tests/e2e/test_disaster_mapper.spec.ts#L190), [CI selection](../../.github/workflows/ci.yml#L312) |
| AUD-020-024 | P2 | UNVERIFIED: load/filter/render/fallback/telemetry latency and 500-marker performance targets have no accepted measurement record. | [SCs](spec.md#L237), [plan performance goals](plan.md#L18), [E2E fixtures](../../tests/e2e/test_disaster_mapper.spec.ts#L12) |
| AUD-020-025 | P2 | UNVERIFIED: WCAG contrast/assistive-technology/mobile results, 90% first-time-user success, and human map approval are not established. | [SC-005](spec.md#L241), [a11y tests](../../tests/e2e/test_disaster_mapper.spec.ts#L207), [constitution quality gates](../../.specify/memory/constitution.md#L280) |
| AUD-020-026 | P2 | UNVERIFIED: 130 unanswered review questions and contradictory design assumptions are not closed by the plan's ALL PASS claim. | [checklist](checklists/requirements.md#L1), [plan gates](plan.md#L23), [research](research.md#L1) |
| AUD-020-027 | P2 | MISSING: HYP-018 stub is missing; portfolio scores and inline "validated" labels do not prove mapper-specific persona/hypothesis validation. | [amendments](spec.md#L248), [stub contract](../028-capstone-alignment/contracts/evidence-stub.contract.md#L38), [postfeature scores](../028-capstone-alignment/evidence/rubric-postfeature.md#L24) |
| AUD-020-028 | P2 | CONFLICT: quickstart versions/env names/config paths are stale; T036 has no accepted successful rehearsal record. | [quickstart](quickstart.md#L7), [API runtime minimum](../../apps/api/pyproject.toml#L10), [web manifest](../../apps/web/package.json#L22), [actual config](../../apps/web/playwright.config.cts#L1) |
| AUD-020-029 | P2 | CONFLICT: active mapper help advertises additional layers, actions, shortcuts, WebSockets, and residency/performance assurances unsupported by this connected read-only experience. | [help layout](../../apps/web/src/content/help/articles/screen-by-screen/disaster-mapper.mdx#L26), [help performance](../../apps/web/src/content/help/articles/screen-by-screen/disaster-mapper.mdx#L283), [live page](../../apps/web/src/app/page.tsx#L155) |

## Remediation Tasks

Every task below is open. Developer/tester instructions describe future authorized work, not work
performed in this audit. V-PY, V-UI, V-E2E, V-INFRA, V-MEASURE, V-HUMAN, and V-DOC refer to the explicit
future validation procedures later in this report. Existing files are linked; suggested new test
files are expressly proposed. Do not change original task states or invent retrospective approvals.

- [ ] AUD-020-001 [P1] Enforce trusted, scoped incident reads

**Obligations:** FR-029, FR-033, A-06, T008, T009, T034; CHK081, CHK083, CHK108, CHK114.
**Expected and observed:** Existing authentication/authorization must apply. The handler has no
principal dependency; [AuthMiddleware](../../apps/api/app/middleware/auth_middleware.py#L19) supplies
anonymous defaults; [Entra](../../apps/api/app/middleware/entra_auth.py#L37) and
[RBAC](../../apps/api/app/middleware/rbac_check.py#L32) protect other prefixes. The
[repository](../../apps/api/app/repositories/incident_map_repository.py#L79) reads all matching seed
disasters without tenant, agency, or jurisdiction authorization predicates. Counts are equally unscoped.
**Impact:** Direct API callers can reach the operational-data read path without the contracted checks;
the public ingress declaration does not demonstrate an external authentication boundary.
**Developer:** Extend the existing trusted-principal and route-family controls to the mapper, including
any compatibility alias. Define allowed reader roles with the existing authority owner; apply their
visibility scope to features, totals, and unmapped counts. Client filter values must never grant access.
Do not solve this only by hiding the page or trusting unsigned identity headers. Preserve authorized
national readership where explicitly permitted and keep rehearsal exclusion independent of identity.
**Tester positive:** Extend [contract tests](../../tests/contract/test_incidents_map_contract.py#L47)
with a verified permitted reader and scoped incidents; assert 200 and exactly the allowed IDs/counts.
**Tester negative:** Missing, malformed, expired, wrong-audience credentials and a valid forbidden role
must yield the approved 401/403 contract with no incident titles or counts leaked; test direct and proxied routes.
**Tester edge:** Two agencies, disjoint jurisdictions, an authorized national reader, rehearsal records,
and a forged jurisdiction query/header must not broaden visibility. Use fake identity verification,
not live credentials, in V-PY and V-E2E.
**Dependencies and completion:** Resolve route compatibility with AUD-020-013; complete only after
deny/allow assertions cover the actual middleware stack and independent deployment-boundary evidence
is reviewed where required. No other route-family authorization is to be broadened incidentally.

- [ ] AUD-020-002 [P1] Resolve the Maps residency and infrastructure-governance conflict

**Obligations:** FR-001, NFR-001, T006, T007, R-004, A-02, A-09, CL-01, CL-07, SCP-059;
CHK097, CHK098, CHK099, CHK112, CHK115.
**Expected and observed:** The requirement is Australia East-only accounts/data/tiles. The
[module](../../infra/modules/azure-maps.bicep#L5) permits `global`, and
[main](../../infra/main.bicep#L442) passes it explicitly. A default road style and AU camera bounds
are not tile-residency enforcement. Incident storage/compute use the AU location parameter, but
actual serving locality, Maps regional availability, policy compliance, and human approval remain UNVERIFIED.
**Impact:** The constitution gate and NFR-001 cannot be accepted as satisfied. This is not proof that
incident data actually crossed a border, nor proof that setting account location to Australia East is supported.
**Developer:** Have architecture/security owners verify the current Maps resource/data-plane locality
capabilities and approved Australian serving path before selecting a correction. Record the conflict
and use the constitution's change-control authority if the literal requirement is infeasible; do not
reuse the model-hosting carve-out or silently relax residency. Check applicable discovered policies,
AVM availability/raw-resource approval, naming/tags, and the Maps module's deployment evidence prospectively.
Do not alter subscription policy to accommodate the template.
**Tester positive:** V-INFRA must show an approved configuration and referenced policy/architecture
decision; an authorized V-MEASURE run must record the actual requested tile hosts and locality evidence.
**Tester negative:** An unapproved location, external tile provider, unsupported regional endpoint,
or absent residency decision must block acceptance rather than be labeled compliant.
**Tester edge:** Check retries, alternate tile styles, cache behavior, CDN redirects, and regional
failure without assuming camera extent or account metadata proves physical serving location.
**Dependencies and completion:** Precedes production validation in AUD-020-003, AUD-020-024, and
AUD-020-025. Completion requires named governance review and verified platform evidence; no deployment
or new resource is authorized by this report.

- [ ] AUD-020-003 [P1] Connect production Maps authentication and deployment configuration

**Obligations:** FR-001, FR-004, FR-029, T006, T007, T013, T014, R-001, R-004; CHK115, CHK130.
**Expected and observed:** [Staging/prod local auth is disabled](../../infra/modules/azure-maps.bicep#L35),
but the [browser](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L79) uses only
`NEXT_PUBLIC_AZURE_MAPS_KEY` or undefined auth. Main supplies no Maps CORS origins or module-output
bindings. [Web app settings](../../infra/main.bicep#L1300) provide `API_ENDPOINT`, while the
[Next proxy](../../apps/web/next.config.ts#L7) reads different variables and otherwise targets localhost.
Source workflow/azd hooks do not demonstrate a production replacement for those missing bindings.
**Impact:** A template-created production account and this browser configuration are incompatible;
the deployed map and incident upstream cannot be assumed operational.
**Developer:** Add the approved Entra/token flow and least-privilege Maps data access, account/client
configuration, allowlisted web origins, and required outputs in the owning module/orchestrator and
browser auth boundary. Align build-time public API settings and server-side upstream configuration
with the actual hosting path. Keep key auth explicitly dev-only; never embed privileged credentials
or weaken production disableLocalAuth to make the UI work. Address dependency cycles explicitly.
**Tester positive:** In V-UI/V-E2E, assert production selects the approved token mechanism and uses the
configured API upstream; V-INFRA checks each environment's auth policy, CORS origins, and outputs.
**Tester negative:** Missing account configuration, expired token, disallowed origin, and absent upstream
must produce a recoverable error/fallback, not silent unauthenticated initialization or localhost traffic.
**Tester edge:** Exercise token renewal, fresh deployments without local env files, cold initialization,
dev key opt-in, and both supported deployment OS paths. Network success needs a separately approved environment.
**Dependencies and completion:** AUD-020-002 residency decision and AUD-020-001 API protection;
complete when configuration is reproducible without developer-local files and both positive/negative
auth paths are asserted. Template source alone is not deployed-auth proof.

- [ ] AUD-020-004 [P1] Restore Australian Warning System marker semantics

**Obligations:** FR-003, FR-003a, FR-038, SC-006, US1-AS3, T005, T012, T030; R-002, CL-02, CL-03.
**Expected and observed:** Markers must use Advice/yellow circle, Watch and Act/orange triangle, and
Emergency Warning/red diamond. The [rendering expression](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L193)
selects by incident type, and the [generator](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L115)
produces only teardrops. A flood stays blue irrespective of its severity. Correct
[tokens](../../packages/ui/src/styles/tokens.css#L46) and API tier values are not consumed for that encoding.
**Impact:** Users cannot infer warning urgency from the map as specified; the required non-colour cue is absent.
**Developer:** Restore tier-driven sprite selection and distinct silhouettes in marker-cluster, mapping
both warning and emergency to the red diamond. Retain useful hazard pictograms only as an additional
cue that does not replace tier semantics; coordinate with other consumers of the shared renderer.
Use an approved outline/background strategy to meet contrast without silently changing required hues.
Keep filter/sidebar naming consistent and distinguish decorative icons from actual markers.
**Tester positive:** Reuse backend severity fixtures and extend the mapper E2E plus proposed V-UI
renderer tests with all four domain values; assert correct layer expressions, sprites, and rendered tier distinctions.
**Tester negative:** Same hazard/different severities must not share only a hazard-coloured silhouette;
wrong hues, unknown tiers, colour-only encoding, or missing icons must fail assertions.
**Tester edge:** Mixed-severity clusters, selected/focused markers, high density, light/dark geographic
backgrounds, HiDPI, and colour-vision simulations. SVG/string assertions alone are not visual contrast proof.
**Dependencies and completion:** AUD-020-009 unknown-tier policy, AUD-020-010 focus treatment, and
AUD-020-025 rendered contrast/human review. Complete only when source mapping and visual evidence agree.

- [ ] AUD-020-005 [P1] Connect bounded map-failure detection to the sortable fallback

**Obligations:** FR-031, NFR-003, SC-008, EC-04, T026, T027, T036; CHK043, CHK084, CHK104, CHK106.
**Expected and observed:** Failure must activate the same-filter sortable table within five seconds.
The [root page](../../apps/web/src/app/page.tsx#L242) always renders DisasterMap. Its
[timeout](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L133) is 15 seconds and is
cleared on `ready`, not successful tile/marker rendering. No tile error event is observed, and async
sprite-setup failure in the ready callback is not routed to the outer initialization catch.
**Impact:** A loaded SDK with failed tiles can leave an unusable canvas indefinitely; a failure overlay
provides no incident-list alternative even though the table component exists.
**Developer:** Give the map wrapper an explicit ready/error/degraded contract and bounded initialization
and tile-failure handling. Connect the existing table in the root page, retain the same query/data/filter
state, and provide a manual map retry. Handle post-ready tile errors and rejected sprite/expansion work;
clean up timers/listeners and guard late async work after disposal/retry. Keep API failure separate from tile failure.
**Tester positive:** V-E2E must force initialization and post-ready tile failures with known incidents;
assert all six table columns, data, shared filters, selection, and retry by the five-second deadline.
**Tester negative:** SDK ready with no usable tiles must not cancel degradation; no empty map-only state,
unhandled rejection, duplicate listener, or lost filter state may be accepted.
**Tester edge:** API succeeds/tiles fail, API fails/tiles succeed, both fail, slow sprites, retry followed
by another failure, and unmount during initialization. Use fake clocks for V-UI; measure real timing separately.
**Dependencies and completion:** AUD-020-018 table correctness and AUD-020-016 mobile fallback usability;
complete only after the connected route, not a standalone table test, meets V-E2E and V-MEASURE assertions.

- [ ] AUD-020-006 [P1] Prevent obsolete request results from replacing current incidents

**Obligations:** FR-013, FR-014, FR-015, FR-023, FR-034, FR-035, EC-05, T011, T018, T022, T029;
CHK047, CHK087.
**Expected and observed:** Only the active query may publish results. The
[fetch](../../apps/web/src/lib/api/incidents-map.ts#L86) never receives the signal. The
[loop](../../apps/web/src/lib/api/incidents-map.ts#L122) checks abort only before awaiting the request,
then calls onProgress without checking again. The [page callback](../../apps/web/src/app/page.tsx#L103)
accepts every publication. Thus an old response can overwrite a newer query's state.
**Impact:** Visible incidents/counts/freshness can disagree with the user's current criteria, a
particularly harmful error during situational assessment.
**Developer:** Thread cancellation through fetch, reject publications after abort, and guard page
updates by request generation or equivalent active-query identity. Apply the same guard to metadata,
errors, completion, and callbacks after unmount. Define whether previous results are cleared or
explicitly shown as stale while a new query is pending; never present them as new-query results.
**Tester positive:** Proposed V-UI loader/page tests use controllable promises: A begins, B begins,
B resolves, then A resolves; only B's IDs/counts/timestamp remain. Extend the existing E2E for the same sequence.
**Tester negative:** Aborted page two, rejected old requests, and callbacks after unmount must not
modify current state or erase a newer error. Verify the network request receives the AbortSignal.
**Tester edge:** Reset during paging, rapid multi-filter changes, retry after partial data, and empty
B following nonempty A. Use the two existing E2E incidents plus distinct IDs for each query generation.
**Dependencies and completion:** Coordinate AUD-020-014 input-intent handling and AUD-020-019 paging
state. V-UI/V-E2E must assert identity and metadata, not only eventual URL text.

- [ ] AUD-020-007 [P1] Make production repository unavailability visible

**Obligations:** FR-029, FR-032, NFR-003, EC-05, T008, T009, T032, T034; CHK048, CHK084, CHK105.
**Expected and observed:** Backend unavailability requires a user-facing error and retry.
[Repository initialization](../../apps/api/app/repositories/incident_map_repository.py#L36) catches
configuration/client failures and keeps an empty in-memory store; [queries](../../apps/api/app/repositories/incident_map_repository.py#L152)
then return successful empty results. Missing COSMOS_ENDPOINT does the same in every environment.
Runtime query exceptions do produce 503; that existing path does not cover initialization failure.
**Impact:** A storage outage/configuration error can look like "no incidents", suppressing the operational warning.
**Developer:** Separate an explicitly authorized dev/test in-memory mode from production readiness.
Preserve initialization failure as unavailable state or fail startup safely; return the approved
503/error contract and allow recovery/retry. Do not mask a configured but unusable store as an empty dataset.
**Tester positive:** Extend [unit](../../tests/unit/test_incident_map_repository.py#L95) and
[contract](../../tests/contract/test_incidents_map_contract.py#L47) homes with an explicit test store and
a recovering injected client; healthy genuine-empty data must still return 200.
**Tester negative:** Missing production config, client-construction failure, credential failure, and
unreachable store must not return an empty 200. Assert telemetry and the page retry path.
**Tester edge:** Failure before first request, recovery without stale singleton state, and production
flags combined with a seeded test store. All V-PY fixtures must block external access before app import.
**Dependencies and completion:** AUD-020-013 error contract and AUD-020-020 failure metrics; complete
when genuine empty data and unavailable data have different asserted outcomes in the connected API/UI.

- [ ] AUD-020-008 [P1] Validate map geometry and make unmapped counts consistent

**Obligations:** FR-002, FR-029, FR-030, EC-02, T003, T004, T008, T009, T029, T033, T034; R-006,
CHK038, CHK070, CHK090.
**Expected and observed:** Valid two-dimensional Points must be plotted, and excluded locations
must be disclosed. [Conversion](../../apps/api/app/api/routes/incidents_map.py#L84) defaults absent
coordinates to `[0, 0]`; [GeoJSONPoint](../../apps/api/app/models/geojson.py#L22) checks array length
but not finite values/ranges. Cosmos [unmapped counting](../../apps/api/app/repositories/incident_map_repository.py#L87)
only counts undefined/null locations; [memory counting](../../apps/api/app/repositories/incident_map_repository.py#L296)
also counts non-Points. Short/non-numeric arrays can fail conversion outside the route's query try/catch.
**Impact:** Fabricated locations, hidden excluded incidents, inconsistent totals, and whole-page failures.
**Developer:** Keep the optional domain field backward compatible, but establish one API-boundary
validity policy shared by mapping and count predicates. Validate finite longitude/latitude and allowed
ranges, never fabricate a point, and handle malformed records without silently understating exclusions.
Define how valid offshore/outside-Australia coordinates are treated; storage residency is not an event-location rule.
**Tester positive:** Extend existing `_make_incident` fixtures in V-PY with valid Australian Points,
null/absent location, and bounded coordinate endpoints; assert exact features and exact unmapped counts.
**Tester negative:** Missing coordinates, wrong geometry, empty object, one/three values, text values,
non-finite numbers, and out-of-range coordinates must not appear at the origin or poison valid rows.
**Tester edge:** A malformed record at a page boundary and identical filters in injected Cosmos and
memory paths must produce the same accounting. Use structured fake query results; no live Cosmos dependency.
**Dependencies and completion:** AUD-020-009 property policy and AUD-020-019 pagination semantics;
complete after schema, exclusion accounting, and UI notices are asserted together via V-PY/V-E2E.

- [ ] AUD-020-009 [P1] Do not downgrade unknown incident severity to Advice

**Obligations:** FR-003, FR-009, FR-017, FR-029, T004, T009, T012, T019, T034; CHK085, CHK086.
**Expected and observed:** Only the documented four domain severities map to the three warning tiers.
The [adapter](../../apps/api/app/api/routes/incidents_map.py#L101) maps any unknown severity to advice,
while [properties](../../apps/api/app/models/geojson.py#L37) accept arbitrary severity/status/phase and level values.
**Impact:** An unrecognized higher-risk severity can be presented as the least urgent warning; schema
drift is hidden instead of disclosed. This is a source-supported failure path, not a claim that such
records were observed in production.
**Developer:** Use an approved explicit unknown/invalid-data policy, typed closed sets where appropriate,
and consistent response/renderer handling. Do not convert missing/unknown severity into reassuring Advice.
Keep the legitimate warning/emergency alias and current supported hazard superset. Define treatment of
unknown status/phase, invalid level, and invalid date without silently manufacturing authoritative values.
**Tester positive:** V-PY asserts each known severity produces a nonempty expected result, including
warning plus emergency in the same tier. V-UI verifies the same semantics in marker/sidebar/fallback.
**Tester negative:** New severity, null/missing required fields, level 0/4, and unknown status/phase
must follow the approved visible data-quality/error policy, never a silent Advice downgrade.
**Tester edge:** Mixed valid/invalid rows, legacy records, and newly introduced legitimate incident types
must not break backward compatibility or hide a severity mapping change behind empty-loop assertions.
**Dependencies and completion:** Domain/operational owner decision in AUD-020-026, aligned with
AUD-020-004 and AUD-020-008. Complete with exact adapter and connected presentation assertions.

- [ ] AUD-020-010 [P1] Implement accessible per-incident navigation and focus

**Obligations:** FR-003a, FR-036, FR-037, FR-038, SC-003, SC-006, T020, T030, T035;
CHK049, CHK050, CHK051, CHK052, CHK053, CHK054, CHK056.
**Expected and observed:** Users must Tab between markers and activate details with Enter/Space.
The [SymbolLayer handlers](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L242)
are pointer-click handlers; the [wrapper](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L223)
adds a map application label, not accessible per-feature controls. Native SDK pan/zoom shortcuts do
not meet this requirement. Focusable rows exist only in the unmounted fallback.
**Impact:** Keyboard and screen-reader users cannot independently select the mapped incidents.
**Developer:** Add a synchronized, discoverable keyboard interaction surface for incident markers and
clusters, meaningful incident/tier labels, visible focus, a documented order, and Enter/Space behavior.
Manage focus entering/leaving details and sheets, prevent off-screen closed-sheet controls remaining
in the tab sequence, and avoid duplicate decorative-icon announcements. Preserve polite count updates
without announcing stale results. Do not claim a generic canvas role is equivalent to marker access.
**Tester positive:** V-UI and the existing E2E home must assert all mapped test IDs are keyboard-reachable,
Enter and Space select the right incident, and closing restores focus; include cluster access.
**Tester negative:** No keyboard trap, invisible focus, stale-count announcement, unlabeled marker,
hidden-sheet focus target, or pointer-only alternative may pass.
**Tester edge:** Zero, one, 500, and co-located incidents; paging while focused; filter removal of the
focused incident; mobile external keyboard; and actual screen-reader traversal in V-HUMAN.
**Dependencies and completion:** AUD-020-004, AUD-020-011, AUD-020-016, and AUD-020-025. Completion
requires both connected assertions and named assistive-technology evidence; no such run occurred here.

- [ ] AUD-020-011 [P2] Ensure clusters expose every overlapping incident

**Obligations:** FR-002, FR-004, FR-005, SC-003, EC-03, T012, T020, T035; CHK008, CHK009, CHK091.
**Expected and observed:** Expansion must reveal individual incidents. The source configures
[clusterMaxZoom 14](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L148) and
[allowOverlap false](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L211), with no
co-located selection alternative at maximum expansion. The [click adapter](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L220)
ignores shapes without getProperties and does not catch rejected expansion. Actual SDK cluster event
representation is UNVERIFIED here; it is not asserted that every cluster click fails.
**Impact:** Identical/near-identical coordinates can leave incidents inaccessible, and expansion errors lack recovery.
**Developer:** Verify the lock-pinned SDK event contract, type the adapter accordingly, and cover all
supported event representations. Provide an accessible co-located incident picker or other approved
expansion behavior when zoom cannot separate incidents. Bound camera changes and report expansion
failure without crashing or changing incident identity. Retain the required 60px radius/count badges.
**Tester positive:** Proposed V-UI layer tests assert cluster count and expansion camera, then V-E2E
selects every incident from a 50+ incident same-location fixture.
**Tester negative:** Empty click events, missing cluster ID, rejected expansion, or unsupported event
shape must not cause an unhandled rejection or open a wrong incident.
**Tester edge:** Exactly equal coordinates, maximum zoom, mixed severity, overlapping labels, HiDPI,
and stale cluster events after filters replace the source. Test SDK-supported shapes, not invented mocks alone.
**Dependencies and completion:** AUD-020-010 access design and AUD-020-005 failure boundary; complete
when all fixture IDs are selectable and real cluster interaction evidence is captured, not just layer existence.

- [ ] AUD-020-012 [P2] Preserve legacy filter bookmarks across the route move

**Obligations:** FR-025, FR-014, EC-07, CL-05, R-007, T014, T016, T018; CHK032, CHK080, CHK082, CHK088.
**Expected and observed:** `/disasters?type=...&year_start=...` must restore filters. The
[legacy redirect](../../apps/web/src/app/disasters/page.tsx#L3) discards the query although the
[root hook](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L95) can parse it.
**Impact:** Shared/bookmarked criteria silently become an unfiltered view.
**Developer:** Preserve and safely canonicalize supported filter parameters when redirecting to the
documented root replacement, or restore the canonical route by approved decision. Do not remove the
root experience/nav merely to match the historical filename. Preserve workspace return links and history.
**Tester positive:** V-E2E visits a legacy URL with all categories and an encoded keyword, follows the
redirect, and asserts the resulting URL, selected controls, request parameters, and returned IDs.
**Tester negative:** Unknown/invalid parameters must follow the documented policy and must not bypass
authorization or become arbitrary redirect targets.
**Tester edge:** Partial queries, repeated parameters, spaces/non-ASCII text, empty criteria, browser
Back/Forward, authentication round-trip, and workspace return. Existing E2E uses the legacy route already.
**Dependencies and completion:** AUD-020-013 parameter contract and AUD-020-014 stable state. Complete
when old and canonical links produce equivalent authorized filter state without full-page interaction resets.

- [ ] AUD-020-013 [P2] Reconcile API version and validation compatibility

**Obligations:** FR-029, T009, T010, T011, T034, R-005, CL-04, A-10; CHK037, CHK048, CHK080.
**Expected and observed:** The contract names `/api/v1/incidents/map` and 400 for invalid parameters.
[Settings](../../apps/api/app/core/settings.py#L10), the [client](../../apps/web/src/lib/api/incidents-map.ts#L85),
and current contract tests use `/api/incidents/map`. FastAPI's numeric/length validation yields the
422 contract explicitly expected by [tests](../../tests/contract/test_incidents_map_contract.py#L241).
**Impact:** A consumer following the written contract requests a different route or handles the wrong error shape/status.
**Developer:** Agree the canonical endpoint and compatibility alias without globally changing the
API prefix or breaking existing endpoints. Align docs, query normalization, numeric/length error
semantics, and authorized error envelopes. Reject invalid input predictably rather than silently
truncating/normalizing values differently at each layer. Preserve parameterized storage queries.
**Tester positive:** V-PY covers both supported route forms, all nine parameters, comma-separated
OR values, AND combinations, metadata defaults, and approved case/whitespace normalization.
**Tester negative:** Invalid enum entries mixed with valid ones, malformed integers, page zero,
page size 0/501, keyword length 201, inverted years, 401/403 and backend 500/503 must match the agreed contract.
**Tester edge:** Boundary values 1/200/500, whitespace-only lists, duplicate values, partial year bounds,
special-character keywords, and compatibility consumers. No broad prefix change is acceptable as a shortcut.
**Dependencies and completion:** AUD-020-001 security and AUD-020-026 prospective contract decision;
complete when docs, actual route registration, client URLs, and assertions agree.

- [ ] AUD-020-014 [P2] Make filter updates stable, debounced, and reset-safe

**Obligations:** FR-013, FR-014, FR-021, FR-022, FR-023, FR-024, EC-07, T016, T018, T021, T022;
R-007, CHK018, CHK029, CHK087, CHK088, CHK093.
**Expected and observed:** Only keyword commits are delayed 300ms; other criteria apply immediately
without undoing each other. [filtersFromURL](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L101)
is a new object on each local-input render and is the page's load dependency. The
[debounce](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L151) captures
older filters, while reset and external navigation do not cancel it.
**Impact:** Typing can re-fetch the old query before the debounce, and reset/newer selections can be undone.
**Developer:** Base requests on stable committed query identity, not a new object per keystroke.
Merge delayed keyword changes with the latest committed criteria, and cancel/supersede timers on
reset and external navigation. Validate URL values consistently with AUD-020-013, handle input length
without discarding user intent, and avoid an initial actionable unfiltered/no-op-hook screen while URL state initializes.
**Tester positive:** Proposed V-UI hook/page tests use fake timers to assert zero premature keyword
requests, one committed request after 300ms, immediate checkbox changes, and correct AND/OR parameters.
**Tester negative:** Type then Reset before 300ms; type then change severity; type then Back; rapid
two-category clicks. None may resurrect cleared criteria or overwrite newer URL state.
**Tester edge:** Clear keyword while retaining filters, exact 200-character input, paste of 201,
URL normalization, deep-link initialization, and overlapping requests using AUD-020-006 fixtures.
**Dependencies and completion:** AUD-020-006 and AUD-020-012; V-UI/V-E2E must assert request counts,
parameters, control values, and visible IDs, not merely that the URL contains a keyword.

- [ ] AUD-020-015 [P2] Complete filter controls and historical-year semantics

**Obligations:** FR-006, FR-007, FR-008, FR-009, FR-012, A-05, T016, T017, T018;
CHK013, CHK015, CHK017, CHK092, CHK119.
**Expected and observed:** Years must span the earliest incident to the current year and each
multi-value category must provide All/Reset. [Years start at 2000](../../packages/ui/src/components/disaster-map/filter-panel.tsx#L125),
the [API additionally bounds 1900-2100](../../apps/api/app/api/routes/incidents_map.py#L118), and
[Severity](../../packages/ui/src/components/disaster-map/filter-panel.tsx#L261) has no All/Clear.
The tier checkbox uses every() so a bookmarked `severity=warning` appears unchecked despite an active filter.
**Impact:** Older incidents cannot be selected by their year, and severity controls misrepresent or
cannot bulk-reset the actual query. The 19-type superset contains all nine required types; it should not be deleted.
**Developer:** Provide a dataset-derived, authorized year extent with a documented empty/future-date
policy; align API bounds with that policy. Add severity All/Reset and a truthful partial-tier state or
canonicalization policy for single warning/emergency URLs. Preserve distinct API domain values and the current type catalogue.
**Tester positive:** V-PY/V-UI/V-E2E cover an 1890/1999 historical fixture, current-year incident,
all categories, category-local reset, and both warning/emergency aliases together.
**Tester negative:** No hard-coded 2000 cutoff, rejected valid historical year, misleading unchecked
active tier, reset of unrelated filters, or selectable rehearsal status.
**Tester edge:** No incidents, one-year extent, new earliest incident, null phase, future record,
inverted bounds, direct single-tier URL, and all 19 current types with the original nine explicitly asserted.
**Dependencies and completion:** AUD-020-013 and AUD-020-026 settle boundary policies; completion
requires matching option/state/request/result assertions and preservation of existing catalogue compatibility.

- [ ] AUD-020-016 [P2] Complete mobile sheet, overlay, and responsive states

**Obligations:** FR-027, FR-028, SC-007, US5-AS1, US5-AS2, US5-AS3, US5-AS4, T015, T023, T024, T025;
CHK010, CHK027, CHK033, CHK034, CHK035, CHK066.
**Expected and observed:** The mobile map must retain usable filters and details. The root
[starts filters open](../../apps/web/src/app/page.tsx#L87); [filter z-index 20](../../apps/web/src/app/globals.css#L1014)
sits above the [detail card at 15](../../apps/web/src/app/globals.css#L1057). Selection does not close
the sheet. Components provide no swipe dismissal or outside-close handler; unmounting details gives
entry animation but no managed exit transition.
**Impact:** A selected incident card can be obscured by the sheet, and required touch interactions are absent.
**Developer:** Coordinate sheet/detail states, implement safe swipe dismissal and tap-outside close
with keyboard equivalents, and retain map visibility. Specify the exactly-768px boundary. Keep open/close
focus and reduced-motion behavior coherent, and constrain long content/navigation widths. Confirm SDK
resizing across filter/sidebar changes and orientation; do not equate a missing orientation listener with a proven resize failure.
**Tester positive:** V-E2E at 360, 375, 767, 768, 769, and desktop widths must exercise search, all
filters, tap selection, close/reopen, pan/pinch, and portrait/landscape with each panel state.
**Tester negative:** No hidden detail under an open sheet, inaccessible hidden focus targets,
unclosable overlay, horizontal overflow, truncated controls, or gesture that unintentionally changes map state.
**Tester edge:** Short landscape height, long title/jurisdiction identifiers, browser text zoom,
virtual keyboard, rotation with details open, network error plus sheet, and reduced motion.
**Dependencies and completion:** AUD-020-010 and AUD-020-018; V-HUMAN/V-E2E measurements and screenshots
must show usable controls and no overflow. CSS source supports layout intent, not completed mobile validation.

- [ ] AUD-020-017 [P2] Preserve complete, current incident detail semantics

**Obligations:** FR-017, FR-018, FR-019, FR-020, T019, T020, T025; CHK023, CHK024, CHK025, CHK028, CHK089, CHK096.
**Expected and observed:** Every required detail field should have an intelligible value/state.
A valid null phase is [omitted](../../packages/ui/src/components/disaster-map/incident-sidebar.tsx#L112)
entirely. Selection is a [stored Feature snapshot](../../apps/web/src/app/page.tsx#L132) and is not
reconciled when refreshed results change/remove that incident. The workspace target and not-found
screen do exist; this is not a missing-workspace claim.
**Impact:** Users cannot distinguish unknown phase from absent UI, and details can remain stale relative to the map.
**Developer:** Display a documented unknown/not-assigned phase state, decide how selected incidents
track refresh/filter removal, and apply that decision consistently. Preserve the real workspace route,
safe incident identity handling, return filters, and the close callback. Resolve the task's ISO-format
wording versus current en-AU display without changing stored timestamps or asserting a timezone that was not supplied.
**Tester positive:** Extend mapper V-E2E/V-UI cases to assert all eight required fields, multi-jurisdiction
display, levels 1/2/3, both red domain values, marker A to B switching, workspace link, and return path.
**Tester negative:** A null phase must not disappear ambiguously; deleted/unavailable workspaces must
show the existing safe error/return route, not invented success or unrelated incident data.
**Tester edge:** Rapid selection, filtered-out/refreshed selected record, long title, empty jurisdiction
array, malformed/offset dates according to the approved contract, and invalid/path-sensitive IDs.
**Dependencies and completion:** AUD-020-006, AUD-020-009, AUD-020-010; complete with connected sidebar
and real workspace-response assertions, not only a hidden-initially assertion.

- [ ] AUD-020-018 [P2] Make the fallback table accurate and keyboard-sortable

**Obligations:** FR-031, FR-036, FR-038, SC-007, EC-04, T026, T030; CHK042, CHK051, CHK090, CHK121.
**Expected and observed:** The six-column sortable fallback must remain intelligible and accessible.
[formatCoords](../../packages/ui/src/components/disaster-map/list-view-fallback.tsx#L46) emits a
negative latitude with `S` and labels absolute longitude `E` even for western coordinates. Sorting
is attached to [non-focusable th elements](../../packages/ui/src/components/disaster-map/list-view-fallback.tsx#L124).
Date sorting is lexical, not explicitly normalized chronologically; tier text is not the shared full AWS label.
**Impact:** The recovered experience would misstate locations and exclude keyboard users from sorting.
**Developer:** Correct signed hemisphere formatting, expose real header buttons with accurate aria-sort,
use approved chronological/date and severity ordering rules, and share tier labels. Preserve row activation,
the same query filters, and readable layout at 360px; coordinate a mobile alternative if six columns cannot fit.
**Tester positive:** V-UI asserts all six sort controls in both directions and keyboard activation;
V-E2E activates the fallback through the real failure path and opens the same incident details.
**Tester negative:** No double-negative southern label, west-as-east label, mouse-only sorting, stale
aria-sort, or filtering mismatch between map and fallback.
**Tester edge:** Zero coordinates, all hemispheres, equal latitudes/different longitudes, dates with
different ISO offsets, tied values, empty data, long text, 500 rows, and narrow screens.
**Dependencies and completion:** AUD-020-005 mounting and AUD-020-016 responsive policy; complete when
the connected table's content, controls, sorting, and access behavior all pass V-UI/V-E2E/V-HUMAN as applicable.

- [ ] AUD-020-019 [P2] Resolve progressive-load scope and consistent completion/freshness

**Obligations:** FR-015, FR-032, FR-034, FR-035, SC-001, SC-004, EC-05, EC-06, T011, T018, T028, T029;
CHK039, CHK040, CHK047, CHK069, CHK072, CHK075, CHK095, CHK122.
**Expected and observed:** FR-035 names an initial 500; the local contract and T011 start at 200 and
accumulate 600 over three full pages. The [loader](../../apps/web/src/lib/api/incidents-map.ts#L111)
publishes every page and stops only at a short page. [Sorting](../../apps/api/app/repositories/incident_map_repository.py#L125)
has no deterministic tie-breaker/snapshot; [failure state](../../apps/web/src/app/page.tsx#L113)
does not finish background progress after a later-page error. Last updated uses the latest page's fetch time,
which does not establish a single snapshot for the entire displayed collection.
**Impact:** Conflicting acceptance scope, duplicate/missed records during changing/tied datasets,
and misleading completeness/freshness after partial failure.
**Developer:** Obtain an explicit initial-render/full-dataset interpretation and implement it without
skipping or repeating offsets. Do not request page 1 at 500 then page 2 at 200 without a compatible
continuation rule. Add stable identity ordering, deduplication/consistency policy, explicit partial/complete/error
state, and honest freshness semantics. Keep progressive rendering non-blocking and filters scoped from page one.
**Tester positive:** V-UI/V-PY/V-E2E use deterministic 0/199/200/500/501/1000-item fixtures and assert
exact ordered ID sets, request offsets/page sizes, progress completion, mapped totals, and timestamp meaning.
**Tester negative:** Later-page failure must preserve/label partial data and offer retry; no perpetual
"loading more", skipped 300 records, duplicate IDs, or fresh-looking timestamp for failed refresh.
**Tester edge:** Exact page-size multiples, empty final page, equal start times, concurrent dataset
changes, historical date filters, unmount, and query reset during a background request.
**Dependencies and completion:** AUD-020-006 and AUD-020-026 precede implementation; AUD-020-024
measures resulting budgets. Complete with an agreed contract and exact-ID completeness assertions.

- [ ] AUD-020-020 [P2] Emit correctly defined and timed mapper telemetry

**Obligations:** NFR-002, SC-009, T031, T032, R-008, CL-08; CHK071, CHK073, CHK077, CHK100, CHK101, CHK102, CHK103.
**Expected and observed:** Five named metrics must reach the observability platform. The
[page](../../apps/web/src/app/page.tsx#L139) logs three names via console.debug; both durations use
page mount time. [Render completion](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L165)
fires immediately after source mutation, not confirmed paint. The [exporter](../../apps/web/src/instrumentation.ts#L1)
is Node-only. Backend process-global counters produce an error log extra, not a defined-window metric;
conversion errors after the query catch and tile errors are omitted.
**Impact:** Filter latency is absent, timings are misleading, and the 60-second queryability target is not demonstrated.
**Developer:** Use the existing observability architecture's browser-safe path, with explicit
navigation-to-interactive, committed-filter-to-render, and receipt-to-marker-render boundaries.
Emit the count gauge with a defined loaded/visible meaning. Define error-rate numerator, denominator,
window, aggregation, and dimensions across API/SDK/tile failures. Cover success and failure paths,
including conversion/timeout failures, without sending raw titles, keywords, or credentials in telemetry.
**Tester positive:** V-UI/V-PY inject a metric sink and controlled clocks; assert exact names, units,
counts, durations, dimensions, and one-shot versus per-update emission. V-MEASURE verifies ingestion.
**Tester negative:** Console-only output, repeated page-load samples on every render, mount-relative
map-render timing, missing filter metric, and omitted failure categories must fail.
**Tester edge:** Zero incidents, progressive pages, cancellation, map retry, token error, validation
failure, server conversion 500, and multiple backend workers with the approved rate window.
**Dependencies and completion:** AUD-020-001 privacy/auth boundary, AUD-020-005 lifecycle, and
AUD-020-019 data state; completion needs all five instrument assertions plus actual <=60s ingestion evidence.

- [ ] AUD-020-021 [P2] Remove source-level scale bottlenecks without changing contracts silently

**Obligations:** FR-014, FR-035, SC-001, SC-002, SC-004, EC-06, T008, T011, T012, T033; R-003, CHK095, CHK124, CHK125.
**Expected and observed:** Large datasets must remain responsive. The
[async repository methods](../../apps/api/app/repositories/incident_map_repository.py#L135) synchronously
materialize data/count queries, with another unmapped count per page and cross-partition access despite
the constant disaster kind in the [seed partition definition](../../infra/main.bicep#L670).
The [client](../../apps/web/src/lib/api/incidents-map.ts#L125) repeatedly copies accumulated arrays and
the [renderer](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L165) clears/re-adds everything.
**Impact:** Event-loop blocking, repeated request units/count work, and growing client work are concrete
source risks; no measured SLO breach is asserted.
**Developer:** Reuse injected clients and approved async/offloaded I/O, scope queries to the correct
partition where valid, avoid redundant counts within a defined loading sequence, and make rendering
incremental or otherwise bounded. Verify indexes against the actual seed schema rather than the retired
container recommendation. Preserve external paging/filter contracts until AUD-020-019 is resolved.
**Tester positive:** V-PY fake-container assertions verify query parameters/partition scope and count
reuse without real Cosmos; V-UI asserts bounded source updates and final IDs.
**Tester negative:** Concurrent reads must not monopolize unrelated API work; no broadened data scope,
loss of unmapped accounting, or hidden record cap may be used as a performance shortcut.
**Tester edge:** 500/1000/10000 incidents, skewed density, tied dates, rapid filtering, and later-page
failures; evaluate latency/CPU/frame/operation counts under V-MEASURE.
**Dependencies and completion:** AUD-020-001 authorization, AUD-020-019 consistency, and AUD-020-024
measurement. Completion requires preserved correctness and recorded budgets, not a speculative optimization claim.

- [ ] AUD-020-022 [P2] Strengthen backend assertions and hermetic test selection

**Obligations:** T033, T034, FR-029, FR-030, NFR-003, R-005, R-006; CHK037, CHK038, CHK048, CHK083, CHK085.
**Expected and observed:** The 22 unit and 25 contract declarations cover basic filters and envelopes,
but [query tests](../../tests/unit/test_incident_map_repository.py#L217) largely inspect fragments/parameter
names. [Contract tests](../../tests/contract/test_incidents_map_contract.py#L117) can pass tier loops
on empty results, omit required-field value semantics and 401/403/500/503 scenarios, and seed a module-global
repository without ensuring Cosmos is disabled. [Global setup](../../tests/conftest.py#L1) does not clear it.
The inspected CI's ordinary pytest lane selects contracts/integration, not this repository unit file.
**Impact:** Tests can miss the defects above or depend on ambient environment; checked task states overstate coverage.
**Developer:** Extend these existing test files and inject repository/auth/clock dependencies before
side-effectful app initialization. Isolate cloud/telemetry environment for hermetic tests. Add mapper unit
selection to an appropriate existing CI lane, preserving other suites; do not replace source assertions with mocks of the handler itself.
**Tester positive:** Assert exact IDs, geometry ranges/types, properties, enums, all filter categories,
AND/OR behavior, descending stable order, exact counts and timestamps, pagination, and valid auth.
**Tester negative:** Cover invalid mixed lists/numbers/lengths, inverted years, rehearsal, unscoped reads,
malformed records, client initialization, query failures, conversion failures, and required 401/403/500/503 outcomes.
**Tester edge:** Empty and full-page results, special-character keywords, partial years, wrong-kind
documents, non-Points, no-location objects, and Cosmos/memory parity with deterministic fake query results.
**Dependencies and completion:** AUD-020-001, AUD-020-007, AUD-020-008, AUD-020-009, AUD-020-013,
AUD-020-019; V-PY must discover the intended tests, avoid cloud access, and record actual results later.

- [ ] AUD-020-023 [P2] Replace superficial E2E checks with connected behavior assertions

**Obligations:** T035, FR-002, FR-004, FR-005, FR-013, FR-016, FR-023, FR-027, FR-031, FR-036; all five story tests.
**Expected and observed:** The [15-case suite](../../tests/e2e/test_disaster_mapper.spec.ts#L81)
does not test actual marker selection/cluster expansion, uses conditional button checks for checkbox
filters and fallback, and labels a heading assertion as a no-results test. Its mobile override is 375px,
not the required 360px. The [.cts config](../../apps/web/playwright.config.cts#L1) does discover it,
but [CI](../../.github/workflows/ci.yml#L312) runs the separate web-coverage-chromium project.
**Impact:** Missing controls/behavior can yield vacuous passes; historical failure snapshots already show assertion drift.
**Developer:** Reuse the existing mapper E2E file and existing web unit/a11y infrastructure. Add
proposed mapper tests under the configured web test homes for hook/loader/layer state. Make mocks vary
by actual filter/page values, not request ordinal. Assert required controls unconditionally, wire an
explicit mapper CI selection, and distinguish deterministic SDK-adapter tests from real-map browser tests.
**Tester positive:** Assert exact filtered IDs/counts, all categories and search/reset/history,
actual marker-to-sidebar-to-workspace flow, cluster expansion, key activation, and automatic fallback/retry.
**Tester negative:** Deliberately remove a control, disconnect a callback, return wrong data, fail tiles,
and delay an obsolete response; each corresponding test must fail meaningfully, not skip its assertions.
**Tester edge:** 360px and breakpoint boundaries, orientation, no-results, null metadata fields,
50 co-located points, 500+ features, and interrupted paging. Preserve separate auth fixtures for protected API cases.
**Dependencies and completion:** Behavioral fixes above and AUD-020-024/AUD-020-025 for genuine
runtime claims. V-UI/V-E2E discovery, assertions, and an actual future CI run must be recorded with no conditional-pass loopholes.

- [ ] AUD-020-024 [P2] Produce reproducible quantitative acceptance evidence

**Obligations:** SC-001, SC-002, SC-004, SC-008, SC-009, NFR-002, NFR-003, T031, T032, T035, T036;
CHK057, CHK058, CHK059, CHK063, CHK072, CHK073, CHK075, CHK077.
**Expected and observed:** 3s load, 1s filter update, responsive 500+ markers, 5s fallback, and 60s
telemetry ingestion need measurements. The [plan](plan.md#L18) adds >=30 FPS; the
[two-item E2E fixture](../../tests/e2e/test_disaster_mapper.spec.ts#L12) and console durations do not establish any target.
**Impact:** There is no defensible quantitative acceptance decision at the requested revision.
**Developer:** After resolving measurement scope, add explicit benchmark scenarios to the existing
mapper test/harness homes, with dataset generation, device/network definitions, timing boundaries,
raw capture, revision/configuration identifiers, and repeatable failure injection. Do not count SDK ready
or data-source mutation as successful interactive render.
**Tester positive:** V-MEASURE records initial agreed dataset render <=3s, committed filters <=1s,
500+ rendered markers with the plan's FPS threshold, fallback <=5s, and all five metrics queryable <=60s.
**Tester negative:** A deliberately slow/failing run must fail its threshold; no averaging away severe
freezes, zero-sample pass, mock-only ingestion, or fabricated result is acceptable.
**Tester edge:** 500/1000/10000 loaded records, dense versus dispersed locations, cold/warm caches,
slow/intermittent network, desktop/mobile, paging failure, and tile failure after initial ready.
**Dependencies and completion:** AUD-020-002, AUD-020-003, AUD-020-005, AUD-020-019, AUD-020-020,
AUD-020-021, AUD-020-023, AUD-020-026. Only actual dated raw results with environment/source provenance
can close this task; this static audit supplies none.

- [ ] AUD-020-025 [P2] Obtain usability, accessibility, and operator approval records

**Obligations:** FR-036, FR-037, FR-038, SC-003, SC-005, SC-006, SC-007, T030, T035, T036;
CHK055, CHK061, CHK062, CHK074, CHK076, constitution public-map review gate.
**Expected and observed:** Required contrast, distinct shapes, keyboard/screen-reader access,
mobile usability, and 90% first-time-user success within 30 seconds are not demonstrated by source,
the [requirements checklist](checklists/requirements.md#L1), or the historical failed snapshots.
R-002's "all colours meet 3:1" is an authored assertion without a rendered measurement record.
**Impact:** Accessibility and public-facing safety approval remain unestablished.
**Developer:** Prepare the corrected experience and an owner-approved protocol defining participants,
task, devices/browsers, assistive technologies, contrast backgrounds/styles, sample size, and reporting.
Include focus/selected/disabled/error states and map/fallback equivalence. Preserve human approval as a separate gate.
**Tester positive:** V-HUMAN measures >=90% of first-time participants finding the target within 30s,
documents the <=2-action detail path definition, and records successful marker/sheet/filter traversal.
Measure >=3:1 marker/background contrast and visually verify the specified three shapes.
**Tester negative:** Include colour-only interpretation, hidden focus, unreadable labels, 360px overflow,
unreachable co-located incidents, missing announcements, and table sorting without a mouse; record failures honestly.
**Tester edge:** Text zoom, reduced motion, narrow landscape, screen reader plus mobile keyboard,
different supported map backgrounds/HiDPI, null phase, and no/large results.
**Dependencies and completion:** AUD-020-004, AUD-020-010, AUD-020-011, AUD-020-016, AUD-020-018,
AUD-020-023; named operator/accessibility reviewers, dates, scope, revision, results, and approval decisions
are required. Automated source checks or agent-authored PASS labels cannot substitute.

- [ ] AUD-020-026 [P2] Close requirement-quality questions through explicit decisions

**Obligations:** All CHK001 through CHK130, plan constitution gates, R-001 through R-008,
FR-029, FR-035, NFR-001, SC-001, T006, T011, T017, T030, T036, SCP-059, SCP-060.
**Expected and observed:** The entire [formal checklist](checklists/requirements.md#L1) is unchecked,
while the [plan](plan.md#L23) declares ALL PASS. Source defaults do not supply approval for unresolved
zoom/extent, visual tokens, dates/timezones, filter defaults, latency scope, auth, failure, residency, or browser policy.
**Impact:** Implementers and testers can satisfy different interpretations while reporting the same requirement complete.
**Developer:** Use the per-question table below as an issue register. Obtain scoped decisions for
true ambiguities, resolve specification/contract/task conflicts prospectively, and link the exact approved
decisions to tests. Preserve originals and the frozen baseline. Do not treat every checklist question
as a new mandatory feature: print/export, extra basemaps, multilingual/country variants, or new action
workflows require separate scope approval. Correct constitution section references without weakening its obligations.
**Tester positive:** V-DOC independently matches every resolved question to a named decision/evidence
and test or explicit out-of-scope disposition; verify initial-page and latency interpretations are consistent.
**Tester negative:** Unsupported platform assumptions, empty sign-off fields, generic ALL PASS,
conflated source/runtime proof, and deletion of inconvenient checklist items must fail review.
**Tester edge:** Exactly 768px, 200 versus 500/600 initial load, old/future years, zero-state, unknown
domain values, offline/regional failure, and new 19-type catalogue compatibility.
**Dependencies and completion:** Coordinate all finding owners; scope/security decisions precede
dependent fixes. Close only with approved, traceable answers, not bulk checkbox edits or a new audit of other specs.

- [ ] AUD-020-027 [P2] Repair amendment evidence without inventing validation

**Obligations:** PER-052, PER-053, PER-054, HYP-018, SCP-058, SCP-059, SCP-060, T036;
linked persona/evidence contracts.
**Expected and observed:** [Inline validated labels](spec.md#L252) do not contain mapper-specific
named SME/practitioner evidence. The [hypothesis](spec.md#L260) points to a missing doubled-prefix
HYP-HYP-018 file; searching both plausible filenames found no replacement. The portfolio postfeature
mean does not test an uplift for this individual spec. D-009 remains explicitly deferred.
**Impact:** Persona and hypothesis claims lack the evidence required to promote them to validated outcomes.
**Developer:** Under a separately authorized owning-feature change, correct the reference and author
a conforming, appropriately owned HYP-018 record with status Not tested unless actual controlled evidence
supports another status. Preserve the frozen baseline; define a per-spec comparator and consultation record
for the stated hypothesis. Link real persona validation meeting the schema or keep it UNVERIFIED.
Do not execute additional agents in this audit or promote PH/JP/BD placeholders without all preconditions.
**Tester positive:** V-DOC verifies six ordered stub headings, >=2 preconditions, falsification threshold,
measurement window, exact ID/name, status, and owning-spec linkage. Validate named reviewer role/date and authority fields.
**Tester negative:** Doubled-prefix/broken links, portfolio-only scores offered as per-spec proof,
proxy-only validation, fabricated consultations, or placeholder countries marked validated must fail.
**Tester edge:** Evidence owned by another feature, withdrawn approval, partial cohort prerequisites,
and amended constitution boundaries; keep recovery and warning-authoring ownership outside this mapper.
**Dependencies and completion:** AUD-020-026 and genuine owner/SME review; authored stubs alone complete
documentation repair, not HYP-018 outcome validation or country-scope promotion.

- [ ] AUD-020-028 [P2] Refresh the quickstart and record a real end-to-end rehearsal

**Obligations:** T001, T002, T036, R-001, A-09, A-10, all five independent story tests;
CHK115, CHK116, CHK117, CHK118.
**Expected and observed:** The [guide](quickstart.md#L7) names Python 3.11/Node 18, an unused
NEXT_PUBLIC_API_URL, and the former Playwright config path; [API metadata](../../apps/api/pyproject.toml#L10)
requires Python >=3.12, the [web manifest](../../apps/web/package.json#L22) uses Next 16.2, and current
configuration uses NEXT_PUBLIC_API_BASE_URL/API_PROXY_UPSTREAM. T036's checked state has no accepted
successful rehearsal record. Declared dependency/lockfile content is not proof that installation ran.
**Impact:** A fresh developer can configure the wrong upstream/runtime, and readiness claims are not reproducible.
**Developer:** After prospective approval, document the actual package/runtime versions, environment
contract, mapped data fixture setup, protected API access, .cts test configuration, and dev versus
production Maps auth. Keep credentials out of docs and source. Retain the existing route replacement
and test homes. Do not run the old branch-checkout or deployment instructions during this audit.
**Tester positive:** A future clean authorized environment follows the corrected guide and completes
all five stories, unmapped/freshness notices, failures/retry, keyboard access, and 360px layout; record revision and commands.
**Tester negative:** Missing key/token, wrong upstream, absent seed data, unavailable storage, and
unsupported prerequisites must produce useful diagnostic guidance, not fabricated successful validation.
**Tester edge:** Windows and Linux, no local env files, existing servers/ports, exact dependency lock,
production auth enabled, and cancellation while paging. V-PY/V-UI/V-E2E/V-INFRA prerequisites apply.
**Dependencies and completion:** Relevant implementation fixes and AUD-020-024/AUD-020-025;
complete only with actual dated rehearsal results and honest unresolved gates. No original checkbox is retroactively edited.

- [ ] AUD-020-029 [P2] Align mapper help with the delivered read-only scope

**Obligations:** FR-033, FR-034, FR-036, NFR-001, SCP-058, SCP-060, T036; associated help/review accuracy.
**Expected and observed:** The active [mapper article](../../apps/web/src/content/help/articles/screen-by-screen/disaster-mapper.mdx#L13)
advertises persona/jurisdiction composition, additional layers, action panes, Alt+L, multi-selection,
WebSockets, localStorage, Australian tile assurances, and 5000-signal performance. The connected
[root page](../../apps/web/src/app/page.tsx#L155) is an incident-filter mapper; its
[viewport hook](../../packages/ui/src/components/disaster-map/use-map-viewport.ts#L11) uses sessionStorage.
**Impact:** Operators/help answers can describe unavailable or out-of-scope actions and unsupported safety/performance guarantees.
**Developer:** Correct this associated screen reference to the verified mapper behavior, or clearly
separate proposed/other-surface capabilities with their actual ownership and evidence. Do not implement
new operational actions, non-AU variants, or WebSocket workflows merely to satisfy an overclaimed article.
Maintain the read-only boundary and genuine workspace link, and make failure/accessibility instructions accurate.
**Tester positive:** V-DOC and V-HUMAN compare each claimed mapper control/shortcut/state with the
connected UI; require evidence for residency and performance statements.
**Tester negative:** No described but unimplemented list shortcut, selection ring, layer rail, mutation,
real-time feed, or validated country expansion may remain presented as delivered.
**Tester edge:** Old bookmarks, root navigation, screen-reader fallback, missing credentials, and
distinguishing incident data from simulation overlays or other persona workspaces.
**Dependencies and completion:** AUD-020-012, AUD-020-025, AUD-020-026, AUD-020-028. Completion needs
owner-reviewed documentation parity, not changes to unrelated experiences or other audit reports.

## Requirement Coverage

Rows assess implementation against the original requirement. Runtime quantities/sign-offs remain
UNVERIFIED even where supporting configuration/components exist. Follow-ups address specific gaps;
an IMPLEMENTED row can still depend on a cross-cutting security or measurement gate.

| ID | Status | Inspected evidence and assessment | Follow-ups |
| --- | --- | --- | --- |
| FR-001 | CONFLICT | [Australia bounds/SDK](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L83) exist; [global account](../../infra/main.bicep#L442) and key-only production path contradict the complete requirement. | AUD-020-002, AUD-020-003 |
| FR-002 | PARTIAL | [Feature-to-Point conversion](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L287) is connected; malformed coordinates and suppressed co-located points are not handled fully. | AUD-020-008, AUD-020-011 |
| FR-003 | CONFLICT | [Type-based sprite expression](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L193) ignores severity for marker colour. API tier mapping itself exists. | AUD-020-004, AUD-020-009 |
| FR-003a | CONFLICT | [Single teardrop silhouette](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L115), not circle/triangle/diamond. | AUD-020-004 |
| FR-004 | PARTIAL | [SDK touch/zoom](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L97) and pointer selection handlers exist; production auth, co-location and actual interaction remain gaps. | AUD-020-003, AUD-020-011, AUD-020-023 |
| FR-005 | PARTIAL | [60px clustered source and labels](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L148) exist; maximum-expansion access/error handling and browser assertions are incomplete. | AUD-020-011, AUD-020-023 |
| FR-006 | IMPLEMENTED | [Mounted filter panel](../../apps/web/src/app/page.tsx#L213) has all five requested categories; detailed control deficiencies are assessed separately. | AUD-020-015, AUD-020-016 |
| FR-007 | PARTIAL | [Year selectors](../../packages/ui/src/components/disaster-map/filter-panel.tsx#L195) reach server filters but omit pre-2000 extent and truthful historical boundary policy. | AUD-020-015 |
| FR-008 | IMPLEMENTED | [Type catalogue](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L20) includes all original nine within 19 supported types, rendered as checkboxes. | AUD-020-015, AUD-020-026 |
| FR-009 | PARTIAL | [Three-tier mapping](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L42) is correct; a single warning/emergency URL is not represented truthfully by every()-based checked state. | AUD-020-015 |
| FR-010 | IMPLEMENTED | [Five operational statuses](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L48), with matching API validation; rehearsal is not offered. | AUD-020-022 |
| FR-011 | IMPLEMENTED | [Four phases](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L56) rendered and passed to repository filtering. | AUD-020-022 |
| FR-012 | PARTIAL | [All/Clear helpers](../../packages/ui/src/components/disaster-map/filter-panel.tsx#L100) cover type/status/phase; severity lacks them. | AUD-020-015 |
| FR-013 | PARTIAL | [Parameterized AND/OR query](../../apps/api/app/repositories/incident_map_repository.py#L93) exists; concurrent URL/request updates can publish mismatched combinations. | AUD-020-006, AUD-020-014 |
| FR-014 | PARTIAL | [Client reload effect](../../apps/web/src/app/page.tsx#L127) updates without document reload, but request identity/debounce handling is incomplete. | AUD-020-006, AUD-020-014 |
| FR-015 | PARTIAL | [Count text](../../apps/web/src/app/page.tsx#L188) follows loaded mapped features; stale callbacks/partial-failure state can mislabel the active result count. | AUD-020-006, AUD-020-019 |
| FR-016 | IMPLEMENTED | [Pointer selection](../../apps/web/src/app/page.tsx#L132) mounts [details](../../apps/web/src/app/page.tsx#L263) for supported marker events. Keyboard/mobile deficiencies are separately identified. | AUD-020-010, AUD-020-016 |
| FR-017 | PARTIAL | [Sidebar fields](../../packages/ui/src/components/disaster-map/incident-sidebar.tsx#L97) exist, but null PPRR disappears and selected-data refresh semantics are incomplete. | AUD-020-017 |
| FR-018 | IMPLEMENTED | [Workspace link](../../packages/ui/src/components/disaster-map/incident-sidebar.tsx#L142) reaches the [existing incident page](../../apps/web/src/app/incidents/[incidentId]/page.tsx#L39) and dashboard handler. Successful deployed navigation is not claimed. | AUD-020-017, AUD-020-023 |
| FR-019 | IMPLEMENTED | [Close control](../../packages/ui/src/components/disaster-map/incident-sidebar.tsx#L81) clears selection in the parent; grid returns to map-only content. | AUD-020-010, AUD-020-016 |
| FR-020 | IMPLEMENTED | [setSelectedIncident](../../apps/web/src/app/page.tsx#L132) replaces the selected feature on another supported marker click. | AUD-020-011, AUD-020-017, AUD-020-023 |
| FR-021 | IMPLEMENTED | [Inline top search](../../apps/web/src/app/page.tsx#L160) is connected; absence of SearchBar import is not absence of search. | AUD-020-014 |
| FR-022 | IMPLEMENTED | [Case-insensitive title predicate](../../apps/api/app/repositories/incident_map_repository.py#L109) and [unit assertions](../../tests/unit/test_incident_map_repository.py#L143) implement the scoped search rule. | AUD-020-014, AUD-020-022 |
| FR-023 | PARTIAL | Shared parameters and AND query exist; [debounced stale closure](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L156) and uncancelled results can undo current criteria. | AUD-020-006, AUD-020-014 |
| FR-024 | PARTIAL | [Clear input](../../apps/web/src/app/page.tsx#L173) updates keyword, but pending intent/navigation races are not safely resolved. | AUD-020-014 |
| FR-025 | PARTIAL | [Legacy redirect](../../apps/web/src/app/disasters/page.tsx#L3) reaches the explicitly moved experience, but does not preserve the required bookmarked criteria. | AUD-020-012 |
| FR-026 | IMPLEMENTED | [Root layout](../../apps/web/src/app/layout.tsx#L29) uses AppShell with common navigation. Auth and actual small-screen usability are separate gates. | AUD-020-001, AUD-020-016 |
| FR-027 | PARTIAL | [Desktop grid](../../apps/web/src/app/globals.css#L474) and [768px mobile sheet](../../apps/web/src/app/globals.css#L1003) exist; mobile interactions/stacking and boundary acceptance are incomplete. | AUD-020-016, AUD-020-025 |
| FR-028 | PARTIAL | [Bottom detail card CSS](../../apps/web/src/app/globals.css#L1057) exists but can be behind the open filter sheet. | AUD-020-016 |
| FR-029 | CONFLICT | [Handler/repository](../../apps/api/app/api/routes/incidents_map.py#L111) provide GeoJSON/filtering/pagination/rehearsal exclusion; route version, auth, error and data-validity obligations are not fully met. | AUD-020-001, AUD-020-007, AUD-020-008, AUD-020-009, AUD-020-013 |
| FR-030 | PARTIAL | [Footer notice](../../apps/web/src/app/page.tsx#L277) is connected; source predicate differences and invalid geometry make the count incomplete. | AUD-020-008 |
| FR-031 | MISSING | [Table artifact](../../packages/ui/src/components/disaster-map/list-view-fallback.tsx#L50) exists but no connected root failure path mounts it. | AUD-020-005, AUD-020-018 |
| FR-032 | PARTIAL | [Initial/progressive overlays](../../apps/web/src/app/page.tsx#L225) exist; later-page failure can leave progress running and stale-data presentation unresolved. | AUD-020-006, AUD-020-019 |
| FR-033 | IMPLEMENTED | [Read-only fetch](../../apps/web/src/lib/api/incidents-map.ts#L86), filter setters, selection and links contain no incident mutation or agent handoff call in the scoped mapper. Help claims disagree, not implementation scope. | AUD-020-001, AUD-020-029 |
| FR-034 | PARTIAL | [Last updated](../../apps/web/src/app/page.tsx#L285) uses server fetched_at; no map WebSocket is connected. Partial/stale request publications need honest freshness semantics. | AUD-020-006, AUD-020-019 |
| FR-035 | CONFLICT | [200-page loop](../../apps/web/src/lib/api/incidents-map.ts#L115) follows the contract's progressive sequence, not the literal initial-500 instruction; consistency/failure gaps remain. | AUD-020-019, AUD-020-026 |
| FR-036 | MISSING | [Canvas application](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L223) has no per-marker Tab/Enter/Space interaction surface; disconnected table row handlers do not satisfy it. | AUD-020-010 |
| FR-037 | PARTIAL | [Polite live count](../../apps/web/src/app/page.tsx#L188) exists; announcement correctness depends on active-query fixes. Actual screen-reader results are UNVERIFIED. | AUD-020-006, AUD-020-010, AUD-020-025 |
| FR-038 | PARTIAL | [Tokens](../../packages/ui/src/styles/tokens.css#L46) exist, but actual marker shapes differ and no inspected rendered-contrast measurements prove 3:1. | AUD-020-004, AUD-020-025 |
| NFR-001 | CONFLICT | [Global Maps binding](../../infra/main.bicep#L442) contradicts AU-only account requirement; incident infra location declarations do not prove tile/request residency. | AUD-020-002, AUD-020-003 |
| NFR-002 | PARTIAL | [Console output](../../apps/web/src/app/page.tsx#L139), Node exporter and [backend log extras](../../apps/api/app/api/routes/incidents_map.py#L155) are not all five correct metric instruments. | AUD-020-020 |
| NFR-003 | PARTIAL | [API error/retry banner](../../apps/web/src/app/page.tsx#L196) exists; table degradation is missing, timeout is 15s, and repository initialization can hide failure. | AUD-020-005, AUD-020-007, AUD-020-019 |
| SC-001 | UNVERIFIED | [Initial rendering code](../../apps/web/src/app/page.tsx#L99) and two-item mocks are not a <=3s measurement; initial/all-dataset scope also conflicts. | AUD-020-019, AUD-020-024, AUD-020-026 |
| SC-002 | UNVERIFIED | [Load effect](../../apps/web/src/app/page.tsx#L127) has no accepted <=1s end-to-end filter measurement. | AUD-020-006, AUD-020-014, AUD-020-020, AUD-020-024 |
| SC-003 | PARTIAL | [Marker callback and workspace link](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L251) support the ordinary two-action route, but keyboard/co-located accessibility and actual interaction count remain unverified. | AUD-020-010, AUD-020-011, AUD-020-017, AUD-020-025 |
| SC-004 | UNVERIFIED | [Clustering configuration](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L148) is not a 500-marker frame-rate/interaction record. | AUD-020-021, AUD-020-024 |
| SC-005 | UNVERIFIED | No accepted mapper-specific first-time-user study in the inspected inputs/linked records; [criterion](spec.md#L241) requires 90% within 30s. | AUD-020-025 |
| SC-006 | CONFLICT | [Actual pins](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L115) do not have the required severity silhouettes. | AUD-020-004, AUD-020-025 |
| SC-007 | UNVERIFIED | [Mobile CSS](../../apps/web/src/app/globals.css#L1003) and [375px source tests](../../tests/e2e/test_disaster_mapper.spec.ts#L241) do not prove usable 360px+ states; specific source gaps are recorded. | AUD-020-016, AUD-020-018, AUD-020-025 |
| SC-008 | MISSING | [15s map overlay](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L133) plus no table mounting cannot establish the specified 5s fallback experience. Runtime timing is also UNVERIFIED. | AUD-020-005, AUD-020-024 |
| SC-009 | UNVERIFIED | Five-name export has known source gaps; no accepted triggering-event-to-Log-Analytics <=60s record. [Current emission](../../apps/web/src/app/page.tsx#L139). | AUD-020-020, AUD-020-024 |

## Acceptance Scenario Coverage

Each numbered scenario retains its original story and ordinal. IMPLEMENTED means the ordinary
scoped path is supported by source, not that the acceptance scenario was executed.

| Scenario | Status | Evidence and assessment | Follow-ups |
| --- | --- | --- | --- |
| US1-AS1 | PARTIAL | [Australia bounds](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L83) on fresh viewport; stored view overrides, legacy query redirect and auth/config remain relevant. | AUD-020-002, AUD-020-003, AUD-020-012 |
| US1-AS2 | PARTIAL | [Point features](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L287) render through the mounted map; validity/co-location gaps. | AUD-020-008, AUD-020-011 |
| US1-AS3 | CONFLICT | [Pins by hazard](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L193), not the exact severity colours/shapes. | AUD-020-004 |
| US1-AS4 | UNVERIFIED | SDK pan/zoom configuration and [source updates](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L156) exist; smoothness/placement under interaction not measured. | AUD-020-011, AUD-020-024 |
| US1-AS5 | IMPLEMENTED | [AppShell wrapping](../../apps/web/src/app/layout.tsx#L29). | AUD-020-025 |
| US2-AS1 | PARTIAL | [Year UI](../../packages/ui/src/components/disaster-map/filter-panel.tsx#L195) and query predicate exist; historical lower bound is hard-coded. | AUD-020-015 |
| US2-AS2 | IMPLEMENTED | [Multi-type predicate](../../apps/api/app/repositories/incident_map_repository.py#L94) and [two-type unit assertion](../../tests/unit/test_incident_map_repository.py#L120). | AUD-020-006, AUD-020-023 |
| US2-AS3 | PARTIAL | [Tier values](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L42) include both red severities; URL single-value checkbox state is misleading. | AUD-020-015 |
| US2-AS4 | IMPLEMENTED | [Status predicate](../../apps/api/app/repositories/incident_map_repository.py#L102) and operational status controls. | AUD-020-006, AUD-020-023 |
| US2-AS5 | IMPLEMENTED | [Phase predicate](../../apps/api/app/repositories/incident_map_repository.py#L106) and [phase unit test](../../tests/unit/test_incident_map_repository.py#L137). | AUD-020-006, AUD-020-023 |
| US2-AS6 | PARTIAL | AND/OR composition exists but [stale merge](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L156) can replace active criteria. | AUD-020-006, AUD-020-014 |
| US2-AS7 | PARTIAL | [Reset](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L146) does not invalidate pending keyword commits. | AUD-020-014 |
| US2-AS8 | PARTIAL | [All/Clear helpers](../../packages/ui/src/components/disaster-map/filter-panel.tsx#L100) omit severity. | AUD-020-015 |
| US2-AS9 | PARTIAL | [Live count](../../apps/web/src/app/page.tsx#L188) is connected but accepts stale/partial result state. | AUD-020-006, AUD-020-019 |
| US3-AS1 | PARTIAL | [Sidebar fields](../../packages/ui/src/components/disaster-map/incident-sidebar.tsx#L97) omit valid null PPRR. | AUD-020-017 |
| US3-AS2 | IMPLEMENTED | [Workspace link](../../packages/ui/src/components/disaster-map/incident-sidebar.tsx#L142), existing detail route, dashboard lookup and not-found return path are connected. | AUD-020-017, AUD-020-023 |
| US3-AS3 | IMPLEMENTED | [Close callback](../../apps/web/src/app/page.tsx#L266) removes sidebar and its two-column layout. | AUD-020-010, AUD-020-016 |
| US3-AS4 | IMPLEMENTED | [Selection replacement](../../apps/web/src/app/page.tsx#L132) replaces displayed properties on another supported marker event. | AUD-020-011, AUD-020-017 |
| US3-AS5 | IMPLEMENTED | [Emergency tier class](../../packages/ui/src/components/disaster-map/incident-sidebar.tsx#L35) reaches [red-derived badge styling](../../apps/web/src/app/globals.css#L891). Actual contrast remains unverified. | AUD-020-025 |
| US4-AS1 | IMPLEMENTED | [Case-insensitive title query](../../apps/api/app/repositories/incident_map_repository.py#L110) and inline search path exist. | AUD-020-014, AUD-020-023 |
| US4-AS2 | PARTIAL | Server conjunction exists; [debounce closure](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L156) and late requests can undo it in the UI. | AUD-020-006, AUD-020-014 |
| US4-AS3 | PARTIAL | [Clear search](../../apps/web/src/app/page.tsx#L173) is wired; pending/external-navigation behavior requires repair. | AUD-020-014 |
| US4-AS4 | IMPLEMENTED | [Zero-marker notice/reset](../../apps/web/src/app/page.tsx#L248) is mounted for successful empty results. It must not mask backend failures. | AUD-020-007, AUD-020-023 |
| US5-AS1 | PARTIAL | [Mobile layout](../../apps/web/src/app/globals.css#L1003) and touchInteraction are set; controls/overlays and physical interaction are not fully established. | AUD-020-016, AUD-020-025 |
| US5-AS2 | PARTIAL | [55vh sheet](../../apps/web/src/app/globals.css#L1014) opens/closes by button; swipe, focus, and combined-state handling absent. | AUD-020-010, AUD-020-016 |
| US5-AS3 | PARTIAL | [50vh detail overlay](../../apps/web/src/app/globals.css#L1057) exists but can sit behind the open sheet. | AUD-020-016 |
| US5-AS4 | UNVERIFIED | Responsive CSS exists; orientation/SDK resize and short-landscape usability have no accepted runtime record. [Map sizing](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L225). | AUD-020-016, AUD-020-025 |

## Edge Case Coverage

| Edge | Status | Source obligation and evidence | Follow-ups |
| --- | --- | --- | --- |
| EC-01 | IMPLEMENTED | No matching incidents: [notice/reset](../../apps/web/src/app/page.tsx#L248) and zero-marker update exist for a successful empty response. Test the actual outcome, not the suite's heading surrogate. | AUD-020-007, AUD-020-023 |
| EC-02 | PARTIAL | Missing location: [notice](../../apps/web/src/app/page.tsx#L277) exists; Cosmos/memory predicates and fabricated-origin behavior undermine accounting. | AUD-020-008 |
| EC-03 | PARTIAL | High-density clustering: [60px source](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L148) with count/zoom handlers; no co-located access solution or 50+ real-cluster assertion. | AUD-020-011 |
| EC-04 | MISSING | Map unavailable: [internal overlay](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L235), not the connected sortable/filterable fallback. | AUD-020-005, AUD-020-018 |
| EC-05 | PARTIAL | Slow/intermittent network: [spinner/progress](../../apps/web/src/app/page.tsx#L225) exist; stale publication, timeout and mid-stream-failure states incomplete. | AUD-020-005, AUD-020-006, AUD-020-007, AUD-020-019 |
| EC-06 | PARTIAL | 1000+ records: [progressive loop](../../apps/web/src/lib/api/incidents-map.ts#L111) and clustering exist; initial-500 conflict and scale/completeness evidence remain open. | AUD-020-019, AUD-020-021, AUD-020-024 |
| EC-07 | PARTIAL | Bookmark persistence: [URL hook](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L95) exists, but old-route redirect and delayed-state races lose intended criteria. | AUD-020-012, AUD-020-014 |

## Assumptions, Clarifications, and Amendments

### Assumptions

| ID | Status | Original assumption and evidence assessment | Follow-ups |
| --- | --- | --- | --- |
| A-01 | UNVERIFIED | Majority of records have location: no measured proportion in the reviewed inputs; optional [domain field](../../packages/domain/src/domain/models/incident.py#L44) does not prove population completeness. | AUD-020-008, AUD-020-026 |
| A-02 | CONFLICT | AU-only data/tiles assumption conflicts with [global Maps binding](../../infra/main.bicep#L442); actual serving locality unverified. | AUD-020-002 |
| A-03 | PARTIAL | No required WebSocket; [timestamp](../../apps/web/src/app/page.tsx#L285) and reloads exist, but freshness after partial/cancelled loads needs definition. | AUD-020-019, AUD-020-029 |
| A-04 | IMPLEMENTED | [Mapper GET client](../../apps/web/src/lib/api/incidents-map.ts#L86), state setters and workspace link preserve read-only scope; no mapper handoff call found. | AUD-020-001, AUD-020-029 |
| A-05 | CONFLICT | Earliest-incident-to-current-year assumption differs from [2000-based controls](../../packages/ui/src/components/disaster-map/filter-panel.tsx#L125). | AUD-020-015 |
| A-06 | PARTIAL | Existing auth controls are present but [protected prefixes](../../apps/api/app/middleware/entra_auth.py#L37) omit this read path; sufficiency is not established. | AUD-020-001 |
| A-07 | PARTIAL | [Known tier mapping](../../apps/api/app/models/geojson.py#L11) is correct; renderer ignores tier and unknown severity falls back to advice. | AUD-020-004, AUD-020-009 |
| A-08 | IMPLEMENTED | [Repository excludes rehearsal](../../apps/api/app/repositories/incident_map_repository.py#L84); API and controls omit it. This is not a substitute for authorization. | AUD-020-001, AUD-020-022 |
| A-09 | CONFLICT | [Maps module](../../infra/modules/azure-maps.bicep#L26) is authored, but regional/auth/configuration obligations and deployed provisioning are unresolved. | AUD-020-002, AUD-020-003, AUD-020-028 |
| A-10 | CONFLICT | [New read router](../../apps/api/app/api/routes/incidents_map.py#L26) leaves existing incident routes in place, but default version/error semantics differ. | AUD-020-013 |

### Clarification Sessions

CL-01 through CL-05 are the five decisions in [pass one](spec.md#L215). CL-06 through CL-12 are
the seven decisions in [pass two](spec.md#L223). All were read; none is silently discarded.

| ID | Status | Decision and implementation assessment | Follow-ups |
| --- | --- | --- | --- |
| CL-01 | CONFLICT | Azure Maps via AU East Bicep: SDK exists but [module is bound global](../../infra/main.bicep#L442). | AUD-020-002, AUD-020-003 |
| CL-02 | PARTIAL | Four severity values to three AWS tiers: [API mapping](../../apps/api/app/models/geojson.py#L11) correct; marker encoding absent. | AUD-020-004, AUD-020-009 |
| CL-03 | CONFLICT | Circle/triangle/diamond decision: [teardrops](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L115) replace required silhouettes without a cited superseding decision. | AUD-020-004 |
| CL-04 | CONFLICT | Separate `/api/v1` map endpoint: [separate router](../../apps/api/app/api/router.py#L58) exists, version prefix differs. | AUD-020-013 |
| CL-05 | PARTIAL | URL-persisted filters: [hook](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L95) exists; redirect/timer races violate complete restoration. | AUD-020-012, AUD-020-014 |
| CL-06 | PARTIAL | GeoJSON Point/FeatureCollection: [models](../../apps/api/app/models/geojson.py#L22) exist, but invalid data and count parity need repair. | AUD-020-008 |
| CL-07 | CONFLICT | AU-only tiles/data and no external tile CDN: [global account](../../infra/main.bicep#L442); no accepted locality verification. | AUD-020-002 |
| CL-08 | PARTIAL | All five named metrics: [current logs](../../apps/web/src/app/page.tsx#L139) do not provide them; exporter/timing gap. | AUD-020-020 |
| CL-09 | PARTIAL | Tab/Enter/Space, live regions, 3:1: count region exists; [map markup](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L223) lacks per-marker access; contrast unverified. | AUD-020-004, AUD-020-010, AUD-020-025 |
| CL-10 | IMPLEMENTED | Read-only, workspace actions elsewhere: [workspace link](../../packages/ui/src/components/disaster-map/incident-sidebar.tsx#L142), no mapper mutations found. | AUD-020-029 |
| CL-11 | PARTIAL | Refresh/reapply, no WebSocket, timestamp: [footer](../../apps/web/src/app/page.tsx#L285) and GET loading exist; stale/partial freshness issue. | AUD-020-019, AUD-020-029 |
| CL-12 | CONFLICT | Default 200 pagination plus initial most-recent 500: [loop](../../apps/web/src/lib/api/incidents-map.ts#L111) follows the inconsistent supporting contract. | AUD-020-019, AUD-020-026 |

### Appended Persona, Hypothesis, and Scope Obligations

| ID | Status | Evidence assessment | Follow-ups |
| --- | --- | --- | --- |
| PER-052 | UNVERIFIED | [Cross-reference and validated label](spec.md#L252) are authored; no mapper-specific named validation satisfying the linked persona schema is established. | AUD-020-027 |
| PER-053 | UNVERIFIED | [Technical-actor catalogue reference](spec.md#L253) exists; actor existence/agent instructions do not prove consultation or SME validation of this map. | AUD-020-027 |
| PER-054 | IMPLEMENTED | [Non-AU placeholder and preconditions](spec.md#L254) are explicit; promotion remains UNVERIFIED and unapproved. No country rollout inferred. | AUD-020-027 |
| HYP-018 | MISSING | [Named evidence stub](spec.md#L260) not found under either plausible filename. Hypothesis outcome remains UNVERIFIED; portfolio scores are not its test. | AUD-020-027 |
| SCP-058 | IMPLEMENTED | [Country deferral](spec.md#L266) and [D-009](../028-capstone-alignment/evidence/decision-record.md#L13) explicitly retain prerequisite gates. Their clearance is UNVERIFIED. | AUD-020-002, AUD-020-027, AUD-020-029 |
| SCP-059 | IMPLEMENTED | [Constitution authority boundary](spec.md#L267) is authored; Maps conflict must be escalated, not resolved by widening the inference-only carve-out. | AUD-020-002, AUD-020-026 |
| SCP-060 | IMPLEMENTED | [Recovery/warning-authoring deferrals](spec.md#L268) are explicit. No operational authoring scope is inferred from the help article. | AUD-020-026, AUD-020-029 |

### Supporting Design and Data Contract Coverage

| ID | Status | Decision/artifact and implementation evidence | Follow-ups |
| --- | --- | --- | --- |
| R-001 | PARTIAL | [Dynamic imports/cleanup](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L72) exist; deployed key/Entra configuration and updated runtime prerequisites disagree with the research. | AUD-020-003, AUD-020-028 |
| R-002 | CONFLICT | [Actual sprites](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L115) are type pins, not the chosen tier sprites. Contrast assertion has no measurement proof. | AUD-020-004, AUD-020-025 |
| R-003 | PARTIAL | [DataSource clustering](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L148) and layers exist; maximum expansion and 10000-point performance claims unverified. | AUD-020-011, AUD-020-024 |
| R-004 | CONFLICT | [Module](../../infra/modules/azure-maps.bicep#L5) permits global and dev keys, main omits CORS/output bindings, Entra browser path absent. | AUD-020-002, AUD-020-003 |
| R-005 | PARTIAL | [Separate repository/router](../../apps/api/app/api/routes/incidents_map.py#L21) preserve single-purpose reads; actual envelope is metadata-based, storage is seed, and version/errors/auth need reconciliation. | AUD-020-001, AUD-020-008, AUD-020-013, AUD-020-026 |
| R-006 | PARTIAL | [Optional location dict](../../packages/domain/src/domain/models/incident.py#L44) matches backward compatibility; promised API-boundary structural validity is incomplete. | AUD-020-008, AUD-020-009 |
| R-007 | PARTIAL | [URL hook](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L95) implements the selected approach, with timer/redirect/state defects. | AUD-020-012, AUD-020-014 |
| R-008 | CONFLICT | Research proposes meter instruments; [actual browser](../../apps/web/src/app/page.tsx#L139) uses console.debug, while exporter is Node-only. | AUD-020-020 |
| DATA-01 | IMPLEMENTED | Incident location remains optional; [domain model](../../packages/domain/src/domain/models/incident.py#L32) retains required incident fields and default phase/level. No migration/backfill execution proved. | AUD-020-008, AUD-020-028 |
| DATA-02 | PARTIAL | [Jurisdiction/organization properties](../../apps/api/app/models/geojson.py#L46) are propagated and displayed as IDs; reference existence, authority scope, and population quality not proved by arrays. | AUD-020-001, AUD-020-017 |
| DATA-03 | PARTIAL | [GeoJSON envelope and metadata](../../apps/api/app/models/geojson.py#L57) authored; identity, finite/ranged geometry, enum/date/level and exact count semantics need stronger validation/assertions. | AUD-020-008, AUD-020-009, AUD-020-022 |
| DATA-04 | PARTIAL | [Parameterized query](../../apps/api/app/repositories/incident_map_repository.py#L56) implements nine query criteria/paging; unknowns, response errors and schema parity assessed above. | AUD-020-008, AUD-020-013, AUD-020-019 |
| DATA-05 | CONFLICT | [Shared seed storage/partition](../../apps/api/app/repositories/incident_map_repository.py#L20) and main differ from the design's incidents-container/index recommendation. Do not invent a missing store; validate the current projection/index policy. | AUD-020-021, AUD-020-026 |
| DATA-06 | PARTIAL | [Readonly endpoint](../../apps/api/app/api/routes/incidents_map.py#L111) and no-store client exist; intended fresh counts, no rehearsal, unavailable-versus-empty, initial batch and partial-failure contracts are covered by explicit follow-ups. | AUD-020-007, AUD-020-019 |

## Original Task Coverage

Each row represents exactly one original task and its exact checkbox state from
[tasks.md](tasks.md#L1). `UNVERIFIED` on an execution task does not mean its source artifact is absent.
No row asserts test execution. The root route and `.cts` config replacements have been inspected.

| Task ID | Original checkbox | Status | Concrete implementation/test evidence and remaining obligation | Follow-ups |
| --- | --- | --- | --- | --- |
| T001 | [x] | UNVERIFIED | [UI dependency](../../packages/ui/package.json#L25) and [3.7.4 lock entry](../../pnpm-lock.yaml#L1596) implement declaration/resolution; `pnpm install` execution is not proven. | AUD-020-028 |
| T002 | [x] | IMPLEMENTED | [GeoJSON models](../../apps/api/app/models/geojson.py#L1), [model package initializer](../../apps/api/app/models/__init__.py#L1), [map folder source](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L1), and [legacy route](../../apps/web/src/app/disasters/page.tsx#L1) establish scaffolding. | AUD-020-012 |
| T003 | [x] | IMPLEMENTED | [Any import and optional location field](../../packages/domain/src/domain/models/incident.py#L2) preserve the existing Incident model/default. No backfill run implied. | AUD-020-008 |
| T004 | [x] | PARTIAL | [Five response model classes and tier map](../../apps/api/app/models/geojson.py#L11) exist; complete valid-Point/domain semantics and assertions absent. | AUD-020-008, AUD-020-009, AUD-020-022 |
| T005 | [x] | IMPLEMENTED | [Three exact CSS tokens](../../packages/ui/src/styles/tokens.css#L46) exist and globals imports them. Their existence does not mean the actual marker layer uses them. | AUD-020-004 |
| T006 | [x] | CONFLICT | [Gen2 resource](../../infra/modules/azure-maps.bicep#L26) exists, but location permits global and auth policy permits dev keys rather than the unconditional task statement. Platform/policy approval unverified. | AUD-020-002, AUD-020-003 |
| T007 | [x] | PARTIAL | [Main module invocation](../../infra/main.bicep#L439) exists; CORS origins and Maps outputs are not wired and location is global. | AUD-020-002, AUD-020-003 |
| T008 | [x] | PARTIAL | [Dynamic queries/paging](../../apps/api/app/repositories/incident_map_repository.py#L56) exist in the replacement seed store; count validity, authorization, failure and async execution gaps remain. | AUD-020-001, AUD-020-007, AUD-020-008, AUD-020-021 |
| T009 | [x] | CONFLICT | [Handler and validation](../../apps/api/app/api/routes/incidents_map.py#L111) exist; default `/api` path, 422 numeric validation, missing map auth, and unsafe adaptation differ from contract. | AUD-020-001, AUD-020-008, AUD-020-009, AUD-020-013 |
| T010 | [x] | IMPLEMENTED | [Import and include](../../apps/api/app/api/router.py#L21) register the mapper router; the dashboard route's shape does not shadow `/incidents/map`. | AUD-020-013 |
| T011 | [x] | PARTIAL | [Typed progressive client](../../apps/web/src/lib/api/incidents-map.ts#L66) exists and follows 200-page task wording; abort/publication and initial-500 specification conflict unresolved. | AUD-020-006, AUD-020-019 |
| T012 | [x] | CONFLICT | [Clustering/layers](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L148) exist, but [type-pin expression](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L193) replaces specified severity sprites. | AUD-020-004, AUD-020-011 |
| T013 | [x] | PARTIAL | [Client-only map lifecycle](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L63), CSS import, bounds/viewport restoration, and disposal exist; auth/failure/access paths incomplete. | AUD-020-003, AUD-020-005, AUD-020-010 |
| T014 | [x] | PARTIAL | [Explicit root replacement](../../apps/web/src/app/page.tsx#L4) loads map/data inside AppShell; old URL query loss and load-state issues mean obligations are not wholly superseded. | AUD-020-006, AUD-020-012, AUD-020-014 |
| T015 | [x] | IMPLEMENTED | [Page/grid CSS](../../apps/web/src/app/globals.css#L327) provides height and desktop side-panel layout. Actual responsive behavior is not proved by styles. | AUD-020-016, AUD-020-025 |
| T016 | [x] | PARTIAL | [Filter hook](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L95) reads/pushes URL state; stable identity, debounce/reset/history correctness and validation are incomplete. | AUD-020-012, AUD-020-014, AUD-020-015 |
| T017 | [x] | PARTIAL | [Filter panel](../../packages/ui/src/components/disaster-map/filter-panel.tsx#L50) renders all categories/current catalogue; fixed year extent and missing severity bulk controls violate task detail. | AUD-020-015, AUD-020-016 |
| T018 | [x] | PARTIAL | [Mounted filters/count/load](../../apps/web/src/app/page.tsx#L91) exist; latest-query correctness and partial-data counts need repair. | AUD-020-006, AUD-020-014, AUD-020-019 |
| T019 | [x] | PARTIAL | [Sidebar](../../packages/ui/src/components/disaster-map/incident-sidebar.tsx#L62) has detail fields/link/close; null PPRR is omitted and task ISO wording differs from local display. | AUD-020-017, AUD-020-026 |
| T020 | [x] | IMPLEMENTED | [Marker callback reconstruction](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L242) reaches [page selection](../../apps/web/src/app/page.tsx#L132); close and replacement are wired for supported event shapes. Actual clicks unverified. | AUD-020-010, AUD-020-011, AUD-020-017, AUD-020-023 |
| T021 | [x] | PARTIAL | [SearchBar artifact](../../packages/ui/src/components/disaster-map/search-bar.tsx#L20) exists, with [live inline equivalent](../../apps/web/src/app/page.tsx#L160). Hook-driven debounce semantics are incomplete, not an absent-search finding. | AUD-020-014 |
| T022 | [x] | PARTIAL | [Inline search and empty notice](../../apps/web/src/app/page.tsx#L248) are connected; active combined-query correctness needs race/debounce fixes and meaningful assertions. | AUD-020-006, AUD-020-014, AUD-020-023 |
| T023 | [x] | PARTIAL | [768px CSS](../../apps/web/src/app/globals.css#L1003) and [touchInteraction](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L99) exist; full mobile/rotation behavior and 360px usability unverified. | AUD-020-016, AUD-020-025 |
| T024 | [x] | PARTIAL | [Sheet styling](../../apps/web/src/app/globals.css#L1014) and [toggle buttons](../../packages/ui/src/components/disaster-map/filter-panel.tsx#L138) exist; swipe dismissal/focus and combined-state behavior absent. | AUD-020-010, AUD-020-016 |
| T025 | [x] | PARTIAL | [Detail overlay CSS](../../apps/web/src/app/globals.css#L1057) exists; no tap-outside handler, managed exit transition, or protection from filter-sheet occlusion. | AUD-020-016, AUD-020-017 |
| T026 | [x] | PARTIAL | [Six-column table](../../packages/ui/src/components/disaster-map/list-view-fallback.tsx#L105) exists and mouse sorts; disconnected filters/mount, coordinate semantics and keyboard sorting need repair. | AUD-020-005, AUD-020-018 |
| T027 | [x] | MISSING | [Root map-only rendering](../../apps/web/src/app/page.tsx#L242) never mounts fallback; [timeout](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L133) is 15s, not the specified 5s integration. | AUD-020-005 |
| T028 | [x] | PARTIAL | [Page-level loading/progress](../../apps/web/src/app/page.tsx#L225) implements relocated indicators; mid-stream-error completion and stale state unresolved. | AUD-020-006, AUD-020-019 |
| T029 | [x] | PARTIAL | [Footer](../../apps/web/src/app/page.tsx#L275) renders both requested notices; correctness depends on unmapped accounting and partial/active fetch metadata. | AUD-020-006, AUD-020-008, AUD-020-019 |
| T030 | [x] | PARTIAL | [Polite count](../../apps/web/src/app/page.tsx#L188), labels and landmarks exist; marker keyboard navigation, focus states and measured contrast are not complete. | AUD-020-004, AUD-020-010, AUD-020-025 |
| T031 | [x] | MISSING | [Console.debug calls](../../apps/web/src/app/page.tsx#L139) are not the required meter instruments; filter_apply_ms absent and timings incorrect. | AUD-020-020 |
| T032 | [x] | PARTIAL | [Error counters/log extras](../../apps/api/app/api/routes/incidents_map.py#L155) cover caught repository errors, not the defined all-failure metric or window/export contract. | AUD-020-020 |
| T033 | [x] | PARTIAL | [22 unit declarations](../../tests/unit/test_incident_map_repository.py#L103) cover ordinary memory filters and limited SQL fragments; query values/parity/failure cases and CI selection incomplete. | AUD-020-022 |
| T034 | [x] | PARTIAL | [25 contract declarations](../../tests/contract/test_incidents_map_contract.py#L74) cover basic schema/filters; all-field semantics, auth and 500/503 cases missing, some checks vacuous/weak. | AUD-020-022 |
| T035 | [x] | PARTIAL | [15 E2E declarations](../../tests/e2e/test_disaster_mapper.spec.ts#L81) are discovered by [replacement config](../../apps/web/playwright.config.cts#L4), but required connected interactions/assertions/360px scope are not established. | AUD-020-023, AUD-020-024, AUD-020-025 |
| T036 | [x] | UNVERIFIED | [Quickstart](quickstart.md#L1) is a procedure, not completion proof; inspected historical error contexts and [failed last-run](../../apps/web/test-results/.last-run.json#L2) do not establish a successful revision-bound rehearsal. | AUD-020-024, AUD-020-025, AUD-020-028 |

## Checklist Evidence Assessment

Every original checklist item remains `[ ]`. The status below assesses the evidence for the
question, not whether an authorized reviewer approved it. IMPLEMENTED means an explicit written
answer or consistency is supported; PARTIAL often means source has a default but requirements or
verification do not close the question. MISSING denotes a missing definition in the reviewed local
inputs, not automatic authorization to add a new product feature. All formal sign-offs remain
UNVERIFIED until actual records meet AUD-020-025/AUD-020-026.

| Checklist ID | Original checkbox | Status | Question-specific evidence assessment | Follow-ups |
| --- | --- | --- | --- | --- |
| CHK001 | [ ] | PARTIAL | Initial fit: R-001 specifies centre/zoom; [live bounds plus saved viewport](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L83) differ. Approved reproducible initial-state rule needed. | AUD-020-026 |
| CHK002 | [ ] | MISSING | Min/max zoom not defined in local requirements; [SDK options](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L88) rely on defaults. | AUD-020-011, AUD-020-026 |
| CHK003 | [ ] | PARTIAL | Marker dimensions are source choices: [30x42 pin](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L115), scale 0.85; no approved severity-marker dimension requirement. | AUD-020-004, AUD-020-026 |
| CHK004 | [ ] | IMPLEMENTED | Exact hues agree in [FR-003](spec.md#L120), clarifications and [tokens](../../packages/ui/src/styles/tokens.css#L46); actual renderer is separately nonconforming. | AUD-020-004 |
| CHK005 | [ ] | CONFLICT | Shape dimension question cannot be closed by teardrop dimensions when [FR-003a](spec.md#L121) requires three other silhouettes. | AUD-020-004, AUD-020-026 |
| CHK006 | [ ] | PARTIAL | [T023](tasks.md#L124) names touch gestures and [touchInteraction](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L99) is enabled; actual pinch/two-finger behavior unverified. | AUD-020-016, AUD-020-025 |
| CHK007 | [ ] | PARTIAL | [Cluster style/label options](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L157) exist; source constants are not an approved design delegation/visual review. | AUD-020-011, AUD-020-026 |
| CHK008 | [ ] | MISSING | No defined terminal expansion/co-location behavior beyond [zoom handler](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L220). | AUD-020-011 |
| CHK009 | [ ] | PARTIAL | [60px radius](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L150) follows FR-005/R-003; HiDPI rationale/verification not documented. | AUD-020-011, AUD-020-025 |
| CHK010 | [ ] | PARTIAL | [Both layouts start open](../../apps/web/src/app/page.tsx#L87); no approved per-layout initial state in local requirements. | AUD-020-016, AUD-020-026 |
| CHK011 | [ ] | PARTIAL | [Source ordering](../../packages/ui/src/components/disaster-map/filter-panel.tsx#L164) is Status, Date, Type, Severity, Phase; formal ordering/delegation not closed. | AUD-020-026 |
| CHK012 | [ ] | IMPLEMENTED | [R-007](research.md#L1) explicitly says all filters unset means show all; hook has corresponding defaults. Formal review still unverified. | AUD-020-014, AUD-020-026 |
| CHK013 | [ ] | PARTIAL | [API inverted-year 400](../../apps/api/app/api/routes/incidents_map.py#L136) is defined; user-facing correction and UI constraints need completion. | AUD-020-013, AUD-020-015 |
| CHK014 | [ ] | IMPLEMENTED | [Year select elements](../../packages/ui/src/components/disaster-map/filter-panel.tsx#L199) implement selectors specified by T017. | AUD-020-015 |
| CHK015 | [ ] | CONFLICT | Dynamic earliest year is in [assumptions](spec.md#L206)/T017, but [source starts 2000](../../packages/ui/src/components/disaster-map/filter-panel.tsx#L125). | AUD-020-015 |
| CHK016 | [ ] | IMPLEMENTED | [R-007 defaults](research.md#L1) and [empty CSV checked state](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L203) define no selected type restriction. | AUD-020-026 |
| CHK017 | [ ] | PARTIAL | Reset-to-unset is documented and [implemented](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L146), but severity bulk reset and pending timers defeat complete behavior. | AUD-020-014, AUD-020-015 |
| CHK018 | [ ] | PARTIAL | R-007/T016 specify keyword-only 300ms delay; [new filter identity per input render](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L101) undermines it. | AUD-020-014 |
| CHK019 | [ ] | IMPLEMENTED | T018 places count above map; [status paragraph](../../apps/web/src/app/page.tsx#L188) supplies text format and live region. | AUD-020-006, AUD-020-019 |
| CHK020 | [ ] | PARTIAL | [features.length](../../apps/web/src/app/page.tsx#L191) excludes unmapped count; loaded versus viewport-visible and partial-data semantics need explicit agreement. | AUD-020-019, AUD-020-020, AUD-020-026 |
| CHK021 | [ ] | PARTIAL | [380px desktop detail track](../../apps/web/src/app/globals.css#L503) is a source default, not an approved responsive width rule. | AUD-020-016, AUD-020-026 |
| CHK022 | [ ] | PARTIAL | [Entry animation](../../apps/web/src/app/globals.css#L792) exists; required exit and reduced-motion handling not established. | AUD-020-016 |
| CHK023 | [ ] | CONFLICT | T019 says ISO-formatted start date; [sidebar](../../packages/ui/src/components/disaster-map/incident-sidebar.tsx#L47) uses browser-local en-AU display. Timezone decision missing. | AUD-020-017, AUD-020-026 |
| CHK024 | [ ] | PARTIAL | [Uppercase comma-separated jurisdiction IDs](../../packages/ui/src/components/disaster-map/incident-sidebar.tsx#L123) are implemented; long/empty list presentation not validated. | AUD-020-017, AUD-020-025 |
| CHK025 | [ ] | IMPLEMENTED | [Level n display](../../packages/ui/src/components/disaster-map/incident-sidebar.tsx#L121) answers numeric format; invalid levels remain a separate data-validation gap. | AUD-020-009 |
| CHK026 | [ ] | IMPLEMENTED | [Open Workspace link](../../packages/ui/src/components/disaster-map/incident-sidebar.tsx#L142) and styling provide concrete text/treatment; usability not measured. | AUD-020-017, AUD-020-025 |
| CHK027 | [ ] | PARTIAL | T025 requires mobile tap-outside close; [sidebar](../../packages/ui/src/components/disaster-map/incident-sidebar.tsx#L74) only exposes a close button. | AUD-020-016 |
| CHK028 | [ ] | PARTIAL | [Selection replacement](../../apps/web/src/app/page.tsx#L132) produces immediate property swap; intended animation/focus semantics lack approval. | AUD-020-017, AUD-020-026 |
| CHK029 | [ ] | IMPLEMENTED | [300ms debounce](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L159) is specified by R-007/T016; behavior defects do not mean the delay was unspecified. | AUD-020-014 |
| CHK030 | [ ] | IMPLEMENTED | [FR-022](spec.md#L149) explicitly limits matching to titles, despite story prose mentioning description; no description search inferred. | AUD-020-026 |
| CHK031 | [ ] | IMPLEMENTED | [Mounted no-results overlay](../../apps/web/src/app/page.tsx#L248) uses the specified content and reset action. | AUD-020-023 |
| CHK032 | [ ] | PARTIAL | [URL state](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L101) supports preservation, but redirect and pending navigation races undermine it. | AUD-020-012, AUD-020-014 |
| CHK033 | [ ] | PARTIAL | [768px and 400px rules](../../apps/web/src/app/globals.css#L1003) exist; tablet/desktop scope and exact boundary acceptance need a decision. | AUD-020-016, AUD-020-026 |
| CHK034 | [ ] | PARTIAL | [55vh sheet maximum](../../apps/web/src/app/globals.css#L1024) is implemented; visible usable map area at short heights not established. | AUD-020-016, AUD-020-025 |
| CHK035 | [ ] | UNVERIFIED | [US5-AS4](spec.md#L99) says adapts smoothly; no accepted landscape/rotation measurement or detailed short-height policy. | AUD-020-016, AUD-020-025, AUD-020-026 |
| CHK036 | [ ] | PARTIAL | [SC-007](spec.md#L243) and T023/T025 set 360px; the FR section uses breakpoint wording and tests override to 375px. | AUD-020-016, AUD-020-023 |
| CHK037 | [ ] | PARTIAL | [Contract](contracts/incidents-map-api.md#L23) enumerates parameters/types/rules; version/year limits/validation statuses diverge in implementation. | AUD-020-013, AUD-020-015 |
| CHK038 | [ ] | PARTIAL | [Response schema](contracts/incidents-map-api.md#L115) and models exist; valid geometry/domain value semantics and tests incomplete. | AUD-020-008, AUD-020-009, AUD-020-022 |
| CHK039 | [ ] | IMPLEMENTED | [started_at DESC](../../apps/api/app/repositories/incident_map_repository.py#L125) follows task/data-model intent; tie/snapshot policy separately open. | AUD-020-019 |
| CHK040 | [ ] | PARTIAL | [Loader](../../apps/web/src/lib/api/incidents-map.ts#L121) has no total cap and runs to a short page; operational size limits and measurement interpretation not agreed. | AUD-020-019, AUD-020-024, AUD-020-026 |
| CHK041 | [ ] | PARTIAL | [Footer notice](../../apps/web/src/app/page.tsx#L277) is nondismissible; no explicit location/dismissibility decision in requirements. | AUD-020-026 |
| CHK042 | [ ] | IMPLEMENTED | [Table state](../../packages/ui/src/components/disaster-map/list-view-fallback.tsx#L55) defaults to started_at descending; mounting and chronological semantics remain separate issues. | AUD-020-018 |
| CHK043 | [ ] | PARTIAL | Manual retry is specified and [implemented](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L240), but no connected fallback/recovery contract. | AUD-020-005 |
| CHK044 | [ ] | IMPLEMENTED | [Map-area spinner/progress](../../apps/web/src/app/page.tsx#L225) gives the requested type/placement; source is relocated to the page. | AUD-020-019 |
| CHK045 | [ ] | PARTIAL | [toLocaleString](../../apps/web/src/app/page.tsx#L286) is a source default, not an agreed timezone/freshness contract. | AUD-020-019, AUD-020-026 |
| CHK046 | [ ] | IMPLEMENTED | [Footer timestamp](../../apps/web/src/app/page.tsx#L285) establishes position; original requirements lack separate layout prescription. | AUD-020-026 |
| CHK047 | [ ] | PARTIAL | [Catch branch](../../apps/web/src/app/page.tsx#L113) shows an error but does not finish/label partial loading coherently. | AUD-020-006, AUD-020-019 |
| CHK048 | [ ] | CONFLICT | [Written error table](contracts/incidents-map-api.md#L170) differs from 422 tests, missing map auth, and unavailability fallback behavior. | AUD-020-001, AUD-020-007, AUD-020-013 |
| CHK049 | [ ] | MISSING | No marker focus/tab-order definition or controller in [map markup](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L223). | AUD-020-010 |
| CHK050 | [ ] | MISSING | [Canvas markers](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L203) have no implemented per-marker focus indicator/state. | AUD-020-010 |
| CHK051 | [ ] | PARTIAL | Native filter/search/close controls exist, but [table headers](../../packages/ui/src/components/disaster-map/list-view-fallback.tsx#L124) are mouse-only and sheet/detail focus incomplete. | AUD-020-010, AUD-020-018 |
| CHK052 | [ ] | IMPLEMENTED | [Showing n incidents](../../apps/web/src/app/page.tsx#L191) matches FR-037's message template. Correct announcement sequencing remains unverified. | AUD-020-010, AUD-020-025 |
| CHK053 | [ ] | IMPLEMENTED | [aria-live polite](../../apps/web/src/app/page.tsx#L188) implements T030. | AUD-020-025 |
| CHK054 | [ ] | PARTIAL | [Filter icon labels](../../packages/ui/src/components/disaster-map/severity-icon.tsx#L42) exist but repeat adjacent text; actual marker/cluster accessible names are missing. | AUD-020-010 |
| CHK055 | [ ] | UNVERIFIED | R-002 asserts contrast against a road background; [actual renderer](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L115) differs and no rendered style/state measurements are supplied. | AUD-020-004, AUD-020-025 |
| CHK056 | [ ] | PARTIAL | [Map application](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L231), filter search and sidebar complementary roles exist; live inline search lacks the standalone SearchBar landmark and per-marker controls. | AUD-020-010 |
| CHK057 | [ ] | PARTIAL | [Plan performance goals](plan.md#L18) give >=30 FPS and latency, but no accepted interaction benchmark scope/result. | AUD-020-024, AUD-020-026 |
| CHK058 | [ ] | PARTIAL | Plan adds FPS threshold to [SC-004](spec.md#L240); input-latency/freeze criteria and actual measures remain open. | AUD-020-024, AUD-020-026 |
| CHK059 | [ ] | MISSING | "Longer than expected" network delay is not bounded by a data-request timeout in [fetch](../../apps/web/src/lib/api/incidents-map.ts#L86). | AUD-020-005, AUD-020-019, AUD-020-026 |
| CHK060 | [ ] | IMPLEMENTED | [Styled workspace link](../../packages/ui/src/components/disaster-map/incident-sidebar.tsx#L142) supplies a concrete prominent treatment; user success unverified. | AUD-020-025 |
| CHK061 | [ ] | UNVERIFIED | [SC-007](spec.md#L243) identifies overflow/truncation but no complete touch/focus/orientation acceptance measurements. | AUD-020-016, AUD-020-025 |
| CHK062 | [ ] | MISSING | [SC-005](spec.md#L241) gives 90%/30s but no participant count/protocol/environment in the reviewed inputs. | AUD-020-025, AUD-020-026 |
| CHK063 | [ ] | MISSING | [SC-001](spec.md#L237) lacks a device/network/cache test profile; no profile-bound measurements supplied. | AUD-020-024, AUD-020-026 |
| CHK064 | [ ] | IMPLEMENTED | [Operational values](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L48) and [rehearsal predicate](../../apps/api/app/repositories/incident_map_repository.py#L84) agree. | AUD-020-022 |
| CHK065 | [ ] | IMPLEMENTED | [Spec tier mapping](spec.md#L120) and [API mapping](../../apps/api/app/models/geojson.py#L11) agree across referenced texts; current marker presentation still conflicts. | AUD-020-004, AUD-020-009 |
| CHK066 | [ ] | PARTIAL | [CSS](../../apps/web/src/app/globals.css#L1003) addresses mobile and <400px, but exact 768px and intermediate/mobile states lack verification. | AUD-020-016, AUD-020-025 |
| CHK067 | [ ] | IMPLEMENTED | [Zero-state text](../../apps/web/src/app/page.tsx#L250) is consistent with edge/story requirements; historical test checks different content. | AUD-020-023 |
| CHK068 | [ ] | CONFLICT | [NFR-003](spec.md#L193) and SC-008 agree at 5s; [source timeout](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L133) is 15s without table activation. | AUD-020-005 |
| CHK069 | [ ] | CONFLICT | [FR-035](spec.md#L168) says 500 initial; contract/T011 use 200-page sequence, reaching 600 on three full pages. | AUD-020-019, AUD-020-026 |
| CHK070 | [ ] | IMPLEMENTED | [GeoJSON model shape](../../apps/api/app/models/geojson.py#L22), spec and data model agree structurally; validity enforcement remains PARTIAL separately. | AUD-020-008 |
| CHK071 | [ ] | IMPLEMENTED | [NFR metric list](spec.md#L184) and [SC-009](spec.md#L245) name the same five metrics; implementation export is incomplete. | AUD-020-020 |
| CHK072 | [ ] | CONFLICT | [SC-001 all mapped](spec.md#L237) versus initial-500/progressive-full-dataset scope has no explicit performance interpretation. | AUD-020-019, AUD-020-024, AUD-020-026 |
| CHK073 | [ ] | PARTIAL | [SC-002](spec.md#L238) is user-visible; R-008 gives filter-to-render intent, but actual timer and network inclusion are not validated. | AUD-020-020, AUD-020-024 |
| CHK074 | [ ] | MISSING | [SC-003](spec.md#L239) lacks an approved action-count protocol for clusters/filters/keyboard activation. | AUD-020-011, AUD-020-025, AUD-020-026 |
| CHK075 | [ ] | MISSING | [SC-004](spec.md#L240) does not resolve loaded versus simultaneously visible markers or the measurement method. | AUD-020-024, AUD-020-026 |
| CHK076 | [ ] | MISSING | [Usability criterion](spec.md#L241) has no sample-size/statistical acceptance method. | AUD-020-025, AUD-020-026 |
| CHK077 | [ ] | MISSING | [SC-009](spec.md#L245) has no accepted event-to-query measurement procedure/result. | AUD-020-020, AUD-020-024 |
| CHK078 | [ ] | PARTIAL | [Empty response overlay](../../apps/web/src/app/page.tsx#L248) covers no data visually but does not distinguish legitimate zero-state from repository initialization failure. | AUD-020-007, AUD-020-026 |
| CHK079 | [ ] | IMPLEMENTED | [Empty filtered result notice/reset](../../apps/web/src/app/page.tsx#L248) implements the stated all-filtered-out outcome. | AUD-020-014, AUD-020-023 |
| CHK080 | [ ] | PARTIAL | [URL parser](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L101) passes raw enums and loosely parses years; server rejects some invalid values, no agreed UI recovery policy. | AUD-020-013, AUD-020-014 |
| CHK081 | [ ] | MISSING | No authenticated deep-link return flow in [root/redirect](../../apps/web/src/app/disasters/page.tsx#L3); auth assumption not enforced by the map route. | AUD-020-001, AUD-020-012 |
| CHK082 | [ ] | PARTIAL | [Hook defaults](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L101) accept partial criteria at `/`, but `/disasters` redirect loses them. | AUD-020-012, AUD-020-014 |
| CHK083 | [ ] | PARTIAL | [Client error body](../../apps/web/src/lib/api/incidents-map.ts#L88) is shown generically; no enforced/verified map 401/403 recovery path. | AUD-020-001, AUD-020-013 |
| CHK084 | [ ] | PARTIAL | API error banner exists, but [map-only rendering](../../apps/web/src/app/page.tsx#L242) lacks mixed-failure fallback and production empty-versus-unavailable distinction. | AUD-020-005, AUD-020-007 |
| CHK085 | [ ] | CONFLICT | [Unknown severity becomes advice](../../apps/api/app/api/routes/incidents_map.py#L101); not an approved unknown-value requirement. | AUD-020-009 |
| CHK086 | [ ] | PARTIAL | [Response strings](../../apps/api/app/models/geojson.py#L42) permit unknown status/phase; formatting/fallback policy and tests absent. | AUD-020-009, AUD-020-026 |
| CHK087 | [ ] | PARTIAL | [Abort controller](../../apps/web/src/app/page.tsx#L93) exists but is not passed through fetch; debounce also captures older filters. | AUD-020-006, AUD-020-014 |
| CHK088 | [ ] | PARTIAL | [router.push and URL sync](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L133) exist; pending timers are not invalidated by external history. | AUD-020-012, AUD-020-014 |
| CHK089 | [ ] | IMPLEMENTED | [Incident error view](../../apps/web/src/app/incidents/[incidentId]/page.tsx#L53) handles load failure with Back to map; no successful workspace test proves all returned IDs resolve. | AUD-020-017, AUD-020-023 |
| CHK090 | [ ] | MISSING | [Point model](../../apps/api/app/models/geojson.py#L22) lacks bounds; outside-AU/offshore policy is not defined by storage sovereignty. | AUD-020-008, AUD-020-026 |
| CHK091 | [ ] | PARTIAL | [Clustering then collision suppression](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L148) supplies no terminal same-coordinate selection policy. | AUD-020-011 |
| CHK092 | [ ] | CONFLICT | Earliest/current-year assumption, [2000 UI floor](../../packages/ui/src/components/disaster-map/filter-panel.tsx#L125), and API 1900-2100 bounds disagree. | AUD-020-015, AUD-020-026 |
| CHK093 | [ ] | PARTIAL | [API max_length 200](../../apps/api/app/api/routes/incidents_map.py#L117) exists; [live input](../../apps/web/src/app/page.tsx#L160) has no corresponding length handling. | AUD-020-013, AUD-020-014 |
| CHK094 | [ ] | PARTIAL | [Parameterized keyword](../../apps/api/app/repositories/incident_map_repository.py#L110) and React text rendering reduce injection risk; special-character/PII/error-copy assertions absent. | AUD-020-001, AUD-020-022 |
| CHK095 | [ ] | UNVERIFIED | [Unbounded progressive loading](../../apps/web/src/lib/api/incidents-map.ts#L121) and clustering do not establish 10000-record behavior. | AUD-020-019, AUD-020-021, AUD-020-024 |
| CHK096 | [ ] | PARTIAL | [Selection setter](../../apps/web/src/app/page.tsx#L132) replaces data, but no rapid-marker/focus/state assertion establishes the full behavior. | AUD-020-017, AUD-020-023 |
| CHK097 | [ ] | MISSING | No accepted AU tile-host/locality verification method in inputs; [global resource binding](../../infra/main.bicep#L442) cannot supply it. | AUD-020-002 |
| CHK098 | [ ] | UNVERIFIED | [SDK configuration](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L88) selects road/Azure Maps but not an evidenced Australian-only serving boundary. | AUD-020-002, AUD-020-024 |
| CHK099 | [ ] | MISSING | [NFR-001](spec.md#L180) does not define browser tile-cache residency/offline implications; do not invent a global allowance. | AUD-020-002, AUD-020-026 |
| CHK100 | [ ] | PARTIAL | [SC timing targets](spec.md#L237) exist; metric-specific operational alert/window/dimension policy is not complete. | AUD-020-020, AUD-020-026 |
| CHK101 | [ ] | CONFLICT | R-008 specifies OpenTelemetry instruments; [live console logging](../../apps/web/src/app/page.tsx#L139) is not that mechanism and Node setup does not instrument this browser component. | AUD-020-020 |
| CHK102 | [ ] | MISSING | [Process-global counters](../../apps/api/app/api/routes/incidents_map.py#L31) have no specified rate window or multi-worker aggregation contract. | AUD-020-020, AUD-020-026 |
| CHK103 | [ ] | PARTIAL | [Log extras](../../apps/api/app/api/routes/incidents_map.py#L160) include counters, but required metric dimensions/privacy policy are not defined or asserted. | AUD-020-020, AUD-020-026 |
| CHK104 | [ ] | CONFLICT | [SDK-ready timeout](../../packages/ui/src/components/disaster-map/disaster-map.tsx#L133) is 15s and not post-ready tile-failure detection. | AUD-020-005 |
| CHK105 | [ ] | PARTIAL | [Manual API retry](../../apps/web/src/app/page.tsx#L200) exists; request timeout, partial-state and initialization-failure policy remain open. | AUD-020-007, AUD-020-019 |
| CHK106 | [ ] | MISSING | No automatic/user-selected table transition is connected at [root](../../apps/web/src/app/page.tsx#L242). | AUD-020-005 |
| CHK107 | [ ] | PARTIAL | GeoJSON and [FastAPI OpenAPI](../../apps/api/app/main.py#L27) support the read endpoint; CAP/EDXL are not explicit mapper outputs and must not be added without scope approval. | AUD-020-026 |
| CHK108 | [ ] | UNVERIFIED | Plan's operational-metadata assumption is not a privacy assessment for free-text titles; [unscoped query](../../apps/api/app/repositories/incident_map_repository.py#L79) and URL keywords need review. | AUD-020-001, AUD-020-025, AUD-020-026 |
| CHK109 | [ ] | IMPLEMENTED | [FR-033](spec.md#L166) and the scoped GET-only mapper satisfy no-irreversible-action intent; separate public-output human approval still applies. | AUD-020-025, AUD-020-029 |
| CHK110 | [ ] | PARTIAL | [Metric/log placeholders](../../apps/web/src/app/page.tsx#L139) do not establish an interaction audit/provenance policy; avoid inventing logging of sensitive search text. | AUD-020-020, AUD-020-026 |
| CHK111 | [ ] | PARTIAL | [Tier names](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L42) agree with constitution; actual marker encoding does not. | AUD-020-004 |
| CHK112 | [ ] | MISSING | [Single-region incident location](../../infra/main.bicep#L580) plus missing fallback does not define this view's region-outage reduced-capability policy. Do not infer deployed DR. | AUD-020-002, AUD-020-005, AUD-020-026 |
| CHK113 | [ ] | MISSING | [Location-majority assumption](spec.md#L202) is not quantified or measured in the accepted record set. | AUD-020-008, AUD-020-026 |
| CHK114 | [ ] | PARTIAL | [Auth assumption](spec.md#L207) has no sufficient connected enforcement/validation for the map endpoint. | AUD-020-001 |
| CHK115 | [ ] | PARTIAL | T006/T007 and [quickstart](quickstart.md#L11) identify the Maps dependency; provisioned state/working prod configuration unverified. | AUD-020-002, AUD-020-003, AUD-020-028 |
| CHK116 | [ ] | IMPLEMENTED | [FR-029](spec.md#L162), T008/T010 and [router](../../apps/api/app/api/router.py#L58) identify the backend dependency. Compatibility issues remain explicit. | AUD-020-013 |
| CHK117 | [ ] | PARTIAL | [SDK lock 3.7.4](../../pnpm-lock.yaml#L1596) and [Maps API version](../../infra/modules/azure-maps.bicep#L26) exist; the research/quickstart runtime versions and install outcome are not current proof. | AUD-020-028 |
| CHK118 | [ ] | PARTIAL | R-006 defines optional/no-migration approach and [domain field](../../packages/domain/src/domain/models/incident.py#L44) exists; no measured backfill/location-coverage outcome established. | AUD-020-008, AUD-020-028 |
| CHK119 | [ ] | CONFLICT | [Original nine-type statement](spec.md#L129) and current [19-type catalogue](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L20) need documented compatibility/exhaustiveness interpretation, not deletion of supported types. | AUD-020-015, AUD-020-026 |
| CHK120 | [ ] | IMPLEMENTED | [Fetch-on-filter](../../apps/web/src/app/page.tsx#L127) plus [server predicates](../../apps/api/app/repositories/incident_map_repository.py#L93) implement server filtering without a document reload. | AUD-020-006, AUD-020-014 |
| CHK121 | [ ] | PARTIAL | T026 explicitly requires all six sortable columns; [switch](../../packages/ui/src/components/disaster-map/list-view-fallback.tsx#L74) covers them, but keyboard/semantic sorting and mounting incomplete. | AUD-020-005, AUD-020-018 |
| CHK122 | [ ] | PARTIAL | [Filters are applied before ordering/paging](../../apps/api/app/repositories/incident_map_repository.py#L119); initial-500/partial-fetch acceptance scope still conflicts. | AUD-020-019, AUD-020-026 |
| CHK123 | [ ] | PARTIAL | Original [story scenarios](spec.md#L18) have local ordinals only; this report supplies USn-ASn for traceability without rewriting originals. Approved long-term scheme unverified. | AUD-020-026 |
| CHK124 | [ ] | MISSING | No explicit bundle budget in the mapper inputs; [dynamic import](../../apps/web/src/app/page.tsx#L25) is an implementation choice, not a measured load budget. | AUD-020-024, AUD-020-026 |
| CHK125 | [ ] | PARTIAL | [no-store fetch](../../apps/web/src/lib/api/incidents-map.ts#L86) is explicit; approved API/tile cache/freshness policy and measured trade-offs not supplied. | AUD-020-019, AUD-020-021, AUD-020-026 |
| CHK126 | [ ] | MISSING | Mapper-specific localisation/Indigenous-language requirements not defined; [SCP-058](spec.md#L266) retains country gates. This question does not authorize new language scope. | AUD-020-026, AUD-020-027 |
| CHK127 | [ ] | MISSING | No print/export requirement in the [feature scope](spec.md#L114); record scope disposition rather than inventing a new mandatory feature. | AUD-020-026 |
| CHK128 | [ ] | MISSING | [Testing configs](../../apps/web/playwright.config.cts#L1) select Chromium/mobile emulation but do not define an approved browser/version support matrix. | AUD-020-025, AUD-020-026 |
| CHK129 | [ ] | MISSING | No mapper session-expiry/idle behavior defined; [auth prefixes](../../apps/api/app/middleware/entra_auth.py#L37) omit it. | AUD-020-001, AUD-020-026 |
| CHK130 | [ ] | MISSING | No mapper-specific approved CSP/script/tile/auth-origin policy in reviewed inputs or [Next config](../../apps/web/next.config.ts#L12). Policy/deployed headers remain unverified. | AUD-020-002, AUD-020-003, AUD-020-026 |

## Plan Gates and Review Records

The plan's ten PASS entries are authored design claims, not proof of a successful review/run.
No sign-off is upgraded by this table. Task phase checkpoints and the MVP/deploy/demo narrative are
also claims of intended readiness; the original task matrix and open findings qualify every checkpoint.

| Gate | Status | Assessment of the original plan gate | Follow-ups |
| --- | --- | --- | --- |
| PG-01 | IMPLEMENTED | Read-only human-in-the-loop design supported by [GET client](../../apps/web/src/lib/api/incidents-map.ts#L86). Separate operator dissemination approval remains UNVERIFIED. | AUD-020-025 |
| PG-02 | CONFLICT | Data sovereignty PASS contradicted by [global Maps binding](../../infra/main.bicep#L442); platform locality unverified. | AUD-020-002 |
| PG-03 | UNVERIFIED | Privacy PASS is based on metadata assumptions, not a named assessment or enforced scoped mapper read boundary. [Map handler](../../apps/api/app/api/routes/incidents_map.py#L111). | AUD-020-001, AUD-020-025 |
| PG-04 | PARTIAL | [GeoJSON/OpenAPI](../../apps/api/app/models/geojson.py#L85) authored; geometry/domain/version fidelity incomplete. | AUD-020-008, AUD-020-009, AUD-020-013 |
| PG-05 | MISSING | Five-second graceful table degradation not connected. [Root](../../apps/web/src/app/page.tsx#L242). | AUD-020-005, AUD-020-007 |
| PG-06 | IMPLEMENTED | Azure Maps/Cosmos/Monitor are the selected services in [plan](plan.md#L11) and inspected source; deployment and locality are not thereby proven. | AUD-020-002, AUD-020-003 |
| PG-07 | PARTIAL | [Log placeholders](../../apps/web/src/app/page.tsx#L139) do not close transparency/metric export/provenance requirements. | AUD-020-020 |
| PG-08 | CONFLICT | [Type-based map pins](../../packages/ui/src/components/disaster-map/marker-cluster.tsx#L193) fail the stated AWS visual encoding. | AUD-020-004 |
| PG-09 | IMPLEMENTED | [All four phase filters](../../packages/ui/src/components/disaster-map/use-disaster-map-filters.ts#L56) exist; recovery policy/authoring stays with its designated owner. | AUD-020-017, AUD-020-027 |
| PG-10 | UNVERIFIED | Test/config/CI source exists but no accepted mapper passing run or review. [CI lane](../../.github/workflows/ci.yml#L312) does not select the general mapper E2E project. | AUD-020-022, AUD-020-023, AUD-020-024, AUD-020-028 |

Additional evidence obligations are **UNVERIFIED**: successful installation, infrastructure
what-if/plan review, AVM/raw-resource approval and applicable policy verification for the Maps module,
deployed authentication/locality, operator approval of a public-facing map, WCAG/assistive-technology
results, latency/FPS/telemetry ingestion runs, usability study, named persona SME validation, and
HYP-018 outcome. Existing IaC and tests are not retrospective records of those activities.

## Future Validation Procedures

**Nothing in this section was executed.** These commands are for a later authorized implementation
and testing session. Do not run the original broad quickstart, shared audit-index helpers, or cloud
operations as part of this report's text-only validation. Product tests may import applications,
start servers, or contact configured services; that is outside this audit's authorization.

### Fixtures and Existing Test Homes

| Fixture set | Contents and intended assertions | Existing home / proposed addition |
| --- | --- | --- |
| MAP-BASE | Extend current Sydney/Brisbane fixtures with all four severities, all five operational statuses, all four phases plus null, original nine and current nineteen hazard types, levels 1/2/3, multiple jurisdictions/organizations. Assert exact IDs and every required property. | [unit helper](../../tests/unit/test_incident_map_repository.py#L16), [contract helper](../../tests/contract/test_incidents_map_contract.py#L19), [E2E data](../../tests/e2e/test_disaster_mapper.spec.ts#L12) |
| MAP-DENY | Allowed/forbidden/anonymous principals; two agencies and disjoint jurisdictions; rehearsal and wrong-kind records; fabricated scope claims. Exact 401/403 and non-leaking counts. | Existing mapper contract file; extend middleware fixtures there without live identity or credentials. |
| MAP-GEO | Missing/null/empty/invalid location, wrong geometry, malformed/nonfinite/range coordinates, all hemispheres/offshore points, invalid domain/date/level values. Exact mapping/exclusion/error policy. | Existing mapper unit/contract helpers; proposed web tests in configured unit/a11y homes. |
| MAP-HISTORY | 1890, 1999, current/future-year and offset-date records, equal timestamps, unknown phase, zero/one-year extents. Exact year options, sorting, labels, and timestamp semantics. | Existing mapper helpers and E2E; proposed mapper table/hook unit tests. |
| MAP-PAGES | 0, 199, 200, 500, 501, 1000, 10000 deterministic unique IDs, all-equal locations versus dispersed points, tied dates and mid-stream mutation. Exact page sequence and complete IDs without duplication. | Existing helpers extended programmatically for future tests, not new production seed data. |
| MAP-RACES | Deferred request A/B, aborted page two, reset before 300ms, navigation before delayed commit, partial-page errors, late failures after unmount. Latest query alone owns all displayed state. | Proposed web unit file(s) under [configured Vitest homes](../../apps/web/vitest.config.ts#L21); extend existing mapper E2E. |
| MAP-FAIL | SDK unavailable, ready-with-failed-tiles, sprite rejection, post-ready tile errors, API 401/403/500/503, missing production storage, retry/recovery. Distinguish failure from real zero results. | Existing mapper E2E and Python tests; proposed renderer/loader tests with injected SDK/client/clocks. |
| MAP-A11Y | Every key/shape/state at 360/375/767/768/769px and desktop, landscape, long labels, text zoom, reduced motion, external keyboard, screen reader, and sortable fallback. | Existing mapper E2E plus proposed web a11y test(s); reuse [Vitest setup configuration](../../apps/web/vitest.config.ts#L29). |

Proposed test files are not existing evidence and were not created here. Prefer the configured
web unit/a11y directories and the three existing mapper test files over introducing a new framework.

### V-PY: Focused Backend Tests

Prerequisites: separately authorized test execution; a configured Python >=3.12 environment with
the API and transitive test dependencies installed, matching [API metadata](../../apps/api/pyproject.toml#L10)
and [CI setup](../../.github/workflows/ci.yml#L36). Isolate/clear Cosmos and telemetry/cloud variables
**before test-module import**, inject fakes, and explicitly control production-auth/test flags.
The current test fixtures alone do not guarantee that isolation. Never place secrets in commands.

From repository root, using that environment's interpreter:

```powershell
python -m pytest tests/unit/test_incident_map_repository.py tests/contract/test_incidents_map_contract.py -q
```

Expected: intended mapper tests are discovered; all exact schema/filter/identity/count/error/race
assertions above pass without external service access. Record actual counts, failures, environment,
revision, and run timestamp. A module imported successfully is not evidence of correct behavior.

### V-UI: Hook, Loader, Renderer, and Table Tests

Prerequisites: separately authorized execution; Node/pnpm aligned with current package/CI versions,
frozen dependencies, the [Vitest config](../../apps/web/vitest.config.ts#L1), and the proposed mapper
tests written first. Inject navigation, fetch, SDK, clock, and metric adapters; do not replace the
behavior under test with a successful stub. Use a mapper-specific filename/tag that this command selects.

```powershell
pnpm --filter @ama/web exec vitest run --config vitest.config.ts disaster-map
```

Expected: no zero-test pass; callback identity, request count/cancellation, query merge/reset/history,
marker tier expressions, keyboard controls, table sorting/location labels, and failure state are
asserted. These tests are not proof of WebGL rendering, real touch behavior, contrast, FPS, or cloud ingestion.

### V-E2E: Connected Mapper Experience

Prerequisites: explicit permission to start local servers/browser; installed compatible dependencies
and Chromium; deterministic MAP fixtures; no ambient production Cosmos/cloud calls. The existing
[Playwright configuration](../../apps/web/playwright.config.cts#L18) starts FastAPI and Next.js and
can reuse servers at ports 8000/3000. Verify their identity/configuration first; isolate or reconfigure
ports in a later approved session rather than stopping unknown user processes. A real Maps run additionally
requires the residency/auth decisions and an approved service environment; mock-based runs must be labeled as such.

```powershell
pnpm --filter @ama/web exec playwright test --config playwright.config.cts test_disaster_mapper.spec.ts --project=chromium --project=mobile
```

Expected: unconditional assertions for all 27 scenarios and seven edges, including actual rendered
marker/cluster selection, all criteria AND/OR behavior, workspace navigation, preserved legacy URLs,
360px/breakpoint/rotation states, keyboard traversal, and <=5s automatic sortable fallback. Remove the
old 375px-only limitation. Record failures rather than bypassing absent UI with `if (isVisible())`.
General mapper tests must be explicitly selected by CI, not confused with the web-coverage projects.

### V-INFRA: Prospective Configuration and Platform Review

Prerequisites: separately authorized infrastructure work; approved residency/identity decisions;
applicable policy-discovery artifacts and resource/module approval; appropriate Bicep tooling and
an output directory outside tracked source. External restore/schema checks, what-if, cloud resource
inspection, and deployment each require authorization outside this audit. No cloud CLI command is
provided as a shortcut around those gates.

Future local syntax/configuration check, writing only to the testing session's temporary directory:

```powershell
bicep build infra/main.bicep --outfile "$env:TEMP/ama-020-main.json"
```

Expected: compatible schema/compiler output, explicit approved location/auth/origin/output bindings,
no developer-local dependency, and a separate recorded infrastructure plan/policy review. Compilation
does not prove deployability, policy compliance, role assignments, endpoint locality, or tile residency.

### V-MEASURE: Performance, Failure Timing, and Telemetry Delivery

Prerequisites: AUD-020-002/AUD-020-003 platform approval, repaired telemetry, production-like approved
build/configuration, bounded dataset/profile agreed under AUD-020-026, and permission for browser/
service measurements. Add explicit `@mapper-measure` cases to the existing E2E file before this command:

```powershell
pnpm --filter @ama/web exec playwright test --config playwright.config.cts test_disaster_mapper.spec.ts --project=chromium --grep @mapper-measure
```

Expected: source/run IDs, device/browser/network/cache/data size, raw timing/frame captures, and
unambiguous measurement boundaries. Require <=3s agreed initial load, <=1s filter-to-visible-update,
500+ markers at the plan's >=30 FPS with usable interactions, <=5s failure-to-list access, and all five
metric events visible to an authorized Log Analytics reader within 60s. Verification of that final
ingestion/locality step is a separately approved observability operation, not a source assertion.
Specify sample counts/tail behavior and include deliberately failing controls. Do not reuse the
current development-server config as proof of production performance without recording the difference.

### V-HUMAN: Accessibility, Usability, and Dissemination Review

Prerequisites: implemented fixes, an agreed protocol/sample size, appropriate operator/SME and
accessibility reviewers, and separate permission for actual user/device tests. Record named reviewer
roles/dates, target revision, dataset, browsers/assistive technologies, decisions, and unresolved issues.
Measure 90% first-time-user completion within 30 seconds, actual marker/background contrast >=3:1,
three silhouette distinctions, keyboard/screen-reader parity, <=2-action detail access as defined,
and 360px+ no-overflow/no-truncation across required states. Obtain explicit human approval of the
public-facing map; do not infer it from source, a green CI job, agent participation, or a self-authored checklist.

### V-DOC: Prospective Contract, Help, and Evidence Review

Use static text/schema/link checks and named owner review against the matrices in this report.
Confirm every CHK has a bounded decision/evidence or explicit scope disposition, every amended ID
has conforming evidence or an honest unverified/deferred state, and the help/quickstart describe the
actual read-only route/configuration. The frozen baseline and all original checkbox states must remain
historical records; approval of future changes must not be backdated.

## Completion Boundary

Completing this audit means coverage and remediation are documented, not that the product meets the
specification. Security/residency decisions precede production verification; race/data/failure and
interaction fixes precede performance/usability sign-off. Source-supported positives include the
moved connected map, application shell, ordinary server filtering, GeoJSON envelope, rehearsal
exclusion, detail routing/close/switch, inline search, notices, and basic responsive styles.

All 29 remediation tasks remain unchecked. Product behavior, tests/builds, current browser render,
accessibility/performance outcomes, deployment, cloud locality, metric ingestion, and human approvals
were not executed or certified by this review. Only this report's text coverage, original states,
follow-up references, existing links/line bounds, and editor diagnostics are eligible for validation here.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 020 only. Three parallel technical reviews examined map API
safety, UI request/render behavior, and route/contract/infrastructure drift. The source-completable stale-request
defect was narrowed to the API client boundary: the progressive loader already accepted an AbortSignal but discarded it
before `fetch`. Page fetches now receive and propagate that signal, allowing the owning controller to cancel obsolete
requests without changing the API contract.

Validation: the touched TypeScript file has no editor diagnostics. The local web TypeScript check reached the changed
file but remains blocked by four pre-existing Playwright return-type errors in
`tests/e2e/web-coverage/cross-cutting/accessibility-and-multilingual.spec.ts`.

Remaining open work includes authenticated/jurisdiction-scoped reads, coordinate/severity validation, repository
availability errors, severity marker semantics, fallback rendering, UI race/state tests, route compatibility,
pagination, telemetry, Azure Maps residency/authentication, browser accessibility/performance, and human evidence.
