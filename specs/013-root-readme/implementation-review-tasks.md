# Implementation Review Tasks: 013 Root README

## Scope and Method

- Review date: **2026-09-11**.
- Reviewed revision: **5b44c249f00e0e4a13ea2579c8c33d06e2471d7a**, confirmed against HEAD.
- This is the primary specification-home report. It covers the complete [specification](spec.md#L1) and the original [historical task list](../feature/013-root-readme/tasks.md#L1), including later clarification and hardening additions. It is independently usable without another audit report.
- This continues the existing audit under the [Review Contract](../001-spec-implementation-audit/README.md#L13). It is not a new feature, implementation plan, approval, or retrospective completion record.
- Only this report and the historical task home's implementation-review-tasks.md are authorized writes. Original specifications, task checkboxes, checklists, evidence, source, root documentation, and the audit index remain unchanged. No branch or commit was created.
- Static documentation, configuration, code, and test-assertion inspection only. No application, import probe, dependency installation, product test, build, browser session, advertised script, cloud operation, deployment, external lookup, actor invocation, or delegation was performed. Existing audit reports were not inputs.
- Source presence establishes authored behavior, not successful execution or deployed enforcement. In particular, a health response, synthetic fixture, checked task, rubric summary, or agent-authored statement does not establish operational readiness or human approval.

### Complete Feature Inputs

The following eight feature-local documents were read in full; the tracked-file inventory contains no additional local amendment, contract, or review file in either feature folder.

| Input | Scope |
| --- | --- |
| [spec.md](spec.md#L1) | Six stories; 18 acceptance scenarios; six independent story tests; six edge cases; 17 FRs; four NFRs; ten SCs; eight clarification decisions; assumptions, dependencies, scope, personas, hypothesis. |
| [requirements.md](checklists/requirements.md#L1) | 16 checked specification-quality items and authoring-feedback claims. |
| [comprehensive.md](checklists/comprehensive.md#L1) | 47 unchecked requirements-quality questions, including three explicitly resolved conflicts. |
| [tasks.md](../feature/013-root-readme/tasks.md#L1) | Exactly 31 original tasks, T001 through T031, all originally checked `[X]`. |
| [plan.md](../feature/013-root-readme/plan.md#L1) | Single-document delivery boundary, constitution gate claims, CHK016/CHK017/CHK018 resolutions. |
| [research.md](../feature/013-root-readme/research.md#L1) | RT-001 through RT-008: diagram, collapsibility, strict readability threshold, prerequisites, authority, links, terminology, line budget. |
| [data-model.md](../feature/013-root-readme/data-model.md#L1) | Ordered section entities, visibility rules, V-001 through V-008 validation rules. |
| [quickstart.md](../feature/013-root-readme/quickstart.md#L1) | Historical authoring instructions, validation snippets, and 11 unchecked definition-of-done items. |

Associated amendment evidence was also inspected: the [persona contract](../027-spec-hardening/contracts/persona-profile.md#L1), [hypothesis-evidence contract](../028-capstone-alignment/contracts/evidence-stub.contract.md#L1), [meta-spec contract](../028-capstone-alignment/contracts/meta-spec-flag.contract.md#L1), [baseline](../028-capstone-alignment/evidence/rubric-baseline.md#L1), [postfeature snapshot](../028-capstone-alignment/evidence/rubric-postfeature.md#L1), and [decision record](../028-capstone-alignment/evidence/decision-record.md#L1). The referenced original [operational personas](../001-disaster-response-hub/spec.md#L167) and [technical actor specification](../004-actor-github-agents/spec.md#L98) were consulted as source material, not as audits.

### Evidence Statuses

| Status | Meaning in this review |
| --- | --- |
| IMPLEMENTED | Inspected source supports the scoped content or behavior; runtime success is not implied. |
| PARTIAL | Some obligations are present, but a named obligation is absent, incomplete, or unsupported. |
| MISSING | A required artifact or behavior was not found after the stated scoped relocation search. |
| CONFLICT | Current documentation, source, or requirements disagree. |
| UNVERIFIED | Available evidence cannot establish execution, measurement, rendering, approval, or deployed state. |
| SUPERSEDED | An explicit later source replaces a specific earlier instruction; not inferred from age alone. |

### Static Baseline and Search Boundaries

- Root [README.md](../../README.md#L1): **382 source lines**, below both 500-line limits even before the NFR-001 blank-line exclusion; ten content sections plus the ToC; four balanced, labelled details blocks; **34 Mermaid body lines**, exceeding T010's 30-line limit.
- Text-only link inspection found **21 relative file/directory-link occurrences, 16 distinct targets, and one broken target** at [README.md](../../README.md#L368). The ten ToC anchors correspond to existing headings, but their order is not the mandated order. External links, badges, hosted rendering, and remote permissions were not verified.
- The broken ADR-031 target has moved to [the corpus ADR](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L1). This is a stale link, not an absent decision. [ADR-032](../../docs/corpus/aidr/decisions/adr-032-oidc-supersession.md#L3) is explicitly Proposed; it is not evidence that credential-based deployment was retired. [cd.yml](../../.github/workflows/cd.yml#L84) still consumes `AZURE_CREDENTIALS`.
- API and agent launcher searches covered their tracked project files and entry points. The actual API module is [app/main.py](../../apps/api/app/main.py#L25); the packaged image starts [dispatcher](../../apps/agents/Dockerfile#L48). Existing per-agent entry points were found. The finding is incorrect documented invocation, not absence of agents.
- The expected RAG `/healthz` contract was searched in API routes, their registration, and the application factory. Existing [API health](../../apps/api/app/api/health.py#L19) and [evidence-health registration](../../apps/api/app/api/router.py#L120) are different contracts, not replacements for the smoke script's four RAG fields.
- Searches for the HYP-011 filename variants covered tracked feature/evidence paths, with a repository filename search and a targeted HYP-011 text search in feature 028. Neither the named doubled-prefix stub nor a relocated HYP-011 file was found. The evidence directory contains the decision record and two rubric snapshots.
- A tracked text search of tests, tools, scripts, and workflow sources found no dedicated root-README/readability validator using `013-root-readme`, `flesch_kincaid`, or `textstat`. This does not prove no historical manual review happened. Generated build trees and installed third-party packages are not implementation evidence for this revision.

## Prioritized Findings

| Priority | Finding and evidence | Follow-up |
| --- | --- | --- |
| P1 | **The visible safety guarantee is stronger than the registered alert path.** [README authority](../../README.md#L157) says recommendations require human approval. [Publish validation](../../apps/api/app/services/public_alert_service.py#L48) accepts `pending_approval`; [publish](../../apps/api/app/services/public_alert_service.py#L66) merely records the supplied persona string. The [registered route](../../apps/api/app/api/routes/alerts.py#L37) adds no approval lookup. The [RBAC protected prefixes](../../apps/api/app/middleware/rbac_check.py#L32) do not include alerts. This is a shared-code safeguard risk, not proof of a deployed exploit or real notification delivery. | AUD-013-001 |
| P1 | **The local quickstart cannot establish its advertised three-runtime setup from the documented commands.** [Root install](../../README.md#L113) is not a Python workspace install; [root dependencies](../../pyproject.toml#L9) do not install the application distributions or the optional dev tools. [API startup](../../README.md#L126) names `main:app`, and [agent startup](../../README.md#L130) names an unprovided top-level launcher. Compare [API packaging](../../apps/api/pyproject.toml#L1), [agent packaging](../../apps/agents/pyproject.toml#L1), and [CI installs](../../.github/workflows/ci.yml#L36). No URLs, expected responses, or degraded-mode acceptance checks are supplied. | AUD-013-002 |
| P1 | **A snippet labelled local can seed the user's active cloud environment.** [README local smoke](../../README.md#L306) calls the postprovision seeder. [Environment loading](../../scripts/seed-database.ps1#L17) imports active `azd` values, then calls a loader whose [Cosmos path](../../scripts/seed_loader.py#L210) upserts and whose [Blob path](../../scripts/seed_loader.py#L240) creates containers. The local snippet contains no explicit dry-run or target approval. | AUD-013-003 |
| P1 | **The RAG smoke command is not a reliable cutover gate.** [README command](../../README.md#L299) supplies only a placeholder base URL. The [script](../../infra/scripts/azd-up-smoke-test.ps1#L83) expects an unregistered RAG `/healthz`; optional telemetry errors warn, and [missing SSE citations still exit zero](../../infra/scripts/azd-up-smoke-test.ps1#L190). The separate [dry run](../../infra/scripts/simulation-final-canary-dry-run.ps1#L92) compares synthetic identical samples and checks an empty-citation event, not live grounded inference. | AUD-013-004 |
| P2 | **The web-coverage proof claim exceeds the assertions.** [README](../../README.md#L308) claims every outcome/persona combination end-to-end. The [gate](../../scripts/web-coverage/_lib/schema_validators.py#L107) counts distinct personas and outcomes separately; the [representative outcome test](../../tests/e2e/web-coverage/capstone/outcome-1-bushfire-extreme-heat.spec.ts#L21) submits canned metric inputs through API requests. Its existence is not a measured lives-saved outcome or proof of all 340 persona/outcome pairs. The snippet also omits Python application installs and Playwright browser installation visible in [CI](../../.github/workflows/ci.yml#L300). | AUD-013-005 |
| P2 | **Quality-check and contribution guidance is incomplete and inconsistent.** [Local checks](../../README.md#L335) omit web tests and explicit type checking; root dev extras are not installed. [Web test scripts](../../apps/web/package.json#L12) do exist. [README branching](../../README.md#L328) conflicts with [CONTRIBUTING](../../CONTRIBUTING.md#L8), and the README neither states commit expectations nor links to their [existing home](../../CONTRIBUTING.md#L63). | AUD-013-006, AUD-013-007 |
| P2 | **Universal-first ordering and visible agent summaries were not delivered.** [README headings](../../README.md#L11) place Architecture and Quickstart before Personas and Agents, and Documentation before Contributing. [All agent descriptions](../../README.md#L159) are hidden together. T009/data-model require a visible summary for each agent. The overview does not explicitly orient all four intended audiences as T004 requires. | AUD-013-008 |
| P2 | **Architecture, versions, roster, and governance context have drifted.** [README stack](../../README.md#L241) says Next.js 15 versus [16.2.6](../../apps/web/package.json#L29); the five-agent summary contains a sixth entry; the diagram advertises per-agent ports while the current [image](../../apps/agents/Dockerfile#L45) starts one dispatcher. The [constitution](../../.specify/memory/constitution.md#L249) now contains a bounded model-hosting residency carve-out. Retain AU data-persistence constraints without presenting an unqualified deployment attestation. | AUD-013-009 |
| P2 | **Prerequisite and documentation navigation obligations remain incomplete.** [Prerequisites](../../README.md#L81) omit numeric minima for uv and Docker and the task's Git minimum. Added PowerShell snippets have no local PowerShell prerequisite. The [walkthrough](../../README.md#L286) is under Developers rather than Operators; the clarification's broader documentation inventory has no route to the evaluation and regional-adaptation artifacts. ADR-031 is linked at its old location. | AUD-013-010, AUD-013-011, AUD-013-012 |
| P2 | **Checked validation tasks are not current validation evidence.** There are no inspected section-specific FK scores, timed newcomer observations, or GitHub desktop/mobile captures tied to this revision. The [historical FK snippet](../feature/013-root-readme/quickstart.md#L207) prints a whole-document rounded score, which cannot establish three separate unrounded scores at or below 8.0. | AUD-013-013, AUD-013-014, AUD-013-015 |
| P2 | **Later hardening claims lack their required evidence.** [HYP-011](spec.md#L230) points to a missing, contract-inconsistent stub name; aggregate rubric uplift does not establish per-spec uplift or consultation on every change. [PER-031 and PER-032](spec.md#L222) say validated, but linked role labels and actor definitions are not dated practitioner signatures. PER-033's placeholder is correctly deferred, not implemented country support. | AUD-013-016, AUD-013-017 |
| P3 | **The completion record is stale and internally inconsistent.** All 31 tasks are checked, all 47 comprehensive questions remain unchecked, and [quality notes](checklists/requirements.md#L34) still describe 15 FRs/seven SCs instead of 17/ten. The plan's gate table uses an older constitutional structure. Preserve those historical records and add a revision-specific reconciliation rather than interpreting checkmarks as proof. | AUD-013-018 |

## Open Follow-ups

All items below are **unchecked future work**, not authorization to change their owning surfaces during this audit. Shared-code changes require their normal owning-feature review. Commands are future-only and assume the prerequisites in the validation section. A proposed checker is explicitly labelled proposed and does not exist yet.

### Safety, Setup, and Evidence Claims

- [ ] **AUD-013-001 (P1): Make the human-approval guarantee defensible.**

  **Original obligations:** FR-005, FR-013; US1-AS3, US4-AS1; T005, T013, T019, T020; Constitution human-in-the-loop boundary.

  **Expected / observed / impact:** Safety-critical publication requires authorized human approval. The registered [publish route](../../apps/api/app/api/routes/alerts.py#L37) accepts a supplied persona ID and the [service](../../apps/api/app/services/public_alert_service.py#L48) accepts `pending_approval`. Operators could mistake a textual guarantee for an enforced approval record. Channel adapters here are local payload builders; this review does not claim real messages were sent.

  **Developer instructions:** Have the alert/approval owner reconcile publication with an authenticated, authorized identity and the applicable recorded approval, including tenant and recommendation linkage. Reject pending, rejected, stale, or mismatched approvals before state mutation. Preserve simulation delivery isolation and explicitly identify prototype limitations in the README and [operator runbook](../../docs/disaster-response-hub/operator-runbooks.md#L29) until enforcement is supported. Do not weaken the constitution to match the implementation.

  **Tester instructions:** Extend [the existing contract test](../../tests/contract/test_live_incident_contract.py#L10) with its `Incident`, `Recommendation`, and `PublicAlert` fixtures. Positive: approved, same-tenant authorized publication records the real approver. Negative: pending/rejected/no approval and a spoofed or unauthorized persona cannot publish. Edge: approval revoked between review and publish, retry, cross-tenant IDs, simulation delivery. Assert denial before any status/audit/channel side effect; expected errors are authorization denial or non-publishable-state responses, not success.

  **Future command / completion:** After isolated Python test dependencies are installed, run `python -m pytest tests/contract/test_live_incident_contract.py -q` with the new rejection cases. Completion requires passing positive and negative source-path assertions, owner review, and documentation that accurately states the supported boundary; no deployment claim follows from local tests.

- [ ] **AUD-013-002 (P1): Repair and bound the no-credentials three-runtime quickstart.**

  **Original obligations:** FR-003; SC-002; US2-AS1; T006, T014.

  **Expected / observed / impact:** A fresh contributor should start API, Agents, and Web using only the listed local prerequisites. [README](../../README.md#L102) does not install the Python applications, uses the wrong API import and agent launcher, and supplies no verification response. Root metadata is not a declared uv application workspace. API [health](../../apps/api/app/api/health.py#L10) reports configured dependencies without a connectivity probe; dispatcher [health](../../apps/agents/dispatcher/agent.py#L200) distinguishes degraded LLM mode.

  **Developer instructions:** Use the actual package boundaries in [API packaging](../../apps/api/pyproject.toml#L1), [agent packaging](../../apps/agents/pyproject.toml#L1), and [pnpm workspace](../../pnpm-workspace.yaml#L1). Document one reproducible install/environment path, repository-root working directories for each separate terminal, the current dispatcher invocation, API/Web URLs, and the exact locally supported degraded behavior. Follow [Playwright's root-CWD setup](../../apps/web/playwright.config.cts#L18) and [CI installation](../../.github/workflows/ci.yml#L36) as source evidence, not as already-verified onboarding. Do not require cloud login or globally disable production guards.

  **Tester instructions:** Positive: a disposable fresh clone with prerequisites, no inherited cloud variables, and application dependencies installed starts three runtimes and serves a defined local response from each. Negative: missing package, wrong CWD, unavailable port, absent credentials, and missing browser must give actionable setup guidance. Edge: Windows and POSIX terminals, existing servers, and degraded/no-model responses. Fixture: the existing seed catalogue plus a clearly synthetic local incident; do not treat `healthy` with stub dependencies as live Azure readiness.

  **Future commands / completion:** Candidate commands to validate after the owner fixes the install instructions are `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`, `python -m dispatcher`, and `pnpm --filter @ama/web dev`, each in its documented environment/CWD. Stop all processes after the future rehearsal. Completion requires verbatim fresh-clone success, expected local response assertions, and a recorded SC-002 timing under AUD-013-015.

- [ ] **AUD-013-003 (P1): Separate local fixture preparation from cloud seeding.**

  **Original obligations:** FR-003's local/cloud separation; US2-AS1; T006, T014; current local web-smoke instructions introduced into the README.

  **Expected / observed / impact:** A locally labelled command must not select and mutate an active cloud environment implicitly. [Seeder environment loading](../../scripts/seed-database.ps1#L17) and [loader writes](../../scripts/seed_loader.py#L210) permit exactly that when configuration and permission are present.

  **Developer instructions:** Update the README's local snippet and the seeder owner's contract to make local fixture mode explicit and non-cloud, with no implicit `azd env` import. Keep authorized postprovision behavior under [azure.yaml](../../azure.yaml#L15) compatible and separately documented. A validation-only dry run must not be described as populating the running API's in-memory stores. Cloud seeding must require an explicit reviewed target and separate authorization.

  **Tester instructions:** Positive: local fixture preparation makes zero Azure calls and produces the intended local state. Negative: an inherited live Cosmos endpoint, storage account, available `azd`, or active production environment cannot cause local-mode writes. Edge: no `azd`, partial endpoint configuration, repeated fixture loads, and malformed seed data. Use dependency-injected client/environment fakes in the existing [tests/unit](../../tests/unit/) location; record attempted network calls rather than using a live account.

  **Future command / completion:** After a specifically scoped local-mode test is added, run `python -m pytest tests/unit -k seed -q` in an isolated environment; verify that the selected tests actually include the new environmental-inheritance cases. Completion requires explicit safe local instructions, zero-cloud-call assertions, and a separate postprovision compatibility test using fake clients.

- [ ] **AUD-013-004 (P1): Align RAG smoke instructions with a reachable, fail-closed contract.**

  **Original obligations:** FR-002, FR-003, FR-006, FR-011; T011, T014, T016, T031; current README RAG validation claims.

  **Expected / observed / impact:** A claimed cutover check should query a registered contract and fail when its promised assertions fail. The [script's `/healthz`](../../infra/scripts/azd-up-smoke-test.ps1#L83) has no matching RAG route in the [registration](../../apps/api/app/api/router.py#L74). [SSE failure](../../infra/scripts/azd-up-smoke-test.ps1#L188) returns success; omitted optional parameters skip inference/telemetry checks. [Dry-run samples](../../infra/scripts/simulation-final-canary-dry-run.ps1#L92) are synthetic and identical, not cutover evidence.

  **Developer instructions:** Have the RAG/API owner establish one registered endpoint contract and make the documented URL include the correct prefix. State which checks are required, optional, synthetic, or live. Either enforce required telemetry/citation failures or rename the operation as a limited informational probe. Preserve the explicit human-controlled deployment boundary; do not change live flags or redeploy as part of documentation repair.

  **Tester instructions:** Positive: a mock HTTP server supplies a conforming RAG response and required citation event. Negative: 404, missing fields, invalid SHA, ungrounded response, unavailable telemetry, no citations, and HTTP/stream exceptions fail the relevant required gate. Edge: only optional parameters omitted, latency breach, empty-corpus disclosure, and early stream closure. Use local HTTP/SSE fixtures and existing [tests/contract](../../tests/contract/) and [tests/devops](../../tests/devops/) locations; do not substitute `/api/healthz/evidence` for the distinct RAG contract.

  **Future command / completion:** Run `pwsh ./infra/scripts/azd-up-smoke-test.ps1 -BaseUrl http://127.0.0.1:18080` only against the future mock server; add locally controlled optional-probe fixtures as appropriate. Completion requires nonzero exits for required failures, correct route wiring, and README labels that do not equate dry-run success with live cutover approval. Live checks remain separately authorized future work.

- [ ] **AUD-013-005 (P2): State the web-coverage suite's actual coverage and setup requirements.**

  **Original obligations:** FR-006, FR-010, FR-011; US2-AS2, US5-AS3, US6-AS2; T012, T015, T016, T022, T031.

  **Expected / observed / impact:** Readers need truthful setup and coverage claims. [The gate](../../scripts/web-coverage/_lib/schema_validators.py#L107) independently counts personas and outcomes, not every pair; [the outcome test](../../tests/e2e/web-coverage/capstone/outcome-1-bushfire-extreme-heat.spec.ts#L21) is a synthetic API/evidence exercise. The README snippet omits editable application installs and browser setup required by [CI](../../.github/workflows/ci.yml#L300). Reused servers may lack the [dual-guard environment](../../apps/web/playwright.config.cts#L23).

  **Developer instructions:** Qualify sampled/persona-specific and synthetic proxy coverage versus UI workflow coverage and real-world outcomes. If full cross-product coverage is intended, obtain scope approval and enforce a matrix, not independent set counts. Link a corrected suite onboarding path, install both Python applications and Chromium, and document server reuse and `AMA_ENVIRONMENT`/`AMA_TEST_SUPPORT` boundaries. Never enable test-support in production.

  **Tester instructions:** Positive: the documented local smoke discovers tagged tests and reaches the intended API/Web processes. Negative: a trace containing all 68 personas and all five outcomes but omitting most pairs must not substantiate the full-pair claim; missing browsers and wrong-environment reused servers are diagnosed. Edge: empty trace, skipped/failing rows, one missing pair, and cold browser cache. Reuse [the outcome fixture](../../tests/e2e/web-coverage/_support/fixtures/data/outcome-1-bushfire-extreme-heat.fixture.json#L1) and the existing coverage suite; use a separate synthetic trace for gate counterexamples.

  **Future commands / completion:** After safe setup, run `pnpm --filter @ama/web exec playwright test --project=web-coverage-chromium --grep "@p1"`; the gate's future fixture command is `python scripts/web-coverage/_lib/schema_validators.py gate --trace <synthetic-trace.json> --gap-register <fixture-register.md>`. Completion requires correct selected-test counts and assertions, an accurate description of matrix limits, and no claims that fixture-derived scores demonstrate lives saved.

### Documentation Correctness

- [ ] **AUD-013-006 (P2): Document runnable quality checks for each runtime.**

  **Original obligations:** FR-010, FR-011; US2-AS2, US5-AS3, US6-AS2; T015, T016, T022.

  **Expected / observed / impact:** A contributor should lint and test the relevant runtime. [README checks](../../README.md#L335) give Python commands without dev-extra installation and web lint/build without web tests. [Root scripts](../../package.json#L5), [web scripts](../../apps/web/package.json#L6), and [CI](../../.github/workflows/ci.yml#L131) expose more precise entry points and different Python test selection.

  **Developer instructions:** State the prerequisite test-tool/application installation, CWD, Python lint/format/test scope, web lint/typecheck/unit/e2e distinctions, and which commands need browsers or external fixtures. Reuse existing scripts. Do not promise that an unqualified repository-wide pytest invocation is the same as CI or that a build is a web test. Separate advisory CI gates from blocking ones.

  **Tester instructions:** Positive: documented commands resolve to the installed scripts and select relevant tests. Negative: a failing web test must not be hidden by a successful build; absent dev tools must be caught during setup. Edge: one-runtime changes, browser-free unit checks, and staging-only tests. Reuse existing Python contract/integration tests and the web Vitest/Playwright suites; do not use this audit as their execution evidence.

  **Future commands / completion:** With dependencies installed, validate `python -m pytest tests/contract tests/integration -q`, `pnpm --filter @ama/web test`, `pnpm --filter @ama/web exec tsc --noEmit`, and the existing `pnpm lint:web` entry point. Completion requires documented scope/prerequisites and expected nonzero exits when a relevant fixture test fails.

- [ ] **AUD-013-007 (P2): Reconcile contribution and branch guidance.**

  **Original obligations:** FR-010; US6-AS1; T015, T022.

  **Expected / observed / impact:** One clear branch/base/PR/commit policy should guide a newcomer. [README](../../README.md#L328) says `feature/<spec-id>-<name>` from `main` and describes main as production-ready, while [CONTRIBUTING](../../CONTRIBUTING.md#L8) describes environment branching and [unprefixed feature names](../../CONTRIBUTING.md#L24). Commit rules exist at [CONTRIBUTING](../../CONTRIBUTING.md#L63) but are not linked from the README.

  **Developer instructions:** Ask the contribution owner to resolve the competing branch/base policies, then make the README a concise summary with a direct canonical contribution link and commit expectations. Preserve main's integration-only deployment semantics in the [CD source](../../.github/workflows/cd.yml#L19); do not infer live branch protection from YAML.

  **Tester instructions:** Positive: a newcomer can identify the approved name, base, PR target, review requirement, and commit format without conflicting instructions. Negative: documentation-only and hot-fix cases must not accidentally deploy or choose contradictory bases. Edge: environment-targeted work and non-code contributions. Fixture: paper examples of a docs change, shared feature, and production hot-fix; no branch need be created for the audit.

  **Future command / completion:** Run `Select-String -Path README.md,CONTRIBUTING.md -Pattern 'feature/','NNN-short-name','main','dev','commit'` as a later comparison, followed by owner review of the examples. Completion requires one consistent documented policy and a working contribution link, not a new branch or commit in this review.

- [ ] **AUD-013-008 (P2): Restore universal-first navigation and visible summaries.**

  **Original obligations:** FR-001, FR-014, FR-016, FR-017; NFR-002; T002, T003, T004, T009, T031.

  **Expected / observed / impact:** Overview, Agents, Personas, Architecture, Quickstart, Structure, Stack, Metrics, Contributing, Documentation is the required order. [Current headings](../../README.md#L11) differ, and [Agents](../../README.md#L159) exposes no per-agent summary until expanded. First-time non-developer readers reach setup before the governance/agent context.

  **Developer instructions:** Reorder the ten sections and ToC together; retain the later FR-017 placement of the ToC after title/description. Give every core agent a short visible summary, keeping only detailed descriptions collapsed. Orient developers, operators, government agencies, and evaluators in the overview. Keep authority, architecture, run commands, and documentation links expanded.

  **Tester instructions:** Positive: headings and ToC have the exact ten-section order; core-agent summaries and authority are visible with all details closed. Negative: moving a section, putting authority inside details, or hiding a summary fails the check. Edge: expanded/collapsed states, extra subheadings, duplicate anchors, and raw Markdown. Fixture: current README plus small in-memory mutated copies, not edited production files.

  **Future command / completion:** A proposed documentation checker at `tools/lint/check_root_readme.py` may expose `--structure`; until authored, manually compare `Select-String -Path README.md -Pattern '^## ','<details>','<summary>'` to the required order. Completion requires the exact order, ten resolvable anchors, and visible summaries with the line budget retained.

- [ ] **AUD-013-009 (P2): Refresh architecture, version, roster, and residency descriptions.**

  **Original obligations:** FR-002, FR-008, FR-009, FR-014; US3, US5-AS2; T010, T011, T017, T018, T024.

  **Expected / observed / impact:** The summary should reflect the current documented deployment model without pretending to attest a deployment. [README](../../README.md#L34) has a 34-line diagram and per-agent ports; [the image](../../apps/agents/Dockerfile#L45) uses a dispatcher. [Next.js](../../apps/web/package.json#L29) is 16.2.6, not 15. A sixth agent is inside a five-agent summary, while the authoritative [architecture](../../docs/disaster-response-hub/architecture.md#L57) also lists Dependency Notifier. The constitution's model-hosting exception is omitted from the residency summary.

  **Developer instructions:** Reconcile core-agent roster versus newer dispatcher roles without deleting required core descriptions or conflating technical persona agents with runtime agents. Show three high-level runtimes and their service relationships in at most 30 Mermaid lines; distinguish the ingestion deployment in [azure.yaml](../../azure.yaml#L47) as supporting scope. Update Next.js and deployment context from current manifests and the constitution, retaining AU-only persisted regulated data and explicitly bounding any non-AU inference exception. Coordinate summary/detail updates with the architecture owner.

  **Tester instructions:** Positive: the core five agents, extra roles, runtime topology, versions, and AU primary region agree with source. Negative: an outdated major version, wrong port, out-of-AU data-store implication, or 31-line diagram fails the content check. Edge: added agent versus added runtime, a model-hosting-only exception, and absent/planned folders clearly labelled. Fixtures: current manifests, dispatcher role set, constitution, and README diagram text.

  **Future command / completion:** Later compare `Select-String -Path README.md,apps/web/package.json,apps/agents/Dockerfile,azure.yaml -Pattern 'Next.js','"next"','dispatcher','8080','host:'`; count Mermaid body lines independently of total README lines. Completion requires accurate version/topology labels, no false residency attestation, and at most 30 diagram lines.

- [ ] **AUD-013-010 (P2): Complete the prerequisite version and installation contract.**

  **Original obligations:** FR-004; US2-AS3; EC-04; T007.

  **Expected / observed / impact:** Every required local tool needs a supported numeric minimum and installation guidance. [README prerequisites](../../README.md#L81) give no uv/Docker minimum or the historical task's Git minimum; the added `pwsh` commands have no PowerShell prerequisite. Older source planning also assumes tools such as uv lock/workspace behavior without current supporting configuration.

  **Developer instructions:** Establish supported minima from actual package/CI compatibility, distinguishing Node's supported minimum from CI's Node 24 selection. Either remove unnecessary Docker from the truly local path or document its specific purpose and minimum. Include PowerShell 7 if its snippets remain. Keep Azure CLI/azd/subscription requirements in the deployment-only block. Link installation and environment-activation instructions; do not invent version floors or imply `latest` is a minimum.

  **Tester instructions:** Positive: a machine at each supported minimum can follow the later setup. Negative: below-minimum versions and absent optional deployment tools receive correct guidance without blocking local use. Edge: unsupported OS shell, existing pnpm/Corepack versions, and a machine without Docker when no local service needs it. Fixture: a declared support matrix and tool-version manifests, not this workstation's installed tools.

  **Future command / completion:** After owner approval of the matrix, run `git --version`, `uv --version`, `node --version`, `pnpm --version`, and `$PSVersionTable.PSVersion` only in the future setup verification environment. Completion requires all required tools to have justified numeric minima and working installation references, with a tested local/cloud split.

- [ ] **AUD-013-011 (P2): Repair the relocated ADR link and check all README links.**

  **Original obligations:** FR-006, FR-012; SC-006, SC-007; T025, T030, T031.

  **Expected / observed / impact:** Every internal destination should exist. [README line 368](../../README.md#L368) points at the former ADR directory; [ADR-031](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L1) exists under the corpus. Readers lose the rationale for deployment credentials.

  **Developer instructions:** Rebase the README destination to the existing decision, then validate all file, directory, and fragment links from the root document. Do not recreate the historical file just to satisfy a stale URL or mark [Proposed ADR-032](../../docs/corpus/aidr/decisions/adr-032-oidc-supersession.md#L3) as completed migration. Retain external-link checking as a separately authorized activity.

  **Tester instructions:** Positive: all 21 current relative-link occurrences, including the moved decision, resolve. Negative: deleted target, case mismatch, and nonexistent heading fragment are detected. Edge: directory links, repeated destinations, pure ToC anchors, URL-encoded paths, and badge query strings. Fixture: root README text and repository paths at the candidate revision.

  **Future command / completion:** A proposed `python tools/lint/check_root_readme.py --links` should distinguish files, directories, fragments, and external URLs; a PowerShell text-only equivalent is sufficient. Completion requires zero broken internal targets and all ToC fragments resolving without weakening the checker or modifying original audit evidence.

- [ ] **AUD-013-012 (P2): Restore audience-specific and comprehensive documentation routes.**

  **Original obligations:** FR-006 and clarification CL-05; US1-AS2; T012.

  **Expected / observed / impact:** Operators should find both runbooks and walkthrough, and the expanded clarification requires routes to the existing hub artifacts. [README Developers](../../README.md#L281) owns the walkthrough, while [Operators](../../README.md#L319) does not. The documentation tree includes [evaluation](../../docs/disaster-response-hub/evaluation/) and [regional adaptation](../../docs/disaster-response-hub/regional-adaptation-asia-pacific.md#L1) beyond the selected links.

  **Developer instructions:** Add the walkthrough to Operators, retain the three evaluator artifacts and developer architecture/spec/constitution links, and provide an audience-appropriate index/route to the rest of the existing hub documentation. Government readers can share the evaluator/operator routes but must know where to go. Link concise prerequisites and run guidance without promoting historical setup placeholders as a verified local tutorial.

  **Tester instructions:** Positive: each of the four audiences can navigate to its expected artifacts using only the README. Negative: a required artifact placed only under the wrong audience, an unlinked major artifact, or a broken index fails review. Edge: an artifact useful to multiple audiences and added nested documentation. Fixture: the actual hub documentation inventory, not the older RT-006 list alone.

  **Future command / completion:** Later inventory with `Get-ChildItem docs/disaster-response-hub -Recurse -File` and compare to README/index routes, then conduct AUD-013-015's discovery exercise. Completion requires all FR-006 destinations in the correct audience context and an explicit route to the expanded artifact set.

### Validation and Amendment Evidence

- [ ] **AUD-013-013 (P2): Measure all three readability-constrained sections correctly.**

  **Original obligations:** FR-015; NFR-003; SC-009; EC-01; CHK016; T004, T005, T006, T008, T027.

  **Expected / observed / impact:** Overview, Quickstart, and Personas must each score at or below 8.0 without rounding. [Research RT-003](../feature/013-root-readme/research.md#L67) defines this; the [historical sample](../feature/013-root-readme/quickstart.md#L207) prints a rounded whole-document score, and no inspected execution evidence records section scores. No failing numeric FK score is asserted by this audit.

  **Developer instructions:** Define reproducible section extraction and Markdown normalization, preserving meaningful prose in lists, tables, and expanded prerequisite content while documenting handling of executable code. Pin the measurement-tool version and retain normalized inputs, unrounded per-section scores, candidate revision, and reviewer observations. Revise prose as needed without losing safety, setup, or role meaning.

  **Tester instructions:** Positive: every required section independently meets 8.0. Negative: one section at 8.01 or 8.4 fails even if the whole-document average passes; missing/renamed sections must not yield a false green. Edge: Unicode, abbreviations, technical names, details blocks, tables, empty extraction, and multiline code fences. Fixture: exact normalized section text plus high-grade and missing-section mutations.

  **Future command / completion:** The proposed checker command is `python tools/lint/check_root_readme.py --readability --sections overview,quickstart,personas --max-grade 8.0`, using a future explicitly installed `textstat` dependency. Completion requires three unrounded passing scores, reproducible inputs, and a non-technical readability review; an aggregate rubric snapshot is not a substitute.

- [ ] **AUD-013-014 (P2): Obtain revision-specific desktop and mobile rendering evidence.**

  **Original obligations:** FR-012, FR-017; NFR-004; SC-006; EC-02, EC-05; T023, T028, T029, T030.

  **Expected / observed / impact:** Valid source structure must render correctly in GitHub desktop and mobile. [README](../../README.md#L34) has balanced diagram/details syntax, but no inspected captures or session record proves render, expansion, or table/anchor usability at this revision.

  **Developer instructions:** Keep meaningful summaries and blank-line boundaries, valid fences, architecture outside details, and stable anchors through reordering. Establish a small explicit GitHub viewport/browser matrix; preserve a readable raw-text fallback. The historical plan's GFM claim is design intent, not a rendering result.

  **Tester instructions:** Positive: desktop and mobile render the diagram, ten links navigate, all four details blocks expand/collapse, and tables remain readable. Negative: malformed fence, missing blank-line boundary, duplicate heading, or diagram hidden in details must fail. Edge: narrow viewport, long role names, touch controls, keyboard navigation, and expanded prerequisite lists. Fixtures: the candidate README and captured immutable revision URL.

  **Future command / completion:** With a future approved documentation lint dependency, run `pnpm exec markdownlint-cli2 README.md`, then manually inspect GitHub desktop/mobile at the candidate commit. Completion requires dated captures with browser/viewport/revision and explicit diagram/details/anchor assertions; lint alone cannot close rendering acceptance.

- [ ] **AUD-013-015 (P2): Record the specified newcomer timing and comprehension outcomes.**

  **Original obligations:** NFR-002; SC-001, SC-002, SC-003, SC-004; all six independent story tests; T014, T019, T022, T031.

  **Expected / observed / impact:** Evaluator comprehension in two minutes, developer comprehension in three, setup under 15 minutes after prerequisites, five-link discovery within 30 seconds, and role/authority discovery within 60 seconds require observed trials. Existing content and checked tasks do not establish these outcomes.

  **Developer instructions:** Define a bounded protocol with unfamiliar readers, questions, pass thresholds, prerequisite-ready setup baseline, platform/network assumptions, and no coaching. Record start/stop times, answers, blockages, revision, and actual reviewer consent. Keep cold dependency installation versus prerequisite-ready timing explicit. Complete the setup/navigation fixes before claiming a successful trial.

  **Tester instructions:** Positive: separate developer, evaluator, government, and operator participants perform the specified tasks and correctly explain purpose, audience, structure, authority, and next step. Negative: failed comprehension or needing outside setup instructions is failure regardless of elapsed time. Edge: mobile, non-technical readers, missing prerequisites, slow network, and fresh versus reused environment. Fixtures: scripted questions and a clean, non-cloud local environment.

  **Future command / completion:** A later observer may use `[System.Diagnostics.Stopwatch]::StartNew()` while following the corrected README and the story scripts. Completion requires individual recorded results against every timing target, actual participant/role/date evidence, and explicit residual failures; no timing is inferred from the 382-line length.

- [ ] **AUD-013-016 (P2): Restore HYP-011's contract-bound evidence and assessment scope.**

  **Original obligations:** The appended [HYP-011](spec.md#L230), its evidence contract, and per-spec actor-consultation/uplift claim; T031 is the original final-review hook, not a historical implementation task for this later amendment.

  **Expected / observed / impact:** A conforming evidence stub should exist, link this spec, and retain `Not tested` until supported. The named HYP-HYP-011 file is absent, while the contract requires a co-located `HYP-011.md` format. [Portfolio snapshots](../028-capstone-alignment/evidence/rubric-postfeature.md#L23) cannot establish this spec's mean uplift or consultation on every change.

  **Developer instructions:** Have the spec/evidence owner reconcile the incorrect pointer with the contract. A proposed canonical home is `specs/013-root-readme/evidence/HYP-011.md`; it is not existing evidence. Include the six required headings, at least two preconditions, bounded measurement window, quantified falsification, owning-spec link, and initial `Not tested` status. Preserve the frozen baseline. Require separate authentic consultation records and a comparable per-spec assessment before any outcome transition.

  **Tester instructions:** Positive: canonical ID, filename, owning link, headings, preconditions, and status agree. Negative: doubled prefix, wrong owner, empty preconditions, aggregate-only score, fabricated consultation, or a score regression cannot establish validation. Edge: a renamed stub, an untested hypothesis, and an explicitly retired hypothesis with approved change control. Fixture: the evidence contract, current HYP statement, and authentic future per-spec records.

  **Future command / completion:** After the future evidence artifact exists, inspect it with `Get-Content specs/013-root-readme/evidence/HYP-011.md` and apply the six contract rules. Completion requires a resolving contract-compliant stub and honest evidence status; proving or falsifying the hypothesis is a separate future outcome, not a requirement to manufacture a pass.

- [ ] **AUD-013-017 (P2): Reconcile persona validation claims with actual practitioner evidence.**

  **Original obligations:** Appended PER-031, PER-032, PER-033 and the referenced persona contract; original FR-005/US4 govern the narrower README role table.

  **Expected / observed / impact:** A `validated` persona reference should resolve to contract-conforming, dated practitioner/SME evidence. [Primary amendment](spec.md#L222) asserts validation, while [linked profiles](../001-disaster-response-hub/spec.md#L169) explicitly defer concrete identities and use role labels. Technical actor definitions do not themselves constitute SME validation. Non-AU placeholders must remain deferred under D-009.

  **Developer instructions:** Have the persona/governance owners map each cross-reference to the actual profiles and signed evidence or explicitly mark the validation outcome unverified. Require the contract's identity, role, date, representative scenarios, and unilateral/countersign authority boundaries. Keep development-time persona agents distinct from practitioners and runtime agents. Preserve PER-033's placeholder and named country/precondition boundaries until real approvals exist.

  **Tester instructions:** Positive: each claimed validated reference has a resolvable profile and dated SME/practitioner evidence. Negative: proxy-only/role-only signatures, agent output, missing dates, or one-sided authority statements cannot pass. Edge: a technical persona not naturally an AIIMS operator, multiple profiles behind a group reference, and a correctly deferred PH/JP/BD placeholder. Fixtures: the current persona contract and authentic future profile/evidence records.

  **Future command / completion:** Later compare `Select-String -Path specs/013-root-readme/spec.md,specs/001-disaster-response-hub/spec.md -Pattern 'PER-03','validated_by','authority_scope'`, then inspect the resolved records. Completion requires truthful validation status and preserved deferrals, not invented reviewer names or a widened international scope.

- [ ] **AUD-013-018 (P3): Reconcile historical completion claims without rewriting history.**

  **Original obligations:** T008, T019, T020, T023, T024, T025, T026, T027, T028, T029, T030, T031; both checklists; plan gate claims and the historical definition of done.

  **Expected / observed / impact:** A completion record should distinguish content, static checks, executions, and approvals at a named revision. [Checked quality notes](checklists/requirements.md#L34) use obsolete requirement counts; [comprehensive questions](checklists/comprehensive.md#L1) and the [historical DoD](../feature/013-root-readme/quickstart.md#L230) remain unchecked. No source establishes all currently checked validation tasks as executed.

  **Developer instructions:** Add a future owner-approved reconciliation record, leaving original task states and evidence untouched. Map all 31 tasks, 31 formal requirements/outcomes, scenarios, edge cases, and amendments to current evidence; quote unresolved contradictions. Identify the authority for ToC placement, raw versus adjusted line counts, and current constitution numbering. Separate authored actor feedback from authenticated human approval and check only new follow-ups when their acceptance evidence exists.

  **Tester instructions:** Positive: every original task appears exactly once with its original `[X]` state and specific evidence; all follow-ups remain open until their gates pass. Negative: omitted/duplicated tasks, stale 15-FR/seven-SC counts, unexplained supersession, or treating this report as a product-test pass is rejected. Edge: later amendments without original T IDs, tests not run, and unresolved external sign-offs. Fixture: the unchanged eight feature-local inputs and candidate remediation evidence.

  **Future command / completion:** Use text-only task-ID extraction and local-link validation of the reconciliation artifact, followed by independent owner review. Completion requires a revision-specific evidence ledger with explicit limitations, not retrospective ticking, source edits during this audit, or a claim that all findings were implemented.

## Requirement and Success-Criterion Coverage

All **31** formal obligations have individual rows. Content-only requirements can be IMPLEMENTED while a related shared-code guarantee or measured outcome remains open.

| ID | Status | Inspected evidence and qualification | Follow-up |
| --- | --- | --- | --- |
| FR-001 | IMPLEMENTED | [README overview](../../README.md#L24) identifies the project, agents, Australian emergency context; T004's fuller audience/readability scope remains open. | AUD-013-008, AUD-013-013 |
| FR-002 | PARTIAL | [Inline diagram and architecture link](../../README.md#L34) exist; current topology and historical 30-line budget need correction. | AUD-013-009, AUD-013-014 |
| FR-003 | CONFLICT | [Quickstart](../../README.md#L102) has incorrect Python installation/entry points; later local smoke can seed cloud. Deployment subsection exists separately. | AUD-013-002, AUD-013-003 |
| FR-004 | PARTIAL | [Two prerequisite blocks](../../README.md#L81) exist; numeric uv/Docker minima are absent. | AUD-013-010 |
| FR-005 | IMPLEMENTED | [Five-role table and visible authority](../../README.md#L145) are authored; actual publish safeguard is a separate source risk. | AUD-013-001 |
| FR-006 | PARTIAL | [Audience links](../../README.md#L273) contain the eight named artifacts, but walkthrough is not under Operators, expanded inventory is incomplete, and ADR-031 is stale. | AUD-013-011, AUD-013-012 |
| FR-007 | IMPLEMENTED | [Five target values](../../README.md#L261) match [capstone](../../capstone.md#L31) and are labelled goals, not results. | - |
| FR-008 | PARTIAL | [Stack/region](../../README.md#L235) are present; Next.js version and qualified residency context need synchronization. | AUD-013-009 |
| FR-009 | IMPLEMENTED | [Collapsed tree](../../README.md#L190) includes all required main directories and core-agent homes; newer topology context remains a follow-up. | AUD-013-009 |
| FR-010 | PARTIAL | [Contribution process](../../README.md#L326) exists but conflicts with canonical branch guidance and lacks commit/web-test instructions. | AUD-013-006, AUD-013-007 |
| FR-011 | PARTIAL | [CI link and check list](../../README.md#L349) exist; local equivalents omit runtime-specific tests/setup. Added proof claims need qualification. | AUD-013-004, AUD-013-005, AUD-013-006 |
| FR-012 | PARTIAL | GFM source is present; [one internal link](../../README.md#L368) is broken and hosted rendering is unverified. | AUD-013-011, AUD-013-014 |
| FR-013 | IMPLEMENTED | [Standalone authority blockquote](../../README.md#L157) and [constitution cross-reference](../../README.md#L324) are visible and linked. Enforcement is not established by that text. | AUD-013-001 |
| FR-014 | PARTIAL | [Five required descriptions](../../README.md#L164) and proper terminology exist; visible roster/count conflicts with the extra entry and current runtime presentation. | AUD-013-008, AUD-013-009 |
| FR-015 | UNVERIFIED | [Overview](../../README.md#L24), [Quickstart](../../README.md#L77), and [Personas](../../README.md#L145) have no inspected separate FK measurements. | AUD-013-013 |
| FR-016 | CONFLICT | [Current ToC/order](../../README.md#L11) differs from [mandated order](spec.md#L150). | AUD-013-008 |
| FR-017 | PARTIAL | ToC and required details blocks exist; [agent summaries](../../README.md#L159) are not visible without expansion as the section model/tasks require. | AUD-013-008, AUD-013-014 |
| NFR-001 | IMPLEMENTED | [README source](../../README.md#L1) is 382 raw lines; adjusted count cannot exceed raw count. | - |
| NFR-002 | UNVERIFIED | ToC/collapsibility exist but no timed developer/evaluator scan evidence, and ordering is wrong. | AUD-013-008, AUD-013-015 |
| NFR-003 | UNVERIFIED | No unrounded three-section FK result; [historical aggregate snippet](../feature/013-root-readme/quickstart.md#L215) is not sufficient. | AUD-013-013 |
| NFR-004 | PARTIAL | Four labelled, balanced details blocks with blank boundaries; desktop/mobile behavior unverified. [Agent summary label](../../README.md#L162) also miscounts contents. | AUD-013-009, AUD-013-014 |
| SC-001 | UNVERIFIED | Purpose/structure text exists; no unfamiliar-reader two/three-minute observations. | AUD-013-015 |
| SC-002 | CONFLICT | Incorrect [startup commands](../../README.md#L119) prevent substantiating the under-15-minute setup claim; no timing supplied. | AUD-013-002, AUD-013-015 |
| SC-003 | UNVERIFIED | All five specified destinations exist under [Documentation](../../README.md#L273); 30-second discovery is not measured. | AUD-013-012, AUD-013-015 |
| SC-004 | PARTIAL | [Standalone role/authority content](../../README.md#L145) exists; no 60-second practitioner reading result. | AUD-013-001, AUD-013-015 |
| SC-005 | IMPLEMENTED | All ten named content areas exist, including [CI/CD within Contributing](../../README.md#L349). Presence does not settle ordering or correctness. | - |
| SC-006 | PARTIAL | One broken internal link; actual GitHub rendering/details behavior unverified. | AUD-013-011, AUD-013-014 |
| SC-007 | PARTIAL | 20 of 21 relative-link occurrences resolve; [ADR destination](../../README.md#L368) is stale. ToC anchors match existing headings. | AUD-013-011 |
| SC-008 | IMPLEMENTED | 382 raw Markdown source lines, below 500. | - |
| SC-009 | UNVERIFIED | No measured Overview/Quickstart scores; union-scope NFR/plan additionally requires Personas. | AUD-013-013 |
| SC-010 | IMPLEMENTED | README uses agent for core AI components and runtime for execution environments; weather/Azure data services are legitimate uses of service. Roster/topology is a separate issue. | AUD-013-009 |

## Scenario Coverage

Acceptance IDs below identify the ordinal scenarios in the six original stories; they do not rename the source scenarios.

| Scenario | Status | Evidence / expected observation | Follow-up |
| --- | --- | --- | --- |
| US1-AS1 | IMPLEMENTED | [Overview](../../README.md#L26) explains Australian multi-agent disaster coordination. Actual reader comprehension is separately unverified. | AUD-013-015 |
| US1-AS2 | IMPLEMENTED | [Documentation](../../README.md#L273) directly links architecture, rubric, constitution, and specs. | AUD-013-012 |
| US1-AS3 | IMPLEMENTED | [AIIMS/authority text](../../README.md#L145) is visible. Source safeguard caveat applies. | AUD-013-001 |
| US2-AS1 | CONFLICT | [Startup](../../README.md#L119) disagrees with application package/launcher source. | AUD-013-002 |
| US2-AS2 | PARTIAL | [Local quality checks](../../README.md#L335) omit web tests/dev setup; no fresh-default-branch pass evidence. | AUD-013-006 |
| US2-AS3 | PARTIAL | [Prerequisites](../../README.md#L81) contain some versions/install links, not all minimum versions. | AUD-013-010 |
| US3-AS1 | IMPLEMENTED | [Structure tree](../../README.md#L198) locates individual core agent folders. | AUD-013-009 |
| US3-AS2 | IMPLEMENTED | [Infrastructure tree](../../README.md#L212) and region text identify Bicep and the AU target. | AUD-013-009 |
| US3-AS3 | IMPLEMENTED | [Tree](../../README.md#L190) identifies Next.js Web and shared UI package. | - |
| US4-AS1 | IMPLEMENTED | [Authority callout](../../README.md#L157) is standalone and expanded; real approval enforcement remains open. | AUD-013-001, AUD-013-015 |
| US4-AS2 | IMPLEMENTED | [AIIMS table](../../README.md#L149) maps the five requested functional roles. | AUD-013-015 |
| US4-AS3 | IMPLEMENTED | [Constitution link](../../README.md#L157) resolves to current governance text. | AUD-013-009 |
| US5-AS1 | IMPLEMENTED | [Metrics](../../README.md#L261) contain all five specified goals. | - |
| US5-AS2 | PARTIAL | [Stack/region](../../README.md#L235) is present but technology version/topology context is stale. | AUD-013-009 |
| US5-AS3 | PARTIAL | [CI reference](../../README.md#L349) exists; runtime-specific local-test instructions are incomplete. | AUD-013-006 |
| US6-AS1 | CONFLICT | [README process](../../README.md#L328) and [CONTRIBUTING](../../CONTRIBUTING.md#L8) disagree; commit guidance is absent from README. | AUD-013-007 |
| US6-AS2 | PARTIAL | [Checks](../../README.md#L335) do not provide lint and tests for every runtime. | AUD-013-006 |
| US6-AS3 | IMPLEMENTED | [CI description/link](../../README.md#L349) identifies real PR checks; execution and hosted required-check settings unverified. | AUD-013-005, AUD-013-006 |

| Independent story test | Status | Unverified or blocked observation | Follow-up |
| --- | --- | --- | --- |
| US1-IT | UNVERIFIED | Unfamiliar reader answers purpose/audience/structure/next step within two minutes. [Source test](spec.md#L32). | AUD-013-008, AUD-013-015 |
| US2-IT | CONFLICT | Clean-machine three-runtime setup is contradicted by current invocations; no timed execution. [Source test](spec.md#L48). | AUD-013-002, AUD-013-015 |
| US3-IT | UNVERIFIED | Locate evacuation code, Bicep, and shared models using only the tree. [Source test](spec.md#L64). | AUD-013-015 |
| US4-IT | UNVERIFIED | Emergency-management professional confirms role mapping and authority. [Source test](spec.md#L80). | AUD-013-001, AUD-013-015 |
| US5-IT | UNVERIFIED | Evaluator finds metrics, stack, and deployment target within 60 seconds. [Source test](spec.md#L96). | AUD-013-009, AUD-013-015 |
| US6-IT | PARTIAL | Contribution workflow rehearsal is blocked by inconsistent branching/incomplete checks. [Source test](spec.md#L112). | AUD-013-006, AUD-013-007, AUD-013-015 |

| Edge case | Status | Evidence / gap | Follow-up |
| --- | --- | --- | --- |
| EC-01 | UNVERIFIED | Non-technical reader/plain language: prose exists but FK/reader validation not demonstrated. [Source](spec.md#L124). | AUD-013-013, AUD-013-015 |
| EC-02 | UNVERIFIED | GitHub mobile rendering and details interaction have no inspected capture. [Source](spec.md#L125). | AUD-013-014 |
| EC-03 | IMPLEMENTED | Main referenced structure directories exist; no missing intended main directory was found. Additional runtime/agent drift is separately identified. [Source](spec.md#L126). | AUD-013-009 |
| EC-04 | PARTIAL | Version-change guidance has install links but incomplete minima/current compatibility context. [Source](spec.md#L127). | AUD-013-010 |
| EC-05 | IMPLEMENTED | Architecture is outside details; fenced tree inside details is balanced in inspected source. Rendering still requires a separate gate. [Source](spec.md#L128). | AUD-013-014 |
| EC-06 | IMPLEMENTED | [Visible standalone authority](../../README.md#L157) exists at first-read depth; source enforcement risk remains. [Source](spec.md#L129). | AUD-013-001 |

## Clarifications, Amendments, and Boundaries

| Item | Status | Disposition and evidence | Follow-up |
| --- | --- | --- | --- |
| CL-01 | CONFLICT | [Universal-first decision](spec.md#L12) is not reflected in current heading/ToC order. | AUD-013-008 |
| CL-02 | PARTIAL | [Earlier after-overview ToC wording](spec.md#L13) is replaced for placement by later explicit [FR-017](spec.md#L151); collapsibility exists but summaries/order need correction. | AUD-013-008 |
| CL-03 | CONFLICT | [No-credentials local setup](spec.md#L14) and separate deployment are not established by the documented startup/local-seed paths. | AUD-013-002, AUD-013-003 |
| CL-04 | IMPLEMENTED | [Mermaid decision](spec.md#L15): inline simplified architecture and full-detail link exist; task-specific budget/current labels/render remain open. | AUD-013-009, AUD-013-014 |
| CL-05 | PARTIAL | [Audience plus complete hub-artifact routing](spec.md#L16) is incomplete beyond the selected links. | AUD-013-012 |
| CL-06 | UNVERIFIED | [FK8 decision](spec.md#L20) has no actual section scores in inspected evidence. | AUD-013-013 |
| CL-07 | PARTIAL | [Length/timing decision](spec.md#L21): 382 lines pass length; two/three-minute reader targets are unverified. | AUD-013-015 |
| CL-08 | PARTIAL | [Collapsibility decision](spec.md#L22) is structurally present; detailed-only collapse must preserve the visible summaries required by the task/model. | AUD-013-008, AUD-013-014 |
| CHK016 resolution | IMPLEMENTED | [Plan](../feature/013-root-readme/plan.md#L39) and current FR-015/NFR-003 use the union: Overview, Quickstart, Personas. SC-009's narrower measurement cannot waive Personas. | AUD-013-013 |
| CHK017 resolution | IMPLEMENTED | Two prerequisite blocks distinguish local tools from Azure deployment. Command correctness and numeric minima remain separate findings. | AUD-013-002, AUD-013-010 |
| CHK018 resolution | IMPLEMENTED | [Primary callout](../../README.md#L157) and [brief cross-reference](../../README.md#L324) follow the resolved pattern. | AUD-013-001 |
| AM-01 meta scope | IMPLEMENTED | [Out-of-scope bullet](spec.md#L208) records delivery-hygiene ownership and delegates capstone outcomes, matching the [meta contract](../028-capstone-alignment/contracts/meta-spec-flag.contract.md#L13). Do not turn this audit into implementing those outcomes. | - |
| PER-031 | PARTIAL | [Cross-reference](spec.md#L222) and [operational profiles](../001-disaster-response-hub/spec.md#L167) exist; dated named SME validation and complete contract shape are not established. | AUD-013-017 |
| PER-032 | UNVERIFIED | [Technical-actor cross-reference](spec.md#L223) exists; development-time definitions are not evidence of practitioner validation. | AUD-013-017 |
| PER-033 | IMPLEMENTED | [PH/JP/BD placeholder](spec.md#L224) explicitly retains D-009/SME preconditions. The [decision record](../028-capstone-alignment/evidence/decision-record.md#L13) preserves the deferral. No country-support validation is implied. | AUD-013-017 |
| HYP-011 | MISSING | [Named stub](spec.md#L230) not found after scoped relocation search. Existing portfolio baseline/postfeature documents do not supply per-spec consultation/uplift evidence. | AUD-013-016 |

Additional assumptions/dependencies: the required main directories, rubric, capstone, architecture, constitution, and CI workflow exist. Azure CLI remains deployment-only for the intended local path. The five-core-agent assumption must be reconciled with documented extra agents, and current constituent dependencies must replace outdated Next.js/uv-workspace assumptions. [Constitution v1.2.0](../../.specify/memory/constitution.md#L249) qualifies the earlier region premise; its protected-data rules are not waived. Original out-of-scope API documentation, production runbooks, detailed agent protocols, infrastructure provisioning, README generation, and badges remain out of scope. Badges are present but were not used as proof of CI, licensing, or maturity.

## Exact Original Task Coverage

There are **31 original tasks and 31 rows below**, all with unchanged original `[X]` state. Checked state is historical metadata, not this review's verdict. No original task is collapsed into a range.

| Task | Original state | Original obligation | Status | Concrete evidence and gap | Follow-up |
| --- | --- | --- | --- | --- | --- |
| T001 | [X] | [Title and one-sentence description](../feature/013-root-readme/tasks.md#L28) | IMPLEMENTED | [Root title/description](../../README.md#L1) match project identity. | - |
| T002 | [X] | [Ten-link ToC in mandated order](../feature/013-root-readme/tasks.md#L29) | PARTIAL | [Ten anchors](../../README.md#L11) resolve, but list order differs from FR-016. | AUD-013-008 |
| T003 | [X] | [Ten H2 content sections in order](../feature/013-root-readme/tasks.md#L30) | PARTIAL | All ten headings exist; [Architecture](../../README.md#L34) precedes required Agents/Personas. | AUD-013-008 |
| T004 | [X] | [Overview, four audiences, constitution, FK8](../feature/013-root-readme/tasks.md#L40) | PARTIAL | [Overview](../../README.md#L24) and constitution link exist; all-four-audience orientation is not explicit and FK8 is unverified. | AUD-013-008, AUD-013-013 |
| T005 | [X] | [AIIMS table, standalone authority, constitution, FK8](../feature/013-root-readme/tasks.md#L41) | PARTIAL | [Table/callout](../../README.md#L145) exist; FK score unverified and publish enforcement contradicts the assurance. | AUD-013-001, AUD-013-013 |
| T006 | [X] | [Local three-runtime quickstart plus deployment link, FK8](../feature/013-root-readme/tasks.md#L42) | PARTIAL | [Commands/deploy subsection](../../README.md#L102) exist but installation/import/launcher are wrong; no section FK evidence. | AUD-013-002, AUD-013-003, AUD-013-013 |
| T007 | [X] | [Collapsed local and Azure prerequisites](../feature/013-root-readme/tasks.md#L43) | PARTIAL | [Split blocks](../../README.md#L81) exist; Git minimum and required version specificity are incomplete. | AUD-013-010 |
| T008 | [X] | [Validate three independent FK scores](../feature/013-root-readme/tasks.md#L44) | UNVERIFIED | No revision-bound scores; [whole-document sample](../feature/013-root-readme/quickstart.md#L215) cannot establish the gate. | AUD-013-013 |
| T009 | [X] | [Five visible agent summaries plus collapsed detail](../feature/013-root-readme/tasks.md#L58) | PARTIAL | [All descriptions](../../README.md#L159) are collapsed together and a sixth entry conflicts with the label. | AUD-013-008, AUD-013-009 |
| T010 | [X] | [Accurate three-runtime Mermaid, five agents, at most 30 lines](../feature/013-root-readme/tasks.md#L59) | PARTIAL | [Inline graph](../../README.md#L36) is outside details, but has 34 body lines and stale process/port context. | AUD-013-009 |
| T011 | [X] | [Architecture context and full-doc link](../feature/013-root-readme/tasks.md#L60) | PARTIAL | [Context/link](../../README.md#L73) exist; independent-process explanation differs from the current dispatcher image. | AUD-013-009 |
| T012 | [X] | [Named links grouped by their audience](../feature/013-root-readme/tasks.md#L61) | PARTIAL | [Documentation](../../README.md#L273) contains named files but places walkthrough outside Operators; expanded inventory remains incomplete. | AUD-013-011, AUD-013-012 |
| T013 | [X] | [Authority cross-reference in Documentation](../feature/013-root-readme/tasks.md#L62) | IMPLEMENTED | [Cross-reference](../../README.md#L324) states the required constitutional authority. Source safeguard caveat remains. | AUD-013-001 |
| T014 | [X] | [Verify exact fresh-clone startup commands](../feature/013-root-readme/tasks.md#L76) | CONFLICT | [Documented invocations](../../README.md#L126) disagree with [API factory](../../apps/api/app/main.py#L25) and [dispatcher entrypoint](../../apps/agents/dispatcher/__main__.py#L14); no fresh-clone execution proof. | AUD-013-002, AUD-013-015 |
| T015 | [X] | [Contribution workflow, commits, per-runtime quality checks](../feature/013-root-readme/tasks.md#L77) | PARTIAL | [Contributing](../../README.md#L326) omits commit guidance/web tests and conflicts with [canonical guidance](../../CONTRIBUTING.md#L24). | AUD-013-006, AUD-013-007 |
| T016 | [X] | [CI reference, local lint/tests, PR checks](../feature/013-root-readme/tasks.md#L78) | PARTIAL | [CI reference](../../README.md#L349) is real; local check coverage/setup and added proof claims are incomplete. | AUD-013-004, AUD-013-005, AUD-013-006 |
| T017 | [X] | [Collapsed descriptive monorepo tree](../feature/013-root-readme/tasks.md#L92) | IMPLEMENTED | [Tree](../../README.md#L190) contains required app/package/infra/spec/test/doc/script homes. Extra-roster context belongs to the separate refresh. | AUD-013-009 |
| T018 | [X] | [Core stack, Azure services, AU primary region](../feature/013-root-readme/tasks.md#L93) | PARTIAL | [Tables/region](../../README.md#L235) exist; Next.js 15 conflicts with [package pin](../../apps/web/package.json#L29). | AUD-013-009 |
| T019 | [X] | [Review five AIIMS roles and standalone authority placement](../feature/013-root-readme/tasks.md#L107) | IMPLEMENTED | [Role table/callout](../../README.md#L149) meets the authored placement/content test; human timed review remains unverified. | AUD-013-001, AUD-013-015 |
| T020 | [X] | [Verify constitution link and consistent cross-reference](../feature/013-root-readme/tasks.md#L108) | IMPLEMENTED | [Primary link](../../README.md#L157) and [cross-reference](../../README.md#L324) resolve and agree textually. No enforcement approval is implied. | AUD-013-001 |
| T021 | [X] | [All five capstone targets with link](../feature/013-root-readme/tasks.md#L122) | IMPLEMENTED | [Metric table](../../README.md#L263) matches [capstone targets](../../capstone.md#L31). | - |
| T022 | [X] | [Complete actionable contribution/check workflow](../feature/013-root-readme/tasks.md#L136) | PARTIAL | [Workflow](../../README.md#L328) lacks complete checks/commits and conflicts with CONTRIBUTING. | AUD-013-006, AUD-013-007 |
| T023 | [X] | [Details labels and blank-line formatting](../feature/013-root-readme/tasks.md#L146) | IMPLEMENTED | Four balanced labelled blocks with blank boundaries in [README](../../README.md#L81); count wording and render validation are separate. | AUD-013-009, AUD-013-014 |
| T024 | [X] | [Agent/runtime terminology consistency](../feature/013-root-readme/tasks.md#L147) | IMPLEMENTED | [Diagram labels](../../README.md#L38), [descriptions](../../README.md#L164), and [stack](../../README.md#L239) distinguish runtime versus agent; services refer to data/weather/Azure services. | AUD-013-009 |
| T025 | [X] | [All relative links resolve](../feature/013-root-readme/tasks.md#L148) | PARTIAL | 20/21 relative occurrences pass; [ADR link](../../README.md#L368) targets a moved file. | AUD-013-011 |
| T026 | [X] | [Enforce 500-line ceiling](../feature/013-root-readme/tasks.md#L149) | IMPLEMENTED | Current [README](../../README.md#L1) is 382 raw lines; no adjustment needed for the ceiling. Historical measurement execution is not inferred. | - |
| T027 | [X] | [Final three-section FK revalidation](../feature/013-root-readme/tasks.md#L150) | UNVERIFIED | No current section inputs, tool version, or unrounded scores; aggregate sample is insufficient. | AUD-013-013 |
| T028 | [X] | [All ten ToC anchors resolve](../feature/013-root-readme/tasks.md#L151) | IMPLEMENTED | [Ten anchors](../../README.md#L13) match actual H2 slugs, including the double-hyphen AIIMS slug; order remains a different failed obligation. | AUD-013-008 |
| T029 | [X] | [Diagram outside details and rendered on GitHub](../feature/013-root-readme/tasks.md#L152) | PARTIAL | [Diagram placement](../../README.md#L36) is correct; no hosted rendering evidence inspected. | AUD-013-014 |
| T030 | [X] | [Verify GitHub desktop/mobile rendering](../feature/013-root-readme/tasks.md#L153) | UNVERIFIED | Source is not a browser capture; details, tables, and Mermaid need actual revision-bound observations. | AUD-013-011, AUD-013-014 |
| T031 | [X] | [Final section/17-FR/ten-SC review](../feature/013-root-readme/tasks.md#L154) | PARTIAL | All content areas exist but order, startup, links, local checks, and measurement evidence do not support a complete pass. Later amendments add separate evidence gaps. | AUD-013-018 |

## Checklist and Design-Evidence Assessment

The [47-item comprehensive checklist](checklists/comprehensive.md#L1) is a requirements-quality questionnaire, not 47 implementation tasks. Every original checkbox remains unchecked. This assessment records each question's current disposition without editing it.

| Item | Assessment | Evidence / follow-up |
| --- | --- | --- |
| CHK001 | IMPLEMENTED | Ten areas map to FRs; distinguish SC-005's CI area from FR-016's Agents heading. AUD-013-018. |
| CHK002 | IMPLEMENTED | T004 and section model specify overview language/context/audiences; delivery gaps AUD-013-008, AUD-013-013. |
| CHK003 | IMPLEMENTED | T009 specifies visible summaries versus collapsed detail; current violation AUD-013-008. |
| CHK004 | IMPLEMENTED | T005/T019 enumerate the five role mappings. |
| CHK005 | IMPLEMENTED | T018/model name the Azure services; synchronization AUD-013-009. |
| CHK006 | PARTIAL | Commands exist but do not fulfill complete per-runtime quality checking. AUD-013-006. |
| CHK007 | PARTIAL | Existence is required, but relocated references need active correction. AUD-013-011. |
| CHK008 | PARTIAL | ToC target defined; maintenance is not an automated generation requirement. AUD-013-008. |
| CHK009 | IMPLEMENTED | RT-001/T010 specify three runtimes, services, and at most 30 lines. AUD-013-009. |
| CHK010 | PARTIAL | No-cloud intent is clear, but supported local/stub behavior and startup verification are not. AUD-013-002. |
| CHK011 | PARTIAL | Numeric examples exist; uv/Docker minima absent. AUD-013-010. |
| CHK012 | IMPLEMENTED | FR-006 names three link groups for four audiences; government routing needs explicit treatment. AUD-013-012. |
| CHK013 | IMPLEMENTED | T015/T022 include branches, commits, PR process, and checks. Delivery conflicts AUD-013-006, AUD-013-007. |
| CHK014 | IMPLEMENTED | CHK018 resolution/model define standalone expanded blockquote. |
| CHK015 | IMPLEMENTED | Research/model supply descriptive summary examples; label accuracy AUD-013-009. |
| CHK016 | IMPLEMENTED | Explicit union-scope resolution; measurement still AUD-013-013. |
| CHK017 | IMPLEMENTED | Explicit split-prerequisite resolution. |
| CHK018 | IMPLEMENTED | Primary authority plus cross-reference pattern is present. |
| CHK019 | PARTIAL | Summary/detail distinction is defined but not implemented in Agents. AUD-013-008. |
| CHK020 | IMPLEMENTED | Terminology section/RT-007 explicitly require README runtime terms despite older architecture wording. |
| CHK021 | PARTIAL | Both enumerate ten areas but different grouping; CI is nested under Contributing, not an extra required H2. AUD-013-018. |
| CHK022 | UNVERIFIED | No controlled comprehension protocol/results. AUD-013-015. |
| CHK023 | UNVERIFIED | Prerequisite-ready timing requires machine/network baseline and a working setup. AUD-013-002, AUD-013-015. |
| CHK024 | UNVERIFIED | No timed five-link discovery evidence. AUD-013-015. |
| CHK025 | IMPLEMENTED | Standalone blockquote outside list/details is defined and present. |
| CHK026 | IMPLEMENTED | RT-003 chooses textstat; actual correct measurement remains AUD-013-013. |
| CHK027 | IMPLEMENTED | V-004 defines contextual terminology inspection, not rejecting legitimate Azure/weather service names. |
| CHK028 | PARTIAL | V-003 file links and V-008 ToC anchors split the checks; fragment-aware follow-up AUD-013-011. |
| CHK029 | PARTIAL | Six stories cover four audiences; visible order/routes remain AUD-013-008, AUD-013-012. |
| CHK030 | PARTIAL | Docs branch is named, but complete non-code contribution path is not coherent. AUD-013-007. |
| CHK031 | PARTIAL | Plan names VS Code preview; GitHub is the normative target. Raw fallback belongs to AUD-013-014, not invented browser support. |
| CHK032 | PARTIAL | Current drift demonstrates maintenance risk; avoid adding auto-generation outside scope. AUD-013-009, AUD-013-018. |
| CHK033 | IMPLEMENTED | RT-002/edge case/model define blank-line and fence handling; hosted result unverified. AUD-013-014. |
| CHK034 | PARTIAL | Edge case requires planned notation but no fixed syntax; current main directories exist. AUD-013-009. |
| CHK035 | PARTIAL | Version references exist, no complete support matrix/change coordination. AUD-013-010. |
| CHK036 | IMPLEMENTED | FR-017 explicitly keeps the architecture outside details. |
| CHK037 | CONFLICT | NFR-001 excludes some blanks while SC-008/V-001 count raw lines. Current 382 passes both; record both methods. AUD-013-018. |
| CHK038 | UNVERIFIED | Scannability requires actual timed reader evidence. AUD-013-015. |
| CHK039 | IMPLEMENTED | RT-003 says unrounded score at or below 8.0; whole-doc rounded sample is inadequate. AUD-013-013. |
| CHK040 | UNVERIFIED | No actual mobile platform/viewport record. AUD-013-014. |
| CHK041 | PARTIAL | Required FR-006 files exist; RT-006's historical no-risk claim is not ongoing validation. AUD-013-011. |
| CHK042 | IMPLEMENTED | CI file exists and is linked; hosted execution/branch rules unverified. |
| CHK043 | CONFLICT | Five-core roster assumption versus sixth documented agent/new dispatcher roles. AUD-013-009. |
| CHK044 | PARTIAL | Constitution/stack/ADR movement demonstrate independently evolving dependencies. AUD-013-009, AUD-013-011. |
| CHK045 | IMPLEMENTED | This report individually traces all ten SCs, retaining unverified measurements. |
| CHK046 | IMPLEMENTED | All 18 acceptance scenarios individually traced above. |
| CHK047 | IMPLEMENTED | Each of six stories has FR-backed content and separate independent-test disposition. |

### Research, Validation Rules, and Review Claims

| Artifact obligation | Current assessment |
| --- | --- |
| RT-001 / V-007 | Inline Mermaid outside details is authored; 34 lines violate the task budget; hosted rendering unverified. |
| RT-002 / V-006 | Four labelled details blocks use the required blank boundaries; count/visibility and rendering remain separate concerns. |
| RT-003 / V-002 | Strict textstat threshold and union scope are defined; no current three-section execution evidence. |
| RT-004 | Local/Azure prerequisite split exists; exact minima, Python package setup, and local-seeder behavior remain incomplete. |
| RT-005 / V-005 | Expanded primary authority and cross-reference exist; real approval enforcement is not proved by documentation. |
| RT-006 / V-003 | Required historical destinations exist, but one additional current relative link is stale. Historical existence checks do not certify the current README. |
| RT-007 / V-004 | Agent/runtime terminology convention is followed in README prose; version/roster/topology claims still drift. |
| RT-008 / V-001 | 382 raw lines pass 500; the 420-480 target is a planning estimate, not a minimum. Collapsing content does not remove its source lines. |
| V-008 | All ten ToC anchors match headings; this does not prove the mandated order. |
| Plan constitution gate | Authored PASS table, using an older six-principle structure; not evidence of security approval or conformity to the current constitution. |
| Requirements checklist | 16 checked authoring-quality items; old 15-FR/seven-SC notes and named agent feedback are not current implementation/human-review evidence. |
| Historical DoD | 11 unchecked items, including readability/rendering; content presence does not retroactively check them. |
| Feature-028 snapshots/decision | Authored portfolio structural assessment (1.8 to 3.8), not per-spec HYP-011 measurement, raw consultation record, or named SME sign-off. D-009 remains a deferral. |
| Linked demo/evaluation content | [Walkthrough](../../docs/disaster-response-hub/demo/walkthrough.md#L1) includes screenshot placeholders; [executive deck](../../docs/disaster-response-hub/demo/executive-deck.md#L42) lists further validation work. These are authored collateral, not evidence that this README's independent tests were executed. |

## Future Validation and Closure Rules

All commands in follow-ups are **instructions for a later authorized remediation/review**, not executions claimed here. Before running them, use a disposable clone at the candidate revision, a declared Python environment with API/agent and test dependencies, pnpm 10.6.3 with a supported Node version, and PowerShell where applicable. Browser tests additionally need installed Chromium and exclusively local API/Web instances. Documentation lint/readability tools must be installed and pinned deliberately; the proposed root-README checker is not currently available. Never allow inherited Azure credentials, endpoints, `azd` selection, or production test-support flags to become fixtures.

Expected gates are: correct local module/package resolution; meaningful local/degraded responses; rejection of unsafe publication and implicit cloud seeding; accurate test/proof claims; complete per-runtime checks; consistent contributor guidance; exact section/visibility/terminology requirements; zero broken internal links; raw and adjusted line counts at most 500; Mermaid body at most 30 lines; three unrounded FK scores at most 8.0; revision-bound desktop/mobile observations; and the specific human timing/approval records. Missing prerequisites, missing proposed validators, empty test selection, warnings, skipped probes, or synthetic green samples must not be reported as a completed gate.

Report-authoring integrity is checked separately using text-only exact original-task/state coverage, unique requirement/scenario/amendment IDs, unchecked follow-up IDs, local path/line-link resolution, and editor diagnostics. These checks establish report integrity only. Original implementation completion, clean-machine execution, cloud readiness, measurements, and external approvals remain limited exactly as recorded above.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 013 only. The root README was corrected at the concrete
source-of-truth points identified by the review: API startup now uses `app.main:app`, the current agent entrypoint is
`python -m dispatcher`, Azure deployment is explicitly credentialed and mutating rather than a local quickstart step,
the five core agents are distinguished from Dependency Notifier, Next.js is recorded as 16.2.6, residency wording is
bounded by the current Constitution, the operator walkthrough is linked, the local seed command is marked local-mode,
and ADR-031 points to its current corpus path.

Validation: `npx --yes markdownlint-cli2 README.md` passed after correcting list/table formatting; targeted README
links to the Constitution, architecture page, ADR-031, walkthrough, and `infra/` exist; `git diff --check` passed.

Remaining open work is intentionally not claimed: clean-machine three-runtime startup, safe seed implementation,
RAG smoke contract, full web-coverage semantics, exact universal-first section reordering, readability scores,
mobile rendering, human timing, contribution-policy owner resolution, and external/SME evidence.
