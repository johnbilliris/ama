# Quickstart: gated reproduction and validation

**Plan**: `C:\code\ama\specs\001-proxy-dependency-upgrades\plan.md`

**Nothing in this document has been executed as an installation or application test during Plan.** These are instructions for a subsequently authorised implementation/validation session. Do not commit, push, dispatch workflows, comment on PRs, publish or deploy merely because a command appears here.

## 1. Freeze inputs and establish the baseline first

Use baseline commit `62d249dc1205644fed934ea167df56695e92b3d2` and the feature's recorded PR heads. Capture any later drift before proceeding; do not relist/expand the 33-PR denominator.

The maintainer should prepare separate clean baseline and candidate copies, with no copied `node_modules`, `.venv`, browser cache, package-manager cache or pre-existing application server. Examples below use `C:\ama-validation\candidate-a` on Windows and `/workspace` inside an isolated Linux runner/container. Use a second separate copy/cache for run B. All paths are examples of absolute validation locations, not permission to overwrite an existing directory.

Before dependency edits, run the relevant existing checks on the unchanged baseline in the same environment. Record exact command, selected tests, exit code and failure signature. Current installed/cached packages are not that baseline evidence.

In each fresh shell, set the approved source controls explicitly. Do not dump credentials or the full environment into logs.

```powershell
Set-Location -LiteralPath 'C:\ama-validation\candidate-a'
$env:NPM_CONFIG_REGISTRY = 'https://packagefeedproxy.microsoft.io/npm/'
$env:PIP_INDEX_URL = 'https://packagefeedproxy.microsoft.io/pypi/simple'
$env:PIP_CONFIG_FILE = 'NUL'
$env:PIP_EXTRA_INDEX_URL = ''
$env:PIP_FIND_LINKS = ''
$env:UV_DEFAULT_INDEX = 'https://packagefeedproxy.microsoft.io/pypi/simple'
$env:UV_INDEX = ''
$env:UV_EXTRA_INDEX_URL = ''
$env:UV_FIND_LINKS = ''
$env:UV_PYTHON_DOWNLOADS = 'never'
$env:PYTHONIOENCODING = 'utf-8'
node --version
python --version
pnpm --version
uv --version
npm config get registry
```

On Linux use `PIP_CONFIG_FILE=/dev/null` and the same source URLs/empty secondary sources. Match and record the existing workflow's remaining settings, including its uv configuration behaviour; verify that local path sources and security overrides remain effective. Repeat this prologue for a new tool invocation: environment and working directory do not persist across CLI tool calls.

Use existing pnpm 10.6.3, uv 0.11.21 and installed Python 3.12. A missing tool/runtime is a prerequisite blocker, not permission to install it from an unapproved source. Record the actual Node 24 patch; jsdom 30.1.1 requires at least 24.15.0 within major 24.

Capture hashes before/after each run for all relevant manifests, locks, registry configuration and workflow files. Keep baseline and candidate identifiers distinct. `git diff --exit-code` is useful but does not replace hashes for untracked inputs.

## 2. Confirm the approved candidate without unrestricted updates

Recheck `research.md` holds before any edit. No whole-repository `pnpm update --latest`, `uv lock --upgrade`, public fallback, removed override, lowered minimum or disabled peer check is allowed.

Examples of narrowly scoped **later** Python lock generation, after the input snapshot:

```powershell
uv lock --project 'C:\ama-validation\candidate-a' --upgrade-package 'idna==3.15' --python 3.12 --no-python-downloads
uv lock --project 'C:\ama-validation\candidate-a\apps\agents' --upgrade-package 'idna==3.15' --upgrade-package 'h2==4.4.1' --upgrade-package 'hpack==4.2.0' --upgrade-package 'setuptools==83.0.0' --upgrade-package 'pydantic-settings==2.14.2' --python 3.12 --no-python-downloads
```

Inspect every resulting lock delta. Exact desired versions, protected overrides and all marker-specific no-downgrade comparisons must hold. These commands are not guarantees that the resolver will produce an acceptable graph. Reject unrelated churn rather than retaining it for convenience.

For npm, update only the authorised importer declarations/companions, then regenerate the one root pnpm lock with pnpm 10.6.3. Keep web Next 16 and UI Next 15 separate. Do not transplant old PR locks. If lock generation proposes weaker integrity fields, an unapproved source, a transitive downgrade or an unexplained companion upgrade, stop for review.

For Actions, edit only approved active references to the full verified SHAs. Keep the six already-matching upload-artifact references and all existing permissions/trigger protections. Do not execute the comment/publication actions as a validation shortcut.

## 3. Perform two truly clean installations per environment

Each row is an independent resolution/validation boundary. Reuse of one artifact download can inform research, but cannot count as two clean installs.

| Environment | Existing recipe / required treatment |
| --- | --- |
| Node 24 Ubuntu x64, root pnpm workspace | Two separate workspace copies and empty stores; include all importers. Record GNU native artifacts and actual Node patch. |
| Node 24 Alpine web Docker build | Two cache-empty builds from the same recorded base-image digest; verify musl SWC/sharp requirements. No deployment. |
| Existing development container on its recorded architecture | Repeat its aggregate Python helper and pnpm recipes in clean environments; include ARM64 only where this is an actual supported consumer. Do not present x64 results as ARM64 validation. |
| Python 3.12 Linux, root development/extras | Two root lock installs with the same extras/markers; include `dev` and affected `load` coverage. |
| Python 3.12 Windows x64 `quality-windows` | Two root `windows-ci` installs and the existing no-deps eval-runner step. The inspected ARM64/Python 3.14 host is not a substitute. |
| Python 3.12 standalone agents | Two installs from `apps\agents\uv.lock`, independently of root. |
| Affected Linux pip CI and application container recipes | Two runs of **each actual recipe**, not a root-uv substitute. API/agents helpers, ingestion/eval/ingest-runner and the devcontainer can resolve differently. Record their installed baselines before imposing constraints. |
| Affected Actions runner environments | Twice retrieve the exact source SHA and required assets without cache; compare blob/asset identity and runner prerequisites. Separate source installation proof from a functional job run. |

If an independently locked API/CLI scope is unchanged, record the unchanged input hashes and non-applicability rationale for upgrading it. If implementation makes it affected, add its independent two-install/quality coverage before readiness. Do not omit a supported environment just because it is unavailable locally.

Example fresh pnpm install (run A):

```powershell
Set-Location -LiteralPath 'C:\ama-validation\candidate-a'
pnpm install --frozen-lockfile --store-dir 'C:\ama-validation\stores\npm-a' --registry 'https://packagefeedproxy.microsoft.io/npm/'
pnpm --recursive list --depth Infinity --json
```

Run B uses a different clean copy and `C:\ama-validation\stores\npm-b`. Frozen-lock installation must not alter inputs. Do not use `--ignore-scripts` as a substitute for validating required native/package lifecycle behaviour.

Example Windows root install, matching the existing job's extras:

```powershell
Set-Location -LiteralPath 'C:\ama-validation\candidate-a'
uv sync --locked --extra windows-ci --no-install-project --no-cache --python 3.12 --no-python-downloads
uv pip install --python 'C:\ama-validation\candidate-a\.venv\Scripts\python.exe' --no-deps --no-cache -e 'C:\ama-validation\candidate-a\apps\eval-runner'
uv pip list --python 'C:\ama-validation\candidate-a\.venv\Scripts\python.exe' --format json
uv run --no-sync ruff check apps tests packages
uv run --no-sync pytest tests/contract tests/integration -q --tb=line --maxfail=10
```

Equivalent Linux lock installs, in separate copies/environments:

```bash
cd /workspace
uv sync --locked --extra dev --extra load --no-cache --python 3.12 --no-python-downloads
uv pip list --python /workspace/.venv/bin/python --format json
uv sync --project /workspace/apps/agents --locked --no-cache --python 3.12 --no-python-downloads
uv pip list --python /workspace/apps/agents/.venv/bin/python --format json
```

Do not treat those uv runs as substitutes for `.github/workflows/ci.yml`'s Linux pip recipe or Dockerfiles that install dependency ranges. For those consumers reproduce the checked-in commands, for example the API/agents Docker helper:

```bash
cd /workspace
python /workspace/scripts/install_pyproject_dependencies.py /workspace/apps/agents/pyproject.toml
python -m pip list --format=json
python -m pip check
```

Use a dedicated environment for that recipe. Account for its complete Docker/CI install sequence and existing security overlay, not only this excerpt. `pip check` findings caused by documented existing overrides are evidence to review; never remove a security override or suppress a mandatory gate to get a clean result.

For ranged recipes, repeated equality is an observation, not a permanent lock guarantee. If a consumer cannot reproducibly realise its approved version decision, leave it incomplete and request the minimal consumer-specific repair. A new global constraints file that downgrades another context is not an acceptable fix.

For each pair, compare: input hashes, installed version maps for that runtime, Action SHAs/assets, approved retrieval URLs, integrity results and before/after repository inputs. An empty package store with a shared browser/tool cache is not sufficient for the relevant artifact claims.

## 4. Execute the applicable existing checks

Use the installed candidate environment and record results for the exact candidate hash. All commands below were **NOT RUN** in Plan.

### Python policy, quality and application behaviour

Canonical runner: `ubuntu-latest`, Python 3.12, `.github\workflows\ci.yml` `python-package-source-policy`, `quality`, `simulation-tenant-isolation`; Windows uses its existing job above.

```bash
cd /workspace
python /workspace/scripts/verify_python_package_sources.py
python -m pytest /workspace/tests/policy -q
ruff check apps tests packages
ruff format --check apps tests packages
mypy apps packages
lint-imports
pytest tests/equivalence -q --tb=short
```

Run the existing `quality` Python test command with `AMA_ENVIRONMENT=test` and `AMA_TRUST_FORWARDED_PRINCIPAL=1`:

```bash
pytest tests/unit tests/contract tests/integration tests/simulation \
  -m "not azure_staging and not azure_foundry_staging and not azure_cosmos_staging and not azure_speech_staging and not azure_blob_worm_staging and not measurement_staging and not e2e and not load and not locust" \
  --cov=apps --cov=packages --cov-report=xml --cov-report=term
pytest tests/benchmark/ --benchmark-json=.benchmarks/current.json -q
python /workspace/scripts/codegen/generate_map_overlay_taxonomy_ts.py --check
```

Apply the existing PowerShell coverage ratchet, preserving the CI phase and threshold:

```powershell
& 'C:\ama-validation\candidate-a\scripts\coverage-ratchet.ps1' -Phase $env:COVERAGE_PHASE -Tier unit
```

The Linux runner uses the same script through `pwsh`. Preserve the existing isolation selector (`spec007_isolation`, strict markers, minimum **113** collected cases) and run the full checked-in selection in the `simulation-tenant-isolation` job. Also retain the other `quality` lint steps: actor catalogue/evidence, feature binding, licence inventory, test-data manifest, indigenous placeholders, simulator isolation, Markdown freshness and RAG opt-out bindings.

### Web, UI consumers and test tooling

Canonical runner: Ubuntu Node 24 / pnpm 10.6.3. Ensure the TypeScript domain package is built before web type checks.

```bash
cd /workspace
pnpm --filter @ama/domain run typecheck
pnpm --filter @ama/domain build
pnpm --filter @ama/web lint
pnpm --filter @ama/web exec tsc --noEmit
pnpm --filter @ama/web test
pnpm --filter @ama/web test:a11y
pnpm --filter @ama/web build
```

These exercise the existing Vitest unit/integration/a11y selections and unchanged webpack build/postbuild behaviour. Add targeted authentication/MSAL, YAML, JSDOM and UI-consumer regression attention without replacing the full applicable selections or weakening TypeScript/ESLint settings.

Use the `story-acceptance` job's Chromium provisioning only after required browser/OS artifact sources are established. Its current command is `pnpm --filter @ama/web exec playwright install --with-deps chromium`; it is Linux-specific and was not executed here. Browser CDN access is not automatically covered by the Actions-only exception.

Preserve `PYTHONPATH=/workspace/packages/domain/src` and the job's test-only `AMA_TEST_SUPPORT`, `AMA_TEST_MODE` and `AMA_ENVIRONMENT` settings. Use fresh isolated servers; the Playwright config's `reuseExistingServer` must not attach to another baseline's process.

```bash
cd /workspace
pnpm --filter @ama/web exec playwright test --list --project=evidence
pnpm --filter @ama/web exec playwright test --project=evidence
pnpm --filter @ama/web exec playwright test --list --project=chromium --project=mobile \
  test_incident_commander_dashboard.spec.ts test_persona_workspace.spec.ts test_dashboard_decision_support.spec.ts
pnpm --filter @ama/web exec playwright test --project=chromium --project=mobile \
  /workspace/tests/e2e/test_incident_commander_dashboard.spec.ts \
  /workspace/tests/e2e/test_persona_workspace.spec.ts \
  /workspace/tests/e2e/test_dashboard_decision_support.spec.ts
```

Retain the existing collection assertions: at least five evidence tests and non-zero story acceptance collection. Other applicable help/web-coverage/axe projects remain their own validation records; a filtered run does not prove the whole Playwright suite.

### Workflow, container and security gates

- Run `python -m pytest /workspace/tests/devops -q` in the prepared Python environment to cover workflow/build contracts, including CI structure, release semantics, existing amd64 publication and authentication wiring.
- Preserve `.github\workflows\spec-035-gate.yml` invariant/contract/type gates and `.github\workflows\eval-pr-gate.yml` unit/quality gates where applicable. Their commands already exist; do not invent replacement checks or waive selectors.
- Keep CodeQL and `security-scan.yml` gitleaks, PSRule and Trivy gates. A HIGH/CRITICAL or newly introduced known vulnerability blocks readiness. Compare baseline/candidate findings; no new allowlist, disabled scan or weakened severity threshold.
- Inspect actual package retrieval in every build/bootstrap step, including pnpm setup, npm/npx tools, build dependencies and native package variants. Preserve stronger integrity protections.
- Source/runner validation for changed Actions must include Node 24 runner minimums, checkout credential/fork behaviour, artifact retention/name semantics and all active references. No live PR comment, signing, registry upload or deployment without separate authority.
- The sovereign CLI job remains on `[self-hosted, ama-au-sovereign, azure-au, linux, x64]` with its preflight/offline gates. An offline cache alone does not prove current proxy availability. If that scope is affected, pair its existing approved offline process with fresh approved-source provenance rather than bypassing it.

Live Azure evaluation/staging, signing identities, a sovereign runner and controlled remote Action executions are unavailable as validated evidence in this Plan. Record them as `blocked` or `not-run` with owner/next action, not as successful skipped tests. This plan does not authorise obtaining new cloud resources or changing residency.

## 5. Produce the human handover

Extend the record defined by `data-model.md`, without building a new system. Link all 33 PRs to their final decisions, scope/environment IDs, two clean-install runs, source/identity/integrity observations, applicable gate results and outstanding blockers.

Publish no completion claim from a catalogue, a declaration change or an unrun command. Distinguish:

- exact/fallback/retained **candidate direction** from an evidence-backed final outcome;
- all PRs accounted for from all upgrades delivered;
- pre-existing failures from new failures, without waiving either;
- local synthetic evidence from Linux/Windows/sovereign/live evidence;
- human Plan approval from permission for implementation, commits, remote PR operations or deployment.

Return to the human gate whenever policy or scope must change. Do not forward automatically to another agent or phase.
