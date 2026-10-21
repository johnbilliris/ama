# Feature Evidence Ledger — 001-arch-docs-refresh

Date: 2026-09-14
Scope: AUD-001 through AUD-022 remediation pass (implementation-focused).

## Environment Constraints

- Reviewer brief files provided via external workspaceStorage paths were not present on disk in this environment (`MISSING` / `BASE_MISSING`).
- Python test execution is blocked by missing local dependencies and TLS handshake failures when attempting dependency bootstrap.

## Executed Commands and Outcomes

1. `check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks` (scoped with `SPECIFY_FEATURE=001-arch-docs-refresh`)
- Result: PASS
- Output: `FEATURE_DIR=C:\code\ama\specs\001-arch-docs-refresh`; docs present: `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, `tasks.md`.

2. Checklist scan for `specs/001-arch-docs-refresh/checklists`
- Result: PARTIAL
- Output summary:
  - `architecture-review.md`: total 121, completed 0, incomplete 121
  - `requirements.md`: total 16, completed 16, incomplete 0

3. Focused baseline tests (publication/gateway/ingestion)
- Command: `python -m pytest tests/integration/test_human_approval_preserved.py tests/integration/test_data_minimisation_gateway.py tests/integration/test_ingestion_pipeline.py -q`
- Result: FAIL (environment)
- Error: `No module named pytest`

4. Focused baseline tests via API venv
- Command: `./apps/api/.venv/Scripts/python.exe -m pytest ...`
- Result: FAIL (environment)
- Error: `No Python at ...Python312\python.exe`

5. Focused baseline tests via `uv`
- Command: `uv run pytest ...`
- Result: FAIL (environment)
- Error: TLS `HandshakeFailure` while fetching dependencies from PyPI.

6. Setup verification for ignore files
- Result: PASS
- Confirmed present: `.gitignore`, `.dockerignore`, `package.json`.

7. `python tools/lint/check_known_gaps.py --root .`
- Result: PASS
- Output: `All 22 rows valid.`

8. `python tools/lint/check_spec_cross_refs.py --root .`
- Result: PASS
- Output: `All 23 spec numbers cited.`

9. XML validation for recovery transition source
- Command: parse `docs/architecture/sequence/recovery-transition.drawio` as XML
- Result: PASS
- Output: `recovery-transition.xml=OK`

10. Windows-compatible diagram hash verification
- Command: PowerShell `Get-FileHash` check against `docs/architecture/.diagram-hashes` (after manifest regeneration)
- Result: PASS
- Output: `manifest-hash-check=OK count=34`

11. Local docs architecture suite (without deployment)
- Commands:
  - `npx --yes markdownlint-cli2 "docs/architecture/**/*.md"`
  - PNG↔Drawio sibling pairing checks (PowerShell)
  - `python tools/lint/check_spec_cross_refs.py --root .`
  - `python tools/lint/check_known_gaps.py --root .`
- Result: PASS
- Output summary: `0 markdownlint issues`, `All 23 spec numbers cited.`, `All 22 rows valid.`, `docs-arch-local-suite=PASS`

## Files Changed in This Pass

### Product
- `apps/api/app/services/public_alert_service.py`
- `apps/api/app/api/routes/alerts.py`
- `apps/api/app/services/recommendation_service.py`
- `apps/api/app/middleware/rbac_check.py`
- `apps/api/app/auth/rbac_registry.py`
- `apps/agents/common/foundry_chat_client.py`
- `apps/api/app/repositories/signal_repository.py`
- `apps/ingestion/worker.py`

### Tests
- `tests/integration/test_alert_publication_enforcement.py`
- `tests/integration/test_alert_publish_route_authentication.py`
- `tests/contract/test_foundry_gateway_fail_closed.py`
- `tests/integration/test_ingestion_signal_repository_wiring.py`
- `tests/contract/test_architecture_docs.py`

### Docs and Tooling
- `.github/workflows/ci.yml`
- `tools/lint/check_spec_cross_refs.py`
- `tools/lint/check_known_gaps.py`
- `docs/architecture/known-gaps.md`
- `docs/architecture/sequence/alert-approval-publication.md`
- `docs/architecture/c4/agent-runtime-llm-gateway.md`
- `docs/architecture/data/integration-point-map.md`
- `docs/architecture/security/rbac-matrix.md`
- `docs/architecture/security/trust-boundary.md`
- `docs/architecture/sequence/recovery-transition.drawio`
- `specs/001-arch-docs-refresh/implementation-review-tasks.md`

## External/Human Gates Left Open

- No CI run URL captured.
- No human architecture/auditor/accessibility sign-off captured.
- No deployment/provisioning commands executed.
- No Draw.io PNG exports performed in this pass.

---

## Pass 2 — 2026-09-15 Diagram-Source and Validator Closure

Scope: diagram **sources**, validator hardening, and direct fixture/mutation tests for
`001-arch-docs-refresh` only. No other feature folder was inspected or modified.

### Rendering Boundary (Decided by Executed Command, Not Assumption)

1. `python .github/skills/drawio-mcp-diagramming/scripts/render_drawio.py docs/architecture/data/multi-jurisdiction-tenancy.drawio --output artifacts/test-scratch/mjt-render-test.png`
   - Result: **FAIL**, exit code 1.
   - Output: `Error: 'drawio' not found on PATH.` followed by the install instructions.
   - Decision taken: preserve all 34 existing PNGs untouched; do **not** fabricate exports; record
     `agent="remediation-source-updated; export=pending-drawio"` on every changed source; regenerate
     `docs/architecture/.diagram-hashes` from the new source bytes; leave every PNG-fidelity and export
     criterion explicitly open.

### Executed Commands and Outcomes

1. XML parse of every architecture diagram source
   - Command: `python` walk of `docs/architecture/**/*.drawio` with `xml.etree.ElementTree.parse`
   - Result: **PASS** — `total 34`, `OK`, zero parse failures.

2. `python tools/lint/check_diagram_manifest.py --root .`
   - Result: **PASS**
   - Output: `OK: diagram manifest validation passed (34 drawio, 34 png, 34 manifest entries).`

3. `python tools/lint/check_spec_cross_refs.py --root .`
   - Result: **PASS**
   - Output: `Note: spec-002 is absent from specs/ inventory and is not required.` / `All 36 spec numbers cited via resolvable local spec links.`

4. `python tools/lint/check_known_gaps.py --root .`
   - Result: **PASS**
   - Output: `All 25 rows valid.` (22 pre-existing rows plus `DRAWIO-EXPORT-01`, `DRAWIO-FALLBACK-01`, `AZURE2-ICON-RENDER`.)

5. `npx --yes markdownlint-cli2 "docs/architecture/**/*.md"`
   - Result: **PASS**
   - Output: `Linting: 40 files` / `Summary: 0 issues in 0 files`

6. Grep assertions
   - `/tenant_id` across all 34 architecture diagram sources: **0 files**.
   - Hierarchical keys in `data/multi-jurisdiction-tenancy.drawio`: `/scope` ×2, `/jurisdictionId` ×11,
     `/dataSourceId` ×2, and one each of the `SCOPE` / `JURISDICTION` / `AUTHORITY` separation labels.
   - Azure2 `img/lib/azure2/` style references in the ten AUD-009 named sources: `azure-resource-topology` 12,
     `au-residency-data-classification` 9, `agent-runtime-llm-gateway` 3, `c4/system` 3, `c4/container` 7,
     `c4/component-agents` 5, `ingestion-data-flow` 4, `cosmos-partitioning` 1, `cicd-pipeline` 4,
     `trust-boundary` 7 — **55 references, 10/10 files non-zero**.
   - Repository-wide: **13 architecture diagram sources** carry Azure2 styles, **64 references**,
     **20 distinct icon paths**, **0 unconfirmed** against
     `.github/skills/drawio-mcp-diagramming/references/azure2-complete-catalog.txt`.
   - Required semantic tokens across the 18 named diagrams: **133 present, 0 missing**.
   - `markdownlint-disable` / `markdownlint-capture` directives under `docs/architecture/`: **none**.

7. `python -m py_compile tools/lint/check_known_gaps.py tools/lint/check_diagram_manifest.py tools/lint/check_spec_cross_refs.py tests/contract/test_architecture_docs.py`
   - Result: **PASS**, exit 0.

8. Direct validator-test harness (pytest unavailable)
   - Command: `python` loader that imports `tests/contract/test_architecture_docs.py` and invokes every
     `test_*` function with a fresh `tempfile.TemporaryDirectory()` path.
   - Result: **PASS** — `RAN 46 PASSED 46 FAILED 0`.
   - Coverage added this pass: 13 diagram-manifest mutation cases, 11 spec-cross-ref negative/positive cases,
     15 known-gaps shape cases (plus the 7 pre-existing cases).

9. Product-module import validation
   - `app.auth.rbac_registry` — **IMPORT OK**
   - `agents.common.model_gateway` — **IMPORT OK**
   - `agents.common.foundry_chat_client` — **IMPORT OK**
   - `tools.lint.check_diagram_manifest`, `check_spec_cross_refs`, `check_known_gaps` — **IMPORT OK**
   - `app.middleware.rbac_check`, `app.main`, `app.services.public_alert_service`,
     `app.repositories.signal_repository`, `ingestion.worker`, `domain.models.evacuation_stage` —
     **IMPORT FAIL**, exact blocker `ModuleNotFoundError: No module named 'pydantic'`.

10. `.diagram-hashes` regeneration
    - Regenerated after all source edits using repository-root-relative paths sorted lexicographically by path,
      `<64-hex><two spaces><path>`, LF line endings, 34 entries. Verified by command 2 above.
    - Note: the file carried a Windows `Hidden` attribute which blocked the first write
      (`PermissionError: [Errno 13]`); the attribute was cleared to `Archive` before regeneration.

### Dependency Blockers (Exact)

- `ModuleNotFoundError: No module named 'pytest'` — blocks all repository pytest suites.
- `ModuleNotFoundError: No module named 'pydantic'` — blocks importing the API, ingestion and domain modules.
- `Error: 'drawio' not found on PATH` — blocks every PNG export.

### Files Changed in This Pass

#### Diagram sources (23)

- `docs/architecture/accessibility/ops-dashboard-user-journey.drawio`
- `docs/architecture/c4/agent-runtime-llm-gateway.drawio`
- `docs/architecture/c4/component-agents.drawio`
- `docs/architecture/c4/component-api.drawio`
- `docs/architecture/c4/component-ingest.drawio`
- `docs/architecture/c4/component-web.drawio`
- `docs/architecture/c4/container.drawio`
- `docs/architecture/c4/system.drawio`
- `docs/architecture/data/cross-sector-touchpoints.drawio`
- `docs/architecture/data/ingestion-data-flow.drawio`
- `docs/architecture/data/multi-jurisdiction-tenancy.drawio`
- `docs/architecture/deployment/azure-resource-topology.drawio`
- `docs/architecture/deployment/cicd-pipeline.drawio`
- `docs/architecture/deployment/cosmos-partitioning.drawio`
- `docs/architecture/operational/pprr-phase-overlay.drawio`
- `docs/architecture/quality/test-pyramid.drawio`
- `docs/architecture/security/au-residency-data-classification.drawio`
- `docs/architecture/security/rbac-matrix.drawio`
- `docs/architecture/security/sli-slo-model.drawio`
- `docs/architecture/security/trust-boundary.drawio`
- `docs/architecture/sequence/audit-provenance.drawio`
- `docs/architecture/sequence/evacuation-five-stage.drawio`
- `docs/architecture/sequence/recovery-transition.drawio`

#### Docs and manifests

- `docs/architecture/.diagram-hashes` (regenerated, 34 entries)
- `docs/architecture/known-gaps.md` (3 new actionable rows)
- `docs/architecture/spec-035-middleware-and-offline.md` (middleware order corrected)

#### Tooling and tests

- `tools/lint/check_known_gaps.py` (explicit no-gap empty state accepted; arbitrary empty files still rejected)
- `tests/contract/test_architecture_docs.py` (39 new direct fixture/mutation tests, 46 total)

#### Specification records

- `specs/001-arch-docs-refresh/implementation-review-tasks.md`
- `specs/001-arch-docs-refresh/feature-evidence-ledger.md`

#### Deliberately unchanged

- All 34 PNG exports under `docs/architecture/` (no export tool; fabricating them was not acceptable).
- `specs/001-spec-implementation-audit/README.md`.
- Every other feature folder and every other `implementation-review-tasks.md`.

### External/Human Gates Still Open After Pass 2

- PNG re-export and visual fidelity review for all 23 changed sources.
- Azure2 icon rendering confirmation in a draw.io host.
- Human architecture, AIIMS, SRE, auditor and accessibility sign-off.
- CI run URL, GitHub Environment protection evidence, Azure resource inventory.
- Repository pytest execution (blocked by missing `pytest` and `pydantic`).
