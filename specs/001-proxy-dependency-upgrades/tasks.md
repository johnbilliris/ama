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
- [ ] T003 **GATED — B-SOURCE-ENV**. The planning evidence found no tracked root `.npmrc`, and a developer’s user-level registry does not establish the npm source for clean CI/bootstrap jobs. After explicit implementation authorization, create the minimal credential-free `C:\code\ama\.npmrc` using only `https://packagefeedproxy.microsoft.io/npm/`, and propagate `NPM_CONFIG_REGISTRY=https://packagefeedproxy.microsoft.io/npm/` to each affected clean install/bootstrap boundary found in `C:\code\ama\.github\workflows\*.yml` and `C:\code\ama\.devcontainer\devcontainer.json`; preserve the existing Docker/Compose registry setting in `C:\code\ama\compose.yaml`. Verify actual final artifact hosts and prove no public npm/PyPI fallback or credential logging. Keep B-SOURCE-ENV open until every relevant path is evidenced; this task must not change Action pins or relax source policy.

<!-- sequential -->
- [ ] T004 **GATED — B-CONSUMER-BASE**. Planning did not establish installed baselines or repeatability for affected pip/helper/container recipes; a `uv.lock` cannot prove their resolution. Before dependency edits, reproduce and record the actual baseline resolutions for every affected consumer using its checked-in recipe: `C:\code\ama\.github\workflows\ci.yml`, `eval-pr-gate.yml`, applicable `spec\*.yml` and other affected workflow recipes; `C:\code\ama\scripts\install_pyproject_dependencies.py`; `C:\code\ama\apps\api\Dockerfile`, `apps\agents\Dockerfile`, `apps\ingestion\Dockerfile`, `apps\ingest-runner\Dockerfile`, `apps\eval-runner\Dockerfile`; and `C:\code\ama\.devcontainer\install-python-dependencies.py`. Record separate recipe/environment IDs and installed maps in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Preserve independently newer results; do not impose root pins, add a global constraints file, or convert consumers to uv. Leave B-CONSUMER-BASE blocking any unresolved consumer decision.

<!-- sequential -->
- [ ] T005 Run the applicable repository quality checks against the unchanged, frozen baseline in the environments assigned by `C:\code\ama\specs\001-proxy-dependency-upgrades\quickstart.md` §4; record exact commands, selectors, versions, exit/status, and failure fingerprints in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Classify each as `passed`, `failed`, `blocked`, `not-run`, or justified `not-applicable`; do not waive a pre-existing failure, infer a pass from a skipped credentialed test, or start version edits until required baseline/source gates are evidenced.

**Checkpoint**: T003–T005 must establish a reproducible source policy and baseline for every in-scope consumer. If any environment, feed, baseline, or required tool is unavailable, record the concrete hold and block only its dependent scope; do not substitute a different environment.

---

## Phase 3: User Story 1 — Account for Every Upgrade Chore (Priority: P1) 🎯 MVP

**Goal**: Preserve every supplied PR and its own target, scope, current resolution, and work-item outcome.

**Independent Test**: A second maintainer can count 33 linked PR rows mapped to exactly 31 IDs, verify the three distinct Next proposals retained under NW-next, and identify every independent lock/importer/Action decision without any dependency edits.

<!-- sequential -->
- [ ] T006 [US1] Audit the frozen register above against `C:\code\ama\specs\001-proxy-dependency-upgrades\research.md` R1 and `spec.md` “Supplied PR Baseline”; preserve all 33 links, targets, and the 31 exact work-item IDs. Confirm the 33-to-31 map and P/F/R/H counts in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; log head or scope drift without overwriting the original snapshot or silently changing the denominator.

<!-- sequential -->
- [ ] T007 [US1] Revalidate the actual resolved baseline and independent scope for every work item against `C:\code\ama\package.json`, `apps\web\package.json`, `packages\ui\package.json`, `pnpm-lock.yaml`, `pyproject.toml`, `uv.lock`, `apps\agents\pyproject.toml`, `apps\agents\uv.lock`, `apps\api\uv.lock`, and `tools\specify-cli\uv.lock`; record actual resolutions and protected scopes in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Keep web Next 16 separate from UI Next 15, root Python separate from agents, and API/specify-cli locks protected; a declaration range or old PR base is not a resolved baseline.

<!-- sequential -->
- [ ] T008 [US1] Enumerate all 55 active Action occurrences across the 25 workflows from the current YAML in `C:\code\ama\.github\workflows\*.yml`, excluding comments/dormant steps; record workflow/job/step, baseline ref, runner, and proposed work item in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Reconcile 42 checkout references, ten upload-artifact references (six already at target), and one each for gitleaks, cosign, and comment; do not rely only on the old PR patch file list.

**Checkpoint**: Story 1 is independently accounted for only when all 33 PRs link to one of the 31 IDs and every distinct resolution context remains separately named.

---

## Phase 4: User Story 2 — Choose an Obtainable, Compatible Version (Priority: P1)

**Goal**: Revalidate approved-source availability, artifact integrity, runtime compatibility, security, and version ordering for all 31 work items without turning access failure into absence.

**Independent Test**: Evidence distinguishes retrieved artifacts, missing required files, incompatible files, trustworthy absence, and access-unavailable/unknown; a reviewer independently reproduces the exact-target/fallback/Action decision or the explicit hold.

<!-- sequential -->
- [ ] T009 [US2] Re-fetch npm metadata and every required candidate, companion, native, and transitive artifact for NW-next, NW-eslint, NW-jsdom, NW-playwright, NW-node-types, NW-msal-react, NW-js-yaml, and NU-next using only `https://packagefeedproxy.microsoft.io/npm/`; record artifact identity, exact URL/final host, retrieval time, checksum provenance/result, platform/engine/peer data, and classification in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Cover Next/@next/env/SWC/sharp and PostCSS relationships, jsdom’s Node `>=24.15.0` patch requirement, the Playwright trio plus browser/OS artifacts, the full MSAL companion graph, and ESLint peer ranges. Preserve stronger existing lock integrity where proxy metadata is SHA-1-only; local SHA-256 is not stronger publisher provenance. Treat browser CDN/source-policy gaps as blockers, not implicit permission.

<!-- sequential -->
- [ ] T010 [US2] Re-fetch and validate the root and agents Python candidate and retained package files for PR-cryptography, PR-idna, PR-msgpack, PR-pyjwt, PR-engineio, PR-socketio, PA-h2, PA-aiohttp, PA-setuptools, PA-pyasn1, PA-mcp, PA-socketio, PA-engineio, PA-idna, PA-starlette, PA-pyjwt, PA-settings, and PA-multipart from only `https://packagefeedproxy.microsoft.io/pypi/simple`; record file tags, Requires-Python, integrity, markers/extras, source, environment, and result in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Cover the actual supported Python 3.12 platforms and native wheels, h2/hpack compatibility, settings dependencies, and the separate root/agents resolutions. Retain `cryptography >=50.0.0,<51`, both PyJWT `>=2.14.0,<3` protections, redis-entraid and mem0ai exceptions, and all newer baselines; do not use public PyPI or assume a wheel sample proves full install closure.

<!-- sequential -->
- [ ] T011 [US2] Revalidate official repository identity, full proposed commit SHA, tree/source-blob identity, release ordering/ancestry, required assets, runner compatibility, and retrieval/integrity for AC-checkout, AC-upload, AC-gitleaks, AC-cosign, and AC-comment; bind results to active references from `C:\code\ama\.github\workflows\*.yml` in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Use official GitHub sources only for Actions; never infer SHA age lexically or from timestamps. Verify runner minimums and checkout fork/credential behavior without executing a live comment, publish, signing, or deployment side effect.

<!-- sequential -->
- [ ] T012 [US2] **BLOCKED — B-ESLINT / PR [#150](https://github.com/johnbilliris/ama/pull/150)**. Keep NW-eslint at its verified baseline and leave the work item incomplete: target `10.12.0` was absent at the planning observation, and researched `10.11.0` conflicts with the available Next lint-plugin peer families. Clear only with new approved-proxy evidence of an eligible, compatible candidate or a separately approved bounded scope/spec change; do not use a major-9 fallback, replace peer families broadly, or weaken lint rules. Record the concrete evidence and next owner/action in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; downstream NW-eslint completion and whole-batch readiness remain gated.

<!-- sequential -->
- [ ] T013 [US2] **BLOCKED — B-TYPES / PR [#146](https://github.com/johnbilliris/ama/pull/146)**. Keep NW-node-types unchanged until an explicit Node 24 runtime/type-surface compatibility assessment and required test evidence exist; archive retrieval alone is insufficient. Do not migrate runtime to Node 26 or invent a major-24 fallback. Record evidence, owner, and next action in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; NW-node-types completion and whole-batch readiness remain gated.

<!-- sequential -->
- [ ] T014 [US2] **BLOCKED — B-MSAL / PR [#144](https://github.com/johnbilliris/ama/pull/144)**. Keep NW-msal-react unchanged until trustworthy approved-proxy retrieval and integrity evidence resolves required `@azure/msal-common@16.14.2` and the complete browser/react companion graph. Repeated access failures or one 404 endpoint are not proof of absence; do not use public npm or downgrade React to force a selection. Record evidence, owner, and next action in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; NW-msal-react completion and whole-batch readiness remain gated.

<!-- sequential -->
- [ ] T015 [US2] **BLOCKED — B-ACTION-BASE / PR [#105](https://github.com/johnbilliris/ama/pull/105)**. Do not change the active gitleaks pin: the current full-SHA baseline is unresolvable in the official upstream evidence and the proposed source/binary alone cannot prove no-downgrade ordering. Require authoritative baseline provenance or a separately approved policy resolution, then revalidate the official proposed SHA and required gitleaks asset/checksum. Record the hold and owner/action in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; AC-gitleaks and whole-batch readiness remain gated.

<!-- sequential -->
- [ ] T016 [US2] **BLOCKED — B-ACTION-BASE / PR [#103](https://github.com/johnbilliris/ama/pull/103)**. Do not change the active cosign pin while the existing full-SHA baseline remains unresolvable; additionally keep the required asset/signature gate open. Retrieve and verify the pinned bootstrap v2.5.2 binary against recorded SHA-256 `bcfeae05557a9f313ee4392d2f335d0ff69ebbfd232019e3736fb04999fe1734`, plus the explicitly requested v2.4.1 `cosign-linux-amd64`, detached signature, and `release/release-cosign.pub` (including recorded key hash and signature result), using official upstream sources. These planning hashes are expected verification inputs, not successful asset results. No publication/signing is authorized. Record the hold in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md` and leave checklist CHK027/CHK028 open until their evidence gates pass.

<!-- sequential -->
- [ ] T017 [US2] Reconcile all 31 work items against the revalidated baselines and T009–T016 evidence; record the selected version/full Action SHA, rejected alternatives, scope, source, rationale, and status in `C:\code\ama\specs\001-proxy-dependency-upgrades\research.md` and `evidence.md`. Prefer an eligible reconciled target; for libraries only, a fallback must be the highest eligible stable version strictly below the target, within its major, and above the verified baseline. Actions allow only the proposed full SHA or an officially proven newer existing baseline. Retained/superseded rows need the same source, compatibility, security, and validation evidence. Keep every unresolved row `blocked`/`incomplete`; do not promote P/F/R/H to completion based on catalogue or cache evidence.

**Checkpoint**: T017 can produce a complete candidate decision register while five PRs remain held. Any unresolved B-SOURCE-ENV, B-CONSUMER-BASE, B-ESLINT, B-TYPES, B-MSAL, B-ACTION-BASE, or artifact-closure issue remains a downstream gate; no policy hold is removed by counting or consolidating work.

---

## Phase 5: User Story 3 — Preserve a Consistent, Secure Dependency Baseline (Priority: P1)

**Goal**: Apply only evidence-cleared, scope-specific changes; keep every declaration, resolution, Action pin, and security constraint consistent without unrelated churn or downgrade.

**Independent Test**: Compare pre/post declarations, importer and marker-specific resolved maps, all affected independent consumer maps, Action SHAs, and protected inputs. Confirm no downgrade, weakened override/check, global normalization, or unapproved change; held work items remain explicitly incomplete.

<!-- sequential -->
- [ ] T018 [US3] **GATED**. Before any version-file edit, create the execution allowlist from T017 and verify the relevant source and baseline prerequisites T003–T005 are closed for each selected scope. Exclude NW-eslint, NW-node-types, NW-msal-react, AC-gitleaks, and AC-cosign while their holds remain open; exclude any other candidate lacking final source, compatibility, or security evidence. Record scope-specific gates in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; do not remove a hold or use an unapproved spec/policy change as an implementation workaround.

<!-- parallel-group: 1 (max 3 concurrent) -->
- [ ] T019 [P] [US3] As the sole writer of the shared pnpm lock, apply only the T017-cleared NW-next (`16.3.8` goal for #149/#133/#132), NU-next (`15.5.21`), NW-jsdom (only the eligible `30.1.1` fallback), NW-playwright (`@playwright/test`/`playwright`/`playwright-core` `1.63.0` as a coupled set), and NW-js-yaml (`4.3.1`) choices. Update declarations and the one lock consistently in `C:\code\ama\apps\web\package.json`, `C:\code\ama\packages\ui\package.json`, and `C:\code\ama\pnpm-lock.yaml`; preserve the web/UI importer split, integrity fields, `sharp@0.35.5`, `source-map-js@1.2.2`, PostCSS protections, and unrelated ranges. Do not edit the blocked ESLint, Node-types, or MSAL work items, and do not run unrestricted `pnpm update --latest`.
- [ ] T020 [P] [US3] Apply only PR-idna’s T017-cleared root `idna 3.15` resolution in `C:\code\ama\uv.lock` (and make a `C:\code\ama\pyproject.toml` declaration change only if the verified scope actually requires it). Preserve root PR-cryptography `50.0.1` and `>=50.0.0,<51`, PR-msgpack `1.2.2`, PR-pyjwt `2.15.0` and `>=2.14.0,<3`, PR-engineio `4.14.0`, PR-socketio `5.17.0`, and all existing security overrides. Leave `C:\code\ama\apps\api\uv.lock` and `C:\code\ama\tools\specify-cli\uv.lock` unchanged; do not normalize their newer idna resolutions to root.
- [ ] T021 [P] [US3] Apply only T017-cleared agents resolutions in `C:\code\ama\apps\agents\uv.lock`: PA-h2 `4.4.1` with required hpack `4.2.0`, PA-idna `3.15`, PA-setuptools `83.0.0`, and PA-settings `2.14.2`; adjust `C:\code\ama\apps\agents\pyproject.toml` only if the actual declaration cannot express the approved choice. Preserve PA-aiohttp `3.14.3`, PA-pyasn1 `0.6.4`, PA-mcp `1.30.0`, PA-socketio `5.17.0`, PA-engineio `4.14.0`, PA-starlette `1.7.0`, PA-pyjwt `2.15.0` with `PyJWT[crypto] >=2.14.0,<3`, and PA-multipart `0.0.32`; keep all root values distinct. Do not run repository-wide `uv lock --upgrade`.

<!-- sequential -->
- [ ] T022 [US3] Reconcile the completed dependency-file edits against the frozen declarations and every actual affected resolution context: all root pnpm importers, root and agents uv marker branches/extras, protected API/specify-cli locks, and independently resolved pip/helper/container recipes. Compare exact before/after dependency maps and integrity fields; reject unexplained resolver churn, transitive downgrades, missing declarations, or forced global versions. Record per-work-item diff and result in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; if a protected scope is affected, stop and require its own reviewed scope and validation boundary.

<!-- sequential -->
- [ ] T023 [US3] With the workflow files as a single-writer surface and only after T003/T011/T017 clear the affected refs, update active Action references in `C:\code\ama\.github\workflows\*.yml`: pin the approved full checkout SHA for its 42 active uses, change only the four upload-artifact uses not already at `b7c566a772e6b6bfb58ed0dc250532a479d7789f`, and pin the one comment-action use to `e8674b075228eee787fea43ef493e45ece1004c9`. Preserve the six upload uses already at target, every trigger/permission/branch guard, sovereign runner labels, fork/credential behavior, `persist-credentials: false`, artifact semantics, and dormant jobs. Leave #105/#103 pins unchanged while blocked. Do not dispatch workflows, post a live comment, publish, sign, or mutate PRs.

<!-- sequential -->
- [ ] T024 [US3] Compare every changed/retained library resolution and Action SHA against the verified same-scope baseline and security constraints using the final manifests/locks/workflows in `C:\code\ama\package.json`, `apps\web\package.json`, `packages\ui\package.json`, `pnpm-lock.yaml`, `pyproject.toml`, `uv.lock`, `apps\agents\pyproject.toml`, `apps\agents\uv.lock`, and `.github\workflows\*.yml`. Confirm zero downgrade, zero weakened cryptography/PyJWT floors or redis-entraid/mem0ai protections, zero disabled/relaxed quality gates, and zero unexplained change. Record the comparison in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; any mismatch blocks dependent installs and readiness.

<!-- sequential -->
- [ ] T025 [US3] Bind the final candidate input-set ID to SHA-256 hashes of all changed and protected manifests, locks, `.npmrc`, workflow refs, Dockerfiles/base-image digests, source settings, runtime/tool versions, extras/markers, and environment matrix in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Capture these hashes only after all permitted dependency and Action edits (T019–T024); any later input drift invalidates the candidate installation and quality evidence.

**Checkpoint**: The three grouped edits may run concurrently only after T018 and only on their disjoint manifest/lock files. Action edits are deliberately serialized because source-policy setup and 55 active Action references share workflow files. Evidence consolidation is serialized because the approved record is the single feature-local `evidence.md`.

---

## Phase 6: User Story 4 — Verify and Hand Over a Reproducible Batch (Priority: P2)

**Goal**: Produce reproducible source, two-clean-install, quality, security, checklist, and blocker evidence for the exact candidate input set.

**Independent Test**: A maintainer other than the preparer can reproduce each recorded command/environment, verify two distinct cache-empty run IDs per affected independent resolution, compare identical installed maps and unchanged inputs, and identify every blocked/not-run check and its owner/next step. Missing evidence leaves readiness blocked; it is never inferred.

<!-- sequential -->
- [ ] T026 [US4] For the Node 24 Ubuntu x64 root pnpm workspace, perform two independent clean copies and two empty, distinct pnpm stores against the exact T025 candidate; run `pnpm install --frozen-lockfile` with only the approved npm proxy and record both full resolved maps, fresh retrieval/integrity, runtime patch, and before/after hashes in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Cover both web and UI importers in the shared lock; no existing `node_modules` or store may be reused.

<!-- sequential -->
- [ ] T027 [US4] For `C:\code\ama\apps\web\Dockerfile`, perform two cache-empty Alpine web builds from the same recorded base-image digest and architecture; record musl SWC/sharp/native artifact retrieval, resolved versions, source/integrity, and unchanged repository inputs in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Do not deploy, float the base image between runs, or substitute GNU/Linux results for musl.

<!-- sequential -->
- [ ] T028 [US4] On each affected supported architecture, perform two isolated devcontainer runs using the checked-in aggregate recipe in `C:\code\ama\.devcontainer\devcontainer.json` and `install-python-dependencies.py`; include its Python helper and frozen pnpm install, distinct empty caches, and actual registry settings. Record installed maps, architecture, sources, hashes, and each run ID in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; do not claim ARM64 coverage from x64.

<!-- sequential -->
- [ ] T029 [US4] For Python 3.12 Linux root development/load resolution, perform two separate cache-empty installs using the actual root recipe (`uv sync --locked --extra dev --extra load --no-cache --python 3.12 --no-python-downloads`) and only the approved Python proxy. Record selected markers/extras, full installed maps, fresh artifacts, and unchanged inputs in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; no lock or source rewrite is allowed during install.

<!-- sequential -->
- [ ] T030 [US4] For Python 3.12 Windows x64 `quality-windows`, perform two isolated `uv sync --locked --extra windows-ci --no-install-project --no-cache --python 3.12 --no-python-downloads` installs plus the existing no-deps eval-runner step from `C:\code\ama\.github\workflows\ci.yml`. Record installed maps, approved-source retrieval, runtime/tool versions, hashes, and distinct run IDs in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; the inspected Windows ARM64/Python 3.14 host is not a substitute.

<!-- sequential -->
- [ ] T031 [US4] For the standalone agents Python 3.12 scope, perform two separate cache-empty locked installs from `C:\code\ama\apps\agents\uv.lock` using the actual agents project recipe and approved Python proxy. Record its independent resolved map, markers, fresh artifact integrity, and unchanged inputs in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; root uv results do not satisfy this task.

<!-- sequential -->
- [ ] T032 [US4] For every affected Linux pip/CI recipe whose resolution is independent of uv locks, perform two clean installations per actual recipe with the same T025 inputs and fresh approved-proxy retrieval. Reproduce the exact applicable install steps in `C:\code\ama\.github\workflows\ci.yml`, `eval-pr-gate.yml`, `spec\*.yml`, and other workflows identified in T004/T008; record each recipe separately in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Do not infer one workflow’s resolution from another, treat a lock-only change as affecting it, add broad constraints, or omit an unavailable supported environment.

<!-- sequential -->
- [ ] T033 [US4] For each affected actual application-container recipe, build twice from the same recorded base image/digest and empty build caches, reproducing the checked-in install behavior in `C:\code\ama\apps\api\Dockerfile`, `apps\agents\Dockerfile`, `apps\ingestion\Dockerfile`, `apps\ingest-runner\Dockerfile`, and `apps\eval-runner\Dockerfile` as applicable. Record distinct run IDs, full installed maps, source/integrity, architecture/libc, and unchanged inputs per recipe in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; record explicit non-applicability for an unaffected recipe and never substitute uv-lock evidence for a pip/helper resolution.

<!-- sequential -->
- [ ] T034 [US4] For each affected Action runner environment and selected Action SHA, perform two separate uncached official-source retrievals and independently compare the full SHA/tree/blob identity and every required release asset/integrity in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Verify runner versions (including documented `2.327.1` minimum and `2.329.0` where checkout’s authenticated Docker-action Git use applies), Node runtime, sovereign runner identity, and checkout/artifact behavior. Do not treat source success as a live functional-job pass; B-ACTION-BASE and the #103 asset/signature hold remain blocking until their specific evidence is accepted.

<!-- sequential -->
- [ ] T035 [US4] Run and record the applicable Python policy, lint, type, application, isolation, benchmark, codegen, and coverage gates from `C:\code\ama\specs\001-proxy-dependency-upgrades\quickstart.md` §4 on the exact candidate: `verify_python_package_sources.py`; `pytest tests/policy`; ruff check/format; mypy; `lint-imports`; `pytest tests/equivalence`; the existing unit/contract/integration/simulation selection with its marker exclusions; `pytest tests/benchmark`; overlay taxonomy `--check`; and the coverage-ratchet script at its existing CI phase/tier. Preserve the `spec007_isolation` selector, strict markers, minimum 113 collected cases, and the remaining existing quality lints. Include the Windows contract/integration recipe and report every failed, blocked, and not-run command in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; do not relax selectors or thresholds.

<!-- sequential -->
- [ ] T036 [US4] Run the web/domain gates on the exact candidate in `C:\code\ama\specs\001-proxy-dependency-upgrades\quickstart.md` §4: domain typecheck/build, web lint, `tsc --noEmit`, web unit/integration tests, a11y tests, and production build/postbuild. Record commands, runtime, candidate hash, exit/status, and regression results in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; preserve current TypeScript/ESLint expectations and include targeted YAML, jsdom, and authentication coverage without replacing full applicable suites.

<!-- sequential -->
- [ ] T037 [US4] After browser/OS artifact sources and integrity are explicitly approved, run the existing Playwright evidence and story-acceptance collection/list and execution commands from `C:\code\ama\specs\001-proxy-dependency-upgrades\quickstart.md` §4 with fresh isolated servers and browser caches. Record at least five evidence tests and non-zero story-acceptance collection, actual Chromium revisions/OS dependencies, selectors, run results, and candidate hashes in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. If the browser source route is not approved or unavailable, leave this gate blocked/not-run; do not claim a cached browser or the Actions-only exception as proof.

<!-- sequential -->
- [ ] T038 [US4] Run the applicable existing workflow/build contract and security checks for the candidate: `python -m pytest tests/devops -q`, the existing spec-035 and eval-PR gate checks, CodeQL, gitleaks, PSRule, and Trivy with the current thresholds/allowlists. Compare baseline and candidate findings; any new known security regression, HIGH/CRITICAL finding, disabled check, or missing required scan blocks readiness. Record exact check applicability/results, runner/tool, hashes, and evidence in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Do not dispatch a workflow, replace the sovereign runner, publish, sign, or use a live PR comment as a test.

<!-- sequential -->
- [ ] T039 [US4] Consolidate every baseline/candidate install and quality record in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md` using the `data-model.md` fields: input-set/run IDs, exact scope/recipe/environment, command/working directory, non-secret source settings, versions, hashes, retrieved artifacts/checksums, installed maps, before/after protected hashes, status, failure fingerprint, and applicability reason. Require two distinct run IDs per affected independently resolved supported environment, identical maps and unchanged declarations/locks/workflows; classify each check as `passed`, `failed`, `blocked`, `not-run`, or reasoned `not-applicable`. Never include credentials, signed redirect query strings, or unsupported availability/security claims.

<!-- sequential -->
- [ ] T040 [US4] Assess all 35 rows CHK001–CHK035 in `C:\code\ama\specs\001-proxy-dependency-upgrades\checklists\implementation-readiness.md` against the specific evidence in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`. Add a concise evidence reference/finding per item; check an item only when its criterion is actually evidenced. Keep B-ESLINT, B-TYPES, B-MSAL, B-ACTION-BASE, B-SOURCE-ENV, B-CONSUMER-BASE, B-VALIDATION, and CHK028’s cosign asset/signature gate open while unresolved; do not check all rows to imply completion.

<!-- sequential -->
- [ ] T041 [US4] Produce an evidence-backed outcome for each of the 33 linked PRs and 31 work items in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`: exact-target upgrade, approved fallback upgrade, verified already-satisfied/superseded, or blocked/incomplete. Every incomplete row must identify its blocker, affected scope/environment, evidence, responsible role, next action, and required human decision. Distinguish accounting completion from delivery; do not label the batch fully upgraded while any required install/check or included work is blocked, failed, or unrun.

**Checkpoint**: Story 4 is not “ready” because a checklist or evidence file is complete. Readiness requires two matching clean installs in every affected independent environment and all applicable required checks passing on the exact candidate; any remaining blocker keeps the affected result and whole-batch claim not ready.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Verify coverage, final integrity, and a reviewable human handover without widening scope.

<!-- sequential -->
- [ ] T042 Crosswalk the final PR/work-item outcomes and evidence against all 22 functional requirements, nine success criteria, and 20 acceptance scenarios in `C:\code\ama\specs\001-proxy-dependency-upgrades\spec.md`; verify the existing 16/16 checklist at `C:\code\ama\specs\001-proxy-dependency-upgrades\checklists\requirements.md` remains unchanged and that each readiness checklist finding links to evidence. Record any uncovered requirement or unresolved acceptance scenario as a blocker in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; do not create a later-phase artifact or change the approved spec to make a failed criterion appear satisfied.

<!-- sequential -->
- [ ] T043 Recheck final candidate hashes and compare every declaration, lock, workflow, source-setting, and protected-scope input after all validation runs; if an install/test altered an input or a feed/candidate changed, invalidate dependent runs and repeat the affected checks. Record the final integrity comparison in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`; report `B-VALIDATION` open for every unmet artifact-closure, clean-install, quality, security, runner, live-credential, or environment gate.

<!-- sequential -->
- [ ] T044 Write the final human handover in `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`, linking all 33 PR targets/outcomes to the 31 scoped work items, chosen/retained versions or full Action SHAs, two-run/source evidence, applicable checks, checklist findings, and blocker owner/next action. State clearly whether only accounting is complete, whether any upgrade is validated, and why the whole batch is or is not ready. No merge, close, update, comment, push, commit, workflow dispatch, publication, or deployment is authorized by the handover.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1, T001–T002)**: Starts from the approved baseline and freezes the exact inputs/environment record.
- **Foundational (Phase 2, T003–T005)**: Depends on Setup. B-SOURCE-ENV and B-CONSUMER-BASE must be closed for each dependent scope before its edits; baseline check failures are recorded, not waived.
- **User Story 1 (Phase 3, T006–T008)**: Depends on the frozen input and environment records. Delivers complete accounting only; it performs no dependency edit.
- **User Story 2 (Phase 4, T009–T017)**: Depends on Foundation and the 33-to-31 ledger. Each work item receives evidence or an explicit hold. T012–T016 do not unblock by passage of time.
- **User Story 3 (Phase 5, T018–T025)**: Depends on the work-item selection and cleared, scope-specific gates. T019–T021 can proceed as the one marked parallel group after T018 because each edits disjoint files. T022 reconciles them. T023 is a single serialized workflow writer. T024–T025 freeze the exact candidate before validation.
- **User Story 4 (Phase 6, T026–T041)**: Depends on T025. Two clean installs are required per affected independently resolved environment; use the actual recipe, source policy, and platform. All quality/security checks apply by scope. T039–T041 consolidate outcomes without hiding failures or holds.
- **Polish (Phase 7, T042–T044)**: Depends on all prior work. Handover may report not-ready; it may not convert an open hold into a pass.

### User Story Dependencies and Gate Propagation

- **US1 (P1)**: After T001–T005. Independent of dependency edits; MVP is the verified 33-PR/31-work-item account.
- **US2 (P1)**: After US1 and the source/baseline records. The exact target is preferred. A library fallback must be stable, lower than target, same major, and above baseline. Actions have no alternative-release fallback. A failed feed request is access-unavailable/unknown, never version absence.
- **US3 (P1)**: After T017 and T018. `NW-next` consolidates #149/#133/#132 only; `NU-next`, root Python, and agents Python remain independent. The shared pnpm lock has one writer. API and specify-cli locks remain protected unless a proved effect is separately scoped and gated.
- **US4 (P2)**: After final candidate hashes T025. Candidate/hash drift invalidates downstream evidence. Required checks cannot be suppressed; unavailable credentials, browser/OS sources, live staging, or sovereign runner capabilities are `blocked`/`not-run`, not passing.

Specific blocker propagation:

- **B-SOURCE-ENV / T003** blocks npm candidate edits (T019) and npm clean-install/artifact claims (T026–T028); public-feed fallback is never allowed.
- **B-CONSUMER-BASE / T004** blocks dependent pip/helper/container selections and readiness (T032–T033); uv locks cannot stand in for those resolutions.
- **B-ESLINT / T012**, **B-TYPES / T013**, and **B-MSAL / T014** block only their named web work items but prevent whole-batch completion until cleared or explicitly resolved through the human policy gate.
- **B-ACTION-BASE / T015–T016** blocks #105/#103 pin changes and outcomes. The separate #103 cosign asset/signature gap also blocks CHK028 and B-VALIDATION.
- **B-VALIDATION** remains batch-blocking until the final artifact closure, two-install pairs, and every applicable quality/security gate are evidenced. No task authorizes remote PR/workflow side effects.

### Plan Batch Mapping

- **B0 — Baseline/source controls**: T001–T008.
- **B1 — Python lock deltas**: T010, T017, T020–T021, T029–T033, T035.
- **B2 — npm runtime/parser deltas**: T009, T017, T019, T026–T028, T036–T037.
- **B3 — npm test tooling**: T009, T019, T026, T036–T037; ESLint/Node-types remain blocked at T012–T013.
- **B4 — Action pins**: T008, T011, T015–T016, T023, T034, T038; workflow edits are serialized.

### Parallel Opportunities

Only the explicit group below is approved for parallel execution; its three tasks share no files and have no unmet dependency after T018:

The single group is T019 (web/UI manifests and shared pnpm lock), T020 (root Python lock), and T021 (agents Python lock/manifests only when needed).

All three tasks defer writes to the shared evidence ledger until the sequential T022/T025 steps. The Action workflow edits serialize with source-policy changes and with each other. Validation records are consolidated sequentially into one `evidence.md`; no other task is marked `[P]`.

## Implementation Strategy

### MVP First — User Story 1 Only

1. Complete T001–T005 to establish the exact baseline, supported-environment matrix, source controls, and baseline check status.
2. Complete T006–T008 and independently audit the 33 PR links against 31 scoped work items and 55 Action references.
3. Stop. This MVP is an accounting/evidence increment only; it is not an upgrade, install, merge, or readiness claim.

### Incremental Delivery

1. Complete US2 source, compatibility, security, and selection evidence; leave T012–T016 explicitly blocked until their concrete evidence or an approved resolution exists.
2. Complete only T018–T025 for work items whose prerequisites have actually cleared; preserve unresolved holds and unrelated scopes.
3. Complete two-clean-install pairs for every affected environment, then every applicable quality/security gate (T026–T038).
4. Finish evidence, checklist, acceptance crosswalk, and human handover (T039–T044). Report any unresolved scope as blocked/incomplete; do not claim whole-batch readiness.

## Notes

- P/F/R/H directions and package/action evidence from the Plan are provisional; re-fetch/revalidate the exact final inputs.
- The approved library sources remain `https://packagefeedproxy.microsoft.io/npm/` and `https://packagefeedproxy.microsoft.io/pypi/simple`; official upstream GitHub is an Actions-only exception.
- Do not remove/relax security floors, overrides, integrity fields, quality checks, runner labels, permissions, or trigger protections.
- No broad dependency refresh, runtime migration, installer conversion, public-feed fallback, new service/framework, unapproved environment expansion, or unauthorised PR/remote mutation is in scope.
- No application/workflow/dependency files are changed by this Phase 5 document-generation output.
