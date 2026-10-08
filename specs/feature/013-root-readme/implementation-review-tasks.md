# Implementation Review Tasks: 013 Root README Historical Task Home

## Scope and Method

- Review date: **2026-09-11**.
- Reviewed revision: **5b44c249f00e0e4a13ea2579c8c33d06e2471d7a**, confirmed against HEAD.
- This is the **historical task-home report**. Its original implementation obligations are the complete local [tasks.md](tasks.md#L1), interpreted against the complete [primary specification](../../013-root-readme/spec.md#L1), local design documents, and later amendments. All findings, task evidence, developer instructions, and tester instructions are included here; another audit report is not required.
- This continues the existing audit under the [Review Contract](../../001-spec-implementation-audit/README.md#L13). It is not a new feature, implementation plan, approval, or retrospective completion record.
- Only this report and the primary specification home's implementation-review-tasks.md are authorized writes. Original specifications, task checkboxes, checklists, evidence, source, root documentation, and the audit index remain unchanged. No branch or commit was created.
- Static documentation, configuration, code, and test-assertion inspection only. No application, import probe, dependency installation, product test, build, browser session, advertised script, cloud operation, deployment, external lookup, actor invocation, or delegation was performed. Existing audit reports were not inputs.
- Source presence establishes authored behavior, not successful execution or deployed enforcement. A health response, synthetic fixture, checked task, rubric summary, or agent-authored statement does not establish operational readiness or human approval.
- This home and the primary home describe the same **31 original tasks and 18 distinct follow-ups**, not 62 original tasks or 36 independent remediations. Local links below are rebased for this historical folder.

### Complete Feature Inputs

All eight feature-local documents were read in full. The tracked-file inventory contains no additional amendment, contract, or review file within either feature folder.

| Input | Scope |
| --- | --- |
| [tasks.md](tasks.md#L1) | Exactly 31 original tasks, T001 through T031, all originally checked `[X]`. This is the original task authority. |
| [plan.md](plan.md#L1) | Single-document delivery boundary, constitution gate claims, CHK016/CHK017/CHK018 resolutions. |
| [research.md](research.md#L1) | RT-001 through RT-008: diagram, collapsibility, strict readability threshold, prerequisites, authority, links, terminology, line budget. |
| [data-model.md](data-model.md#L1) | Ordered section entities, visibility rules, V-001 through V-008 validation rules. |
| [quickstart.md](quickstart.md#L1) | Historical authoring instructions, validation snippets, and 11 unchecked definition-of-done items. |
| [Primary spec.md](../../013-root-readme/spec.md#L1) | Six stories; 18 acceptance scenarios; six independent story tests; six edge cases; 17 FRs; four NFRs; ten SCs; eight clarification decisions; assumptions, dependencies, scope, personas, hypothesis. |
| [Primary requirements.md](../../013-root-readme/checklists/requirements.md#L1) | 16 checked specification-quality items and authoring-feedback claims. |
| [Primary comprehensive.md](../../013-root-readme/checklists/comprehensive.md#L1) | 47 unchecked requirements-quality questions, including three explicitly resolved conflicts. |

Associated amendment evidence was also inspected: the [persona contract](../../027-spec-hardening/contracts/persona-profile.md#L1), [hypothesis-evidence contract](../../028-capstone-alignment/contracts/evidence-stub.contract.md#L1), [meta-spec contract](../../028-capstone-alignment/contracts/meta-spec-flag.contract.md#L1), [baseline](../../028-capstone-alignment/evidence/rubric-baseline.md#L1), [postfeature snapshot](../../028-capstone-alignment/evidence/rubric-postfeature.md#L1), and [decision record](../../028-capstone-alignment/evidence/decision-record.md#L1). Referenced original [operational personas](../../001-disaster-response-hub/spec.md#L167) and [technical actor specification](../../004-actor-github-agents/spec.md#L98) were consulted as source material, not audits.

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

- Root [README.md](../../../README.md#L1): **382 source lines**, below both 500-line limits before the NFR-001 blank-line exclusion; ten content sections plus ToC; four balanced, labelled details blocks; **34 Mermaid body lines**, exceeding T010's 30-line limit.
- Text-only link inspection found **21 relative file/directory-link occurrences, 16 distinct targets, and one broken target** at [README.md](../../../README.md#L368). The ten ToC anchors correspond to existing headings, but their order is not mandated order. External links, badges, hosted rendering, and remote permissions were not verified.
- ADR-031 has moved to [the corpus ADR](../../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L1). The finding is a stale link, not absent rationale. [ADR-032](../../../docs/corpus/aidr/decisions/adr-032-oidc-supersession.md#L3) remains Proposed and does not establish completed OIDC migration. [cd.yml](../../../.github/workflows/cd.yml#L84) still consumes `AZURE_CREDENTIALS`.
- Launcher searches covered tracked API/agent project files and entry points. The actual API factory is [app/main.py](../../../apps/api/app/main.py#L25); the packaged image starts [dispatcher](../../../apps/agents/Dockerfile#L48). Per-agent entry points also exist. Do not label agent behavior missing because the README's launcher is wrong.
- The RAG `/healthz` contract was searched in API routes, router registration, and the application factory. Existing [API health](../../../apps/api/app/api/health.py#L19) and [evidence-health registration](../../../apps/api/app/api/router.py#L120) are different contracts, not replacements for the smoke script's RAG fields.
- HYP-011 filename variants were searched in tracked feature/evidence paths, with a repository filename search and targeted HYP-011 text search in feature 028. Neither the doubled-prefix stub nor a relocated HYP-011 file was found. Feature 028's evidence directory contains a decision record and two rubric snapshots.
- A tracked text search of tests, tools, scripts, and workflows found no dedicated root-README/readability validator using `013-root-readme`, `flesch_kincaid`, or `textstat`. This does not disprove a historical manual review. Generated build trees and installed third-party packages are not implementation evidence for this revision.

## Prioritized Findings

| Priority | Finding and evidence | Follow-up |
| --- | --- | --- |
| P1 | **The visible safety guarantee is stronger than the registered alert path.** [README authority](../../../README.md#L157) says recommendations require human approval. [Validation](../../../apps/api/app/services/public_alert_service.py#L48) accepts `pending_approval`; [publication](../../../apps/api/app/services/public_alert_service.py#L66) merely records the supplied persona string. The [route](../../../apps/api/app/api/routes/alerts.py#L37) adds no approval lookup, and [RBAC protected prefixes](../../../apps/api/app/middleware/rbac_check.py#L32) exclude alerts. This is a shared-code safeguard risk, not proof of a deployed exploit or actual notification delivery. | AUD-013-001 |
| P1 | **The documented local quickstart does not establish three runnable runtimes.** [Root install](../../../README.md#L113) does not declare a Python application workspace. [Root dependencies](../../../pyproject.toml#L9) omit application distributions and optional dev tooling; [API](../../../README.md#L126) and [agent](../../../README.md#L130) invocations disagree with [API packaging](../../../apps/api/pyproject.toml#L1), [agent packaging](../../../apps/agents/pyproject.toml#L1), and the dispatcher entry point. [CI](../../../.github/workflows/ci.yml#L36) installs the applications separately. Verification URLs, expected responses, and degraded-mode limits are absent. | AUD-013-002 |
| P1 | **A locally labelled snippet can seed an active cloud environment.** [README local smoke](../../../README.md#L306) runs a seeder that [imports active azd values](../../../scripts/seed-database.ps1#L17). The loader's [Cosmos](../../../scripts/seed_loader.py#L210) and [Blob](../../../scripts/seed_loader.py#L240) paths write when configuration/permission are present. No explicit dry-run or reviewed target is required by the local snippet. | AUD-013-003 |
| P1 | **The RAG smoke command is not a reliable cutover gate.** [README](../../../README.md#L299) supplies only a placeholder base URL. [The script](../../../infra/scripts/azd-up-smoke-test.ps1#L83) expects an unregistered RAG `/healthz`, treats telemetry failures as warnings, and [returns zero without SSE citations](../../../infra/scripts/azd-up-smoke-test.ps1#L190). [The dry run](../../../infra/scripts/simulation-final-canary-dry-run.ps1#L92) checks identical synthetic samples and empty-citation serialization, not real grounded inference. | AUD-013-004 |
| P2 | **The web-coverage proof claim exceeds its assertions.** [README](../../../README.md#L308) claims every outcome/persona combination end-to-end, while [the gate](../../../scripts/web-coverage/_lib/schema_validators.py#L107) counts distinct sets independently. [A representative outcome test](../../../tests/e2e/web-coverage/capstone/outcome-1-bushfire-extreme-heat.spec.ts#L21) posts synthetic evaluator inputs; it does not demonstrate all 340 pairs or real lives saved. [CI](../../../.github/workflows/ci.yml#L300) additionally installs Python applications and Chromium, omitted from the snippet. | AUD-013-005 |
| P2 | **Local checks and contribution instructions are incomplete and inconsistent.** [README checks](../../../README.md#L335) omit web tests and explicit type checking; [web test scripts](../../../apps/web/package.json#L12) exist. [README branching](../../../README.md#L328) conflicts with [CONTRIBUTING](../../../CONTRIBUTING.md#L8), and its [commit guidance](../../../CONTRIBUTING.md#L63) is not linked or summarized. | AUD-013-006, AUD-013-007 |
| P2 | **Required information order and visible summaries were not delivered.** [README ToC/headings](../../../README.md#L11) put Architecture/Quickstart before Agents/Personas and Documentation before Contributing. [All agent summaries](../../../README.md#L159) are collapsed. T004's explicit four-audience orientation is not supplied by the overview. | AUD-013-008 |
| P2 | **Architecture, versions, roster, and governance context have drifted.** [README stack](../../../README.md#L241) says Next.js 15 versus [16.2.6](../../../apps/web/package.json#L29). The five-agent summary contains a sixth agent; per-agent port labels do not describe the current [dispatcher image](../../../apps/agents/Dockerfile#L45). The [constitution](../../../.specify/memory/constitution.md#L249) contains a bounded model-hosting residency exception; retain AU persistence rules without implying an unqualified deployment attestation. | AUD-013-009 |
| P2 | **Prerequisites and documentation routing are incomplete.** [Prerequisites](../../../README.md#L81) lack uv/Docker minima and the task's Git minimum; PowerShell snippets lack a PowerShell prerequisite. [Walkthrough](../../../README.md#L286) is not under Operators; the expanded documentation inventory is not routed; ADR-031 is linked at its previous location. | AUD-013-010, AUD-013-011, AUD-013-012 |
| P2 | **Checked validation is not current validation evidence.** No inspected section-specific FK scores, timed newcomer observations, or GitHub captures establish the current requirements. [The historical sample](quickstart.md#L207) prints a rounded whole-document score rather than three unrounded section scores. | AUD-013-013, AUD-013-014, AUD-013-015 |
| P2 | **Later hardening claims lack contract-bound evidence.** [HYP-011](../../013-root-readme/spec.md#L230) links a missing doubled-prefix stub; portfolio uplift is not per-spec consultation/uplift evidence. [PER-031/PER-032](../../013-root-readme/spec.md#L222) validation assertions are not backed by dated practitioner signatures. PER-033's explicit deferral is not implemented international support. | AUD-013-016, AUD-013-017 |
| P3 | **The completion ledger is stale.** All 31 tasks are checked, all 47 comprehensive questions are unchecked, and [quality notes](../../013-root-readme/checklists/requirements.md#L34) still count 15 FRs/seven SCs rather than 17/ten. The plan's constitution table uses an older structure. Preserve these original records and append a revision-specific reconciliation. | AUD-013-018 |

## Open Follow-ups

These are **unchecked future tasks**, not permission to change source during this review. Shared-code fixes need owning-feature review. Commands below are future-only; prerequisites and closure rules appear in this report's final section. Proposed new checker/evidence paths are explicitly labelled and are not existing evidence.

### Safety, Setup, and Evidence Claims

- [ ] **AUD-013-001 (P1): Make the human-approval guarantee defensible.**

  **Original obligations:** FR-005, FR-013; US1-AS3, US4-AS1; T005, T013, T019, T020; Constitution human-in-the-loop boundary.

  **Expected / observed / impact:** Publication should require authorized human approval. The [route](../../../apps/api/app/api/routes/alerts.py#L37) forwards an arbitrary supplied persona ID; the [service](../../../apps/api/app/services/public_alert_service.py#L48) accepts `pending_approval`. Operators could confuse a visible guarantee with an enforced approval record. Channel adapters in this service build local payloads; real notification delivery was not established.

  **Developer instructions:** Have the alert/approval owner bind publication to an authenticated authorized identity and the applicable recorded approval, including tenant/recommendation linkage. Reject pending, rejected, stale, and mismatched approvals before mutation. Preserve simulation isolation. Qualify prototype limitations in the README and [operator runbook](../../../docs/disaster-response-hub/operator-runbooks.md#L29) until enforcement is supported; never weaken the constitution to match a bypass.

  **Tester instructions:** Extend [the existing contract test](../../../tests/contract/test_live_incident_contract.py#L10), reusing its `Incident`, `Recommendation`, and `PublicAlert` fixtures. Positive: approved same-tenant publication records the actual authorized approver. Negative: pending/rejected/missing approvals and spoofed or unauthorized persona IDs cannot publish. Edge: revoked approval, retries, cross-tenant IDs, and simulated delivery. Assert denial before status/audit/channel side effects; expect authorization or non-publishable-state errors, not success.

  **Future command / completion:** With isolated application/test dependencies, run `python -m pytest tests/contract/test_live_incident_contract.py -q` after adding the rejection assertions. Completion requires passing positive/negative source-path checks, owner review, and accurate README/runbook boundaries; local tests do not attest a deployment.

- [ ] **AUD-013-002 (P1): Repair and bound the no-credentials three-runtime quickstart.**

  **Original obligations:** FR-003; SC-002; US2-AS1; T006, T014.

  **Expected / observed / impact:** A new contributor should start all three runtimes with only local prerequisites. [README installation/startup](../../../README.md#L102) does not install the applications, uses incorrect module targets, and gives no verification responses. [API health](../../../apps/api/app/api/health.py#L10) does not actually probe configured dependency connectivity; [dispatcher health](../../../apps/agents/dispatcher/agent.py#L200) can explicitly report degraded LLM mode.

  **Developer instructions:** Follow real [API](../../../apps/api/pyproject.toml#L1), [agent](../../../apps/agents/pyproject.toml#L1), and [pnpm workspace](../../../pnpm-workspace.yaml#L1) boundaries. Document reproducible dependency/environment setup, repository-root CWD and activation for each separate terminal, the dispatcher entry point, URLs, and supported local degraded behavior. Use [Playwright setup](../../../apps/web/playwright.config.cts#L18) and [CI installs](../../../.github/workflows/ci.yml#L36) as implementation references, not proof of completed onboarding. Do not require cloud login or globally disable production protections.

  **Tester instructions:** Positive: a disposable fresh clone with declared prerequisites and no inherited Azure configuration starts API, Agents, and Web with specified local responses. Negative: missing package, incorrect CWD, occupied port, absent credentials, and missing browser have actionable guidance. Edge: Windows/POSIX activation, existing servers, and no-model/degraded responses. Fixture: existing seed catalogue and a clearly synthetic local incident; stub `healthy` must not imply cloud readiness.

  **Future commands / completion:** After install instructions are corrected, validate `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`, `python -m dispatcher`, and `pnpm --filter @ama/web dev` in their documented environments/CWDs, then stop future processes. Completion requires verbatim fresh-clone success, meaningful local response assertions, and AUD-013-015's recorded setup timing.

- [ ] **AUD-013-003 (P1): Separate local fixtures from cloud seeding.**

  **Original obligations:** FR-003's local/cloud separation; US2-AS1; T006, T014; README's added local web-smoke instructions.

  **Expected / observed / impact:** Local instructions must not implicitly choose and mutate the user's active cloud environment. [The PowerShell wrapper](../../../scripts/seed-database.ps1#L17) imports `azd` values and invokes [writing loader paths](../../../scripts/seed_loader.py#L210) when configuration/permission are available.

  **Developer instructions:** Make local fixture mode explicit and non-cloud, with no inherited `azd env` selection. Preserve authorized postprovision behavior in [azure.yaml](../../../azure.yaml#L15) under a separate documented target/approval boundary. A validation-only dry run must not be described as materializing the running API's in-memory stores. Cloud seeding needs an explicit reviewed target and separate permission.

  **Tester instructions:** Positive: local fixture preparation performs no Azure calls and produces intended local state. Negative: inherited Cosmos/storage configuration, available `azd`, or an active production environment cannot trigger local-mode writes. Edge: missing `azd`, partial endpoints, malformed fixtures, and repeated local loads. Use fake clients/environment injection in [tests/unit](../../../tests/unit/) and record attempted calls; do not use real accounts.

  **Future command / completion:** Add a scoped local-mode test, then run `python -m pytest tests/unit -k seed -q`; verify the selected tests include environmental-inheritance cases. Completion requires zero-cloud-call assertions, explicit safe README instructions, and a separate fake-client postprovision compatibility check.

- [ ] **AUD-013-004 (P1): Make RAG smoke instructions reachable and fail-closed.**

  **Original obligations:** FR-002, FR-003, FR-006, FR-011; T011, T014, T016, T031; current RAG validation claims in root documentation.

  **Expected / observed / impact:** A cutover gate should query a registered contract and fail its required assertions. [The requested `/healthz`](../../../infra/scripts/azd-up-smoke-test.ps1#L83) does not match [registered API health](../../../apps/api/app/api/router.py#L74); [SSE failure](../../../infra/scripts/azd-up-smoke-test.ps1#L188) returns success. Omitted optional arguments skip inference/telemetry. [Identical synthetic dry-run samples](../../../infra/scripts/simulation-final-canary-dry-run.ps1#L92) cannot prove live cutover.

  **Developer instructions:** Have the RAG/API owner define one real route/response contract and correct the README URL/prefix. Label required, optional, synthetic, and live checks separately. Enforce required telemetry/citation failures or label the operation a limited informational probe. Keep deployment and live-flag changes behind their existing human-controlled boundary. Do not substitute the unrelated evidence-health endpoint.

  **Tester instructions:** Positive: a local mock server supplies conforming RAG health and a required citation event. Negative: 404, missing fields, invalid SHA, ungrounded answer, telemetry outage, absent citations, and HTTP/stream errors fail required gates. Edge: optional arguments omitted, latency overrun, empty-corpus disclosure, and early stream closure. Use mock HTTP/SSE fixtures with existing [tests/contract](../../../tests/contract/) and [tests/devops](../../../tests/devops/) locations.

  **Future command / completion:** Run `pwsh ./infra/scripts/azd-up-smoke-test.ps1 -BaseUrl http://127.0.0.1:18080` only against a future mock server, adding controlled optional-probe fixtures. Completion requires correct route wiring and nonzero exits for required failures; dry-run success must not be labelled live approval. Actual live validation remains separately authorized future work.

- [ ] **AUD-013-005 (P2): Describe actual web-coverage depth and setup.**

  **Original obligations:** FR-006, FR-010, FR-011; US2-AS2, US5-AS3, US6-AS2; T012, T015, T016, T022, T031.

  **Expected / observed / impact:** Readers need truthful coverage and installation claims. [The gate](../../../scripts/web-coverage/_lib/schema_validators.py#L107) counts independent sets, while [the representative test](../../../tests/e2e/web-coverage/capstone/outcome-1-bushfire-extreme-heat.spec.ts#L21) exercises synthetic API/evidence behavior. [CI prerequisites](../../../.github/workflows/ci.yml#L300) and [server environment/reuse](../../../apps/web/playwright.config.cts#L23) are omitted from the short local instructions.

  **Developer instructions:** Distinguish sampled persona/outcome coverage, synthetic metric proxies, UI workflows, and actual outcomes. If the full cross-product is intended, obtain scope approval and enforce a pair matrix. Correct the linked onboarding steps to install both Python apps and Chromium and explain the dual guard and reused-server risk. Never enable test-support in production.

  **Tester instructions:** Positive: documented smoke discovers its tagged tests and reaches the intended local processes. Negative: a synthetic trace containing all personas and outcomes but missing most pairs cannot substantiate full-pair coverage; missing browser and wrong-environment reused server are diagnosed. Edge: empty trace, failing/skipped rows, one missing pair, and cold cache. Reuse [the outcome fixture](../../../tests/e2e/web-coverage/_support/fixtures/data/outcome-1-bushfire-extreme-heat.fixture.json#L1) and existing suite; use an independent synthetic trace for the matrix counterexample.

  **Future commands / completion:** After safe setup, run `pnpm --filter @ama/web exec playwright test --project=web-coverage-chromium --grep "@p1"`; for a controlled gate fixture use `python scripts/web-coverage/_lib/schema_validators.py gate --trace <synthetic-trace.json> --gap-register <fixture-register.md>`. Completion requires correct selected-test/assertion counts and an accurate coverage statement, not a claim that proxy inputs prove lives saved.

### Documentation Correctness

- [ ] **AUD-013-006 (P2): Supply runnable per-runtime quality checks.**

  **Original obligations:** FR-010, FR-011; US2-AS2, US5-AS3, US6-AS2; T015, T016, T022.

  **Expected / observed / impact:** Contributors should lint and test each relevant runtime. [README checks](../../../README.md#L335) omit test-tool setup and web tests. [Root scripts](../../../package.json#L5), [web scripts](../../../apps/web/package.json#L6), and [CI selection](../../../.github/workflows/ci.yml#L131) provide the actual command owners.

  **Developer instructions:** State application/test dependency setup, CWD, Python lint/format/test selection, and web lint/typecheck/unit/e2e distinctions. Explain browser/external-fixture prerequisites. Reuse existing scripts and distinguish advisory CI gates from blocking ones; do not present a build as a test or unqualified pytest as CI parity.

  **Tester instructions:** Positive: each documented command resolves and selects meaningful relevant checks. Negative: successful build cannot conceal a failed web test; absent dev tools are identified during setup. Edge: single-runtime work, browser-free unit checks, and staging-only suites. Fixtures: existing Python contract/integration and web Vitest/Playwright tests, not historical checklist ticks.

  **Future commands / completion:** With dependencies installed, validate `python -m pytest tests/contract tests/integration -q`, `pnpm --filter @ama/web test`, `pnpm --filter @ama/web exec tsc --noEmit`, and `pnpm lint:web`. Completion requires explicit scope/prerequisites and expected nonzero results for relevant failing-fixture cases.

- [ ] **AUD-013-007 (P2): Reconcile branch, PR, and commit guidance.**

  **Original obligations:** FR-010; US6-AS1; T015, T022.

  **Expected / observed / impact:** A newcomer needs one coherent workflow. [README](../../../README.md#L328) specifies prefixed features from `main`; [CONTRIBUTING](../../../CONTRIBUTING.md#L8) specifies environment branching and [unprefixed names](../../../CONTRIBUTING.md#L24). [Commit expectations](../../../CONTRIBUTING.md#L63) exist but are neither summarized nor linked from the README.

  **Developer instructions:** Obtain contribution-owner resolution of branch names, bases, and targets; synchronize the README summary and canonical contribution link. Include commit expectations. Preserve the integration-only main/deployment-environment distinction shown by [CD](../../../.github/workflows/cd.yml#L19). Do not infer hosted branch protection from configuration files.

  **Tester instructions:** Positive: a newcomer identifies approved name, base, PR target, review requirement, and commit format without contradictions. Negative: docs-only work or hot-fixes must not unintentionally deploy or choose conflicting bases. Edge: environment-targeted changes and non-code contributions. Fixture: paper examples for a docs change, shared feature, and production hot-fix; no real branch is needed in this audit.

  **Future command / completion:** Later compare `Select-String -Path README.md,CONTRIBUTING.md -Pattern 'feature/','NNN-short-name','main','dev','commit'` and have the owner review example workflows. Completion requires one consistent policy and a resolving contribution link, not creating a branch or commit during this review.

- [ ] **AUD-013-008 (P2): Restore ordered navigation and visible agent summaries.**

  **Original obligations:** FR-001, FR-014, FR-016, FR-017; NFR-002; T002, T003, T004, T009, T031.

  **Expected / observed / impact:** Required order is Overview, Agents, Personas, Architecture, Quickstart, Structure, Stack, Metrics, Contributing, Documentation. [Current headings](../../../README.md#L11) differ, and [Agents](../../../README.md#L159) hides every summary. Government/operator readers reach technical setup before required governance context.

  **Developer instructions:** Reorder sections and ToC together, retaining later FR-017's ToC-after-title/description placement. Supply visible short summaries for each core agent and collapse only details. Explicitly orient all four audiences in the overview. Keep human authority, architecture, quickstart commands, and documentation links expanded.

  **Tester instructions:** Positive: exactly ordered headings/ToC and visible agent summaries/authority with details closed. Negative: reordered section, hidden authority, or collapsed summary fails. Edge: expanded state, extra subheadings, duplicate anchors, and raw Markdown. Fixture: current README with in-memory mutation cases, not edits to original files.

  **Future command / completion:** A proposed `tools/lint/check_root_readme.py --structure` checker may implement this; until authored, compare `Select-String -Path README.md -Pattern '^## ','<details>','<summary>'` to the required sequence. Completion requires correct order, ten resolvable anchors, visible summaries, and preserved line budget.

- [ ] **AUD-013-009 (P2): Refresh topology, versions, agent roster, and residency context.**

  **Original obligations:** FR-002, FR-008, FR-009, FR-014; US3, US5-AS2; T010, T011, T017, T018, T024.

  **Expected / observed / impact:** The root summary should match current source without attesting a deployment. [Diagram](../../../README.md#L34) is 34 lines with per-agent ports; [the image](../../../apps/agents/Dockerfile#L45) uses one dispatcher. [Next.js](../../../apps/web/package.json#L29) is 16.2.6. A sixth agent conflicts with the five-agent summary, while [architecture](../../../docs/disaster-response-hub/architecture.md#L57) also names Dependency Notifier. The constitutional model-hosting exception is not explained.

  **Developer instructions:** Reconcile five required core agents with added roles; do not delete core descriptions or confuse development-time persona agents with runtime agents. Keep the three-runtime Mermaid summary within 30 lines, identifying ingestion in [azure.yaml](../../../azure.yaml#L47) as supporting scope. Update versions and coordinate architecture detail changes. Preserve Australian persisted regulated data and explicitly bound non-AU model-hosting exceptions without certifying live deployment state.

  **Tester instructions:** Positive: core/extra agents, topology, versions, and primary AU region agree with manifests and constitution. Negative: stale major version, wrong port, data-store residency relaxation, or 31-line diagram fails. Edge: added agent versus runtime, model-hosting-only exception, and clearly labelled planned/missing folders. Fixtures: manifests, dispatcher role set, current constitution, and diagram text.

  **Future command / completion:** Compare `Select-String -Path README.md,apps/web/package.json,apps/agents/Dockerfile,azure.yaml -Pattern 'Next.js','"next"','dispatcher','8080','host:'` in future review and independently count Mermaid body lines. Completion requires correct content, at most 30 diagram lines, and no false compliance/deployment attestation.

- [ ] **AUD-013-010 (P2): Complete numeric prerequisites and installation guidance.**

  **Original obligations:** FR-004; US2-AS3; EC-04; T007.

  **Expected / observed / impact:** Required tools need justified numeric minima and installation routes. [README](../../../README.md#L81) lacks uv/Docker minima and the task's Git minimum; added `pwsh` commands lack a PowerShell prerequisite. Historical uv workspace/lock assumptions do not establish current packaging behavior.

  **Developer instructions:** Define supported minima from actual project and CI compatibility. Distinguish supported Node minimum from CI's Node 24. Remove unnecessary Docker from a truly local flow or specify its purpose/version. Include PowerShell 7 when required. Keep Azure CLI/azd/subscription deployment-only; provide environment activation and installation links. Do not replace a minimum with `latest` or invent version floors.

  **Tester instructions:** Positive: minimum-version environments follow setup. Negative: below-minimum tools and absent deployment-only tools produce correct guidance without blocking local mode. Edge: OS shells, existing pnpm/Corepack, and no Docker where no service requires it. Fixture: approved tool-support matrix rather than this machine's configuration.

  **Future command / completion:** After the matrix is approved, inspect `git --version`, `uv --version`, `node --version`, `pnpm --version`, and `$PSVersionTable.PSVersion` in the future verification environment. Completion requires justified numeric minima, installation references, and verified local/deployment separation.

- [ ] **AUD-013-011 (P2): Rebase ADR-031 and verify all README destinations.**

  **Original obligations:** FR-006, FR-012; SC-006, SC-007; T025, T030, T031.

  **Expected / observed / impact:** Internal links must resolve. [README line 368](../../../README.md#L368) uses the old ADR location; [the existing decision](../../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L1) is under corpus. Readers cannot follow the deployment-credential rationale through the current link.

  **Developer instructions:** Change the destination to the existing ADR and validate file, directory, and fragment links relative to the root README. Do not recreate obsolete content merely to satisfy a link or treat [Proposed ADR-032](../../../docs/corpus/aidr/decisions/adr-032-oidc-supersession.md#L3) as a completed migration. Keep external-link validation separate and authorized.

  **Tester instructions:** Positive: every current relative occurrence resolves, including the moved ADR. Negative: removed file, incorrect case, and nonexistent heading fragment fail. Edge: directory links, repeated targets, ToC-only anchors, encoded paths, and badge query strings. Fixture: candidate README and repository path inventory.

  **Future command / completion:** A proposed `python tools/lint/check_root_readme.py --links` or equivalent PowerShell text check must distinguish files/directories/fragments/external links. Completion requires zero broken internal links and resolving ToC anchors without weakening checks or rewriting historical evidence.

- [ ] **AUD-013-012 (P2): Restore complete audience-oriented documentation routes.**

  **Original obligations:** FR-006, CL-05; US1-AS2; T012.

  **Expected / observed / impact:** Operators should find the walkthrough and runbooks, with routes to the expanded hub-artifact inventory. [Developers](../../../README.md#L281) holds the walkthrough, [Operators](../../../README.md#L319) does not; [evaluation](../../../docs/disaster-response-hub/evaluation/) and [regional adaptation](../../../docs/disaster-response-hub/regional-adaptation-asia-pacific.md#L1) also exist without an audience route in the README.

  **Developer instructions:** Add the walkthrough to Operators; retain evaluator rubric/capstone/deck and developer architecture/spec/constitution links. Provide an audience index or direct paths for the rest of the hub documentation. Explain where government readers should go. Do not promote historical setup placeholders into a verified local tutorial merely by linking them.

  **Tester instructions:** Positive: each of four audiences reaches its expected artifacts using the README. Negative: required content only under the wrong audience, an omitted major artifact, or broken index fails. Edge: multi-audience documents and newly added nested files. Fixture: actual hub documentation inventory, not only the old RT-006 list.

  **Future command / completion:** Later inventory with `Get-ChildItem docs/disaster-response-hub -Recurse -File`, compare routes, and conduct AUD-013-015 discovery trials. Completion requires correct FR-006 group placement and explicit routes to the expanded artifact set.

### Validation and Amendment Evidence

- [ ] **AUD-013-013 (P2): Measure Overview, Quickstart, and Personas independently.**

  **Original obligations:** FR-015; NFR-003; SC-009; EC-01; CHK016; T004, T005, T006, T008, T027.

  **Expected / observed / impact:** Each section must score at or below unrounded 8.0. [RT-003](research.md#L67) defines the method, but [the sample](quickstart.md#L207) prints rounded whole-document FK. No inspected record gives current per-section scores. This audit does not assert a failing numeric FK score.

  **Developer instructions:** Define reproducible heading extraction and Markdown normalization, documenting code handling and retaining meaningful prose in tables/lists/expanded prerequisites. Pin the readability tool and retain normalized inputs, unrounded scores, revision, and reviewer observations. Improve wording without dropping safety or setup meaning.

  **Tester instructions:** Positive: all three section scores independently meet 8.0. Negative: 8.01/8.4 fails despite a passing whole-document average; missing/renamed section cannot pass as empty text. Edge: abbreviations, technical names, Unicode, details, tables, and multiline fences. Fixtures: normalized candidate text plus high-grade/missing-section mutations.

  **Future command / completion:** Proposed checker: `python tools/lint/check_root_readme.py --readability --sections overview,quickstart,personas --max-grade 8.0`, requiring future explicit installation/pinning of `textstat`. Completion requires three reproducible unrounded passing scores and non-technical review; portfolio rubric numbers do not satisfy this gate.

- [ ] **AUD-013-014 (P2): Obtain actual revision-specific GitHub rendering evidence.**

  **Original obligations:** FR-012, FR-017; NFR-004; SC-006; EC-02, EC-05; T023, T028, T029, T030.

  **Expected / observed / impact:** GitHub desktop/mobile should render valid source correctly. [README syntax](../../../README.md#L34) is balanced, but no inspected capture/session establishes actual diagram, table, anchor, and details behavior.

  **Developer instructions:** Keep descriptive summaries, blank-line boundaries, valid fences, expanded architecture/authority, and stable anchors through reordering. Define a small explicit browser/viewport matrix with readable raw Markdown fallback. Treat the plan's rendering statements as intent until observed.

  **Tester instructions:** Positive: diagram renders, all ten anchors navigate, all four details blocks toggle, and tables remain readable on desktop/mobile. Negative: malformed fence, missing blank boundary, duplicate heading, or hidden architecture fails. Edge: narrow viewport, long names, touch/keyboard navigation, and expanded prerequisites. Fixture: candidate README at an immutable revision URL.

  **Future command / completion:** After a future approved documentation-lint dependency is installed, run `pnpm exec markdownlint-cli2 README.md`, then inspect GitHub desktop/mobile manually. Completion requires dated browser/viewport/revision captures and explicit assertions; lint alone cannot close hosted-rendering acceptance.

- [ ] **AUD-013-015 (P2): Record newcomer timing and comprehension trials.**

  **Original obligations:** NFR-002; SC-001, SC-002, SC-003, SC-004; all independent story tests; T014, T019, T022, T031.

  **Expected / observed / impact:** Required outcomes are two-minute evaluator comprehension, three-minute developer comprehension, under-15-minute prerequisite-ready setup, 30-second five-link discovery, and 60-second role/authority discovery. Existing content/checkmarks do not demonstrate them.

  **Developer instructions:** Define unfamiliar-reader trials, questions, pass rules, machine/network assumptions, prerequisite-ready baseline, and no coaching. Record times, answers, blockers, revision, and actual consent/reviewer identity. Distinguish cold installation from prerequisite-ready timing. Fix setup/navigation before representing a trial as successful.

  **Tester instructions:** Positive: developer, evaluator, government, and operator participants correctly explain purpose/audience/structure/next step and meet applicable times. Negative: failed comprehension or requiring extra setup guidance fails regardless of elapsed time. Edge: mobile, non-technical readers, missing prerequisites, slow network, and reused versus clean environments. Fixtures: question script and a clean non-cloud setup.

  **Future command / completion:** A later observer can use `[System.Diagnostics.Stopwatch]::StartNew()` while following corrected instructions. Completion requires individual target-bound records with dates/roles/revision and honest residual failures, not timing inferred from line count.

- [ ] **AUD-013-016 (P2): Restore HYP-011's evidence contract and per-spec assessment.**

  **Original obligations:** Appended [HYP-011](../../013-root-readme/spec.md#L230), its evidence contract, consultation-on-every-change and per-spec uplift claim. T031 is an original final-review hook, not a historical task implementing this later addition.

  **Expected / observed / impact:** A matching evidence stub must exist and remain `Not tested` until supported. The named HYP-HYP-011 artifact is absent; the contract requires a co-located `HYP-011.md`. [Portfolio snapshots](../../028-capstone-alignment/evidence/rubric-postfeature.md#L23) do not establish this spec's uplift or consultation history.

  **Developer instructions:** Have the evidence/spec owner reconcile the pointer and contract. A proposed canonical home is `specs/013-root-readme/evidence/HYP-011.md`, not an existing file and not a duplicate under this historical task folder. Include all six headings, at least two preconditions, a bounded window, quantified falsification, owner link, and initial `Not tested`. Preserve the frozen baseline; require authentic consultation records and comparable per-spec scoring before any status transition.

  **Tester instructions:** Positive: ID, canonical filename, owner, headings, preconditions, and status align. Negative: doubled prefix, wrong owner, empty preconditions, aggregate-only score, fabricated consultation, or per-criterion regression cannot validate the hypothesis. Edge: renamed, genuinely untested, or explicitly retired stub with approved change control. Fixtures: current statement, evidence contract, authentic future records.

  **Future command / completion:** After the future stub exists, inspect `Get-Content specs/013-root-readme/evidence/HYP-011.md` and apply all six contract rules. Completion requires a resolving compliant stub and honest outcome status; it does not require manufacturing a validated hypothesis.

- [ ] **AUD-013-017 (P2): Reconcile persona validation with practitioner evidence.**

  **Original obligations:** Appended PER-031, PER-032, PER-033 and persona contract; original FR-005/US4 retain the narrower README table scope.

  **Expected / observed / impact:** Validated references require dated practitioner/SME evidence. [The amendment](../../013-root-readme/spec.md#L222) asserts validation, while [linked profiles](../../001-disaster-response-hub/spec.md#L169) defer concrete identities and use role labels. Actor definitions are not practitioner signatures. PER-033's D-009 country deferral must remain intact.

  **Developer instructions:** Map references to real profiles and signatures or explicitly retain unverified validation status. Require contract identity/role/date, representative scenarios, and unilateral/countersign boundaries. Distinguish technical persona agents from practitioners and runtime agents. Do not promote PH/JP/BD placeholders without actual approvals and precondition clearance.

  **Tester instructions:** Positive: each validated claim resolves to a profile and dated SME/practitioner evidence. Negative: proxy-only/role-only signature, AI output, missing dates, or one-sided authority cannot pass. Edge: technical persona outside natural AIIMS operator roles, grouped profiles, and a correctly deferred non-AU placeholder. Fixtures: current contract plus authentic future records.

  **Future command / completion:** Later compare `Select-String -Path specs/013-root-readme/spec.md,specs/001-disaster-response-hub/spec.md -Pattern 'PER-03','validated_by','authority_scope'`, then inspect resolved evidence. Completion requires truthful status and preserved scope, not invented reviewers or automatic international expansion.

- [ ] **AUD-013-018 (P3): Reconcile completion evidence without rewriting original records.**

  **Original obligations:** T008, T019, T020, T023, T024, T025, T026, T027, T028, T029, T030, T031; both checklists, plan gates, historical DoD.

  **Expected / observed / impact:** Completion should distinguish authored content, static checks, executions, and approvals at a revision. [Quality notes](../../013-root-readme/checklists/requirements.md#L34) contain stale counts; [comprehensive questions](../../013-root-readme/checklists/comprehensive.md#L1) and [DoD](quickstart.md#L230) are unchecked despite the task list's all-checked state. Current execution of those validation tasks is not established.

  **Developer instructions:** Add a separately owner-approved reconciliation record, preserving original task states/evidence. Map every original task, formal obligation, scenario, edge, and amendment to current evidence and unresolved conflicts. Explicitly choose authorities for ToC placement, raw/adjusted counts, and current constitution numbering. Keep agent-authored review separate from human approval and only close new tasks on actual acceptance evidence.

  **Tester instructions:** Positive: exact one-row original-task coverage, unchanged `[X]` states, concrete evidence, and honest follow-up statuses. Negative: omissions/duplicates, obsolete 15-FR/seven-SC counts, unexplained supersession, or treating this audit as a product test pass fails. Edge: amendments without original T IDs, skipped executions, external approvals pending. Fixtures: unchanged eight feature inputs and future evidence.

  **Future command / completion:** Apply text-only task-ID/state extraction and local-link checks to the future reconciliation artifact, then independent owner review. Completion requires a current evidence ledger with explicit limitations, not retrospective task ticking or source changes during this audit.

## Requirement and Success-Criterion Coverage

All **31** formal obligations are individually covered. Authored-content compliance is distinguished from measured outcomes and shared-code guarantees.

| ID | Status | Inspected evidence and qualification | Follow-up |
| --- | --- | --- | --- |
| FR-001 | IMPLEMENTED | [Overview](../../../README.md#L24) identifies the project, agents, and Australian context; fuller audience/readability obligations remain separate. | AUD-013-008, AUD-013-013 |
| FR-002 | PARTIAL | [Inline graph/link](../../../README.md#L34) exist; topology, 30-line task budget, and actual render need attention. | AUD-013-009, AUD-013-014 |
| FR-003 | CONFLICT | [Quickstart](../../../README.md#L102) has wrong package/entry-point instructions; added local seeding may touch cloud. Separate deployment subsection exists. | AUD-013-002, AUD-013-003 |
| FR-004 | PARTIAL | [Split prerequisite blocks](../../../README.md#L81) exist; numeric uv/Docker minima missing. | AUD-013-010 |
| FR-005 | IMPLEMENTED | [Role table/visible authority](../../../README.md#L145) authored; actual publication enforcement is a separate risk. | AUD-013-001 |
| FR-006 | PARTIAL | [Audience links](../../../README.md#L273) contain named artifacts but misplaced walkthrough, incomplete expanded inventory, and stale ADR link remain. | AUD-013-011, AUD-013-012 |
| FR-007 | IMPLEMENTED | [Five metrics](../../../README.md#L261) match [capstone](../../../capstone.md#L31) and are labelled goals. | - |
| FR-008 | PARTIAL | [Stack/region](../../../README.md#L235) present; current version and bounded residency context need synchronization. | AUD-013-009 |
| FR-009 | IMPLEMENTED | [Tree](../../../README.md#L190) includes required directories/core-agent homes; newer topology is separate. | AUD-013-009 |
| FR-010 | PARTIAL | [Contribution process](../../../README.md#L326) lacks commit/web-test guidance and conflicts with branch instructions. | AUD-013-006, AUD-013-007 |
| FR-011 | PARTIAL | [CI reference](../../../README.md#L349) is real; local equivalents/setup and added proof claims are incomplete. | AUD-013-004, AUD-013-005, AUD-013-006 |
| FR-012 | PARTIAL | GFM authored; [one internal target](../../../README.md#L368) broken and hosted rendering unverified. | AUD-013-011, AUD-013-014 |
| FR-013 | IMPLEMENTED | [Standalone callout](../../../README.md#L157) and [cross-reference](../../../README.md#L324) visible/resolving; text does not establish enforcement. | AUD-013-001 |
| FR-014 | PARTIAL | [Core descriptions](../../../README.md#L164) use agent terminology; visible summaries/count and current roster presentation need reconciliation. | AUD-013-008, AUD-013-009 |
| FR-015 | UNVERIFIED | No inspected separate FK measurements for [Overview](../../../README.md#L24), [Quickstart](../../../README.md#L77), and [Personas](../../../README.md#L145). | AUD-013-013 |
| FR-016 | CONFLICT | [Current order](../../../README.md#L11) differs from [specification](../../013-root-readme/spec.md#L150). | AUD-013-008 |
| FR-017 | PARTIAL | ToC/details exist, but [agent summaries](../../../README.md#L159) are not visible as required by tasks/model. | AUD-013-008, AUD-013-014 |
| NFR-001 | IMPLEMENTED | [README](../../../README.md#L1) has 382 raw lines; adjusted count cannot be larger. | - |
| NFR-002 | UNVERIFIED | Scannability/timing not measured; ordering is also wrong. | AUD-013-008, AUD-013-015 |
| NFR-003 | UNVERIFIED | No three unrounded scores; [whole-document snippet](quickstart.md#L215) cannot prove them. | AUD-013-013 |
| NFR-004 | PARTIAL | Four balanced labelled blocks with blank boundaries; [agent summary label](../../../README.md#L162) miscounts content and actual interaction unverified. | AUD-013-009, AUD-013-014 |
| SC-001 | UNVERIFIED | No two/three-minute unfamiliar-reader records. | AUD-013-015 |
| SC-002 | CONFLICT | [Incorrect startup](../../../README.md#L119) and absent timing cannot support under-15-minute setup. | AUD-013-002, AUD-013-015 |
| SC-003 | UNVERIFIED | Five required targets exist under [Documentation](../../../README.md#L273); no 30-second discovery measurement. | AUD-013-012, AUD-013-015 |
| SC-004 | PARTIAL | [Standalone authority/roles](../../../README.md#L145) present; 60-second government/practitioner result unverified. | AUD-013-001, AUD-013-015 |
| SC-005 | IMPLEMENTED | Ten content areas exist, including [CI/CD nested in Contributing](../../../README.md#L349); correctness/order are separate. | - |
| SC-006 | PARTIAL | Broken ADR target; actual GitHub/table/details render unverified. | AUD-013-011, AUD-013-014 |
| SC-007 | PARTIAL | 20/21 relative occurrences resolve; [ADR target](../../../README.md#L368) stale. Ten ToC anchors match headings. | AUD-013-011 |
| SC-008 | IMPLEMENTED | 382 raw lines, below 500. | - |
| SC-009 | UNVERIFIED | Overview/Quickstart scores not measured; union-scope requirement also includes Personas. | AUD-013-013 |
| SC-010 | IMPLEMENTED | Agent/runtime terms are used correctly; legitimate weather/Azure data services are not misuse. Roster/topology remains separate. | AUD-013-009 |

## Scenario Coverage

The acceptance IDs below refer to each story's original ordinal scenario, not new source IDs.

| Scenario | Status | Evidence / expected observation | Follow-up |
| --- | --- | --- | --- |
| US1-AS1 | IMPLEMENTED | [Overview](../../../README.md#L26) explains Australian multi-agent disaster coordination; reader comprehension remains separately unverified. | AUD-013-015 |
| US1-AS2 | IMPLEMENTED | [Documentation](../../../README.md#L273) directly links architecture, rubric, constitution, and specs. | AUD-013-012 |
| US1-AS3 | IMPLEMENTED | [AIIMS/authority](../../../README.md#L145) is visible; shared safeguard caveat applies. | AUD-013-001 |
| US2-AS1 | CONFLICT | [Startup](../../../README.md#L119) contradicts package and launcher source. | AUD-013-002 |
| US2-AS2 | PARTIAL | [Local checks](../../../README.md#L335) omit web tests/dev setup; no fresh-clone success evidence. | AUD-013-006 |
| US2-AS3 | PARTIAL | [Prerequisites](../../../README.md#L81) provide some versions/install links, not all numeric minima. | AUD-013-010 |
| US3-AS1 | IMPLEMENTED | [Agent tree](../../../README.md#L198) identifies individual core-agent homes. | AUD-013-009 |
| US3-AS2 | IMPLEMENTED | [Infrastructure tree](../../../README.md#L212) and region text identify Bicep/AU target. | AUD-013-009 |
| US3-AS3 | IMPLEMENTED | [Tree](../../../README.md#L190) identifies Web and shared UI package. | - |
| US4-AS1 | IMPLEMENTED | [Expanded authority callout](../../../README.md#L157) exists; enforcement/timing remain open. | AUD-013-001, AUD-013-015 |
| US4-AS2 | IMPLEMENTED | [Five-role table](../../../README.md#L149) maps functions to capabilities. | AUD-013-015 |
| US4-AS3 | IMPLEMENTED | [Constitution link](../../../README.md#L157) resolves. | AUD-013-009 |
| US5-AS1 | IMPLEMENTED | [Metrics](../../../README.md#L261) contain all five goals. | - |
| US5-AS2 | PARTIAL | [Stack/region](../../../README.md#L235) exists but version/topology is stale. | AUD-013-009 |
| US5-AS3 | PARTIAL | [CI link](../../../README.md#L349) exists; runtime-specific test guidance incomplete. | AUD-013-006 |
| US6-AS1 | CONFLICT | [README](../../../README.md#L328) and [CONTRIBUTING](../../../CONTRIBUTING.md#L8) disagree; no README commit expectations. | AUD-013-007 |
| US6-AS2 | PARTIAL | [Quality commands](../../../README.md#L335) omit complete per-runtime tests. | AUD-013-006 |
| US6-AS3 | IMPLEMENTED | [CI reference](../../../README.md#L349) describes real PR checks; hosted execution/required checks unverified. | AUD-013-005, AUD-013-006 |

| Independent story test | Status | Unverified or blocked observation | Follow-up |
| --- | --- | --- | --- |
| US1-IT | UNVERIFIED | Unfamiliar visitor answers purpose/audience/structure/next step within two minutes. [Source](../../013-root-readme/spec.md#L32). | AUD-013-008, AUD-013-015 |
| US2-IT | CONFLICT | Clean-machine three-runtime setup contradicted by current commands, with no timing record. [Source](../../013-root-readme/spec.md#L48). | AUD-013-002, AUD-013-015 |
| US3-IT | UNVERIFIED | Reader locates evacuation code, Bicep, and shared models using only the README. [Source](../../013-root-readme/spec.md#L64). | AUD-013-015 |
| US4-IT | UNVERIFIED | Emergency-management professional confirms role mapping and authority. [Source](../../013-root-readme/spec.md#L80). | AUD-013-001, AUD-013-015 |
| US5-IT | UNVERIFIED | Evaluator finds metrics, stack, and region within 60 seconds. [Source](../../013-root-readme/spec.md#L96). | AUD-013-009, AUD-013-015 |
| US6-IT | PARTIAL | Contribution rehearsal blocked by inconsistent branch/incomplete check guidance. [Source](../../013-root-readme/spec.md#L112). | AUD-013-006, AUD-013-007, AUD-013-015 |

| Edge case | Status | Evidence / gap | Follow-up |
| --- | --- | --- | --- |
| EC-01 | UNVERIFIED | Non-technical prose/FK8 has no measured or reader evidence. [Source](../../013-root-readme/spec.md#L124). | AUD-013-013, AUD-013-015 |
| EC-02 | UNVERIFIED | GitHub mobile rendering/details interaction lacks inspected capture. [Source](../../013-root-readme/spec.md#L125). | AUD-013-014 |
| EC-03 | IMPLEMENTED | Required main structure directories exist; new-role/topology drift is separately identified. [Source](../../013-root-readme/spec.md#L126). | AUD-013-009 |
| EC-04 | PARTIAL | Install links exist but minima/version-change compatibility is incomplete. [Source](../../013-root-readme/spec.md#L127). | AUD-013-010 |
| EC-05 | IMPLEMENTED | Mermaid outside details and balanced fenced tree supported by source; actual rendering separate. [Source](../../013-root-readme/spec.md#L128). | AUD-013-014 |
| EC-06 | IMPLEMENTED | [Standalone visible authority](../../../README.md#L157) exists; enforcement caveat remains. [Source](../../013-root-readme/spec.md#L129). | AUD-013-001 |

## Clarifications, Amendments, and Boundaries

| Item | Status | Disposition and evidence | Follow-up |
| --- | --- | --- | --- |
| CL-01 | CONFLICT | [Universal-first clarification](../../013-root-readme/spec.md#L12) does not match current heading/ToC order. | AUD-013-008 |
| CL-02 | PARTIAL | [Earlier after-overview ToC instruction](../../013-root-readme/spec.md#L13) is replaced for placement by later [FR-017](../../013-root-readme/spec.md#L151). Collapsibility exists but summaries/order remain incomplete. | AUD-013-008 |
| CL-03 | CONFLICT | [Local no-credentials decision](../../013-root-readme/spec.md#L14) not established by documented startup/local-seed behavior. | AUD-013-002, AUD-013-003 |
| CL-04 | IMPLEMENTED | [Mermaid decision](../../013-root-readme/spec.md#L15) reflected in inline graph/full-detail link; budget/current labels/render still need work. | AUD-013-009, AUD-013-014 |
| CL-05 | PARTIAL | [Audience and expanded artifact routing](../../013-root-readme/spec.md#L16) incomplete. | AUD-013-012 |
| CL-06 | UNVERIFIED | [FK8 decision](../../013-root-readme/spec.md#L20) has no actual scores. | AUD-013-013 |
| CL-07 | PARTIAL | [Length/timing decision](../../013-root-readme/spec.md#L21): 382 lines pass, timed comprehension not measured. | AUD-013-015 |
| CL-08 | PARTIAL | [Collapse choices](../../013-root-readme/spec.md#L22) are structurally present; visible summaries required by tasks/model missing. | AUD-013-008, AUD-013-014 |
| CHK016 resolution | IMPLEMENTED | [Plan](plan.md#L39) and current FR-015/NFR-003 establish union scope; SC-009 cannot waive Personas. | AUD-013-013 |
| CHK017 resolution | IMPLEMENTED | Local/deployment prerequisites split into two blocks; minima/command correctness remain separate. | AUD-013-002, AUD-013-010 |
| CHK018 resolution | IMPLEMENTED | [Primary statement](../../../README.md#L157) and [cross-reference](../../../README.md#L324) implement the resolved pattern. | AUD-013-001 |
| AM-01 meta scope | IMPLEMENTED | [Delivery-hygiene flag](../../013-root-readme/spec.md#L208) delegates capstone outcomes per [meta contract](../../028-capstone-alignment/contracts/meta-spec-flag.contract.md#L13). This review does not implement those outcomes. | - |
| PER-031 | PARTIAL | [Cross-reference](../../013-root-readme/spec.md#L222) and [operational profiles](../../001-disaster-response-hub/spec.md#L167) exist; full contract/detailed human validation not established. | AUD-013-017 |
| PER-032 | UNVERIFIED | [Technical-actor reference](../../013-root-readme/spec.md#L223) is authored; agent definitions are not practitioner validation. | AUD-013-017 |
| PER-033 | IMPLEMENTED | [PH/JP/BD placeholder](../../013-root-readme/spec.md#L224) keeps D-009/SME preconditions, consistent with [decision record](../../028-capstone-alignment/evidence/decision-record.md#L13). No implemented country support implied. | AUD-013-017 |
| HYP-011 | MISSING | [Named evidence stub](../../013-root-readme/spec.md#L230) absent after scoped relocation search; portfolio snapshots do not replace per-spec evidence. | AUD-013-016 |

Assumptions/dependencies: all required main directories, rubric, capstone, architecture, constitution, and CI file exist. The intended local path does not require Azure CLI. Reconcile the five-core-agent premise with extra agents and current dependencies with outdated Next.js/uv-workspace assumptions. [Constitution v1.2.0](../../../.specify/memory/constitution.md#L249) bounds the earlier region premise without waiving protected-data rules. Detailed API documentation, production runbooks, detailed protocols, infrastructure provisioning, automatic README generation, and badges remain outside this feature's delivery scope. Existing badges were not used as evidence of CI, licensing, or maturity.

## Exact Original Task Coverage

The local original [task list](tasks.md#L1) has **31 tasks**. This table contains **31 separate rows**, preserving every original `[X]` state. A checkmark is historical metadata, not an audit verdict; no task is collapsed into a range.

| Task | Original state | Original obligation | Status | Concrete evidence and gap | Follow-up |
| --- | --- | --- | --- | --- | --- |
| T001 | [X] | [Title and one-sentence description](tasks.md#L28) | IMPLEMENTED | [Root title/description](../../../README.md#L1) match identity. | - |
| T002 | [X] | [Ten-link ToC in mandated order](tasks.md#L29) | PARTIAL | [Ten anchors](../../../README.md#L11) resolve, but order differs from FR-016. | AUD-013-008 |
| T003 | [X] | [Ten H2 sections in order](tasks.md#L30) | PARTIAL | All headings exist; [Architecture](../../../README.md#L34) precedes Agents/Personas. | AUD-013-008 |
| T004 | [X] | [Overview, four audiences, constitution, FK8](tasks.md#L40) | PARTIAL | [Overview](../../../README.md#L24) and link exist; four-audience orientation not explicit and FK8 unverified. | AUD-013-008, AUD-013-013 |
| T005 | [X] | [Role table, standalone authority, constitution, FK8](tasks.md#L41) | PARTIAL | [Table/callout](../../../README.md#L145) exist; FK8 unverified and publication safeguard contradicts assurance. | AUD-013-001, AUD-013-013 |
| T006 | [X] | [Local three-runtime setup, deployment link, FK8](tasks.md#L42) | PARTIAL | [Commands/deploy subsection](../../../README.md#L102) exist; package/entry points wrong and readability unmeasured. | AUD-013-002, AUD-013-003, AUD-013-013 |
| T007 | [X] | [Collapsed local/Azure prerequisites](tasks.md#L43) | PARTIAL | [Split blocks](../../../README.md#L81) exist; Git minimum and numeric specificity incomplete. | AUD-013-010 |
| T008 | [X] | [Validate three FK scores](tasks.md#L44) | UNVERIFIED | No revision-specific section scores; [whole-doc sample](quickstart.md#L215) cannot establish gate. | AUD-013-013 |
| T009 | [X] | [Visible core-agent summaries/collapsed detail](tasks.md#L58) | PARTIAL | [Descriptions](../../../README.md#L159) all collapsed; sixth entry conflicts with five-agent label. | AUD-013-008, AUD-013-009 |
| T010 | [X] | [Three-runtime/five-agent graph at most 30 lines](tasks.md#L59) | PARTIAL | [Inline graph](../../../README.md#L36) outside details but 34 body lines/stale process and port labels. | AUD-013-009 |
| T011 | [X] | [Architecture context/full-doc link](tasks.md#L60) | PARTIAL | [Context/link](../../../README.md#L73) exist; independent-process wording disagrees with current dispatcher image. | AUD-013-009 |
| T012 | [X] | [Named audience-grouped documentation links](tasks.md#L61) | PARTIAL | [Documentation](../../../README.md#L273) misplaces operator walkthrough and omits expanded routes. | AUD-013-011, AUD-013-012 |
| T013 | [X] | [Authority cross-reference in Documentation](tasks.md#L62) | IMPLEMENTED | [Cross-reference](../../../README.md#L324) authored; safeguard caveat remains separate. | AUD-013-001 |
| T014 | [X] | [Verify exact fresh-clone commands](tasks.md#L76) | CONFLICT | [Invocations](../../../README.md#L126) differ from [API factory](../../../apps/api/app/main.py#L25) and [dispatcher](../../../apps/agents/dispatcher/__main__.py#L14); no setup execution proof. | AUD-013-002, AUD-013-015 |
| T015 | [X] | [Workflow, commits, per-runtime checks](tasks.md#L77) | PARTIAL | [Contributing](../../../README.md#L326) lacks complete checks/commits and conflicts with [canonical instructions](../../../CONTRIBUTING.md#L24). | AUD-013-006, AUD-013-007 |
| T016 | [X] | [CI reference, local tests/lint, PR checks](tasks.md#L78) | PARTIAL | [CI link](../../../README.md#L349) real; local check setup/depth and added proof claims incomplete. | AUD-013-004, AUD-013-005, AUD-013-006 |
| T017 | [X] | [Descriptive collapsed monorepo tree](tasks.md#L92) | IMPLEMENTED | [Tree](../../../README.md#L190) covers required app/package/infra/spec/test/doc/script homes. Extra-roster context separate. | AUD-013-009 |
| T018 | [X] | [Core stack, services, AU deployment target](tasks.md#L93) | PARTIAL | [Stack/region](../../../README.md#L235) present; Next.js 15 conflicts with [package pin](../../../apps/web/package.json#L29). | AUD-013-009 |
| T019 | [X] | [Review five roles/standalone authority](tasks.md#L107) | IMPLEMENTED | [Table/callout](../../../README.md#L149) meet content/placement test; human timed review not established. | AUD-013-001, AUD-013-015 |
| T020 | [X] | [Verify constitution link/consistent cross-reference](tasks.md#L108) | IMPLEMENTED | [Primary](../../../README.md#L157) and [cross-reference](../../../README.md#L324) resolve and agree textually; not proof of enforcement. | AUD-013-001 |
| T021 | [X] | [All five capstone targets/link](tasks.md#L122) | IMPLEMENTED | [Targets](../../../README.md#L263) match [capstone](../../../capstone.md#L31). | - |
| T022 | [X] | [Complete actionable contribution/check workflow](tasks.md#L136) | PARTIAL | [Workflow](../../../README.md#L328) incomplete and conflicts with CONTRIBUTING. | AUD-013-006, AUD-013-007 |
| T023 | [X] | [Details labels/blank-line formatting](tasks.md#L146) | IMPLEMENTED | Four balanced labelled blocks/blank boundaries in [README](../../../README.md#L81); label count and rendering separate. | AUD-013-009, AUD-013-014 |
| T024 | [X] | [Agent/runtime terminology](tasks.md#L147) | IMPLEMENTED | [Graph](../../../README.md#L38), [descriptions](../../../README.md#L164), [stack](../../../README.md#L239) use correct terms; data/weather services are legitimate. | AUD-013-009 |
| T025 | [X] | [All relative links resolve](tasks.md#L148) | PARTIAL | 20/21 relative occurrences resolve; [ADR target](../../../README.md#L368) moved. | AUD-013-011 |
| T026 | [X] | [500-line limit](tasks.md#L149) | IMPLEMENTED | [README](../../../README.md#L1) is 382 raw lines; historical measurement execution not inferred. | - |
| T027 | [X] | [Final three-section FK validation](tasks.md#L150) | UNVERIFIED | No current extraction/tool-version/unrounded-score record; aggregate sample inadequate. | AUD-013-013 |
| T028 | [X] | [Ten ToC anchors resolve](tasks.md#L151) | IMPLEMENTED | [Anchors](../../../README.md#L13) match H2 slugs including AIIMS double hyphen; order is a separate obligation. | AUD-013-008 |
| T029 | [X] | [Diagram expanded and rendered on GitHub](tasks.md#L152) | PARTIAL | [Placement](../../../README.md#L36) correct; hosted render unverified. | AUD-013-014 |
| T030 | [X] | [GitHub desktop/mobile rendering](tasks.md#L153) | UNVERIFIED | Source is not a browser record; details/table/Mermaid observations remain absent. | AUD-013-011, AUD-013-014 |
| T031 | [X] | [Final order/17-FR/ten-SC review](tasks.md#L154) | PARTIAL | Areas exist but startup/order/links/checks/measurements fail a complete verdict; later amendment gaps separate. | AUD-013-018 |

## Checklist and Design-Evidence Assessment

All 47 [comprehensive questions](../../013-root-readme/checklists/comprehensive.md#L1) remain originally unchecked. They are requirements-quality questions, not additional implementation tasks. Each is assessed here without changing its original state.

| Item | Assessment | Evidence / follow-up |
| --- | --- | --- |
| CHK001 | IMPLEMENTED | Ten areas have FR mappings; CI area is nested under Contributing whereas Agents is its own heading. AUD-013-018. |
| CHK002 | IMPLEMENTED | T004/model define overview language/context/audiences; delivery AUD-013-008, AUD-013-013. |
| CHK003 | IMPLEMENTED | T009 defines visible summaries versus detail; actual violation AUD-013-008. |
| CHK004 | IMPLEMENTED | T005/T019 enumerate five roles. |
| CHK005 | IMPLEMENTED | T018/model enumerate services; currency AUD-013-009. |
| CHK006 | PARTIAL | Commands present but complete per-runtime quality workflow missing. AUD-013-006. |
| CHK007 | PARTIAL | Existence required; moved references require correction. AUD-013-011. |
| CHK008 | PARTIAL | ToC target defined, not automated generation. AUD-013-008. |
| CHK009 | IMPLEMENTED | RT-001/T010 specify runtime/service scope and 30-line ceiling. AUD-013-009. |
| CHK010 | PARTIAL | Local/no-cloud intent defined but actual setup/stub acceptance unclear. AUD-013-002. |
| CHK011 | PARTIAL | Numeric examples exist; uv/Docker minima missing. AUD-013-010. |
| CHK012 | IMPLEMENTED | Three groups cover four audiences; government routing needs clarity. AUD-013-012. |
| CHK013 | IMPLEMENTED | T015/T022 scope includes branches, commits, PRs, checks. Delivery AUD-013-006, AUD-013-007. |
| CHK014 | IMPLEMENTED | CHK018/model define expanded standalone blockquote. |
| CHK015 | IMPLEMENTED | Research/model provide summary examples; count accuracy AUD-013-009. |
| CHK016 | IMPLEMENTED | Explicit union resolution; measurement AUD-013-013. |
| CHK017 | IMPLEMENTED | Explicit local/Azure split resolution. |
| CHK018 | IMPLEMENTED | Primary authority/cross-reference pattern present. |
| CHK019 | PARTIAL | Defined summary/detail distinction not delivered. AUD-013-008. |
| CHK020 | IMPLEMENTED | Terminology/RT-007 explicitly distinguish README runtime wording from older architecture. |
| CHK021 | PARTIAL | Two ten-area lists group Agents/CI differently; CI nested, not extra H2. AUD-013-018. |
| CHK022 | UNVERIFIED | Controlled comprehension protocol/results absent. AUD-013-015. |
| CHK023 | UNVERIFIED | Setup timing needs working commands and explicit baseline. AUD-013-002, AUD-013-015. |
| CHK024 | UNVERIFIED | No timed five-link discovery. AUD-013-015. |
| CHK025 | IMPLEMENTED | Standalone expanded blockquote defined/present. |
| CHK026 | IMPLEMENTED | RT-003 chooses textstat; actual correct measurement AUD-013-013. |
| CHK027 | IMPLEMENTED | V-004 uses contextual agent/runtime terminology inspection. |
| CHK028 | PARTIAL | V-003 file/V-008 ToC checks split; fragment-aware follow-up AUD-013-011. |
| CHK029 | PARTIAL | Six stories cover four audiences; visibility/routes incomplete. AUD-013-008, AUD-013-012. |
| CHK030 | PARTIAL | Docs branch exists; coherent full path still AUD-013-007. |
| CHK031 | PARTIAL | Plan names VS Code preview; normative target GitHub. Raw fallback AUD-013-014. |
| CHK032 | PARTIAL | Drift demonstrates maintenance risk; no automatic README generation added. AUD-013-009, AUD-013-018. |
| CHK033 | IMPLEMENTED | RT-002/edge/model define fence and blank-line handling; render AUD-013-014. |
| CHK034 | PARTIAL | Planned notation required, no fixed syntax; current main directories exist. AUD-013-009. |
| CHK035 | PARTIAL | No complete minimum-version/support/change matrix. AUD-013-010. |
| CHK036 | IMPLEMENTED | FR-017 keeps architecture outside details. |
| CHK037 | CONFLICT | NFR-001 adjusted versus SC-008/V-001 raw count; 382 passes both. Record both. AUD-013-018. |
| CHK038 | UNVERIFIED | Scannability needs actual reader timing. AUD-013-015. |
| CHK039 | IMPLEMENTED | RT-003 forbids rounding above 8.0; whole-doc sample insufficient. AUD-013-013. |
| CHK040 | UNVERIFIED | No mobile platform/viewport observation record. AUD-013-014. |
| CHK041 | PARTIAL | FR-006 files exist; RT-006 is not ongoing validation. AUD-013-011. |
| CHK042 | IMPLEMENTED | CI exists/linked; hosted execution/required-check configuration unverified. |
| CHK043 | CONFLICT | Five-core premise versus sixth description and current dispatcher roles. AUD-013-009. |
| CHK044 | PARTIAL | Dependencies evolve independently; constitution/versions/ADR movement illustrate drift. AUD-013-009, AUD-013-011. |
| CHK045 | IMPLEMENTED | Ten SCs individually traced here with unverified outcomes retained. |
| CHK046 | IMPLEMENTED | All 18 acceptance scenarios individually traced. |
| CHK047 | IMPLEMENTED | All six stories have FR-backed content and independent-test dispositions. |

### Research, Validation Rules, and Review Claims

| Artifact obligation | Current assessment |
| --- | --- |
| RT-001 / V-007 | Mermaid outside details authored; 34 lines exceed T010; hosted render unverified. |
| RT-002 / V-006 | Four labelled details blocks have blank boundaries; count/visibility and rendering separate. |
| RT-003 / V-002 | Strict textstat union scope defined; no current three-section execution evidence. |
| RT-004 | Prerequisite split present; numeric minima, package setup, and safe local-seeder behavior incomplete. |
| RT-005 / V-005 | Expanded primary authority/cross-reference present; not proof of enforced human authorization. |
| RT-006 / V-003 | Required historical targets exist; a current added target is stale. Old existence checks do not certify today's document. |
| RT-007 / V-004 | Agent/runtime wording correct; roster/version/topology drift remains. |
| RT-008 / V-001 | 382 raw lines pass; 420-480 is a target estimate, not a floor. Details do not remove source lines. |
| V-008 | Ten anchors match headings; that does not establish mandated order. |
| Plan constitution gate | Authored PASS table with older six-principle structure, not security review or current constitutional conformance evidence. |
| Requirements checklist | 16 checked authoring items; old counts/named agent feedback do not establish implementation or human approval. |
| Historical DoD | 11 unchecked items; artifact presence does not retrospectively complete them. |
| Feature-028 snapshots/decision | Authored portfolio assessment from 1.8 to 3.8, not this spec's HYP-011 consultation/uplift or practitioner signatures; D-009 remains deferred. |
| Linked demo/evaluation material | [Walkthrough](../../../docs/disaster-response-hub/demo/walkthrough.md#L1) has screenshot placeholders; [executive deck](../../../docs/disaster-response-hub/demo/executive-deck.md#L42) lists further validation. Authored collateral is not proof of README story-test execution. |

## Future Validation and Closure Rules

Every command in this report is **future-only remediation/review guidance**, not an execution claimed by the audit. Use a disposable clone at the candidate revision with an explicit Python environment, API/agent and test dependencies, pnpm 10.6.3, supported Node, and PowerShell where applicable. Browser checks require installed Chromium and exclusively local API/Web instances. Pin and install documentation/readability tools deliberately; the proposed README checker does not yet exist. Never use inherited Azure credentials/endpoints, `azd` environment selection, or production test-support flags as local fixtures.

Expected closure gates: correct package/module resolution; defined local/degraded responses; denied unsafe publication and implicit cloud writes; truthful test/proof scope; complete per-runtime checks; consistent contributor instructions; exact order/visibility/terminology; zero broken internal links; raw and adjusted source counts at most 500; at most 30 Mermaid body lines; three unrounded FK scores at most 8.0; dated desktop/mobile observations; and specified reader timing/practitioner evidence. Missing tools, empty test selection, skipped probes, warnings, and synthetic green samples do not establish a completed gate.

Report-authoring integrity is validated separately by text-only exact original-task/state coverage, unique requirement/scenario/amendment IDs, unchecked follow-up IDs, rebased local path/line-link resolution, and editor diagnostics. These checks establish this report's integrity only. Original implementation completion, clean-machine execution, cloud readiness, measurements, and external approvals remain limited exactly as recorded above.
