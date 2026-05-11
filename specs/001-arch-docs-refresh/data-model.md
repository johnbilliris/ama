# Data Model: Comprehensive Architectural Documentation & Diagrams Refresh

**Branch**: `001-arch-docs-refresh` | **Phase**: 1 — Design  
**Generated**: 2026-05-11

This feature is documentation-as-code; there is no application database. "Entities" are the
logical artefact types produced and consumed by this feature, along with their structure, validation
rules, and relationships.

---

## Entity Map

```
ArchitecturePage
  ├── embeds 1..* DiagramPair
  ├── cites 1..* SpecReference
  └── cites 0..* ADRReference

DiagramPair
  ├── has 1   DrawioSource
  ├── has 1   PngExport
  └── has 1   ManifestEntry (in HashManifest)

HashManifest
  └── contains 1..* ManifestEntry

KnownGapsRegistry
  └── contains 0..* GapEntry

ADRNavigationIndex
  └── lists 1..* ADREntry (cross-reference to docs/decisions/)

LintScript
  ├── check_spec_cross_refs.py
  └── check_known_gaps.py

CIJob (docs-arch in ci.yml)
  └── runs LintScript × 4 + shell checks
```

---

## Entities

### 1. ArchitecturePage

A Markdown document under `docs/architecture/` forming part of the documentation set.

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `path` | `string` (repo-relative) | ✅ | Must match `docs/architecture/**/*.md` |
| `purpose_statement` | `string` | ✅ | First non-heading, non-image line of the file; one sentence |
| `persona_clusters` | `string[]` | ✅ | At least one of: Operational, Sector, Technical-Architecture, Technical-Build, Technical-Quality, Technical-Experience |
| `diagram_refs` | `string[]` | ✅ (except text-only pages) | Each ref must resolve to a sibling or relative `.png` file |
| `spec_citations` | `SpecReference[]` | ✅ | At least one, per FR-012 |
| `adr_citations` | `ADRReference[]` | ❌ (optional) | Must resolve to `docs/decisions/{spec-id}/{id}-{slug}.md` |
| `view_type` | `enum` | ✅ | One of: c4, sequence, operational, data, security, deployment, governance, accessibility |
| `index_path` | `string` | ✅ | Front-matter banner linking to `docs/architecture/README.md` |

**Validation rules**:
- `markdownlint-cli2` must report zero violations against repo `.markdownlint.jsonc`
- Every `![alt](path.png)` reference must have a sibling `.drawio` file (CI enforces)
- Every `spec-NNN` citation must appear in the cross-ref check allowlist (001–037)
- `purpose_statement` must be present on all pages (FR-003)

**State transitions**: N/A (static files)

---

### 2. DiagramPair

An atomic unit consisting of a Draw.io XML source file and its PNG raster export.

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `drawio_path` | `string` (repo-relative) | ✅ | Must match `docs/architecture/**/*.drawio` |
| `png_path` | `string` (repo-relative) | ✅ | Same directory; same base name as drawio_path; `.png` extension |
| `diagram_id` | `string` | ✅ | One of the 32 IDs in SC-007 inventory (post-Amendment 1; e.g., `C4-L1`, `SEQ-01`, `QUAL-01`) |
| `title` | `string` | ✅ | Matches SC-007 inventory title |
| `uses_azure_stencils` | `bool` | ✅ (if depicting Azure services) | Must use Azure shape stencils (FR-008) |
| `human_itl_marked` | `bool` | conditional | Required `true` for actuation diagrams (FR-009); SEQ-01, SEQ-02, SEQ-03, SEQ-05 |
| `manifest_entry` | `ManifestEntry` | ✅ | hash in `.diagram-hashes` must match SHA256 of drawio file |

**Invariants**:
- For every `.drawio` there MUST be a sibling `.png` (CI check: `find` one-liner)
- For every `.png` there MUST be a sibling `.drawio` (CI check: inverse `find`)
- SHA256 of `.drawio` file MUST match the manifest entry (CI check via `sha256sum`)

**32 diagram pairs** (authoritative list, post-Amendment 1): See plan.md Diagram Inventory table.

---

### 3. DrawioSource

The `.drawio` XML file checked into the repository.

| Field | Type | Notes |
|-------|------|-------|
| `xml_format` | Draw.io XML v21+ | `<mxfile>` root element |
| `stencil_library` | Azure / General | Confirm via shape `style` attributes referencing `shape=mxgraph.azure.*` |
| `file_path` | repo-relative string | e.g., `docs/architecture/c4/system.drawio` |

---

### 4. PngExport

The raster PNG produced by exporting the DrawioSource.

| Field | Type | Notes |
|-------|------|-------|
| `file_path` | repo-relative string | Sibling of `.drawio`; same base name |
| `resolution` | int (DPI) | 150 DPI recommended for GitHub Markdown rendering |
| `background` | colour | White (`#FFFFFF`) for light-theme readability |

---

### 5. HashManifest

The file `docs/architecture/.diagram-hashes` containing one entry per `.drawio` file.

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `path` | `string` | ✅ | docs/architecture/ repo-relative path to `.drawio` file |
| `sha256` | `string` (64 hex chars) | ✅ | SHA256 hex digest of the `.drawio` file at last PNG export |
| `format` | `"sha256  <path>"` | ✅ | Two spaces between hash and path; sorted by path |

**Validation rules**:
- Entries sorted lexicographically by path
- No duplicate paths
- Every `.drawio` under `docs/architecture/` has exactly one entry
- CI: `sha256sum --check docs/architecture/.diagram-hashes` reports zero failures

---

### 6. ManifestEntry

A single line in the HashManifest.

| Field | Type | Example |
|-------|------|---------|
| `sha256_hex` | 64-char hex string | `a3f2c1...` |
| `drawio_path` | repo-relative string | `c4/system.drawio` |
| `raw_line` | `"{sha256_hex}  {drawio_path}"` | Two-space separator (sha256sum format) |

---

### 7. KnownGapsRegistry

The file `docs/architecture/known-gaps.md` containing a Markdown table (FR-023).

| Column | Type | Required | Validation |
|--------|------|----------|------------|
| `area_spec` | string | ✅ | Area name or spec number (e.g., `BICEP-DEP-01`, `spec-037`) |
| `gap_description` | string | ✅ | One sentence describing what is missing |
| `follow_up_task_ref` | string | ✅ | Non-empty, non-`TBD`; GitHub issue number, task ID, or tracking ref |
| `date_identified` | `YYYY-MM-DD` | ✅ | ISO 8601 date |
| `status` | enum | ✅ | One of: `Open`, `In Progress`, `Resolved` |

**Validation rules** (enforced by `check_known_gaps.py` and `docs-arch` CI job):
- No row may have an empty or `TBD` `follow_up_task_ref` (FR-023, SC-008)
- Table header must use exact column names (CI parser relies on them)

**Initial known-gaps entries** (to be seeded at implementation time):

| Area/Spec | Gap Description | Follow-up Task Ref | Date Identified | Status |
|-----------|----------------|-------------------|----------------|--------|
| BICEP-DEP-01 | Bicep module dependency graph deferred; requires auto-generation tooling from `infra/bicep/` | https://github.com/johnbilliris/ama/issues/new?title=BICEP-DEP-01+Bicep+module+dependency+graph | 2026-05-11 | Open |
| DUPE-036 | Two `036-*` spec directories observed; counted as one shipped spec for cross-ref purposes | `tasks.md#T061` | 2026-05-11 | Open |
| CAP-MIG-01 | `capacity-model.md` at root not yet migrated to `deployment/` or `governance/` subdir | `tasks.md#T067` | 2026-05-11 | Open |
| COSM-MIG-01 | Root-level `cosmos-partitioning.md` not yet migrated; superseded by `deployment/cosmos-partitioning.md` | `tasks.md#T068` | 2026-05-11 | Open |
| MDW-MIG-01 | Root-level `spec-035-middleware-and-offline.md` not yet migrated to a named subdir | `tasks.md#T069` | 2026-05-11 | Open |
| FOUNDRY-REGION | Specific non-AU Foundry regions not hard-coded in SEC-01 diagram; registry-gated mechanism only | `tasks.md#T044` | 2026-05-11 | Open |
| SPEC-037 | Spec 037 capstone evidence pack cross-reference to be verified during T064 | `tasks.md#T064` | 2026-05-11 | Open |
| C4-L4 | C4 Level 4 (Code) views deferred per spec assumption — author on demand only | `tasks.md#T071` | 2026-05-11 | Open |
| LYCHEE-CFG | `.lychee.toml` exclude patterns for spec deep-link anchors not yet authored; iterate after first CI run | `tasks.md#T063` | 2026-05-11 | Open |
| WCAG-AUDIT-FULL | WCAG 2.2 coverage map is text/table only in this feature; full automated audit deferred | `tasks.md#T054` | 2026-05-11 | Open |
| SPEC-RANGE-VERIFY | Spec ID range (001–037, with 002 absent) verified by `check_spec_cross_refs.py` against filesystem | `tasks.md#T064` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-RISK-01 | RISK-01 (`operational/hazard-risk-register.drawio`) not yet authored; if `drawio-mcp-diagramming` skill unavailable, hand-author in Draw.io desktop using quickstart.md Step 1 | `tasks.md#RISK-01` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-OPS-03 | OPS-03 (`operational/pprr-phase-overlay.drawio`) not yet authored; if MCP unavailable, hand-author; source: constitution §PPRR Lifecycle | `tasks.md#OPS-03` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-SECTOR-05 | SECTOR-05 (`data/cross-sector-touchpoints.drawio`) not yet authored; if MCP unavailable, hand-author as a data-flow extension of SECTOR-02/SECTOR-03 | `tasks.md#SECTOR-05` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-BUILD-01 | BUILD-01 (`c4/agent-llm-gateway.drawio`) not yet authored; if MCP unavailable, hand-author as C4 component view in `c4/`; uses Azure AI/OpenAI shape stencils | `tasks.md#BUILD-01` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-QUAL-01 | QUAL-01 (`quality/test-pyramid.drawio`) not yet authored; if MCP unavailable, hand-author; `quality/` subdir must be created first (new subdir, Amendment 1) | `tasks.md#QUAL-01` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-EXP-01 | EXP-01 (`accessibility/ops-dashboard-user-journey.drawio`) not yet authored; if MCP unavailable, hand-author as user-journey flow in `accessibility/` | `tasks.md#EXP-01` | 2026-05-11 | Open |

---

### 8. ADRNavigationIndex

The file `docs/architecture/adr/README.md` — a cross-reference table, not a file store.

| Column | Type | Required |
|--------|------|----------|
| `decision_number` | string | ✅ (e.g., `01`) |
| `title` | string | ✅ |
| `status` | enum | ✅ (Proposed / Accepted / Deprecated / Superseded) |
| `date` | `YYYY-MM-DD` | ✅ |
| `motivating_spec` | string | ✅ (e.g., `spec-036`) |
| `canonical_path` | repo-relative link | ✅ (must resolve to `docs/decisions/{spec-id}/{id}-{slug}.md`) |

**Invariants**:
- `canonical_path` links are validated by `lychee` link checker in `docs-arch` CI job
- Index is NOT a store; no ADR files live in `docs/architecture/adr/`

---

### 9. SpecReference

A citation of a shipped spec number within an architecture page.

| Field | Type | Validation |
|-------|------|------------|
| `spec_number` | `NNN` (zero-padded 3 digits) | Must be in range `001`–`037` |
| `spec_id` | string | e.g., `spec-022` |
| `source_page` | `ArchitecturePage.path` | Page containing the citation |
| `citation_format` | string | Inline text or HTML comment e.g., `<!-- spec-cross-ref: spec-022 -->` |

**`check_spec_cross_refs.py` logic**:
1. Build allowlist of spec numbers from `specs/*/` directory names (deduped prefix)
2. Build exclusion list from `docs/architecture/known-gaps.md` (archived/superseded entries)
3. Scan `docs/architecture/**/*.md` for pattern `spec-NNN` or `spec NNN`
4. Assert every allowlist entry (minus exclusions) appears in at least one page
5. Exit 0 on clean, 1 on missing citations (with structured report)

---

### 10. LintScript

A Python script under `tools/lint/` providing a CI-invocable validation command.

| Script | Purpose | Exit codes |
|--------|---------|------------|
| `check_spec_cross_refs.py` | Assert all shipped spec numbers cited in architecture pages | 0 = clean, 1 = missing citations |
| `check_known_gaps.py` | Assert no known-gaps row has empty/TBD Follow-up Task Ref | 0 = clean, 1 = violations |

**Common interface** (both scripts):
- Accepts `--root <repo-root>` optional argument (defaults to `cwd`)
- Prints structured report to stdout on failure
- Compatible with Python 3.12; no third-party imports (stdlib only: `pathlib`, `re`, `sys`, `argparse`)

---

### 11. CIJob (`docs-arch`)

The `docs-arch` job added to `.github/workflows/ci.yml`.

| Property | Value |
|----------|-------|
| `name` | `docs-arch` |
| `runs-on` | `ubuntu-latest` |
| `needs` | (none — runs in parallel with `quality` job) |
| `timeout-minutes` | `10` |
| `triggers` | Same as `quality` job: push to `main`/`dev`/`staging`/`production`; PR to `main` |
| `path-filter` | None — runs on every PR regardless of changed files |

**Steps** (in execution order):

| Step name | Tool | Validates |
|-----------|------|-----------|
| `checkout` | `actions/checkout` | — |
| `markdownlint` | `npx markdownlint-cli2 "docs/architecture/**/*.md"` | FR-022 |
| `link-check` | `lychee docs/architecture/` | FR-021b |
| `png-drawio-pairing` | `find` shell one-liner | FR-021a |
| `hash-manifest-check` | `sha256sum --check docs/architecture/.diagram-hashes` | FR-021d |
| `spec-cross-ref-check` | `python tools/lint/check_spec_cross_refs.py` | FR-021c, FR-011 |
| `known-gaps-check` | `python tools/lint/check_known_gaps.py` | FR-023, SC-008 |

---

## Entity Relationships

```
docs/architecture/README.md (index)
  │
  ├── links to → ArchitecturePage × ~35
  │                 │
  │                 ├── embeds → DiagramPair × 32 (post-Amendment 1)
  │                 │             ├── DrawioSource → ManifestEntry (HashManifest)
  │                 │             └── PngExport
  │                 ├── cites → SpecReference (001–037)
  │                 └── optionally cites → ADREntry (docs/decisions/)
  │
  ├── links to → KnownGapsRegistry (docs/architecture/known-gaps.md)
  └── links to → ADRNavigationIndex (docs/architecture/adr/README.md)

CI (docs-arch job)
  ├── validates → ArchitecturePage (markdownlint)
  ├── validates → ArchitecturePage internal links (lychee)
  ├── validates → DiagramPair pairing (find)
  ├── validates → ManifestEntry integrity (sha256sum)
  ├── validates → SpecReference coverage (check_spec_cross_refs.py)
  └── validates → KnownGapsRegistry completeness (check_known_gaps.py)
```
