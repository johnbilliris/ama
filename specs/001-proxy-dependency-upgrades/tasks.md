# Tasks: Proxy-Constrained Dependency Upgrades

**Input**: Approved design documents in `C:\code\ama\specs\001-proxy-dependency-upgrades\`  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, `evidence.md`, `.specify\memory\constitution.md`, and `checklists\implementation-readiness.md`  
**Contracts**: No `contracts\` directory or new interface is in scope; use existing repository tests and workflow contracts.

**Execution boundary**: This is the Phase 5 task plan only. All execution tasks below require the later human implementation/validation authorization applicable to them. This document does not authorize dependency or workflow edits now, installation, PR lifecycle operations, workflow dispatch, commit, push, merge, publication, or deployment. Do not remove or weaken a policy hold to make a task pass. A blocked task may be cleared only by the evidence or separately approved policy resolution named in that task.

**Planning status**: The 33 PRs and 31 work items below are the fixed supplied inventory and approved research reconciliation. The P/F/R/H entries and candidate versions are planning directions only; none is a final delivery outcome. Planning retrievals are not complete artifact closure, clean-install evidence, compatibility proof, security clearance, or a test pass.

## Frozen PR and Work-Item Traceability

This register preserves the work-item IDs, scope identities, PR links, and requested targets from `research.md` R1 and `spec.md` “Supplied PR Baseline”. Scope abbreviations follow `research.md`: NW = web importer in the single root `pnpm-lock.yaml`; NU = UI importer in that same lock; PR = root `uv.lock`; PA = `apps\agents\uv.lock`; AC = active GitHub Actions references. P = proposed-target direction, F = tentative library fallback, R = retain/supersede direction, H = hold. These are provisional, not verified outcomes.

| Work item | Independent scope | Supplied PR reference(s) and preserved target(s) | Plan direction |
|---|---|---|---|
| NW-next | `apps\web` importer / root `pnpm-lock.yaml` | [#149](https://github.com/johnbilliris/ama/pull/149) `16.3.6 → 16.3.8`; [#133](https://github.com/johnbilliris/ama/pull/133) `16.2.6 → 16.2.11`; [#132](https://github.com/johnbilliris/ama/pull/132) `16.2.6 → 16.2.11` | P: `16.3.8`; preserve all three targets |
| NW-eslint | `apps\web` importer / root `pnpm-lock.yaml` | [#150](https://github.com/johnbilliris/ama/pull/150) `9.39.4 → 10.12.0` | H: B-ESLINT |
| NW-jsdom | `apps\web` importer / root `pnpm-lock.yaml` | [#148](https://github.com/johnbilliris/ama/pull/148) `25.0.1 → 30.1.2` | F: tentative `30.1.1`, subject to final eligibility |
| NW-playwright | `apps\web` importer / root `pnpm-lock.yaml` | [#147](https://github.com/johnbilliris/ama/pull/147) `1.59.1 → 1.63.0` | P: keep `@playwright/test`, `playwright`, and `playwright-core` coupled |
| NW-node-types | `apps\web` importer / root `pnpm-lock.yaml` | [#146](https://github.com/johnbilliris/ama/pull/146) `22.13.10 → 26.6.4` | H: B-TYPES |
| NW-msal-react | `apps\web` importer / root `pnpm-lock.yaml` | [#144](https://github.com/johnbilliris/ama/pull/144) `5.3.2 → 5.7.2` | H: B-MSAL |
| NW-js-yaml | `apps\web` importer / root `pnpm-lock.yaml` | [#137](https://github.com/johnbilliris/ama/pull/137) `4.1.1 → 4.3.1` | P: `4.3.1` |
| NU-next | `packages\ui` importer / root `pnpm-lock.yaml` | [#130](https://github.com/johnbilliris/ama/pull/130) `15.5.18 → 15.5.21` | P: `15.5.21`; do not normalize to web Next 16 |
| PR-cryptography | Root Python resolution / `uv.lock` | [#135](https://github.com/johnbilliris/ama/pull/135) `46.0.7 → 50.0.0` | R: retain `50.0.1` and `cryptography >=50.0.0,<51` |
| PA-h2 | Agents Python resolution / `apps\agents\uv.lock` | [#136](https://github.com/johnbilliris/ama/pull/136) `4.3.0 → 4.4.1` | P: `h2 4.4.1` with required `hpack 4.2.0` |
| PR-idna | Root Python resolution / `uv.lock` | [#111](https://github.com/johnbilliris/ama/pull/111) `3.11 → 3.15` | P: `3.15` in root only |
| PA-aiohttp | Agents Python resolution / `apps\agents\uv.lock` | [#134](https://github.com/johnbilliris/ama/pull/134) `3.13.5 → 3.14.3` | R: exact target already locked; completion unverified |
| PR-msgpack | Root Python resolution / `uv.lock` | [#121](https://github.com/johnbilliris/ama/pull/121) `1.1.2 → 1.2.1` | R: retain `1.2.2` |
| PR-pyjwt | Root Python resolution / `uv.lock` | [#116](https://github.com/johnbilliris/ama/pull/116) `2.12.1 → 2.13.0` | R: retain `2.15.0` and `pyjwt >=2.14.0,<3` |
| PR-engineio | Root Python resolution / `uv.lock` | [#124](https://github.com/johnbilliris/ama/pull/124) `4.13.1 → 4.13.2` | R: retain `4.14.0`; planning retrieval included a failed attempt and successful retry |
| PR-socketio | Root Python resolution / `uv.lock` | [#123](https://github.com/johnbilliris/ama/pull/123) `5.16.1 → 5.16.2` | R: retain `5.17.0` and its engineio relationship |
| PA-setuptools | Agents Python resolution / `apps\agents\uv.lock` | [#129](https://github.com/johnbilliris/ama/pull/129) `82.0.1 → 83.0.0` | P: `83.0.0`; keep root `84.0.0` distinct |
| PA-pyasn1 | Agents Python resolution / `apps\agents\uv.lock` | [#128](https://github.com/johnbilliris/ama/pull/128) `0.6.3 → 0.6.4` | R: exact target already locked; completion unverified |
| PA-mcp | Agents Python resolution / `apps\agents\uv.lock` | [#127](https://github.com/johnbilliris/ama/pull/127) `1.27.1 → 1.28.1` | R: retain `1.30.0` |
| PA-socketio | Agents Python resolution / `apps\agents\uv.lock` | [#126](https://github.com/johnbilliris/ama/pull/126) `5.16.1 → 5.16.2` | R: retain `5.17.0`, independent of PR #123 |
| PA-engineio | Agents Python resolution / `apps\agents\uv.lock` | [#125](https://github.com/johnbilliris/ama/pull/125) `4.13.1 → 4.13.2` | R: retain `4.14.0`, independent of PR #124 |
| PA-idna | Agents Python resolution / `apps\agents\uv.lock` | [#112](https://github.com/johnbilliris/ama/pull/112) `3.11 → 3.15` | P: `3.15`, separate from root PR #111 |
| PA-starlette | Agents Python resolution / `apps\agents\uv.lock` | [#120](https://github.com/johnbilliris/ama/pull/120) `1.0.0 → 1.3.1` | R: retain `1.7.0`; do not downgrade |
| PA-pyjwt | Agents Python resolution / `apps\agents\uv.lock` | [#115](https://github.com/johnbilliris/ama/pull/115) `2.12.1 → 2.13.0` | R: retain `2.15.0` and `PyJWT[crypto] >=2.14.0,<3` |
| PA-settings | Agents Python resolution / `apps\agents\uv.lock` | [#122](https://github.com/johnbilliris/ama/pull/122) `2.14.1 → 2.14.2` | P: `2.14.2`; keep root `2.15.0` distinct |
| PA-multipart | Agents Python resolution / `apps\agents\uv.lock` | [#117](https://github.com/johnbilliris/ama/pull/117) `0.0.28 → 0.0.31` | R: retain `0.0.32` |
| AC-checkout | Active `actions/checkout` references | [#145](https://github.com/johnbilliris/ama/pull/145) `v4 → v7`; verified proposed full SHA `3d3c42e5aac5ba805825da76410c181273ba90b1` | P: proposed SHA; 42 active uses require runner and behavior checks |
| AC-upload | Active `actions/upload-artifact` references | [#143](https://github.com/johnbilliris/ama/pull/143) `v4 → v6`; verified proposed full SHA `b7c566a772e6b6bfb58ed0dc250532a479d7789f` | P: retain six already matching uses; assess the other four |
| AC-gitleaks | Active `gitleaks/gitleaks-action` reference | [#105](https://github.com/johnbilliris/ama/pull/105) `dcedce43c6f43de0b836d1fe38946645c9c638dc → ff98106e4c7b2bc287b24eaf42907196329070c7` | H: B-ACTION-BASE; proposed source is not baseline provenance |
| AC-cosign | Active `sigstore/cosign-installer` reference | [#103](https://github.com/johnbilliris/ama/pull/103) `f713795cb21599bc4e5c4b58cbad1da852d7eeb9 → 398d4b0eeef1380460a10c8013a76f728fb906ac` | H: B-ACTION-BASE and required asset/signature evidence |
| AC-comment | Active `peter-evans/create-or-update-comment` reference | [#102](https://github.com/johnbilliris/ama/pull/102) `v4 → v5`; verified proposed full SHA `e8674b075228eee787fea43ef493e45ece1004c9` | P: proposed SHA; no live comment test |

**Inventory invariant**: 33/33 included PRs (10 npm, 18 Python, five Actions), 31 scope-aware work items, and provisional directions P=12, F=1, R=15, H=5. Do not delete duplicate PR entries, merge root/agents or web/UI scopes, or treat a planning direction as a final outcome.

## Format and Path Conventions

Every task line uses `- [ ] Tnnn [P?] [USn?] Description with file path`. `[P]` is present only for the three tasks in the explicitly marked parallel group below. User-story tasks carry exactly one `[US1]`–`[US4]` label; Setup, Foundational, and Polish tasks do not. All file paths are rooted at `C:\code\ama`. No test framework, dependency service, new API, or persistence layer is introduced.

---

## Phase 1: Setup

**Purpose**: Freeze the approved inputs and the real validation environments before any future authorized edit.

<!-- sequential -->
- [ ] T001 Compare the execution-start `git rev-parse HEAD` with baseline `62d249dc1205644fed934ea167df56695e92b3d2`; re-hash the dependency manifests, lockfiles, workflow files, and source-policy inputs recorded in `evidence.md` E0; recheck only the 33 linked PR heads/bases/files in the traceability register against `evidence.md` E1. Preserve the original observations, append any changed head/base or local-input drift as a new observation in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`, and stop for an explicit scope decision if inputs drift; do not broaden PR discovery or perform remote mutations.

<!-- sequential -->
- [ ] T002 Build and record the exact supported-environment matrix from `C:\code\ama\specs\001-proxy-dependency-upgrades\plan.md` and `quickstart.md` in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`: Node 24 web/UI workspace, Alpine web, the actual devcontainer architecture, Python 3.12 Linux root, Python 3.12 Windows x64 `windows-ci`, standalone agents, each affected Linux pip/helper/container recipe, and each affected Action runner. Record exact runtime/tool versions, OS, architecture, libc/base-image digest, importer/lock or unlocked recipe, extras/markers, and effective source settings. Do not use the inspected Windows ARM64/Python 3.14 host as CI evidence or assume the image/runner version.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish clean-source and true-consumer baselines before version edits. These gates block dependent work; they are not policy waivers.

<!-- sequential -->
- [ ] T003 **GATED — B-SOURCE-ENV (root npm policy)**. After explicit implementation authorization, create only the minimal credential-free `C:\code\ama\.npmrc` containing `registry=https://packagefeedproxy.microsoft.io/npm/`. Do not add credentials, a public-source fallback, or unrelated settings, and do not modify workflow or devcontainer files in this task. Record the file hash and intended source policy in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; this configuration alone does not close B-SOURCE-ENV.

<!-- sequential -->
- [ ] T004 **GATED — B-SOURCE-ENV (GitHub workflow npm boundaries)**. After T003, propagate `NPM_CONFIG_REGISTRY=https://packagefeedproxy.microsoft.io/npm/` to each actual npm/pnpm retrieval, install, or package-manager bootstrap boundary in `C:\code\ama\.github\workflows\ci.yml`, `C:\code\ama\.github\workflows\spec-035-gate.yml`, and `C:\code\ama\.github\workflows\cd.yml`; do not add a no-op setting if a `cd.yml` step does not use the registry, but record the boundary review in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Preserve all other workflow files unless a separately evidenced in-scope npm boundary is found and recorded before editing. Preserve triggers, permissions, runner labels, and all Action references; do not change Action pins in this task. Record the exact affected jobs and source-setting results.

<!-- sequential -->
- [ ] T005 **GATED — B-SOURCE-ENV (devcontainer npm boundary)**. After T004, set `NPM_CONFIG_REGISTRY=https://packagefeedproxy.microsoft.io/npm/` for the frozen pnpm install in `C:\code\ama\.devcontainer\devcontainer.json` so the post-create command uses the approved proxy. Preserve the existing proxy settings in `C:\code\ama\.devcontainer\Dockerfile` and `C:\code\ama\compose.yaml`; do not add credentials or a public fallback. Record the configuration and effective source-setting check in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; keep B-SOURCE-ENV open if any relevant boundary or actual artifact host remains unverified.

<!-- sequential -->
- [ ] T006 **GATED — B-CONSUMER-BASE**. Planning did not establish installed baselines or repeatability for affected pip/helper/container recipes; a `uv.lock` cannot prove their resolution. Before dependency edits, reproduce and record the actual baseline resolutions for every affected consumer using its checked-in recipe: `C:\code\ama\.github\workflows\ci.yml`, `eval-pr-gate.yml`, applicable `spec\*.yml` and other affected workflow recipes; `C:\code\ama\scripts\install_pyproject_dependencies.py`; `C:\code\ama\apps\api\Dockerfile`, `apps\agents\Dockerfile`, `apps\ingestion\Dockerfile`, `apps\ingest-runner\Dockerfile`, `apps\eval-runner\Dockerfile`; and `C:\code\ama\.devcontainer\install-python-dependencies.py`. Record separate recipe/environment IDs and installed maps in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Preserve independently newer results; do not impose root pins, add a global constraints file, or convert consumers to uv. Leave B-CONSUMER-BASE blocking any unresolved consumer decision.

<!-- sequential -->
- [ ] T007 Run the applicable repository quality checks against the unchanged, frozen baseline in the environments assigned by `C:\code\ama\specs\001-proxy-dependency-upgrades\quickstart.md` §4; record exact commands, selectors, versions, exit/status, and failure fingerprints in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Classify each as `passed`, `failed`, `blocked`, `not-run`, or justified `not-applicable`; do not waive a pre-existing failure, infer a pass from a skipped credentialed test, or start version edits until required baseline/source gates are evidenced.

**Checkpoint**: T003–T005 establish the scoped npm proxy settings; T006–T007 establish affected consumer baselines and unchanged-baseline check status. Do not close B-SOURCE-ENV from configuration alone: record approved-source behavior and keep any unverified boundary or artifact host blocked. If an environment, feed, baseline, or required tool is unavailable, record the concrete hold and block only its dependent scope; do not substitute a different environment.

---

## Phase 3: User Story 1 — Account for Every Upgrade Chore (Priority: P1) 🎯 MVP

**Goal**: Preserve every supplied PR and its own target, scope, current resolution, and work-item outcome.

**Independent Test**: A second maintainer can count 33 linked PR rows mapped to exactly 31 IDs, verify the three distinct Next proposals retained under NW-next, and identify every independent lock/importer/Action decision without any dependency edits.

<!-- sequential -->
- [ ] T008 [US1] Audit the frozen register above against `C:\code\ama\specs\001-proxy-dependency-upgrades\research.md` R1 and `spec.md` “Supplied PR Baseline”; preserve all 33 links, targets, and the 31 exact work-item IDs. Confirm the 33-to-31 map and P/F/R/H counts in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; log head or scope drift without overwriting the original snapshot or silently changing the denominator.

<!-- sequential -->
- [ ] T009 [US1] Revalidate the actual resolved baseline and independent scope for every work item against `C:\code\ama\package.json`, `apps\web\package.json`, `packages\ui\package.json`, `pnpm-lock.yaml`, `pyproject.toml`, `uv.lock`, `apps\agents\pyproject.toml`, `apps\agents\uv.lock`, `apps\api\uv.lock`, and `tools\specify-cli\uv.lock`; record actual resolutions and protected scopes in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Keep web Next 16 separate from UI Next 15, root Python separate from agents, and API/specify-cli locks protected; a declaration range or old PR base is not a resolved baseline.

<!-- sequential -->
- [ ] T010 [US1] Enumerate all 55 active Action occurrences across the 25 workflows from the current YAML in `C:\code\ama\.github\workflows\*.yml`, excluding comments/dormant steps; record workflow/job/step, baseline ref, runner, and proposed work item in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Reconcile 42 checkout references, ten upload-artifact references (six already at target), and one each for gitleaks, cosign, and comment; do not rely only on the old PR patch file list.

**Checkpoint**: Story 1 is independently accounted for only when all 33 PRs link to one of the 31 IDs and every distinct resolution context remains separately named.

---

## Phase 4: User Story 2 — Choose an Obtainable, Compatible Version (Priority: P1)

**Goal**: Revalidate approved-source availability, artifact integrity, runtime compatibility, security, and version ordering for all 31 work items without turning access failure into absence.

**Independent Test**: Evidence distinguishes retrieved artifacts, missing required files, incompatible files, trustworthy absence, and access-unavailable/unknown; a reviewer independently reproduces the exact-target/fallback/Action decision or the explicit hold.

<!-- sequential -->
- [ ] T011 [US2] Re-fetch npm metadata and every required candidate, companion, native, and transitive artifact for NW-next, NW-eslint, NW-jsdom, NW-playwright, NW-node-types, NW-msal-react, NW-js-yaml, and NU-next using only `https://packagefeedproxy.microsoft.io/npm/`; record artifact identity, exact URL/final host, retrieval time, checksum provenance/result, platform/engine/peer data, and classification in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Cover Next/@next/env/SWC/sharp and PostCSS relationships, jsdom’s Node `>=24.15.0` patch requirement, the Playwright trio plus browser/OS artifacts, the full MSAL companion graph, and ESLint peer ranges. Preserve stronger existing lock integrity where proxy metadata is SHA-1-only; local SHA-256 is not stronger publisher provenance. Treat browser CDN/source-policy gaps as blockers, not implicit permission.

<!-- sequential -->
- [ ] T012 [US2] Re-fetch and validate the root and agents Python candidate and retained package files for PR-cryptography, PR-idna, PR-msgpack, PR-pyjwt, PR-engineio, PR-socketio, PA-h2, PA-aiohttp, PA-setuptools, PA-pyasn1, PA-mcp, PA-socketio, PA-engineio, PA-idna, PA-starlette, PA-pyjwt, PA-settings, and PA-multipart from only `https://packagefeedproxy.microsoft.io/pypi/simple`; record file tags, Requires-Python, integrity, markers/extras, source, environment, and result in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Cover the actual supported Python 3.12 platforms and native wheels, h2/hpack compatibility, settings dependencies, and the separate root/agents resolutions. Retain `cryptography >=50.0.0,<51`, both PyJWT `>=2.14.0,<3` protections, redis-entraid and mem0ai exceptions, and all newer baselines; do not use public PyPI or assume a wheel sample proves full install closure.

<!-- sequential -->
- [ ] T013 [US2] Revalidate official repository identity, full proposed commit SHA, tree/source-blob identity, release ordering/ancestry, required assets, runner compatibility, and retrieval/integrity for AC-checkout, AC-upload, AC-gitleaks, AC-cosign, and AC-comment; bind results to active references from `C:\code\ama\.github\workflows\*.yml` in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Use official GitHub sources only for Actions; never infer SHA age lexically or from timestamps. Verify runner minimums and checkout fork/credential behavior without executing a live comment, publish, signing, or deployment side effect.

<!-- sequential -->
- [ ] T014 [US2] **BLOCKED — B-ESLINT / PR [#150](https://github.com/johnbilliris/ama/pull/150)**. Keep NW-eslint at its verified baseline and leave the work item incomplete: target `10.12.0` was absent at the planning observation, and researched `10.11.0` conflicts with the available Next lint-plugin peer families. Clear only with new approved-proxy evidence of an eligible, compatible candidate or a separately approved bounded scope/spec change; do not use a major-9 fallback, replace peer families broadly, or weaken lint rules. Record the concrete evidence and next owner/action in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; downstream NW-eslint completion and whole-batch readiness remain gated.

<!-- sequential -->
- [ ] T015 [US2] **BLOCKED — B-TYPES / PR [#146](https://github.com/johnbilliris/ama/pull/146)**. Keep NW-node-types unchanged until an explicit Node 24 runtime/type-surface compatibility assessment and required test evidence exist; archive retrieval alone is insufficient. Do not migrate runtime to Node 26 or invent a major-24 fallback. Record evidence, owner, and next action in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; NW-node-types completion and whole-batch readiness remain gated.

<!-- sequential -->
- [ ] T016 [US2] **BLOCKED — B-MSAL / PR [#144](https://github.com/johnbilliris/ama/pull/144)**. Keep NW-msal-react unchanged until trustworthy approved-proxy retrieval and integrity evidence resolves required `@azure/msal-common@16.14.2` and the complete browser/react companion graph. Repeated access failures or one 404 endpoint are not proof of absence; do not use public npm or downgrade React to force a selection. Record evidence, owner, and next action in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; NW-msal-react completion and whole-batch readiness remain gated.

<!-- sequential -->
- [ ] T017 [US2] **BLOCKED — B-ACTION-BASE / PR [#105](https://github.com/johnbilliris/ama/pull/105)**. Do not change the active gitleaks pin: the current full-SHA baseline is unresolvable in the official upstream evidence and the proposed source/binary alone cannot prove no-downgrade ordering. Require authoritative baseline provenance or a separately approved policy resolution, then revalidate the official proposed SHA and required gitleaks asset/checksum. Record the hold and owner/action in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; AC-gitleaks and whole-batch readiness remain gated.

<!-- sequential -->
- [ ] T018 [US2] **BLOCKED — B-ACTION-BASE / PR [#103](https://github.com/johnbilliris/ama/pull/103)**. Do not change the active cosign pin while the existing full-SHA baseline remains unresolvable; additionally keep the required asset/signature gate open. Retrieve and verify the pinned bootstrap v2.5.2 binary against recorded SHA-256 `bcfeae05557a9f313ee4392d2f335d0ff69ebbfd232019e3736fb04999fe1734`, plus the explicitly requested v2.4.1 `cosign-linux-amd64`, detached signature, and `release/release-cosign.pub` (including recorded key hash and signature result), using official upstream sources. These planning hashes are expected verification inputs, not successful asset results. No publication/signing is authorized. Record the hold in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md` and leave checklist CHK027/CHK028 open until their evidence gates pass.

<!-- sequential -->
- [ ] T019 [US2] **PROVISIONAL INVENTORY ONLY**. Reconcile the 31 work items against the revalidated baselines and T011–T018 observations; record each PR-to-work-item link, target, verified baseline, candidate set, provisional candidate/retain direction, rejected alternatives, approved source, rationale, and evidence gaps in `C:\code\ama\specs\001-proxy-dependency-upgrades\research.md` and `evidence.md`. For a library fallback, record the candidate ordering and the policy checks (stable, same major as target, strictly below target, above baseline, and highest eligible/retrievable/secure candidate); for Actions record only the proposed full SHA or a verified newer existing baseline. Label every proposed or retain/supersede direction provisional; do not finalize a retained/superseded outcome, claim final retrieval/compatibility/security/installation/validation, or convert P/F/R/H into completion here. Final outcomes are reconciled only by T046 after the required evidence tasks. Keep every unresolved row blocked/incomplete.

**Checkpoint**: T019 is a provisional candidate inventory only; it cannot close B-SOURCE-ENV, B-CONSUMER-BASE, B-ESLINT, B-TYPES, B-MSAL, B-ACTION-BASE, or artifact-closure issues, nor finalize any PR outcome. All 33 PRs remain provisional/incomplete until the applicable evidence is complete and T046 reconciles the outcome; no hold is removed by counting or consolidating work.

---

## Phase 5: User Story 3 — Preserve a Consistent, Secure Dependency Baseline (Priority: P1)

**Goal**: Apply only evidence-cleared, scope-specific changes; keep every declaration, resolution, Action pin, and security constraint consistent without unrelated churn or downgrade.

**Independent Test**: Compare pre/post declarations, importer and marker-specific resolved maps, all affected independent consumer maps, Action SHAs, and protected inputs. Confirm no downgrade, weakened override/check, global normalization, or unapproved change; held work items remain explicitly incomplete.

<!-- sequential -->
- [ ] T020 [US3] **GATED**. Before any version-file edit, build the execution allowlist from the provisional inventory in T019 plus final pre-edit source, compatibility, security, and baseline evidence; verify the applicable prerequisites T003–T007 and T011–T018 for each selected scope. Exclude NW-eslint, NW-node-types, NW-msal-react, AC-gitleaks, and AC-cosign while their holds remain open; exclude any other candidate lacking those pre-edit gates. T019 is not authority to edit or finalize a version. Do not require T030–T042 installation/validation evidence before edits: those checks run after the candidate is created and are required for T046 final outcomes, not a prerequisite to start the later install/check steps. Record scope-specific gates in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; do not remove a hold or use an unapproved spec/policy change as an implementation workaround.

<!-- parallel-group: 1 (max 3 concurrent) -->
- [ ] T021 [P] [US3] As the sole writer of the shared pnpm lock, apply only the T020-authorized NW-next (`16.3.8` goal for #149/#133/#132), NU-next (`15.5.21`), NW-jsdom (only if the `30.1.1` fallback remains eligible after final pre-edit evidence), NW-playwright (`@playwright/test`/`playwright`/`playwright-core` `1.63.0` as a coupled set), and NW-js-yaml (`4.3.1`) choices. Update declarations and the one lock consistently in `C:\code\ama\apps\web\package.json`, `C:\code\ama\packages\ui\package.json`, and `C:\code\ama\pnpm-lock.yaml`; preserve the web/UI importer split, integrity fields, `sharp@0.35.5`, `source-map-js@1.2.2`, PostCSS protections, and unrelated ranges. Do not edit the blocked ESLint, Node-types, or MSAL work items, and do not run unrestricted `pnpm update --latest`.
- [ ] T022 [P] [US3] Apply only T020-authorized PR-idna `idna 3.15` resolution in `C:\code\ama\uv.lock` (and make a `C:\code\ama\pyproject.toml` declaration change only if the verified scope actually requires it). Preserve root PR-cryptography `50.0.1` and `>=50.0.0,<51`, PR-msgpack `1.2.2`, PR-pyjwt `2.15.0` and `>=2.14.0,<3`, PR-engineio `4.14.0`, PR-socketio `5.17.0`, and all existing security overrides. Leave `C:\code\ama\apps\api\uv.lock` and `C:\code\ama\tools\specify-cli\uv.lock` unchanged; do not normalize their newer idna resolutions to root.
- [ ] T023 [P] [US3] Apply only T020-authorized agents resolutions in `C:\code\ama\apps\agents\uv.lock`: PA-h2 `4.4.1` with required hpack `4.2.0`, PA-idna `3.15`, PA-setuptools `83.0.0`, and PA-settings `2.14.2`; adjust `C:\code\ama\apps\agents\pyproject.toml` only if the actual declaration cannot express the approved choice. Preserve PA-aiohttp `3.14.3`, PA-pyasn1 `0.6.4`, PA-mcp `1.30.0`, PA-socketio `5.17.0`, PA-engineio `4.14.0`, PA-starlette `1.7.0`, PA-pyjwt `2.15.0` with `PyJWT[crypto] >=2.14.0,<3`, and PA-multipart `0.0.32`; keep all root values distinct. Do not run repository-wide `uv lock --upgrade`.

<!-- sequential -->
- [ ] T024 [US3] Reconcile the completed dependency-file edits against the frozen declarations and every actual affected resolution context: all root pnpm importers, root and agents uv marker branches/extras, protected API/specify-cli locks, and independently resolved pip/helper/container recipes. Compare exact before/after dependency maps and integrity fields; reject unexplained resolver churn, transitive downgrades, missing declarations, or forced global versions. Record per-work-item diff and result in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; if a protected scope is affected, stop and require its own reviewed scope and validation boundary.

<!-- sequential -->
- [ ] T025 [US3] After the source-policy setup (T003–T005), active-reference inventory (T010), official Action evidence (T013), provisional inventory (T019), and allowlist gate (T020), update only active Action references in this disjoint workflow partition: `C:\code\ama\.github\workflows\amend-loop-coupling.yml`, `C:\code\ama\.github\workflows\cd.yml`, `C:\code\ama\.github\workflows\chaos-quarterly.yml`, `C:\code\ama\.github\workflows\ci.yml`, `C:\code\ama\.github\workflows\codeql.yml`, `C:\code\ama\.github\workflows\corpus-ingest.yml`, `C:\code\ama\.github\workflows\dora-metrics.yml`, and `C:\code\ama\.github\workflows\dr-drill.yml`. Pin the inventoried checkout uses to `3d3c42e5aac5ba805825da76410c181273ba90b1`; change an upload-artifact use only if T010 shows it is one of the four non-target references, using `b7c566a772e6b6bfb58ed0dc250532a479d7789f`. Preserve all six already-target upload uses across the batch and every trigger, permission, runner, credential, artifact, and dormant-job behavior. Do not dispatch workflows or mutate PRs.

<!-- sequential -->
- [ ] T026 [US3] Continue the serialized single-writer Action update only after T025, in this disjoint partition: `C:\code\ama\.github\workflows\drift-detection.yml`, `C:\code\ama\.github\workflows\eval-pr-gate.yml`, `C:\code\ama\.github\workflows\eval-publish-dataset.yml`, `C:\code\ama\.github\workflows\foundry-carveout-review-6mo.yml`, `C:\code\ama\.github\workflows\foundry-carveout-review.yml`, `C:\code\ama\.github\workflows\help-gates.yml`, `C:\code\ama\.github\workflows\help-snapshot.yml`, and `C:\code\ama\.github\workflows\nightly-load.yml`. Pin the inventoried checkout uses to `3d3c42e5aac5ba805825da76410c181273ba90b1`; change an upload-artifact use only if T010 identifies it as one of the four non-target references, using `b7c566a772e6b6bfb58ed0dc250532a479d7789f`; pin the one approved comment-action use in `C:\code\ama\.github\workflows\foundry-carveout-review.yml` to `e8674b075228eee787fea43ef493e45ece1004c9`. Preserve all security, trigger, permission, runner, fork/credential, and action behavior; do not post a live comment or mutate PRs.

<!-- sequential -->
- [ ] T027 [US3] Continue the serialized single-writer Action update only after T026, in this disjoint partition: `C:\code\ama\.github\workflows\prompts-publish.yml`, `C:\code\ama\.github\workflows\security-scan.yml`, `C:\code\ama\.github\workflows\simulation-load-test.yml`, `C:\code\ama\.github\workflows\simulation-stub-sweep.yml`, `C:\code\ama\.github\workflows\spec-035-gate.yml`, `C:\code\ama\.github\workflows\spec-036-50-agent-load.yml`, `C:\code\ama\.github\workflows\spec-036-blue-green-e2e.yml`, `C:\code\ama\.github\workflows\staging-promotion.yml`, and `C:\code\ama\.github\workflows\web-coverage-iteration.yml`. Pin the inventoried checkout uses to `3d3c42e5aac5ba805825da76410c181273ba90b1`; change an upload-artifact use only if T010 identifies it as one of the four non-target references, using `b7c566a772e6b6bfb58ed0dc250532a479d7789f`. Leave the #105 gitleaks and #103 cosign references unchanged while B-ACTION-BASE / T017–T018 or the #103 asset/signature gate remains open. Preserve all permissions, runner labels, branch/fork guards, `persist-credentials: false`, and dormant steps; do not dispatch workflows, publish, sign, or mutate PRs.

<!-- sequential -->
- [ ] T028 [US3] After T021–T027, compare every changed/retained library resolution and Action SHA against the verified same-scope baseline and security constraints using the final manifests/locks/workflows in `C:\code\ama\package.json`, `apps\web\package.json`, `packages\ui\package.json`, `pnpm-lock.yaml`, `pyproject.toml`, `uv.lock`, `apps\agents\pyproject.toml`, `apps\agents\uv.lock`, and `.github\workflows\*.yml`. Confirm zero downgrade, zero weakened cryptography/PyJWT floors or redis-entraid/mem0ai protections, zero disabled/relaxed quality gates, and zero unexplained change. Record the comparison in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; any mismatch blocks dependent installs and readiness.

<!-- sequential -->
- [ ] T029 [US3] Bind the final candidate input-set ID to SHA-256 hashes of all changed and protected manifests, locks, `.npmrc`, workflow refs, Dockerfiles/base-image digests, source settings, runtime/tool versions, extras/markers, and environment matrix in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Capture these hashes only after all permitted dependency and Action edits (T021–T028); any later input drift invalidates the candidate installation and quality evidence.

**Checkpoint**: The three grouped package edits T021–T023 may run concurrently only after T020 and only on their disjoint manifest/lock files. Action edits T025–T027 are deliberately serialized after source-policy setup and the 55-reference inventory; each task owns its listed workflow partition, leaves #105/#103 unchanged while held, and preserves the single-writer workflow gate. Evidence consolidation is serialized because the approved record is the single feature-local `evidence.md`.

---

## Phase 6: User Story 4 — Verify and Hand Over a Reproducible Batch (Priority: P2)

**Goal**: Produce reproducible source, two-clean-install, quality, security, checklist, and blocker evidence for the exact candidate input set.

**Independent Test**: A maintainer other than the preparer can reproduce each recorded command/environment, verify two distinct cache-empty run IDs per affected independent resolution, compare identical installed maps and unchanged inputs, and identify every blocked/not-run check and its owner/next step. Missing evidence leaves readiness blocked; it is never inferred.

<!-- sequential -->
- [ ] T030 [US4] For the Node 24 Ubuntu x64 root pnpm workspace, perform two independent clean copies and two empty, distinct pnpm stores against the exact T029 candidate; run `pnpm install --frozen-lockfile` with only the approved npm proxy and record both full resolved maps, fresh retrieval/integrity, runtime patch, and before/after hashes in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Cover both web and UI importers in the shared lock; no existing `node_modules` or store may be reused.

<!-- sequential -->
- [ ] T031 [US4] For `C:\code\ama\apps\web\Dockerfile`, perform two cache-empty Alpine web builds from the same recorded base-image digest and architecture; record musl SWC/sharp/native artifact retrieval, resolved versions, source/integrity, and unchanged repository inputs in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Do not deploy, float the base image between runs, or substitute GNU/Linux results for musl.

<!-- sequential -->
- [ ] T032 [US4] On each affected supported architecture, perform two isolated devcontainer runs using the checked-in aggregate recipe in `C:\code\ama\.devcontainer\devcontainer.json` and `install-python-dependencies.py`; include its Python helper and frozen pnpm install, distinct empty caches, and actual registry settings. Record installed maps, architecture, sources, hashes, and each run ID in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; do not claim ARM64 coverage from x64.

<!-- sequential -->
- [ ] T033 [US4] For Python 3.12 Linux root development/load resolution, perform two separate cache-empty installs using the actual root recipe (`uv sync --locked --extra dev --extra load --no-cache --python 3.12 --no-python-downloads`) and only the approved Python proxy. Record selected markers/extras, full installed maps, fresh artifacts, and unchanged inputs in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; no lock or source rewrite is allowed during install.

<!-- sequential -->
- [ ] T034 [US4] For Python 3.12 Windows x64 `quality-windows`, perform two isolated `uv sync --locked --extra windows-ci --no-install-project --no-cache --python 3.12 --no-python-downloads` installs plus the existing no-deps eval-runner step from `C:\code\ama\.github\workflows\ci.yml`. Record installed maps, approved-source retrieval, runtime/tool versions, hashes, and distinct run IDs in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; the inspected Windows ARM64/Python 3.14 host is not a substitute.

<!-- sequential -->
- [ ] T035 [US4] For the standalone agents Python 3.12 scope, perform two separate cache-empty locked installs from `C:\code\ama\apps\agents\uv.lock` using the actual agents project recipe and approved Python proxy. Record its independent resolved map, markers, fresh artifact integrity, and unchanged inputs in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; root uv results do not satisfy this task.

<!-- sequential -->
- [ ] T036 [US4] For every affected Linux pip/CI recipe whose resolution is independent of uv locks, perform two clean installations per actual recipe with the same T029 inputs and fresh approved-proxy retrieval. Reproduce the exact applicable install steps in `C:\code\ama\.github\workflows\ci.yml`, `eval-pr-gate.yml`, `spec\*.yml`, and other workflows identified in T006/T010; record each recipe separately in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Do not infer one workflow’s resolution from another, treat a lock-only change as affecting it, add broad constraints, or omit an unavailable supported environment.

<!-- sequential -->
- [ ] T037 [US4] For each affected actual application-container recipe, build twice from the same recorded base image/digest and empty build caches, reproducing the checked-in install behavior in `C:\code\ama\apps\api\Dockerfile`, `apps\agents\Dockerfile`, `apps\ingestion\Dockerfile`, `apps\ingest-runner\Dockerfile`, and `apps\eval-runner\Dockerfile` as applicable. Record distinct run IDs, full installed maps, source/integrity, architecture/libc, and unchanged inputs per recipe in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; record explicit non-applicability for an unaffected recipe and never substitute uv-lock evidence for a pip/helper resolution.

<!-- sequential -->
- [ ] T038 [US4] For each affected Action runner environment and selected Action SHA, perform two separate uncached official-source retrievals and independently compare the full SHA/tree/blob identity and every required release asset/integrity in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Verify runner versions (including documented `2.327.1` minimum and `2.329.0` where checkout’s authenticated Docker-action Git use applies), Node runtime, sovereign runner identity, and checkout/artifact behavior. Do not treat source success as a live functional-job pass; B-ACTION-BASE and the #103 asset/signature hold remain blocking until their specific evidence is accepted.

<!-- sequential -->
- [ ] T039 [US4] Run and record the applicable Python policy, lint, type, application, isolation, benchmark, codegen, and coverage gates from `C:\code\ama\specs\001-proxy-dependency-upgrades\quickstart.md` §4 on the exact candidate: `verify_python_package_sources.py`; `pytest tests/policy`; ruff check/format; mypy; `lint-imports`; `pytest tests/equivalence`; the existing unit/contract/integration/simulation selection with its marker exclusions; `pytest tests/benchmark`; overlay taxonomy `--check`; and the coverage-ratchet script at its existing CI phase/tier. Preserve the `spec007_isolation` selector, strict markers, minimum 113 collected cases, and the remaining existing quality lints. Include the Windows contract/integration recipe and report every failed, blocked, and not-run command in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; do not relax selectors or thresholds.

<!-- sequential -->
- [ ] T040 [US4] Run the web/domain gates on the exact candidate in `C:\code\ama\specs\001-proxy-dependency-upgrades\quickstart.md` §4: domain typecheck/build, web lint, `tsc --noEmit`, web unit/integration tests, a11y tests, and production build/postbuild. Record commands, runtime, candidate hash, exit/status, and regression results in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; preserve current TypeScript/ESLint expectations and include targeted YAML, jsdom, and authentication coverage without replacing full applicable suites.

<!-- sequential -->
- [ ] T041 [US4] After browser/OS artifact sources and integrity are explicitly approved, run the existing Playwright evidence and story-acceptance collection/list and execution commands from `C:\code\ama\specs\001-proxy-dependency-upgrades\quickstart.md` §4 with fresh isolated servers and browser caches. Record at least five evidence tests and non-zero story-acceptance collection, actual Chromium revisions/OS dependencies, selectors, run results, and candidate hashes in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. If the browser source route is not approved or unavailable, leave this gate blocked/not-run; do not claim a cached browser or the Actions-only exception as proof.

<!-- sequential -->
- [ ] T042 [US4] Run the applicable existing workflow/build contract and security checks for the candidate: `python -m pytest tests/devops -q`, the existing spec-035 and eval-PR gate checks, CodeQL, gitleaks, PSRule, and Trivy with the current thresholds/allowlists. Compare baseline and candidate findings; any new known security regression, HIGH/CRITICAL finding, disabled check, or missing required scan blocks readiness. Record exact check applicability/results, runner/tool, hashes, and evidence in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Do not dispatch a workflow, replace the sovereign runner, publish, sign, or use a live PR comment as a test.

<!-- sequential -->
- [ ] T043 [US4] Consolidate every baseline/candidate install and quality record in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md` using the `data-model.md` fields: input-set/run IDs, exact scope/recipe/environment, command/working directory, non-secret source settings, versions, hashes, retrieved artifacts/checksums, installed maps, before/after protected hashes, status, failure fingerprint, and applicability reason. Require two distinct run IDs per affected independently resolved supported environment, identical maps and unchanged declarations/locks/workflows; classify each check as `passed`, `failed`, `blocked`, `not-run`, or reasoned `not-applicable`. Never include credentials, signed redirect query strings, or unsupported availability/security claims.

<!-- sequential -->
- [ ] T044 [US4] Assess all 35 rows CHK001–CHK035 in `C:\code\ama\specs\001-proxy-dependency-upgrades\checklists\implementation-readiness.md` against the specific evidence in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Add a concise evidence reference/finding per item; check an item only when its criterion is actually evidenced. Keep B-ESLINT, B-TYPES, B-MSAL, B-ACTION-BASE, B-SOURCE-ENV, B-CONSUMER-BASE, B-VALIDATION, and CHK028’s cosign asset/signature gate open while unresolved; do not check all rows to imply completion.

<!-- sequential -->
- [ ] T045 [US4] After T030–T042 validation runs and T043–T044 evidence/checklist records, recheck final candidate hashes and compare every declaration, lock, workflow, source-setting, and protected-scope input. If any install/test altered an input or a feed/candidate changed, invalidate the dependent runs, repeat the affected checks, and refresh T043–T044 before continuing. Record the final integrity comparison in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; report `B-VALIDATION` open for every unmet artifact-closure, clean-install, quality, security, runner, live-credential, or environment gate.

<!-- sequential -->
- [ ] T046 [US4] **FINAL STATUS RECONCILIATION**. Only after the provisional inventory in T019; relevant source/retrieval, compatibility/security, and hold evidence in T011–T018; authorized implementation, consistency, and candidate-hash evidence in T020–T029; every applicable final retrieval, clean-install, and required validation task in T030–T042; evidence/checklist consolidation in T043–T044; and final input-integrity check in T045 have reached evidence-backed terminal statuses, reconcile all 33 individual PR outcomes across the 31 work items in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. A retained/already-satisfied/superseded outcome requires its own final approved-source retrieval, compatibility/security assessment, installation evidence, and applicable required validation; a blocked, failed, not-run, or unsupported gate remains blocked/incomplete with its scope, evidence, responsible role, and next action. T019 is provisional inventory only and cannot supply a final outcome. Never downgrade, weaken a security/source rule, or label the batch complete while an included outcome or required gate remains unresolved.

**Checkpoint**: Story 4 is not “ready” because a checklist or evidence file is complete. T046 may finalize a retained/superseded outcome only when its relevant final retrieval, compatibility/security, installation, and required validation evidence is complete; otherwise it remains blocked/incomplete. Readiness requires two matching clean installs in every affected independent environment and all applicable required checks passing on the exact candidate; any remaining blocker keeps the affected result and whole-batch claim not ready.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Crosswalk final outcomes, prepare the handover, and obtain independent acceptance review without widening scope.

<!-- sequential -->
- [ ] T047 Crosswalk the final PR/work-item outcomes and evidence against all 22 functional requirements, nine success criteria, and 20 acceptance scenarios in `C:\code\ama\specs\001-proxy-dependency-upgrades\spec.md`; verify the existing 16/16 checklist at `C:\code\ama\specs\001-proxy-dependency-upgrades\checklists\requirements.md` remains unchanged and that each readiness checklist finding links to evidence. Record any uncovered requirement or unresolved acceptance scenario as a blocker in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Keep SC-004 and SC-009 pending until the independent second-maintainer review in T049 is complete and satisfactory; do not claim either criterion passed before then. Do not create a later-phase artifact or change the approved spec to make a failed criterion appear satisfied.

<!-- sequential -->
- [ ] T048 Prepare the human handover in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`, linking all 33 PR targets/outcomes to the 31 scoped work items, chosen/retained versions or full Action SHAs, two-run/source evidence, applicable checks, checklist findings, and blocker owner/next action. State clearly whether only accounting is complete, whether any upgrade is validated, and why the batch is or is not ready; identify SC-004 and SC-009 as pending T049 and make no pass claim for either. Do not authorize merge, close, update, comment, push, commit, workflow dispatch, publication, or deployment.

<!-- sequential -->
- [ ] T049 An independent second maintainer who did not prepare the candidate evidence or T046 outcomes reviews the completed record only after T011–T019, T020–T029, all applicable validation tasks T030–T042, evidence/checklist/integrity tasks T043–T045, outcome reconciliation T046, and crosswalk/handover T047–T048 are complete. Independently recompute every library fallback decision from the recorded target, verified baseline, candidate set, retrieval/eligibility evidence, and approved policy: the candidate must be stable, in the target's major, strictly below the target, above the verified baseline, and the highest candidate with sufficient approved-source retrieval, compatibility, and security evidence; if none qualifies, independently confirm the blocked result. Include jsdom if it remains a fallback and any fallback that remains blocked. Review all 33 individual PR outcomes for the selected/chosen-or-retained version or full Action SHA, rationale, source/retrieval evidence, validation status, blockers, and next action. Record the reviewer’s identity, review time, result (`passed`, `needs-correction`, or `blocked`), decision-by-decision comparison, and findings in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; update the handover’s review result only from that record. SC-004 and SC-009 pass only if the independent replay agrees and the per-PR record is sufficient; discrepancies or missing evidence keep them pending/failed and the affected outcome blocked until corrected and reviewed again. Do not change code, dependencies, workflows, PRs, or policy during review.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1, T001–T002)**: Starts from the approved baseline and freezes the exact inputs/environment record.
- **Foundational (Phase 2, T003–T007)**: Depends on Setup. T003–T005 establish the narrowly scoped npm proxy configuration; T006–T007 record consumer baselines and baseline check results. B-SOURCE-ENV and B-CONSUMER-BASE must be closed for each dependent scope before its edits; candidate retrieval/install evidence can still reopen a source gate, and baseline check failures are recorded, not waived.
- **User Story 1 (Phase 3, T008–T010)**: Depends on the frozen input and environment records. Delivers complete accounting only; it performs no dependency edit.
- **User Story 2 (Phase 4, T011–T019)**: Depends on Foundation and the 33-to-31 ledger. Each work item receives evidence or an explicit hold. T014–T018 do not unblock by passage of time. T019 is a provisional candidate inventory, not final status.
- **User Story 3 (Phase 5, T020–T029)**: Depends on the provisional inventory and cleared, scope-specific pre-edit gates. T021–T023 are the one marked parallel group after T020 because they edit disjoint manifest/lock paths. T024 reconciles dependency edits. T025–T027 are serialized workflow writers for disjoint, explicitly listed partitions. T028 compares all edits and T029 freezes the exact candidate before validation.
- **User Story 4 (Phase 6, T030–T046)**: Depends on T029. T030–T042 perform the applicable final retrieval, two-clean-install, and quality/security checks using each actual recipe and platform. T043–T045 consolidate records, assess the readiness checklist, and recheck final input integrity. T046 finalizes outcomes only after the relevant evidence and validation tasks have terminal, evidence-backed statuses; missing, blocked, failed, or not-run evidence cannot become a retained/satisfied pass.
- **Polish (Phase 7, T047–T049)**: Depends on T046. T047 crosswalks the final outcomes, T048 prepares the handover with SC-004/SC-009 still pending, and T049 is the independent second-maintainer review required before those criteria can pass.

### User Story Dependencies and Gate Propagation

- **US1 (P1)**: After T001–T007. Independent of dependency edits; MVP is the verified 33-PR/31-work-item account.
- **US2 (P1)**: After US1 and the source/baseline records. T019 captures only provisional candidates and rationale. The exact target is preferred. A library fallback must be stable, lower than target, same major, and above baseline. Actions have no alternative-release fallback. A failed feed request is access-unavailable/unknown, never version absence.
- **US3 (P1)**: After provisional T019 and the T020 allowlist gate. `NW-next` consolidates #149/#133/#132 only; `NU-next`, root Python, and agents Python remain independent. The shared pnpm lock has one writer. API and specify-cli locks remain protected unless a proved effect is separately scoped and gated. Final version/outcome status waits for T046.
- **US4 (P2)**: After candidate hashes T029. Candidate/hash drift invalidates downstream evidence. T046 depends on all applicable T011–T018, T020–T029, and T030–T045 evidence tasks; unavailable credentials, browser/OS sources, live staging, or sovereign runner capabilities are `blocked`/`not-run`, not passing.

Specific blocker propagation:

- **B-SOURCE-ENV / T003–T005** blocks npm candidate edits (T021) and npm clean-install/artifact claims (T030–T032); configuration alone does not establish artifact availability, and public-feed fallback is never allowed.
- **B-CONSUMER-BASE / T006** blocks dependent pip/helper/container selections and readiness (T036–T037); uv locks cannot stand in for those resolutions.
- **B-ESLINT / T014**, **B-TYPES / T015**, and **B-MSAL / T016** block only their named web work items but prevent whole-batch completion until cleared or explicitly resolved through the human policy gate.
- **B-ACTION-BASE / T017–T018** blocks #105/#103 pin changes in T027 and their outcomes. The separate #103 cosign asset/signature gap also blocks CHK028 and B-VALIDATION.
- **B-VALIDATION** remains batch-blocking until the final artifact closure, two-install pairs, and every applicable quality/security gate are evidenced. No task authorizes remote PR/workflow side effects.

### Plan Batch Mapping

- **B0 — Baseline/source controls**: T001–T010.
- **B1 — Python lock deltas**: T012, T019, T022–T023, T033–T037, T039.
- **B2 — npm runtime/parser deltas**: T011, T019, T021, T030–T032, T040–T041.
- **B3 — npm test tooling**: T011, T021, T030, T040–T041; ESLint/Node-types remain blocked at T014–T015.
- **B4 — Action pins**: T010, T013, T017–T018, T025–T027, T038, T042; workflow edits are serialized.

### Parallel Opportunities

Only the explicit group below is approved for parallel execution; its three tasks share no manifest/lock files, do not write the shared evidence ledger, and have no unmet dependency after T020:

The single group is T021 (web/UI manifests and shared pnpm lock), T022 (root Python lock), and T023 (agents Python lock/manifests only when needed).

All three tasks defer writes to the shared evidence ledger until sequential reconciliation/candidate-freeze tasks T024/T028/T029. The Action workflow edits T025–T027 are deliberately sequential even though their file partitions are disjoint, because they share the workflow surface and must follow source-policy setup. Validation records are consolidated sequentially into one `evidence.md`; no other task is marked `[P]`.

## Implementation Strategy

### MVP First — User Story 1 Only

1. Complete T001–T007 to establish the exact baseline, supported-environment matrix, scoped source controls, consumer baselines, and baseline check status.
2. Complete T008–T010 and independently audit the 33 PR links against 31 scoped work items and 55 Action references.
3. Stop. This MVP is an accounting/evidence increment only; it is not an upgrade, install, merge, or readiness claim.

### Incremental Delivery

1. Complete US2 source, compatibility, security, and selection evidence; leave T014–T018 explicitly blocked until their concrete evidence or an approved resolution exists, and keep T019 provisional.
2. Complete only T020–T029 for work items whose prerequisites have actually cleared; preserve unresolved holds and unrelated scopes.
3. Complete two-clean-install pairs for every affected environment, then every applicable quality/security gate (T030–T042).
4. Finish evidence consolidation, readiness checklist, and final input-integrity review (T043–T045), then finalize per-PR statuses in T046 only from that evidence.
5. Complete the requirements/acceptance crosswalk and handover (T047–T048), then have the independent second maintainer complete T049. Keep SC-004/SC-009 pending until that review passes; report any unresolved scope as blocked/incomplete and do not claim whole-batch readiness.

## Notes

- P/F/R/H directions and package/action evidence from the Plan are provisional; re-fetch/revalidate the exact final inputs.
- The approved library sources remain `https://packagefeedproxy.microsoft.io/npm/` and `https://packagefeedproxy.microsoft.io/pypi/simple`; official upstream GitHub is an Actions-only exception.
- Do not remove/relax security floors, overrides, integrity fields, quality checks, runner labels, permissions, or trigger protections.
- No broad dependency refresh, runtime migration, installer conversion, public-feed fallback, new service/framework, unapproved environment expansion, or unauthorised PR/remote mutation is in scope.
- No application/workflow/dependency files are changed by this Phase 5 document-generation output.
