# Feature Specification: Proxy-Constrained Dependency Upgrades

**Feature Branch**: `001-proxy-dependency-upgrades`  
**Created**: 2026-10-09  
**Status**: Clarified — Phase 2 complete; awaiting approval to plan  
**Input**: User description:

> There is a large list of chores to bump up many libraries to the latest versions. These are documented as GitHub pull requests starting with the title starting as "chore".
> Although the update / upgrade is already suggested by the chore pull request, the version must be available in the package feed proxy; otherwise, the closest version available in the package feed proxy shall be used.

## Clarifications

### Round 1

- Q: Should the five GitHub Actions chore PRs be included? A: Include all five, with their source policy to be approved next. All 33 supplied PRs are in scope.
- Q: What source policy applies to the included GitHub Actions updates? A: Allow official upstream GitHub repositories and releases, with verified full commit-SHA pins and retrieval checks. This exception covers Actions only; npm and Python packages must still come through their configured proxies.
- Q: How should the closest library fallback be selected when the proposed version is unavailable or incompatible? A: Use the highest eligible stable version below the target within the target's major version; block if none exists. Compatibility, proxy retrieval, no-downgrade rules, and security protections still apply. Do not select a higher version or cross major versions as a fallback.
- Q: May an unavailable or incompatible Action target be replaced with an alternative release? A: No. Require the proposed target or a verified newer existing baseline; otherwise block the upgrade. Do not apply numeric closest-version ordering to commit hashes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Account for Every Upgrade Chore (Priority: P1)

As a repository maintainer, I want a complete, scope-aware account of the upgrade chores so that no request is lost, duplicate work is avoided, and older proposals do not undo newer dependencies.

**Why this priority**: An upgrade batch cannot be reviewed safely without knowing which requests and dependency contexts it covers.

**Independent Test**: Reconcile the supplied PR snapshot against a proposed batch record without changing any dependencies. Every PR must remain traceable to its scope decision and, when included, its upgrade decision.

**Acceptance Scenarios**:

1. **Given** the supplied snapshot contains 33 chore PRs, **When** the batch is recorded, **Then** all 33 PRs are individually accounted for and included: 28 library PRs and five GitHub Actions PRs, each subject to its approved source policy in FR-002.
2. **Given** several PRs concern the same library in the same dependency scope, **When** work is consolidated, **Then** one upgrade decision can satisfy several PRs while retaining every source PR, each requested target, and an individual outcome; conflicting targets are explicitly reconciled rather than discarded.
3. **Given** the same library appears in the root dependency context, an application, and a shared package, **When** the batch is consolidated, **Then** each distinct scope retains its own resolved baseline, compatibility assessment, and validation coverage even if the work or chosen version is shared.
4. **Given** the original PR version is older than the current declaration, or its precise scope is missing from the supplied snapshot, **When** its outcome is assessed, **Then** the actual resolved baseline and scope must be established before declaring it satisfied; unknown scope is an explicit blocker rather than an assumed root scope.
5. **Given** new or changed chore PRs appear after the recorded snapshot, **When** the batch is reviewed, **Then** the original 33 remain traceable, changes are disclosed, and additions or removals require an explicit scope decision rather than silently changing the denominator.

---

### User Story 2 - Choose an Obtainable, Compatible Version (Priority: P1)

As a maintainer, I want the proposed version, or an approved closest compatible alternative, to be obtainable through its approved source so that the upgrade can actually be used without bypassing the organisation's source policy. Libraries use the configured package feed proxies; Actions use the explicitly approved official upstream GitHub sources.

**Why this priority**: A publicly announced release is not a usable upgrade if its required package files cannot be obtained through the approved source.

**Independent Test**: Evaluate recorded examples of an obtainable target, an absent version, an incompatible package file, and an inaccessible feed. A reviewer must distinguish their outcomes and reproduce the selection from the same evidence and approved policy.

**Acceptance Scenarios**:

1. **Given** the requested target is compatible, meets existing security constraints, is not a downgrade, and its required files are retrievable under FR-002, **When** the upgrade is selected, **Then** the exact target is preferred and the scope, source, version or verified full commit SHA, retrieval time, required environments, and retrieval result are recorded.
2. **Given** a library feed is accessible but the target version or a package file needed for a supported environment is absent, or the target is incompatible, **When** alternatives are evaluated, **Then** the highest eligible stable version below the target within the target's major version is selected, with evidence explaining the rejected target and rejected alternatives. If no candidate advances the verified baseline without violating the constraints, the work item remains blocked; a higher or different-major fallback is not allowed.
3. **Given** authentication failure, denied access, timeout, rate limiting, or a feed service error prevents a trustworthy check, **When** availability is assessed, **Then** the result is feed/access unavailable or unknown, not proof that the version is absent; dependent selection is blocked and no public-feed fallback is used.
4. **Given** public release metadata, a proxy catalogue entry, an Actions tag, or previously cached files exist, **When** availability is claimed, **Then** that information alone is insufficient: retrieval of the actual files required for the recorded environments through the approved source must be evidenced. Each Action must resolve to a verified full commit SHA in its official repository, and any required action-specific release assets must have retrieval and integrity evidence.
5. **Given** no eligible upgrade can be obtained, **When** the work item is reported, **Then** its existing version is not downgraded, the unavailable or incompatible choices are explained, and the upgrade remains blocked or incomplete rather than being counted as delivered.
6. **Given** the feed or candidate set changes after initial investigation, **When** final readiness is assessed, **Then** the evidence is tied to the final validation runs; failed revalidation reopens the blocker and earlier success is not presented as current availability.
7. **Given** an included Action's proposed release or commit is unavailable, unverifiable, or incompatible, **When** the decision is recorded, **Then** the upgrade is blocked rather than replaced with an alternative release, unless the existing baseline is demonstrably newer and satisfies the same source, compatibility, security, and validation requirements. Commit timestamps or lexical hash ordering alone cannot prove that a baseline is newer.

---

### User Story 3 - Preserve a Consistent, Secure Dependency Baseline (Priority: P1)

As a maintainer responsible for application stability, I want dependency declarations and resolved versions to agree across every affected scope without weakening existing protections, so that an apparent upgrade does not introduce a downgrade or hidden regression.

**Why this priority**: A version-range edit alone can leave users running an older package, and an older chore proposal must not weaken a newer security baseline.

**Independent Test**: Compare an affected scope's before-and-after dependency records, security constraints, and resolved versions. Include an intentionally stale resolution and a proposed version below an existing security minimum.

**Acceptance Scenarios**:

1. **Given** a selected version affects several declarations or independently resolved dependency records, **When** the upgrade is considered complete, **Then** every affected declaration and lock agrees with that scope's approved version decision; unrelated scopes are not forced onto a common version merely because the library name matches.
2. **Given** a declaration permits the requested version but the resolved dependency remains older, **When** fulfilment is reviewed, **Then** the PR is not marked complete from the declaration alone and the discrepancy is resolved or reported as a blocker.
3. **Given** the verified current resolution is newer than a PR target, **When** the PR is reconciled, **Then** the newer version is retained rather than downgraded and is labelled already satisfied or superseded only after proxy retrieval, compatibility, security, and validation evidence support that outcome.
4. **Given** a candidate or a required related dependency change would reduce an existing resolved version, violate a security minimum, weaken an override, or introduce a known security regression, **When** it is reviewed, **Then** it is rejected or blocked; necessary related changes are disclosed, unrelated churn is excluded, and protective checks are not disabled to obtain a pass.

---

### User Story 4 - Verify and Hand Over a Reproducible Batch (Priority: P2)

As a release reviewer, I want reproducible installation and validation evidence plus an honest list of unresolved blockers, so that I can judge readiness without assuming that an edited file or an unrun check proves success.

**Why this priority**: Complete accounting is valuable on its own, but approval of the upgrades also requires evidence that the repository still works.

**Independent Test**: Review a candidate batch's evidence pack containing successful, failed, blocked, and not-run examples. Verify that another maintainer can repeat the stated checks and cannot mistake partial completion for full readiness.

**Acceptance Scenarios**:

1. **Given** a candidate dependency set and its recorded supported environments, **When** two clean installations are performed for each affected independently resolved environment using the same inputs, **Then** both obtain library packages through the configured proxies and Actions through their approved official sources, produce the same resolved versions and full Action commit SHAs, and leave declarations, locks, and workflow references unchanged.
2. **Given** an affected scope is proposed as ready, **When** the repository's applicable build, lint, type-check, unit-test, integration-test, and other required checks are reviewed, **Then** all have recorded passing results for the candidate baseline; a non-applicable check has an explicit rationale and is not recorded as a passed execution.
3. **Given** a check fails, cannot run, or has not run, **When** the handover is prepared, **Then** its status, affected scopes and PRs, cause, evidence, responsible role, and next action are stated; pre-existing failures are distinguished using baseline evidence but are not silently waived.
4. **Given** the accounting record is complete but some included work remains blocked, **When** completion is reported, **Then** the report distinguishes accounting completion from upgrade readiness, links every PR to its outcome and evidence, and does not claim the whole batch is ready. No merge, close, update, push, deployment, or later lifecycle phase is authorised merely by producing the report.

### Edge Cases

- Several PRs propose different targets for one scope, while another PR for the same library covers a genuinely different scope. Preserve both source traceability and separate compatibility decisions.
- A newer declaration or security override coexists with an older resolved version. Investigate the actual resolution; neither the declaration nor the original PR baseline proves fulfilment.
- The target is in the proxy catalogue but its package file is missing, corrupt, withdrawn, or unavailable for a required runtime or platform. Do not equate catalogue visibility with an installable package.
- A proxy cannot be reached, returns a permission error, or suffers a partial outage. Do not infer version absence from an untrustworthy response or switch to a public feed.
- A package reference would retrieve files directly from a public source instead of the configured proxy. Treat the source-policy breach as a blocker, not an acceptable availability workaround.
- Only an older-than-current, incompatible, prerelease, or security-disallowed alternative can be found. Do not silently accept it to reduce the outstanding count.
- Library alternatives lie above and below the target or cross release boundaries. Only lower stable versions within the target's major are eligible; choose the highest eligible version that advances the verified baseline. A candidate in another minor within the same major is allowed; a higher or different-major fallback is not.
- Different environments need different package files for the same version. Evidence must cover every affected supported environment; one successful download cannot stand in for all of them.
- Existing caches allow an installation to succeed while the proxy no longer supplies the package. Final clean-install evidence must not rely solely on those caches.
- A transitive dependency or a shared lock affects more scopes than the originating PR mentions. Include those effects in consistency and regression checks without merging their identities.
- A validation failure predates the upgrade, required credentials or services are unavailable, or an affected scope lacks baseline evidence. State the limitation and resulting readiness blocker; do not invent a pass.
- GitHub Actions targets include both release tags and commit identifiers and are not library versions supplied by the two confirmed package feeds. Use the proposed target or a verified newer existing baseline; an unavailable or incompatible target does not authorise an alternative release. Their approved official-source exception does not permit fetching npm or Python dependencies from public feeds.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The batch MUST account for all 33 supplied chore PRs by identifier, link, ecosystem, package or action, proposed target, affected scope, and inclusion status. Each included PR MUST remain traceable to its work item and eventual outcome.
- **FR-002**: The batch MUST include all 33 supplied PRs: 28 library PRs and five GitHub Actions PRs. npm and Python package files MUST come through their configured proxies. Actions MAY be retrieved from their official upstream GitHub repositories and releases, but every changed Action reference MUST use a verified full commit-SHA pin. Required action-specific release assets MUST be retrievable from their official upstream sources with verified integrity. This Actions-only exception MUST NOT permit public-feed bypass for npm or Python packages.
- **FR-003**: Consolidation MUST use package identity and dependency scope, not package name alone. Several PRs MAY share a work item, but no source PR, proposed target, distinct resolution context, or required validation coverage may be lost.
- **FR-004**: Each work item MUST reconcile all its PR targets against its verified current baseline. The highest proposed release version for the same scope is the initial batch goal; lower proposals remain individually accounted for, and a newer verified current version MUST NOT be replaced with an older proposal. Commit-only Action targets MUST be reconciled using verified official repository history or release provenance, never lexical hash ordering or timestamps alone; incomparable targets remain blocked for explicit resolution.
- **FR-005**: The batch MUST record the scope snapshot and baseline used for decisions. Unspecified scopes MUST be established before selection; later PR or baseline changes MUST be disclosed and reconciled rather than silently expanding, shrinking, or invalidating the batch.
- **FR-006**: Fulfilment and supersession decisions MUST use actual resolved versions in every affected dependency context, not declaration ranges, cached installations, or PR descriptions alone.
- **FR-007**: The work item's reconciled PR target from FR-004 MUST be preferred over an alternative when it is eligible and retrievable, unless a newer verified current version is being retained. Eligibility requires compatibility with supported environments, dependency relationships, existing security constraints, and the no-downgrade rule.
- **FR-008**: Availability evidence MUST demonstrate retrieval of the actual files needed for the affected supported environments with valid identity and integrity under FR-002: library packages through the configured proxies; Action source at the verified full commit SHA and required action-specific release assets through official upstream GitHub sources. Public release information, catalogue visibility, tags, or cached files alone MUST NOT qualify. Direct public-feed bypass for library packages MUST NOT be used.
- **FR-009**: Evidence MUST distinguish obtainable versions, conclusively absent versions, missing or incompatible package files, failed integrity checks, and feed/access failures or unknown results. A feed/access failure MUST block dependent availability conclusions instead of being relabelled as version absence.
- **FR-010**: A library fallback MUST be the highest eligible stable version strictly below the reconciled PR target and within that target's major version, using the ecosystem's version ordering. Candidates MUST meet FR-007 and FR-008 and advance the verified current resolution to count as an upgrade. Crossing minor versions within the target major is allowed; selecting a higher or different-major fallback is prohibited. Rejected alternatives and the chosen ordering MUST be recorded; an empty or ambiguous eligible set MUST remain blocked rather than use an arbitrary selection. Actions MUST use the proposed release or commit, resolved to a verified full commit SHA, or retain a verified newer existing baseline under FR-014. Alternative Action releases are not authorised; an unusable target without an eligible newer baseline MUST remain blocked.
- **FR-011**: If no candidate satisfies the approved selection, compatibility, security, source, and no-downgrade constraints, the work item MUST remain blocked or incomplete with a stated reason; retaining the existing version in that situation MUST NOT be misreported as a delivered upgrade.
- **FR-012**: Every selected or retained version MUST have an evidence record linking its PRs, scope, original targets, verified current resolution, chosen version or full Action commit SHA, observed alternatives, source, observation time, retrieval and integrity results, compatibility assessment, and selection rationale. The record MUST be revalidated against final installation results and MUST NOT disclose credentials.
- **FR-013**: Every affected declaration, resolved lock, and Action workflow reference MUST consistently represent its scope's approved version or full commit-SHA decision, including shared and independently maintained resolution contexts. Consistency MUST NOT require unrelated scopes to use one global version.
- **FR-014**: The batch MUST NOT reduce any changed existing library or Action below its verified pre-change baseline in the same dependency context. A newer current version MAY satisfy or supersede older PR goals only with the same source, compatibility, security, and validation evidence required for a changed version. A newer Action baseline MUST be established through official release ordering or verified repository ancestry and provenance; an incomparable commit, a later timestamp, or an apparent hash order MUST NOT qualify.
- **FR-015**: Existing security-related minimum versions, overrides, and protective quality checks MUST NOT be silently weakened or removed. The batch MUST NOT introduce a known security regression relative to its verified baseline; conflicts MUST be reported as blockers rather than resolved by lowering protection.
- **FR-016**: Related dependency or compatibility changes MUST be limited to those necessary for the included upgrades, with their reasons and affected scopes recorded. Unrelated upgrades, scope-wide version normalisation, and unexplained dependency churn MUST be excluded.
- **FR-017**: Readiness evidence MUST include two clean installations per affected independently resolved environment using the same recorded baseline and supported environment inputs. Both MUST retrieve required library packages through the configured proxies and Actions through their approved official sources, resolve the same versions and full Action commit SHAs, and leave declarations, locks, and workflow references unchanged.
- **FR-018**: Each affected scope MUST satisfy the repository's applicable build, lint, type-check, unit-test, integration-test, and other required quality checks without disabling checks or weakening expectations to conceal regression. Check applicability MUST be recorded with reasons; the project's required gates cannot be waived by this specification.
- **FR-019**: Validation records MUST distinguish passed, failed, blocked, and not-run checks and identify their baseline, affected scopes, evidence, and reproducible conditions. Each blocker MUST state its cause or uncertainty, impacted PRs, responsible role, and next action; pre-existing failures MUST be distinguished by evidence, not assumption.
- **FR-020**: The final accounting MUST give every included PR an evidence-backed outcome: exact-target upgrade, approved fallback upgrade, verified already-satisfied or superseded, or blocked/incomplete. Excluded PRs MUST retain their policy reason. Complete accounting MUST NOT be described as full upgrade completion while included work or required checks remain blocked, failed, or unrun.
- **FR-021**: Maintainers MUST receive a reviewable handover linking PR outcomes, version decisions, consistency checks, validation results, and blockers, sufficient for another maintainer to reproduce the conclusions without relying on the original author's unstated knowledge.
- **FR-022**: This feature MUST remain a bounded upgrade chore batch, not a new dependency automation service. Neither this specification nor the batch report authorises merging, closing, updating, or commenting on existing PRs, pushing changes, deployment, or bypassing human lifecycle gates; those actions require separate explicit authorisation.

### Key Entities *(include if feature involves data)*

- **Chore PR**: A supplied upgrade proposal, identified by repository and PR number, with package or action, original and target versions where known, scope, inclusion decision, and individual outcome.
- **Dependency Scope**: An application, shared package, root dependency context, or separately resolved environment whose compatibility and resolved versions must be assessed independently.
- **Upgrade Work Item**: One package-and-scope decision linked to one or more PRs, its verified baseline, proposed targets, selected or retained version, rationale, and completion status.
- **Availability and Selection Evidence**: Time-bound observations of the approved source, considered versions, required package files, retrieval and integrity outcomes, compatibility constraints, and the approved selection policy.
- **Validation Record**: Reproduction conditions and results for installations and quality checks, linked to the exact candidate baseline and affected scopes.
- **Blocker**: An unresolved scope, policy, source, compatibility, consistency, security, or validation problem with affected work items, evidence, responsible role, and next action.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 33 supplied PRs have a traceable scope decision, and 100% of included PRs link to an individual outcome and supporting work item; zero PRs disappear through consolidation or exclusion.
- **SC-002**: Review of the complete batch finds zero cases where different dependency scopes were collapsed solely because a package name matched, and 100% of consolidated proposals retain their original targets and separate outcomes.
- **SC-003**: For 100% of selected or retained versions claimed ready, reviewers can verify retrieval of the required files for all affected supported environments under FR-002: library packages through approved proxies and Actions through verified full commit-SHA pins and official upstream sources. Zero availability claims rely only on public metadata, catalogue listings, tags, or pre-existing caches.
- **SC-004**: Given the same recorded candidate evidence and FR-010 selection policy, two maintainers independently reach the same version decision for every fallback work item, including whether it must remain blocked.
- **SC-005**: Comparison with the verified baseline finds zero downgraded existing libraries or Actions in the same dependency context, zero weakened security constraints or protective checks, and zero newly introduced known security regressions.
- **SC-006**: Every affected independently resolved environment has two successful clean installations with identical resolved versions and Action commit SHAs and no resulting changes to recorded declarations, locks, or workflow references before that environment is labelled ready.
- **SC-007**: For every scope labelled ready, 100% of applicable required quality checks have passing evidence for the candidate baseline; no failed, blocked, or unrun check is represented as passed.
- **SC-008**: At handover, 100% of included PRs have either a verified completion outcome or an actionable blocker. The batch is labelled fully upgrade-complete only when every included PR has a verified completion outcome and zero unresolved readiness blockers remain.
- **SC-009**: In acceptance review, a maintainer other than the preparer can correctly identify each PR's outcome, chosen-version rationale, source evidence, validation status, and any next action from the delivered record alone, with zero requests for missing decision information.

## Scope and Boundaries

- **Included**: A one-time, reviewable upgrade batch for all 28 supplied library chores and all five supplied GitHub Actions chores; source-constrained version selection; necessary related compatibility work; consistent declarations and resolved locks; reproducible validation; and explicit accounting of unsupported or blocked upgrades.
- **Policy decisions**: Scope, sources, library fallback ordering, and the exact-target/no-fallback Action policy are clarified. No version availability, actual fallback selection, or successful execution is asserted by this specification.
- **Excluded**: A new dependency automation service; unrelated feature work or broad runtime migrations; unbounded pursuit of newly published releases; public-feed bypass; weakened security policy; and unauthorised PR lifecycle operations, commits, pushes, or deployments.
- **Specification and clarification boundary**: Phases 1 and 2 produce only the feature specification and its specification-quality checklist. Planning, task generation, analysis, review, dependency edits, application or workflow changes, installations, and project test execution belong to separately authorised later phases.

## Assumptions and Dependencies

### Assumptions

- The orchestrator's supplied inventory is the Phase 1 source of truth: 10 library PRs from the npm ecosystem, 18 Python library PRs, and five GitHub Actions PRs. It has not been independently re-inventoried for this specification.
- The proposed chore targets define the batch goals; "latest" does not authorise an open-ended search for unrelated newer releases. A same-scope higher current version is retained when verified rather than downgraded. Library fallbacks follow FR-010; Actions require the proposed target or a verified newer existing baseline.
- Stable releases are the default candidate population. Prerelease adoption, changed supported runtimes, or weakened security constraints are not implicitly authorised by a request to upgrade libraries.
- Supported runtimes, platforms, compatibility expectations, and required quality gates are those already established by the repository for affected scopes. Identifying their exact validation coverage belongs to Plan, not a new implementation design in this specification.
- "Clean installation" means an isolated installation from the recorded dependency inputs that demonstrates current proxy retrieval rather than relying solely on previously installed or cached packages.
- The supplied current declarations, including cryptography `>=50.0.0,<51` and the pyjwt override `>=2.14.0,<3`, are warning signals that some proposals may already be superseded. They are not proof of actual resolved versions or security outcomes.
- Required scope information missing from the compact inventory will be verified before implementation. A scope marked "not supplied" below must not be assumed to mean the repository root.

### Dependencies

- The configured library sources supplied by the orchestrator are `https://packagefeedproxy.microsoft.io/npm/` and `https://packagefeedproxy.microsoft.io/pypi/simple`. They are source-policy constraints, not evidence that any requested release or package file is currently available.
- The user approved official upstream GitHub repositories and releases for the five included Actions, subject to full commit-SHA pins and retrieval/integrity checks. This approval does not establish availability or authorise public npm/Python sources.
- Authorised access to those proxies, required package files, and the supported validation environments is necessary for later availability and reproducibility checks. Availability failures must remain explicit blockers.
- Current repository declarations, all affected resolution records, existing security overrides, and required quality gates must be available for baseline and final comparison.
- The scope and selection policy decisions are recorded in Clarifications. Planning requires approval at the Phase 2 human gate; approval of this specification is not evidence of package or Action availability.

## Supplied PR Baseline

Source: the orchestrator-provided inventory, supplied on 2026-10-09. The versions below are proposal history, not verified current resolutions, confirmed proxy releases, or test results. "Not supplied" denotes missing scope information, not an inferred root scope.

### Library Chores — Included (28)

| PR | Ecosystem | Library | Proposed change | Supplied scope |
| --- | --- | --- | --- | --- |
| [#149](https://github.com/johnbilliris/ama/pull/149) | npm | next | 16.3.6 → 16.3.8 | `apps\web` |
| [#150](https://github.com/johnbilliris/ama/pull/150) | npm | eslint | 9.39.4 → 10.12.0 | `apps\web` |
| [#148](https://github.com/johnbilliris/ama/pull/148) | npm | jsdom | 25.0.1 → 30.1.2 | `apps\web` |
| [#147](https://github.com/johnbilliris/ama/pull/147) | npm | @playwright/test | 1.59.1 → 1.63.0 | `apps\web` |
| [#146](https://github.com/johnbilliris/ama/pull/146) | npm | @types/node | 22.13.10 → 26.6.4 | `apps\web` |
| [#144](https://github.com/johnbilliris/ama/pull/144) | npm | @azure/msal-react | 5.3.2 → 5.7.2 | `apps\web` |
| [#133](https://github.com/johnbilliris/ama/pull/133) | npm | next | 16.2.6 → 16.2.11 | Root lock scope |
| [#137](https://github.com/johnbilliris/ama/pull/137) | npm | js-yaml | 4.1.1 → 4.3.1 | Not supplied |
| [#132](https://github.com/johnbilliris/ama/pull/132) | npm | next | 16.2.6 → 16.2.11 | `apps\web` |
| [#130](https://github.com/johnbilliris/ama/pull/130) | npm | next | 15.5.18 → 15.5.21 | `packages\ui` |
| [#135](https://github.com/johnbilliris/ama/pull/135) | Python | cryptography | 46.0.7 → 50.0.0 | Not supplied |
| [#136](https://github.com/johnbilliris/ama/pull/136) | Python | h2 | 4.3.0 → 4.4.1 | `apps\agents` |
| [#111](https://github.com/johnbilliris/ama/pull/111) | Python | idna | 3.11 → 3.15 | Not supplied |
| [#134](https://github.com/johnbilliris/ama/pull/134) | Python | aiohttp | 3.13.5 → 3.14.3 | `apps\agents` |
| [#121](https://github.com/johnbilliris/ama/pull/121) | Python | msgpack | 1.1.2 → 1.2.1 | Not supplied |
| [#116](https://github.com/johnbilliris/ama/pull/116) | Python | pyjwt | 2.12.1 → 2.13.0 | Not supplied |
| [#124](https://github.com/johnbilliris/ama/pull/124) | Python | python-engineio | 4.13.1 → 4.13.2 | Not supplied |
| [#123](https://github.com/johnbilliris/ama/pull/123) | Python | python-socketio | 5.16.1 → 5.16.2 | Not supplied |
| [#129](https://github.com/johnbilliris/ama/pull/129) | Python | setuptools | 82.0.1 → 83.0.0 | `apps\agents` |
| [#128](https://github.com/johnbilliris/ama/pull/128) | Python | pyasn1 | 0.6.3 → 0.6.4 | `apps\agents` |
| [#127](https://github.com/johnbilliris/ama/pull/127) | Python | mcp | 1.27.1 → 1.28.1 | `apps\agents` |
| [#126](https://github.com/johnbilliris/ama/pull/126) | Python | python-socketio | 5.16.1 → 5.16.2 | `apps\agents` |
| [#125](https://github.com/johnbilliris/ama/pull/125) | Python | python-engineio | 4.13.1 → 4.13.2 | `apps\agents` |
| [#112](https://github.com/johnbilliris/ama/pull/112) | Python | idna | 3.11 → 3.15 | `apps\agents` |
| [#120](https://github.com/johnbilliris/ama/pull/120) | Python | starlette | 1.0.0 → 1.3.1 | `apps\agents` |
| [#115](https://github.com/johnbilliris/ama/pull/115) | Python | pyjwt | 2.12.1 → 2.13.0 | `apps\agents` |
| [#122](https://github.com/johnbilliris/ama/pull/122) | Python | pydantic-settings | 2.14.1 → 2.14.2 | `apps\agents` |
| [#117](https://github.com/johnbilliris/ama/pull/117) | Python | python-multipart | 0.0.28 → 0.0.31 | `apps\agents` |

### GitHub Actions Chores — Included, Official Upstream Sources Approved (5)

| PR | Action | Proposed change | Scope decision |
| --- | --- | --- | --- |
| [#145](https://github.com/johnbilliris/ama/pull/145) | actions/checkout | 4 → 7 | Included; official upstream, full SHA required |
| [#143](https://github.com/johnbilliris/ama/pull/143) | actions/upload-artifact | 4 → 6 | Included; official upstream, full SHA required |
| [#105](https://github.com/johnbilliris/ama/pull/105) | gitleaks/gitleaks-action | `dcedce43c6f43de0b836d1fe38946645c9c638dc` → `ff98106e4c7b2bc287b24eaf42907196329070c7` | Included; official upstream, full SHA required |
| [#103](https://github.com/johnbilliris/ama/pull/103) | sigstore/cosign-installer | `f713795cb21599bc4e5c4b58cbad1da852d7eeb9` → `398d4b0eeef1380460a10c8013a76f728fb906ac` | Included; official upstream, full SHA required |
| [#102](https://github.com/johnbilliris/ama/pull/102) | peter-evans/create-or-update-comment | 4 → 5 | Included; official upstream, full SHA required |
