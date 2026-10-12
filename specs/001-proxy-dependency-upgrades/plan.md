# Implementation Plan: Proxy-Constrained Dependency Upgrades

**Branch**: `001-proxy-dependency-upgrades` | **Date**: 2026-10-09  
**Spec**: `C:\code\ama\specs\001-proxy-dependency-upgrades\spec.md`  
**Input**: Approved clarified specification; orchestrator Phase 3 (Plan) only.  
**Baseline commit**: `62d249dc1205644fed934ea167df56695e92b3d2`  
**Status**: Prepared for the human Plan gate; implementation and upgrade readiness are **not approved**.

## Summary

Reconcile the fixed 33-PR inventory into 31 package-and-scope work items, then perform a finite maintenance batch using existing pnpm, uv, GitHub Actions and repository tests. Preserve every original PR, independently resolved scope, newer baseline and security override. Do not merge the PR branches: several are old, omit locks, or contain unrelated resolver churn.

Planning established lock baselines and exact PR changes, inspected approved-feed metadata, downloaded package files without installing them, and verified all five proposed Action source commits. `research.md` contains the 33-row decision matrix; `evidence.md` records observations and digests. Evidence-backed **delivery** counts are not established: no clean installs, application checks or final security validation ran.

The provisional directions are **12 proposed-target, one fallback, 15 retain/supersede, and five held PRs**. These are planning classifications, not completed upgrades. The held PRs are #150, #146, #144, #105 and #103. Native/transitive file coverage and final validation remain outstanding even for otherwise promising candidates.

## Technical Context

**Language/Version**: Existing Python 3.12 CI/container baseline; TypeScript 6.0.3; Node.js 24. The inspected Windows ARM64 host has Python 3.14.7, Node 24.16.0 and uv 0.11.21, and is not equivalent to the CI environments.  
**Primary Dependencies**: Existing pnpm 10.6.3 workspace; Next.js 16.3.6 web / 15.5.18 UI development dependency; React 19.2.6; ESLint 9.39.4; Playwright 1.59.1; FastAPI/Pydantic/Azure SDK dependency graphs. No new technology or automation framework. Exact candidates and companions are in `research.md`.  
**Storage**: Version-controlled Markdown batch evidence only; downloaded public artifacts remain in session scratch. No new database, service, telemetry store or cloud resource.  
**Testing**: Existing pytest/coverage/benchmark, ruff, mypy 2.0.0, import-linter, TypeScript compiler, Vitest/axe, Playwright, source-policy checks, workflow contract tests, CodeQL, gitleaks and Trivy. Commands and applicability are in `quickstart.md`.  
**Target Platform**: Ubuntu GitHub-hosted runners, Windows x64 Python CI, Python 3.12 Linux container builds, Node 24 glibc development/CI and the existing Alpine web Dockerfile. Preserve the current `linux/amd64` azd publication target; do not infer a multiarch deployment from stale comments.  
**Project Type**: One-off dependency maintenance of an existing monorepo; no new public or internal application interface.  
**Performance Goals**: Preserve the existing benchmark gate, coverage ratchet, build behaviour and safety-critical application behaviour; no new numerical SLA.  
**Constraints**: npm/Python artifacts only through their approved Microsoft proxies; official upstream exception only for Actions; no downgrade, weakened overrides, suppressed checks, unrelated upgrades, broad runtime migration, package-manager migration or remote mutations.  
**Scale/Scope**: 10 npm, 18 Python and five Action PRs. One pnpm workspace lock; root and agents uv locks are primary Python decision scopes. API and specify-cli locks were independently inspected and remain protected. Current Action usage is 55 active references across 25 workflows, not merely the lines present in the old PR patches.

## Constitution Check

*Gate assessed before research and re-evaluated after design against constitution v1.2.0.*

| Constitutional requirement | Design response | Pre-research / post-design |
| --- | --- | --- |
| I: life safety; II/III and emergency-management behaviours | No operational decision changes. Preserve regression, isolation, accessibility, scenario and benchmark gates; fail closed on an unsafe candidate. | PASS / PASS |
| IV: transparency and auditability | Immutable baseline and PR identities; per-scope decisions, retrieval evidence, validation status and named-owner blockers. No metadata-only completion claims. | PASS / PASS |
| Non-negotiable 1: human authorisation | Stop at Plan. No installs, application/workflow edits, commits, pushes, PR operations or deployment. Later execution and remote effects need their own approval. | PASS / PASS |
| VIII and non-negotiables 2–3: Azure, residency, privacy | No infrastructure or platform-data movement. Requests contain public dependency identities or authorised repository reads, not secrets or operational data. No widening of the Foundry carve-out. | PASS / PASS |
| Non-negotiables 4–5: interoperability and graceful degradation | Existing contracts remain unchanged; dependency-sensitive authentication, HTTP, streaming, offline and degraded-mode tests remain applicable. | PASS / PASS |
| Quality gates: lint, unit and integration before merge | Concrete existing checks and two clean installs per affected environment are required. Their execution status is NOT RUN, not PASS. Pre-existing failures are not waived. | PASS design / execution pending |
| Infrastructure What-If and public-output approval | No IaC or public warning changes; not applicable to this batch. Any scope expansion reopens the gate. | N/A / N/A |
| Governance | Approved spec and existing requirements checklist remain untouched; no constitutional exemption requested. | PASS / PASS |

**Planning gate**: constitution-compatible, suitable for human review with explicit blockers.  
**Delivery gate**: **ERROR / NOT READY** while any selected work lacks source, compatibility, security or validation evidence. Specification policy questions are resolved; failed/unrun observations are deliberately not converted into policy exceptions.

## Project Structure

### Documentation produced in this phase

Base directory: `C:\code\ama\specs\001-proxy-dependency-upgrades`

```text
spec.md                      # approved input; unchanged
checklists\requirements.md   # existing specification checklist; unchanged
plan.md                      # this implementation plan
research.md                  # decisions, 33-PR reconciliation and blockers
data-model.md                # finite evidence-record design, not runtime models
quickstart.md                # gated reproduction and validation procedure
evidence.md                  # baseline, PR provenance and retrieval observations
```

No `tasks.md`, new checklist, API schema or `contracts\` directory is generated. This internal maintenance batch introduces no interface to contract. Application contract tests are reused rather than replaced.

### Existing repository surfaces

All paths below are relative to `C:\code\ama`.

| Surface | Planned treatment after later authorisation |
| --- | --- |
| `package.json`, `pnpm-lock.yaml`, `pnpm-workspace.yaml` | Preserve root protections/workspace layout; one writer for the shared lock. No unrestricted update command. |
| `apps\web\package.json`, `packages\ui\package.json` | Apply independent approved choices, including necessary MSAL companions only if their evidence clears. No UI Next 15-to-16 normalisation. |
| `apps\web\eslint.config.mjs`, Vitest/Playwright/TypeScript configuration | Change only demonstrated compatibility breakage. Do not relax rules, skip tests or change expected behaviour to pass. |
| Root and `apps\agents` Python manifests/locks | Targeted independent lock updates; declarations already satisfying their scoped goals need no cosmetic edits. |
| `apps\api\uv.lock`, `tools\specify-cli\uv.lock`, other Python manifests | Protected comparison scopes, not blanket upgrade targets. Change only if a proved dependency effect requires it and is recorded. |
| `.github\workflows\*.yml` | Exact approved Action pins and necessary source-policy propagation. Preserve triggers, permissions, sovereign runner labels, quality gates and dormant jobs. |
| `.devcontainer\*`, application Dockerfiles, install helpers | Existing independently resolving consumers; reproduce their actual commands. No general conversion to uv or new build framework. |
| `tests\policy`, `tests\devops`, existing application suites | Existing validation surfaces; only narrowly justified compatibility coverage may be proposed during implementation. |

**Structure decision**: use the existing layout and a feature-local handover. Scratch probe scripts and downloaded packages are not implementation deliverables and must not be added to the repository.

## Resolved Scope and Environment Boundaries

| Resolution context | Baseline/effect | Required validation boundary |
| --- | --- | --- |
| pnpm `apps/web` importer | #149/#132/#133 consolidate to a 16.3.8 goal; the other six web package decisions retain their identities. | Entire workspace resolution, domain build, web build/types/lint/unit/a11y/E2E. Two fresh installs for each affected recorded platform. |
| pnpm `packages/ui` importer | #130 remains Next 15.5.21, independent of web Next 16. | Same shared-lock installs, separate importer assertions and UI consumer regression coverage. No fictitious second npm lock. |
| Root `uv.lock` | #111 advances idna 3.11 to 3.15; five other root PRs have newer retained candidates. | Python 3.12 Linux root development graph and existing Windows `windows-ci` graph, each twice. Preserve marker-specific resolutions. |
| `apps/agents/uv.lock` | h2/idna/setuptools/pydantic-settings need advances; eight PRs have retained candidates. | Separate Python 3.12 agents environment, twice; root results cannot stand in for this lock. |
| API and specify-cli standalone locks | API idna 3.20 and CLI idna 3.19 are not targets for a downgrade to 3.15. | Keep bytes unchanged unless an actual related change is justified. If affected later, add independent installs/gates before claiming readiness. |
| Linux pip CI, Docker builds and devcontainer helper | Several install from ranges, not from any uv lock. Installed baselines were **not** established by reading those locks. | Capture baseline/candidate resolutions using each actual recipe twice. Do not claim a lock-only change updates these environments, or impose root pins on a newer independent baseline. |
| Actions | checkout 42 uses; upload-artifact 10 uses (six already at proposed SHA); one use each for the other three. | Full source/asset re-retrieval twice per affected runner environment, exact SHA comparison, runner compatibility and applicable workflow gates. No live comments/publications without separate approval. |

For Linux container/development paths, record base-image digest, architecture and libc, not just a floating image tag. ARM64 wheel observations are additional development-platform evidence, not authorisation to change deployment architecture. Native Windows ARM64/Python 3.14 observations are diagnostic only unless explicitly included in the supported validation matrix.

## Minimal Batches and Dependency Order

These are planning units, not an execution task list. Every unit remains behind the human Plan and subsequent lifecycle gates.

| Batch | Scope and intended result | Prerequisite / stop condition |
| --- | --- | --- |
| B0 — Baseline and source controls | Freeze input hashes and the 33 PR heads; record baseline checks on actual supported install recipes; establish clean-runner npm proxy configuration and runtime/image versions. | Before any version edit. Unreachable sources or unverified independent baselines block the affected selection. |
| B1 — Python lock deltas | Root: idna 3.15. Agents: idna 3.15, h2 4.4.1 with hpack 4.2.0, setuptools 83.0.0, pydantic-settings 2.14.2. Retain 13 equal/newer Python outcomes subject to evidence. | B0. Keep root h2 4.4.1, setuptools 84.0.0, settings 2.15.0 and newer security versions; reject unrelated resolver churn. |
| B2 — npm runtime/parser deltas | Web Next 16.3.8; UI Next 15.5.21; js-yaml 4.3.1. Conditional MSAL React 5.7.2 + browser 5.24.0 + common 16.14.2 only when the companion source gap clears. | B0. Native Next/SWC/sharp and integrity coverage remain required. Matching version numbers alone do not justify a config upgrade. |
| B3 — npm test tooling | Playwright/test/playwright-core 1.63.0 as a coupled set. Tentative jsdom fallback 30.1.1, with Node 24 patch satisfying `>=24.15.0`. Hold ESLint 10 and Node 26 types pending blockers. | B2 because of the shared lock; B1 and the actual API environment before cross-stack E2E. Do not install optional canvas solely to satisfy an optional peer. |
| B4 — Action pins | checkout v7.0.1 SHA, remaining upload-artifact v6 SHA uses, comment v5 SHA. Keep #105/#103 blocked pending baseline provenance; verified proposed source SHAs are not sufficient. | B0; official provenance and runner prerequisites. Serialize shared workflow edits. No fallback release or job execution with unapproved remote effects. |

B1 and B2 have no package-file dependency on each other; B4 has no dependency on their version choices. Final cross-stack validation depends on the resulting candidate union. Retest after any shared-lock or workflow change rather than reusing evidence for a different candidate.

### Source-policy repair is necessary, not a new product

The inspected npm registry is configured in the developer's user context; no tracked root `.npmrc` exists and CI's global environment establishes Python sources but not npm. Some pnpm lock entries have only integrity, so a clean hosted runner must not be assumed to inherit the local registry.

During authorised implementation, establish a minimal credential-free repository npm registry setting and propagate `NPM_CONFIG_REGISTRY=https://packagefeedproxy.microsoft.io/npm/` to affected bootstrap/install jobs outside that configuration's context. Retain the Docker registry environment. Inspect actual retrieval routes; no extra/public feed or direct public tarball is an acceptable workaround. Do not introduce a source-selection service.

## Validation and Handover

`quickstart.md` maps concrete existing commands and runners to affected scopes. Required evidence includes:

- Baseline/candidate input hashes, effective source policy, resolved versions, marker/extras selection, runtime/OS/architecture and tool versions.
- Two independent, cache-empty installs **per affected independently resolved supported environment**, using identical candidate inputs. Compare installed graphs and Action SHAs; declarations, locks and workflow references must remain unchanged.
- Fresh approved-source retrieval and integrity evidence for native variants, transitive/build requirements and Action release assets actually needed by those environments.
- Applicable build, lint, strict typing, unit, integration, scenario, accessibility, workflow, benchmark and security results. Preserve coverage thresholds and marker exclusions.
- Separate `passed`, `failed`, `blocked` and `not-run` records. The same failure signature on an independently reproduced baseline demonstrates a pre-existing failure, not permission to waive it.
- A 33-row outcome record. A complete inventory or partial batch cannot be labelled fully upgraded; all readiness blockers must be closed for that claim.

No existing installation, cache or old catalogue replaces this evidence. Feed changes reopen decisions, including retained versions.

## Human Plan Gate

Review the five held PRs and cross-cutting blockers in `research.md`. The maintainer may approve proceeding through later planning gates with those holds intact. Removing a hold requires technical evidence; changing fallback, runtime or no-downgrade policy requires explicit specification-level approval, not an implementation workaround.

Agent context introduces no new technology. The standard context updater was run successfully in a disposable mirror to avoid unrelated formatting/history changes to `C:\code\ama\.github\agents\copilot-instructions.md`. Its output had no substantive context difference; the real guidance and manual additions remain byte-for-byte unchanged.

**Stop here:** no tasks/checklist generation, implementation, installation, test execution, commit, push, PR mutation, deployment or handoff is authorised by this document.

## Complexity Tracking

No constitutional violations or additional runtime abstractions. A feature-local evidence record and existing commands replace the rejected alternatives of an automation service, new persistence layer, resolver framework or global version-normalisation project.
