# Research: finite proxy-constrained upgrade batch

**Feature**: `C:\code\ama\specs\001-proxy-dependency-upgrades`  
**Date**: 2026-10-09 (Australia/Sydney)  
**Reference baseline**: `62d249dc1205644fed934ea167df56695e92b3d2`  
**Evidence**: `C:\code\ama\specs\001-proxy-dependency-upgrades\evidence.md`

This is planning research, not an installation or security attestation. Research used existing local parsers/tooling, read-only `gh api` calls for exactly the supplied PRs, approved proxy metadata, and direct artifact retrieval into session scratch. No research agents, application tests, package installs, PR mutations or later-phase agents were invoked.

## R1 — Reconcile proposals against resolved, independent scopes

**Decision**: retain the original denominator of 33 and use 31 work items. Consolidate #149/#132/#133 only: all affect web Next.js and its importer in the single root pnpm lock. Keep #130 as the UI package's independent Next.js 15 decision. Keep duplicate Python PRs as root-versus-agents lock decisions.

**Rationale**: read-only PR file/patch inspection established all previously missing scopes. #137 changes `apps\web\package.json` and `pnpm-lock.yaml`; #135 changes the root Python manifest/lock; #111/#121/#116/#124/#123 change the root `uv.lock`. No app-local npm locks exist at this baseline. The API and specify-cli uv locks really are separate and must not be collapsed into root.

**Alternatives considered**: applying all PR patches (stale or incomplete locks and unrelated churn); consolidating by name only (loses Python scope identity); upgrading all Next consumers to 16 (unauthorised normalisation). Rejected.

### Complete proposal-to-decision matrix

Paths in the scope column are relative to `C:\code\ama`. `NW` = web importer in root `pnpm-lock.yaml`; `NU` = UI importer in that same lock; `PR` = root `uv.lock`; `PA` = `apps\agents\uv.lock`.

Directions: **P** proposed-target direction; **F** tentative policy fallback; **R** retain/supersede direction; **H** held. None is a final completion outcome. Every row still requires final source, compatibility, security and validation evidence.

| PR | Work item / scope | Original target | Resolved baseline now | Planning direction and reason |
| --- | --- | --- | --- | --- |
| [#149](https://github.com/johnbilliris/ama/pull/149) | NW-next | 16.3.8 | 16.3.6 | **P** 16.3.8; highest same-scope goal; tarball verified, native graph pending. |
| [#150](https://github.com/johnbilliris/ama/pull/150) | NW-eslint | 10.12.0 | 9.39.4 | **H** B-ESLINT: target 404; 10.11.0 bytes verified but required plugins exclude ESLint 10. |
| [#148](https://github.com/johnbilliris/ama/pull/148) | NW-jsdom | 30.1.2 | 25.0.1 | **F** 30.1.1, highest lower stable major-30 catalogue version; bytes verified, Node patch/transitive/test checks pending. |
| [#147](https://github.com/johnbilliris/ama/pull/147) | NW-playwright | 1.63.0 | 1.59.1 | **P** 1.63.0 with playwright/core 1.63.0; all three npm archives verified; browsers/runner tests pending. |
| [#146](https://github.com/johnbilliris/ama/pull/146) | NW-node-types | 26.6.4 | 22.13.10 | **H** B-TYPES: bytes verified, Node 24 API/runtime compatibility not established. |
| [#144](https://github.com/johnbilliris/ama/pull/144) | NW-msal-react | 5.7.2 | 5.3.2 | **H** B-MSAL: target/browser bytes verified; required common 16.14.2 source evidence unresolved. |
| [#133](https://github.com/johnbilliris/ama/pull/133) | NW-next | 16.2.11 | 16.3.6 | **R** older proposal; shares the 16.3.8 goal with #149; not a separate root package. |
| [#137](https://github.com/johnbilliris/ama/pull/137) | NW-js-yaml | 4.3.1 | 4.1.1 | **P** 4.3.1; web declaration and shared lock, including affected transitive consumers. |
| [#132](https://github.com/johnbilliris/ama/pull/132) | NW-next | 16.2.11 | 16.3.6 | **R** older proposal; same work item as #149/#133, separately traceable. |
| [#130](https://github.com/johnbilliris/ama/pull/130) | NU-next | 15.5.21 | 15.5.18 | **P** 15.5.21; no move to web's Next major. |
| [#135](https://github.com/johnbilliris/ama/pull/135) | PR-cryptography | 50.0.0 | 50.0.1 | **R** 50.0.1; retain `>=50.0.0,<51`, not the older PR patch. |
| [#136](https://github.com/johnbilliris/ama/pull/136) | PA-h2 | 4.4.1 | 4.3.0 | **P** 4.4.1 with hpack 4.2.0; root h2 already differs. |
| [#111](https://github.com/johnbilliris/ama/pull/111) | PR-idna | 3.15 | 3.11 | **P** 3.15 in root only; newer API/CLI locks are protected. |
| [#134](https://github.com/johnbilliris/ama/pull/134) | PA-aiohttp | 3.14.3 | 3.14.3 | **R** exact target already locked; manifest floor agrees, completion still unverified. |
| [#121](https://github.com/johnbilliris/ama/pull/121) | PR-msgpack | 1.2.1 | 1.2.2 | **R** retain 1.2.2. |
| [#116](https://github.com/johnbilliris/ama/pull/116) | PR-pyjwt | 2.13.0 | 2.15.0 | **R** retain 2.15.0 and security override `>=2.14.0,<3`. |
| [#124](https://github.com/johnbilliris/ama/pull/124) | PR-engineio | 4.13.2 | 4.14.0 | **R** retain 4.14.0; wheel retrieval succeeded after a transient connection failure. |
| [#123](https://github.com/johnbilliris/ama/pull/123) | PR-socketio | 5.16.2 | 5.17.0 | **R** retain 5.17.0 with its existing engineio relationship. |
| [#129](https://github.com/johnbilliris/ama/pull/129) | PA-setuptools | 83.0.0 | 82.0.1 | **P** 83.0.0; do not copy root's already newer 84.0.0 into this decision. |
| [#128](https://github.com/johnbilliris/ama/pull/128) | PA-pyasn1 | 0.6.4 | 0.6.4 | **R** exact target already locked. |
| [#127](https://github.com/johnbilliris/ama/pull/127) | PA-mcp | 1.28.1 | 1.30.0 | **R** retain 1.30.0; existing declaration already requires at least 1.28.1. |
| [#126](https://github.com/johnbilliris/ama/pull/126) | PA-socketio | 5.16.2 | 5.17.0 | **R** independent agents record, not absorbed by #123. |
| [#125](https://github.com/johnbilliris/ama/pull/125) | PA-engineio | 4.13.2 | 4.14.0 | **R** independent agents record, not absorbed by #124. |
| [#112](https://github.com/johnbilliris/ama/pull/112) | PA-idna | 3.15 | 3.11 | **P** 3.15, separately resolved/validated from #111. |
| [#120](https://github.com/johnbilliris/ama/pull/120) | PA-starlette | 1.3.1 | 1.7.0 | **R** retain 1.7.0; no downgrade to an old security proposal. |
| [#115](https://github.com/johnbilliris/ama/pull/115) | PA-pyjwt | 2.13.0 | 2.15.0 | **R** retain 2.15.0 and agents' `PyJWT[crypto]>=2.14.0,<3`. |
| [#122](https://github.com/johnbilliris/ama/pull/122) | PA-settings | 2.14.2 | 2.14.1 | **P** 2.14.2; root settings 2.15.0 remains distinct. |
| [#117](https://github.com/johnbilliris/ama/pull/117) | PA-multipart | 0.0.31 | 0.0.32 | **R** retain 0.0.32. |
| [#145](https://github.com/johnbilliris/ama/pull/145) | AC-checkout / active workflows | v7 / `3d3c42e5…` | 32 uses at `93cb6efe…`; 10 at v4 | **P** full proposed SHA verified as v7.0.1; release ordering, runner and workflow checks required. |
| [#143](https://github.com/johnbilliris/ama/pull/143) | AC-upload / active workflows | `b7c566a7…` | Six already at target; three `ea165f8d…`; one v4 | **P** retain six and change four uses only after validation; not wholly already satisfied. |
| [#105](https://github.com/johnbilliris/ama/pull/105) | AC-gitleaks / security-scan | `ff98106e…` | `dcedce43…` | **H** B-ACTION-BASE: proposed source and binary verified, existing full SHA unresolvable upstream. |
| [#103](https://github.com/johnbilliris/ama/pull/103) | AC-cosign / prompts-publish | `398d4b0e…` | `f713795c…` | **H** B-ACTION-BASE: proposed source verified, existing full SHA unresolvable; required assets not retrieved. |
| [#102](https://github.com/johnbilliris/ama/pull/102) | AC-comment / foundry-carveout-review | v5 | v4 | **P** `e8674b075228eee787fea43ef493e45ece1004c9`; official ancestry/source verified; no live comment test authorised. |

Accounting: **33/33 included; 10 npm + 18 Python + five Actions; 31 work items**. Provisional direction counts are P=12, F=1, R=15, H=5. Final exact/fallback/already-satisfied counts are not established; all 33 remain incomplete for delivery until their gates pass.

## R2 — Use live approved-source evidence, with explicit uncertainty

**Decision**: query only `https://packagefeedproxy.microsoft.io/npm/` and `https://packagefeedproxy.microsoft.io/pypi/simple` for libraries. Follow their HTTPS Microsoft artifact links/redirects; reject public npm/PyPI artifact destinations. Retrieve fresh bytes, verify supplied checksums and package identity, and record time/environment coverage.

**Rationale**: a catalogue can list a release while artifacts fail; an installed cache can conceal missing files. The successful Python wheel samples cover CPython 3.12 Windows x64, Linux x64 and Linux arm64 where applicable, not every transitive wheel or every future interpreter allowed by an open-ended Python declaration.

**Alternatives considered**: `npm view`/release announcements alone; a successful cached install; public-feed fallback; treating a connection reset as absence. Rejected by FR-002/008/009/017.

Observed distinctions:

- ESLint 10.12.0 and jsdom 30.1.2 were absent from successful full catalogues and their exact proxy version endpoints returned HTTP 404. This supports target absence at the observation time.
- An initial eslint-config-next catalogue connection reset was followed by successful metadata and artifact retrieval. It was a transient access failure, not a missing release.
- The first engineio 4.14.0 wheel request failed with Windows socket error 10054. A fresh retry succeeded and matched the hashes in all three application/root locks.
- MSAL common catalogue requests repeatedly failed with connection resets. An exact scoped version endpoint returned 404, but without a trustworthy catalogue/artifact chain this is **unresolved source evidence**, not a proven eligible fallback set.
- `source-map-js@1.2.2` and `sharp@0.35.5` are now freshly retrievable with matching SHA-512 SRI. The October 6 hint is obsolete. Commit `f8560dd5002d5a060284bef2fc21721ceb66f5c5` is relevant minimal prior art: the root override and affected lock edges were changed together.
- Some npm proxy records supply only a SHA-1 shasum. Evidence distinguishes that weaker published checksum from SHA-512 SRI and also records locally computed SHA-256. Do not downgrade an existing stronger lock integrity field; require acceptable stronger provenance before final security readiness where necessary. Download success is not a security clearance.

No public advisory/security scan was run during Plan. Existing protective minima, overrides and required scans remain mandatory.

## R3 — Bound npm migrations and fallback ordering

**Decision**: prefer the reconciled target; use npm SemVer ordering for stable lower same-major alternatives only. Research used the already-installed SemVer 7.8.5 module, not lexical sorting or a newly installed dependency.

**Rationale and coupled changes**:

- **Next**: web 16.3.8 and UI 15.5.21 archives are verified. Each requires matching `@next/env` and platform SWC artifacts. Next 16 also needs its declared `@swc/helpers` and newer PostCSS relationship. Keep the existing sharp 0.35.5, PostCSS minimum and source-map-js 1.2.2 protections. Native GNU/musl/Windows artifacts remain unverified; reject a transitive downgrade in the final lock.
- **ESLint**: below absent 10.12.0, the first candidates are 10.11.0, 10.10.0, 10.9.1, 10.9.0 and 10.8.1. 10.11.0 is downloadable and allows Node 24, but both current config-next 16.2.6 and researched 16.3.8 require plugin families whose available versions exclude ESLint 10: react 7.37.5, import 2.32.0 and jsx-a11y 6.10.2. Successful catalogues found **no ESLint-10-compatible release within those config ranges**. This rejects the entire major-10 fallback set for that graph, not just the highest artifact. Keep 9.39.4 as a blocked baseline, not a delivered major-9 fallback. Do not replace lint families or disable peer/rule checks to force installation.
- **jsdom**: stable lower candidates are 30.1.1, 30.1.0, 30.0.1 and 30.0.0. 30.1.1 is the highest and its archive is verified. It requires Node `^22.22.2 || ^24.15.0 || >=26.0.0`; keep Node 24 and establish the actual patch in CI/container images. The inspected local 24.16.0 satisfies this bound but does not prove CI does. DOM/CSS/selector/cookie behaviour, undici and other transitive requirements need validation. Canvas `^3.2.3` is optional and is not installed in the current graph.
- **Playwright**: keep test, playwright and playwright-core at 1.63.0 together. Their archives require Node >=20 and are verified. Browser revisions, Chromium binaries, Linux OS dependencies and the two-server test harness remain separate unverified requirements. Do not use a cached 1.59 browser to claim 1.63 validation.
- **Node types**: 26.6.4's archive is verified; the repository actually runs Node 24. A different types major is a compatibility risk, not proof that every API call fails. Require an explicit Node-24 surface/runtime compatibility assessment plus type/build/test evidence. Do not silently move the runtime to 26 or choose a major-24 types version as a major-26 fallback.
- **MSAL**: React 5.7.2 requires browser `^5.24.0`; browser is currently resolved at 5.9.0 despite its permissive declaration. The smallest researched companion is browser 5.24.0, which in turn requires common **16.14.2**. Current common instances include 16.5.2 and 16.14.1; do not globally normalise older unrelated instances. Common 16.14.2 source evidence remains unresolved, so the complete graph cannot be selected. Do not downgrade to a lower React release on a feed-access failure.
- **js-yaml**: 4.3.1 belongs to the web declaration plus shared lock. Validate direct YAML use and transitive tool consumers; retain existing @types/js-yaml unless an actual incompatibility requires change.

**Alternatives considered**: unrestricted `pnpm update --latest`; matching every Next/config/types version number; ESLint 9 as a fallback to a 10 target; Node 26 migration; a higher fallback such as jsdom 30.2. Rejected as outside the approved policy or unnecessarily broad.

## R4 — Preserve Python security baselines and independent locks

**Decision**: use `packaging.version.Version` (PEP 440) and wheel tags/Requires-Python. Only five Python PRs currently need advances in their own lock scopes. Do not refresh the other dependencies just because the lock is being touched.

**Rationale**:

- h2 4.4.1 requires `hpack>=4.2,<5` and `hyperframe>=6.1,<7`. Agents has hpack 4.1.0 and hyperframe 6.1.0; only the hpack advance to 4.2.0 is necessary. Both target wheels are verified. Root already has h2 4.4.1/hpack 4.2.0.
- Settings 2.14.2 requires Pydantic >=2.7.0, python-dotenv >=0.21.0 and typing-inspection >=0.4.0. Agents' Pydantic 2.12.5 fits; root's settings 2.15.0/Pydantic 2.13.5 do not need to be copied over.
- Downloaded FastAPI 0.138.0 (root) and 0.141.1 (agents/API) metadata permit Starlette >=0.46.0 and Pydantic >=2.9.0. The current Starlette 1.7.0 is not excluded by those declared bounds. This is metadata compatibility evidence, not an HTTP/runtime test pass.
- Root and agents PyJWT both resolve to 2.15.0, not the 2.13.0 proposal. Preserve root `pyjwt>=2.14.0,<3` and application security minima. Root's redis-entraid 1.2.1 override is an existing compatibility/security exception; do not remove it to satisfy a resolver or `pip check`.
- Preserve cryptography 50.0.1 and the major-50 minimum, and the existing mem0ai security override. Root/agents mem0ai 2.0.20/2.0.2 remain different. This batch does not authorise general prerelease adoption.
- API `uv.lock` has idna 3.20; specify-cli has 3.19, cryptography 50.0.1 and PyJWT 2.15.0. These are independently newer, not targets for root idna 3.15 normalisation.
- Root universal lock markers can select different versions on different interpreters. Validate the actually supported Python 3.12 environments, retain marker branches, and do not infer tested support for every future Python version from `>=3.12`.

**Alternatives considered**: replaying old Dependabot lock patches; `uv lock --upgrade` across the repository; treating declarations as exact installed versions; sharing a global constraint file between independently newer environments. Rejected.

## R5 — Verify Actions by official identity and provenance

**Decision**: only the proposed full SHA or a proved newer existing baseline is eligible. Retrieve official source archives and verify their files against Git blob identities in the official pinned commit's complete tree. A local archive SHA-256 alone is not independent source verification.

| Action | Verified proposed SHA | Provenance / remaining limitation |
| --- | --- | --- |
| checkout | `3d3c42e5aac5ba805825da76410c181273ba90b1` | Official v7 and v7.0.1 resolve here. Existing `93cb6efe…` is v5.0.1, not the stale v5.0.0 comment; v4 resolved to v4.4.0. Compare histories diverge, so use verified stable release ordering (7.0.1 > 5.0.1 / 4.4.0), not ancestry or timestamps alone. |
| upload-artifact | `b7c566a772e6b6bfb58ed0dc250532a479d7789f` | Official v6 resolves here; the v4 baseline is an ancestor. Six active occurrences already match; four do not. |
| gitleaks-action | `ff98106e4c7b2bc287b24eaf42907196329070c7` | Source/tree verified; hard-coded default gitleaks 8.24.3 Linux x64 archive and official checksums retrieved/matched. Existing full SHA returned Git API 404 and commit API 422. No ordering proof. |
| cosign-installer | `398d4b0eeef1380460a10c8013a76f728fb906ac` | Source/tree verified. Existing full SHA returned Git API 404 and commit API 422. No ordering proof; required release assets not fetched. |
| create-or-update-comment | `e8674b075228eee787fea43ef493e45ece1004c9` | Official v5 resolves here and is ahead of v4 (`71345be0265236311c031f5c7866368bd1eff043`). No actual comment created. |

**Rationale**: all five proposed sources are retrievable, but two existing baselines cannot be verified. That does not authorise an assumption that any working replacement is newer. Retrieve authoritative provenance or obtain an explicit policy resolution at the appropriate human gate; keep those changes blocked in the meantime.

Checkout/upload/comment use Node 24; current gitleaks target uses Node 20; cosign is composite. Checkout/upload document runner minimum **2.327.1**, with **2.329.0** needed for checkout's authenticated Git use from Docker container actions. The self-hosted sovereign runner in `ci.yml` needs explicit version evidence. Never replace it with a non-sovereign hosted runner to get a pass.

Checkout v7 changes fork handling for privileged triggers and credential persistence. Preserve `persist-credentials: false` where set; do not introduce an unsafe opt-in to recover a failing workflow. Retain permissions and branch/event protections. Do not enable commented-out jobs.

Cosign's source pins bootstrap **v2.5.2**, while the repository explicitly requests **v2.4.1**. Required Linux x64 assets therefore include both binaries, the v2.4.1 detached signature and release public key, with the pinned bootstrap/key hashes and signature verification. Checking only the new action's default release would miss the actual workflow. This plan changes neither the requested cosign binary release nor its verification.

**Alternatives considered**: assuming hash order is version order; using later timestamps; trusting workflow comments/tags without resolving them; replacing an unavailable target with a convenient Action release; applying the Actions exception to npm/Python packages. Rejected.

## R6 — Validate actual consumers, not an imaginary all-locked pipeline

**Decision**: capture separate baseline and candidate evidence for the existing pnpm/uv contexts **and** for affected consumers that resolve through pip/helper commands. Use two isolated clean installs per context/platform with identical inputs and compare full installed version maps.

**Rationale**: `quality-windows` uses root `uv sync --locked --extra windows-ci`; Linux `quality` installs editable Python applications with pip, and API/agents Dockerfiles use `scripts\install_pyproject_dependencies.py`. The devcontainer has its own aggregate installer. Their installed graphs cannot be inferred from `uv.lock`, and a lock edit alone does not update them.

If reproducing a ranged consumer produces a different or newer graph, keep that consumer independent. Do not impose root pins and accidentally downgrade it. If deterministic fulfilment needs a small consumer-specific constraint or recipe change, document its exact baseline and security effects for approval; do not turn this batch into a repository-wide installer conversion.

Source policy is also environmental: local npm uses the user's `.npmrc`, whereas a clean hosted runner does not inherit it. Plan minimal checked-in policy plus bootstrap environment propagation, with actual network evidence. Existing Python source-policy checks remain mandatory.

Ubuntu quality/story/accessibility/security gates, Windows quality, standalone agents checks and affected container recipes are required. Live evaluation, signing/publication and self-hosted runner operations require their actual credentials/approvals; no dispatch occurred. Browser payload and OS-package provisioning must be reconciled with the approved environment/source policy; the Actions exception is not a general browser-CDN exemption.

**Alternatives considered**: one cached local install for the whole monorepo; using Python 3.14 ARM64 as proof of Python 3.12 x64; treating skipped credentialed tests as passes; disabling failing checks; adding a permanent dependency-reconciliation service. Rejected.

## R7 — Keep evidence proportional to a one-off batch

**Decision**: maintain one reviewable feature-local record using the entities in `data-model.md`, the initial observations in `evidence.md`, and existing validation outputs. No new application model classes, schema package, service, CLI, scheduling system or public API.

**Rationale**: the work has a fixed denominator and a human handover. The record needs provenance and reproducibility, not production persistence.

**Alternatives considered**: a new database/evidence API, reusable reconciliation engine or dependency-bot product. Rejected as unnecessary scope.

## Blockers and owner actions

| ID | Affected PRs/scopes | Current cause or uncertainty | Responsible role / next action |
| --- | --- | --- | --- |
| B-ESLINT | #150 | No eligible major-10 graph within the researched Next plugin families. | Frontend maintainer: leave blocked until upstream compatible releases are available, or request separately approved bounded migration/spec changes. No major-9 fallback. |
| B-TYPES | #146 | Node 26 declaration surface versus Node 24 runtime has no compatibility proof. | Frontend maintainer: demonstrate Node-24-safe API use and tests without a runtime migration; otherwise retain baseline as incomplete and return for scope/policy decision. |
| B-MSAL | #144 | common 16.14.2 metadata/artifact chain is unverified after access failures; no fallback set established. | Dependency/feed maintainer: obtain reliable approved-proxy evidence for the required graph; then evaluate compatibility or a policy-compliant fallback. No public-feed bypass. |
| B-ACTION-BASE | #105, #103 | Existing full pins are unresolvable in official repositories; monotonicity/security comparison cannot be proved. | Repository/security maintainer: supply authoritative baseline provenance or request explicit policy resolution. Proposed bytes alone do not clear this hold. |
| B-SOURCE-ENV | All npm consumers | Local user registry is not a reproducible CI source policy; some records have only SHA-1 published checksums. | DevOps/dependency maintainer: enforce proxy at each install/bootstrap boundary, preserve stronger integrity protections, verify final artifacts. |
| B-CONSUMER-BASE | Affected pip/helper/container consumers | Independently installed baselines and repeatability not observed; locks do not govern these recipes. | Backend/DevOps maintainer: reproduce actual baseline recipes, preserve newer results, approve any necessary minimal per-consumer consistency fix. |
| B-VALIDATION | All 33 | No clean installs/tests/security clearance; native/transitive coverage incomplete; cosign assets/signature and live/sovereign checks outstanding. | QA/DevOps/security owners: execute `quickstart.md` only after approval; record failures/unrun checks individually. |

The first four blocker IDs hold five individual PRs. Cross-cutting blockers prevent any final readiness claim. A human can approve the Plan with holds intact; neither approval nor complete accounting silently excludes those PRs or authorises remote mutations.

## Phase 8 provisional PR/work-item decision ledger (T019)

**Status: provisional only.** This appendix preserves one direction for each of the 33 source PRs and a separately scoped direction for each of the 31 work items. Nothing below is a final outcome, artifact-closure claim, clean-install result, security clearance, or policy waiver. See `evidence.md` E6–E12 for the execution-start source/workflow hashes, per-environment holds, current proxy artifact observations, official Action identities, and open gates. The original E1 snapshot and R1 rows above are retained.

**Count units remain distinct:**

| Unit | P | F | R | H | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Individual PR directions | 12 | 1 | 15 | 5 | 33 |
| Scoped work-item directions | 12 | 1 | 13 | 5 | 31 |

`NW-next` reconciles one aggregate provisional P work item (`16.3.8`) to three individually preserved source directions: #149 P, `16.3.6 → 16.3.8`, originally `apps\web`; #133 R, `16.2.6 → 16.2.11`, originally supplied as root-lock scope; #132 R, `16.2.6 → 16.2.11`, originally `apps\web`. Their current common revalidated resolution scope is the `apps\web` importer in the single root `pnpm-lock.yaml`. This count reconciliation does not finalize the work item.

### Per-PR provisional source and direction records

In every row, `scope` is the separately revalidated scope; the source PR's original supplied scope/target remain in R1 and `spec.md`. `Evidence/gaps` refers to the detailed E1/E2/E3/E4 and E6–E12 observation records, not an outcome certificate. All npm/Python evidence used the approved Microsoft proxy; all Action evidence used official upstream sources.

| PR | Original proposed change | Revalidated scope and baseline | Candidate / rejected alternatives | Provisional direction and evidence gap |
| --- | --- | --- | --- | --- |
| #149 | Next `16.3.6 → 16.3.8` | NW web importer/root pnpm lock, baseline `16.3.6` | `16.3.8`; no older target substituted | **P**; proxy archive SRI checked, direct Linux x64 GNU/musl SWC and `@next/env` fetched; broader native/transitive and installs pending |
| #150 | ESLint `9.39.4 → 10.12.0` | NW web importer/root pnpm lock, baseline `9.39.4` | Target absent; `10.11.0` fetched but excluded by ESLint-9-only react/import/jsx-a11y peers; no major-9 fallback | **H** B-ESLINT; retain baseline; compatible major-10 family or separately approved bounded scope change required |
| #148 | jsdom `25.0.1 → 30.1.2` | NW web importer/root pnpm lock, baseline `25.0.1` | Target absent; `30.1.1` is highest lower stable same-major candidate observed | **F** provisional; archive SRI checked; requires Node `>=24.15.0` in major 24 and full transitive/runtime/test evidence; actual CI patch missing |
| #147 | `@playwright/test` `1.59.1 → 1.63.0` | NW web importer/root pnpm lock; current trio `1.59.1` | Target trio `@playwright/test`/`playwright`/`playwright-core` `1.63.0`, coupled | **P**; package archives fetched; browser CDN/OS payload source not approved/retrieved and CI tests not run |
| #146 | `@types/node` `22.13.10 → 26.6.4` | NW web importer/root pnpm lock, baseline `22.13.10`, Node 24 runtime | Exact target archive retrieved; no invented major-24 substitute | **H** B-TYPES; Node-24 surface/runtime compatibility assessment and tests missing |
| #144 | MSAL React `5.3.2 → 5.7.2` | NW web importer/root lock; React `5.3.2`, browser `5.9.0`, common `16.5.2`/`16.14.1` | React `5.7.2` → browser `5.24.0` → common `16.14.2`; no public-feed bypass/React downgrade | **H** B-MSAL; direct archives/SRI and peers now observed; full source-host approval, auth tests and clean install remain open |
| #133 | Next `16.2.6 → 16.2.11` | NW web importer/root lock; baseline Next `16.3.6` | Original older goal preserved; shared NW goal `16.3.8` belongs to #149 | **R** provisional; #133’s old target does not supersede current shared work-item goal; not a delivered retain outcome |
| #137 | js-yaml `4.1.1 → 4.3.1` | NW web importer/root lock; baseline `4.1.1` | Exact `4.3.1` | **P**; archive matched proxy SHA-1 only (no SHA-512 SRI); stronger final provenance and YAML/build tests pending |
| #132 | Next `16.2.6 → 16.2.11` | NW web importer/root lock; baseline Next `16.3.6` | Original older goal preserved; shared NW goal `16.3.8` belongs to #149 | **R** provisional; target and originally supplied `apps\web` scope retained; no delivered retain evidence |
| #130 | UI Next `15.5.18 → 15.5.21` | NU UI importer/root lock, baseline `15.5.18`, independent of web Next 16 | Exact `15.5.21` | **P**; archive matched proxy SHA-1 only; full peer/native closure and UI workspace tests pending |
| #135 | cryptography `46.0.7 → 50.0.0` | PR root uv lock, current `50.0.1`; `>=50.0.0,<51` | Retain `50.0.1`; target would be lower | **R** provisional; proxy wheels/hashes observed for multiple platforms; installed/quality/security evidence pending |
| #136 | h2 `4.3.0 → 4.4.1` | PA agents uv lock, baseline `4.3.0`, hpack `4.1.0` | `4.4.1` plus required hpack `4.2.0`; hyperframe remains `6.1.0` | **P**; h2/hpack wheels, dependency ranges and hashes checked; separate agents clean install pending |
| #111 | idna `3.11 → 3.15` | PR root uv lock, baseline `3.11` | Exact `3.15`; do not normalize API `3.20` or CLI `3.19` | **P**; wheel/proxy SHA and supported platform-neutral metadata checked; root installed map/quality pending |
| #134 | aiohttp `3.13.5 → 3.14.3` | PA agents lock, baseline already `3.14.3` | Retain `3.14.3` | **R** provisional; x64/ARM64/Linux and Windows wheel hashes checked; install/runtime validation pending |
| #121 | msgpack `1.1.2 → 1.2.1` | PR root uv lock, current `1.2.2` | Retain `1.2.2` | **R** provisional; Linux x64/ARM64 and Windows 3.12 wheels match proxy and lock hashes; installed/quality evidence pending |
| #116 | PyJWT `2.12.1 → 2.13.0` | PR root uv lock, current `2.15.0`; `>=2.14.0,<3` | Retain `2.15.0` | **R** provisional; proxy wheel/lock hash checked; installed/security evidence pending |
| #124 | engineio `4.13.1 → 4.13.2` | PR root uv lock, current `4.14.0` | Retain `4.14.0` | **R** provisional; proxy wheel/lock hash checked after separately recorded prior transient failure; install/quality evidence pending |
| #123 | socketio `5.16.1 → 5.16.2` | PR root uv lock, current `5.17.0` | Retain `5.17.0` and engineio relation | **R** provisional; wheel/lock hash checked; full consumer validation pending |
| #129 | setuptools `82.0.1 → 83.0.0` | PA agents uv lock, baseline `82.0.1`, root independently `84.0.0` | Exact agents target `83.0.0`; do not copy root `84.0.0` | **P**; proxy wheel/hash checked; install and agents regression checks pending |
| #128 | pyasn1 `0.6.3 → 0.6.4` | PA agents uv lock, already `0.6.4` | Retain `0.6.4` | **R** provisional; proxy wheel/lock hash checked; independent validation pending |
| #127 | mcp `1.27.1 → 1.28.1` | PA agents uv lock, current `1.30.0` | Retain `1.30.0`; do not downgrade | **R** provisional; wheel/lock hash checked; consumer tests pending |
| #126 | socketio `5.16.1 → 5.16.2` | PA agents uv lock, current `5.17.0` | Retain `5.17.0`, separate from #123 | **R** provisional; wheel/lock hash checked; agents validation pending |
| #125 | engineio `4.13.1 → 4.13.2` | PA agents uv lock, current `4.14.0` | Retain `4.14.0`, separate from #124 | **R** provisional; wheel/lock hash checked; agents validation pending |
| #112 | idna `3.11 → 3.15` | PA agents uv lock, baseline `3.11` | Exact `3.15`, separate from root #111 | **P**; proxy wheel/hash checked; agents map/clean installation pending |
| #120 | Starlette `1.0.0 → 1.3.1` | PA agents uv lock, current `1.7.0` | Retain `1.7.0`, not downgrade | **R** provisional; proxy wheel/lock hash checked; runtime regression evidence pending |
| #115 | PyJWT `2.12.1 → 2.13.0` | PA agents uv lock, current `2.15.0`; `PyJWT[crypto]>=2.14.0,<3` | Retain `2.15.0` and security floor | **R** provisional; proxy wheel/lock hash checked; security/installation checks pending |
| #122 | pydantic-settings `2.14.1 → 2.14.2` | PA agents uv lock, baseline `2.14.1`; root separately `2.15.0` | Exact agents target `2.14.2`, no root normalization | **P**; wheel hash and declared dependency floors checked against current agents pydantic/dotenv/typing-inspection versions; full install pending |
| #117 | python-multipart `0.0.28 → 0.0.31` | PA agents uv lock, current `0.0.32` | Retain `0.0.32` | **R** provisional; proxy wheel/lock hash checked; agents install/test pending |
| #145 | checkout v4 / old refs → v7 | 42 active uses; Ubuntu, Windows x64, sovereign Linux x64 | Exact proposed SHA `3d3c42e5aac5ba805825da76410c181273ba90b1` (v7.0.1); six v4 plus 32 v5.0.1 refs | **P** provisional; official SHA/tree/source and release ordering rechecked; runner minimums, fork/credential behavior and actual workflow tests pending |
| #143 | upload-artifact v4 → v6 | Ten active uses; six already target, three v4.6.2 SHA and one v4 tag | Exact proposed SHA `b7c566a772e6b6bfb58ed0dc250532a479d7789f`; retain six target refs | **P** provisional; official SHA/tree/proposed source verified, v4 is its ancestor; runner/job behavior and clean evidence pending |
| #105 | Gitleaks baseline SHA → proposed `ff98106e4c7b2bc287b24eaf42907196329070c7` | AC-gitleaks `security-scan.yml`; current pin `dcedce43c6f43de0b836d1fe38946645c9c638dc` | Proposed SHA only; no alternative release allowed | **H** B-ACTION-BASE; official target/source and v8.24.3 asset/checksum verified; baseline SHA is still unresolvable, so no-downgrade remains unproved |
| #103 | Cosign baseline SHA → proposed `398d4b0eeef1380460a10c8013a76f728fb906ac` | AC-cosign `prompts-publish.yml`; current pin `f713795cb21599bc4e5c4b58cbad1da852d7eeb9` | Proposed SHA only; no alternative action release | **H** B-ACTION-BASE; target source verified and v2.5.2 plus requested v2.4.1 binary/signature/key verified; baseline SHA still unresolvable, pin remains unchanged |
| #102 | create-or-update-comment v4 → v5 | AC-comment, one Ubuntu reference | Exact full SHA `e8674b075228eee787fea43ef493e45ece1004c9` | **P** provisional; official SHA/tree/v5 and v4 ancestry verified; no live comment or functional workflow run authorized |

### Separately scoped provisional work-item directions (31 rows)

| Work item | Revalidated scope / current resolution | Source PRs and targets preserved | Provisional work-item direction / gates |
| --- | --- | --- | --- |
| `NW-next` | `apps\web` importer/root pnpm lock; Next `16.3.6` | #149 `16.3.6→16.3.8`; #133 `16.2.6→16.2.11`; #132 `16.2.6→16.2.11` | **P** goal `16.3.8`; per-PR P/R/R remain as above; native/full source and install gates open |
| `NW-eslint` | Web importer/root lock; ESLint `9.39.4` | #150 `9.39.4→10.12.0` | **H** B-ESLINT |
| `NW-jsdom` | Web importer/root lock; jsdom `25.0.1` | #148 `25.0.1→30.1.2` | **F** tentative `30.1.1`; Node patch, source-host, transitive and tests open |
| `NW-playwright` | Web importer/root lock; trio `1.59.1` | #147 `1.59.1→1.63.0` | **P** coupled trio `1.63.0`; browser and OS artifact source/tests open |
| `NW-node-types` | Web importer/root lock; types `22.13.10`, Node runtime 24 | #146 `22.13.10→26.6.4` | **H** B-TYPES |
| `NW-msal-react` | Web importer/root lock; React `5.3.2` / browser `5.9.0` / common variants | #144 `5.3.2→5.7.2` | **H** B-MSAL |
| `NW-js-yaml` | Web importer/root lock; `4.1.1` | #137 `4.1.1→4.3.1` | **P** `4.3.1`; SHA-1-only record and tests pending |
| `NU-next` | `packages\ui` importer/root lock; Next `15.5.18` | #130 `15.5.18→15.5.21` | **P** `15.5.21`; keep Next 15 distinct |
| `PR-cryptography` | Root uv; `50.0.1`, floor `>=50.0.0,<51` | #135 `46.0.7→50.0.0` | **R** `50.0.1`; final installed/security evidence pending |
| `PA-h2` | Agents uv; h2 `4.3.0`, hpack `4.1.0` | #136 `4.3.0→4.4.1` | **P** h2 `4.4.1` + hpack `4.2.0`; independent agents install pending |
| `PR-idna` | Root uv; idna `3.11` | #111 `3.11→3.15` | **P** `3.15`, not API/CLI |
| `PA-aiohttp` | Agents uv; `3.14.3` | #134 `3.13.5→3.14.3` | **R** `3.14.3`; completion not final |
| `PR-msgpack` | Root uv; `1.2.2` | #121 `1.1.2→1.2.1` | **R** `1.2.2`; completion not final |
| `PR-pyjwt` | Root uv; `2.15.0` and `>=2.14.0,<3` | #116 `2.12.1→2.13.0` | **R** `2.15.0`; completion not final |
| `PR-engineio` | Root uv; `4.14.0` | #124 `4.13.1→4.13.2` | **R** `4.14.0`; completion not final |
| `PR-socketio` | Root uv; `5.17.0` | #123 `5.16.1→5.16.2` | **R** `5.17.0`; completion not final |
| `PA-setuptools` | Agents uv; `82.0.1`, root `84.0.0` | #129 `82.0.1→83.0.0` | **P** agents `83.0.0`; do not copy root value |
| `PA-pyasn1` | Agents uv; `0.6.4` | #128 `0.6.3→0.6.4` | **R** `0.6.4`; completion not final |
| `PA-mcp` | Agents uv; `1.30.0` | #127 `1.27.1→1.28.1` | **R** `1.30.0`; completion not final |
| `PA-socketio` | Agents uv; `5.17.0` | #126 `5.16.1→5.16.2` | **R** `5.17.0`, distinct root |
| `PA-engineio` | Agents uv; `4.14.0` | #125 `4.13.1→4.13.2` | **R** `4.14.0`, distinct root |
| `PA-idna` | Agents uv; `3.11` | #112 `3.11→3.15` | **P** `3.15`, distinct root |
| `PA-starlette` | Agents uv; `1.7.0` | #120 `1.0.0→1.3.1` | **R** `1.7.0`, no downgrade |
| `PA-pyjwt` | Agents uv; `2.15.0`, `PyJWT[crypto]>=2.14.0,<3` | #115 `2.12.1→2.13.0` | **R** `2.15.0`; preserve floor |
| `PA-settings` | Agents uv; `2.14.1`, root `2.15.0` | #122 `2.14.1→2.14.2` | **P** agents `2.14.2`, distinct root |
| `PA-multipart` | Agents uv; `0.0.32` | #117 `0.0.28→0.0.31` | **R** `0.0.32`; no downgrade |
| `AC-checkout` | 42 active refs; Ubuntu 40, Windows 1, sovereign Linux/x64 1 | #145 `v4→v7`, mixed verified v5/v4 baseline refs | **P** proposed full SHA only; runner/source/behavior gates open |
| `AC-upload` | Ten active refs; six already proposed SHA, four v4.6.2 refs | #143 `v4→v6` | **P** proposed full SHA only where not already target; runner/job validation pending |
| `AC-gitleaks` | `security-scan.yml`, one active ref | #105 old SHA → proposed SHA | **H** B-ACTION-BASE despite proposed action/asset evidence |
| `AC-cosign` | `prompts-publish.yml`, one active ref | #103 old SHA → proposed SHA | **H** B-ACTION-BASE despite target and asset signature evidence |
| `AC-comment` | `foundry-carveout-review.yml`, one active ref | #102 v4→v5 | **P** proposed full SHA; no live comment test |

The work-item ledger deliberately does not join separately resolved Python scopes or web/UI importers. T019 **does not** close B-SOURCE-ENV, B-CONSUMER-BASE, B-ESLINT, B-TYPES, B-MSAL, B-ACTION-BASE, B-VALIDATION, or finalize any PR direction.
