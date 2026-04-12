# Research: Root README.md

**Feature**: 013-root-readme
**Date**: 2025-07-17
**Status**: Complete — all unknowns resolved

## Research Tasks

### RT-001: GitHub Mermaid Rendering Capabilities and Constraints

**Decision**: Use inline Mermaid code blocks (` ```mermaid `) for the architecture diagram.

**Rationale**: GitHub natively renders Mermaid diagrams on both desktop and mobile since 2022. No external tooling or image hosting needed. The diagram is version-controlled as text, producing meaningful diffs on changes. This is the most maintainable approach for a project that doesn't yet have any Mermaid diagrams.

**Alternatives Considered**:
- **PNG/SVG image file**: Rejected — requires separate tooling to regenerate, binary diffs are meaningless, accessibility is limited (no text extraction).
- **ASCII art**: The existing `architecture.md` uses ASCII art, but Mermaid is superior for the README because GitHub renders it as an interactive diagram with better visual clarity for first-time readers.
- **External diagram service** (e.g., draw.io, Lucidchart): Rejected — introduces external dependency, images go stale, not version-controlled as text.

**Constraints identified**:
- Mermaid diagrams inside `<details>` blocks can render inconsistently on some GitHub mobile clients → FR-017 already requires the architecture diagram to NOT be in a collapsible block (confirmed alignment).
- Keep the Mermaid diagram under ~30 lines for readability and rendering speed.
- Use `graph TD` (top-down) for the three-tier architecture to match the mental model in the existing ASCII diagram.

---

### RT-002: Collapsible `<details>` Blocks — GitHub Rendering Behaviour

**Decision**: Use HTML `<details><summary>` blocks for verbose sections; always include a blank line after `<summary>` and before closing `</details>` to ensure Markdown rendering inside the block.

**Rationale**: GitHub-Flavoured Markdown requires a blank line between HTML tags and Markdown content for the Markdown to be parsed. Without the blank line, content renders as raw text. This is the most common pitfall with `<details>` blocks.

**Alternatives Considered**:
- **No collapsible blocks**: Rejected — NFR-001 caps the README at 500 lines; without collapsible blocks, the detailed file tree and prerequisites would push the document well beyond this limit while making it unscannable.
- **Tab-based navigation**: Not supported by GitHub Markdown.

**Best practices identified**:
1. Always use `<summary>` with a descriptive label (NFR-004).
2. Add a blank line after `<summary>` tag.
3. Add a blank line before `</details>` tag.
4. Do NOT nest Mermaid code fences inside `<details>` (rendering is unreliable).
5. Test on both GitHub desktop and mobile after merge.

**Pattern**:
```html
<details>
<summary>📂 Repository Structure</summary>

```text
apps/
├── api/
...
```

</details>
```

---

### RT-003: Flesch-Kincaid Grade Level Validation Tooling

**Decision**: Use the `textstat` Python library for FK Grade Level validation (SC-009), with `textstat.flesch_kincaid_grade()`.

**Rationale**: `textstat` is a well-maintained Python library (already in the Python ecosystem of this project), produces consistent FK scores, and can be scripted for CI validation. The spec references it as an example tool (SC-009). It aligns with the project's Python-first tooling.

**Alternatives Considered**:
- **Hemingway Editor**: Web-based, not scriptable for CI, requires manual copy-paste. Good for manual spot-checks but not automatable.
- **readable.io**: Online service, requires account, not suitable for CI.
- **`py-readability-metrics`**: Less maintained than `textstat`.

**Threshold interpretation** (addresses CHK039):
- FK score must be ≤ 8.0 (no rounding — 8.4 does NOT pass).
- Validate only the overview, quickstart, and personas sections (per CHK016 union resolution).
- Extract section text by parsing between headings, stripping Markdown formatting before analysis.

---

### RT-004: Prerequisites Split Strategy (CHK017 Resolution)

**Decision**: Split the prerequisites section into two subsections: "Required for Local Development" and "Required for Azure Deployment".

**Rationale**: The spec has an apparent conflict — FR-004 lists Azure CLI as a prerequisite, but FR-003 and the Assumptions section state the quickstart requires no Azure credentials. The resolution (provided by the user) splits prerequisites by context:

**Local Development prerequisites** (required for quickstart):
- Python ≥ 3.12 (from `pyproject.toml`)
- Node.js ≥ 22 (from Next.js 15 requirements + project conventions)
- pnpm = 10.6.3 (from `package.json` `packageManager` field)
- uv (Python package manager, from `uv.lock` presence)
- Docker (from `Dockerfile` presence in apps/api, apps/ingestion, apps/web)
- Git ≥ 2.x

**Azure Deployment prerequisites** (NOT required for quickstart):
- Azure CLI ≥ 2.60
- Azure subscription with Australia East region access
- Azure Developer CLI (`azd`) (from `azure.yaml` presence)

**Alternatives Considered**:
- **Single flat list with annotations**: Rejected — readers scanning for quickstart prerequisites would see Azure CLI and assume they need it, causing confusion.
- **Separate page for deployment prerequisites**: Rejected — over-engineering for a 2-item list.

---

### RT-005: IC Authority Statement Placement (CHK018 Resolution)

**Decision**: Place the single, primary IC authority statement in the AIIMS Personas section (FR-005), with a brief cross-reference sentence near the constitution link (FR-013).

**Rationale**: The AIIMS Personas section is the natural home for governance and authority statements because that's where readers go to understand role boundaries. Duplicating the full statement would violate DRY and risk the two copies diverging.

**Implementation pattern**:
```markdown
## 👥 AIIMS Personas & Human Authority

... role mapping table ...

> **⚠️ Human Authority**: The Incident Commander retains final decision
> authority over all safety-critical system outputs, including evacuations,
> public alerts, and resource dispatch recommendations. The platform
> recommends; humans decide.

... later, in documentation links or safety section ...

See the [Project Constitution](.specify/memory/constitution.md) for the
complete life-safety principles, including the requirement that the Incident
Commander retains final authority over all safety-critical decisions.
```

**Alternatives Considered**:
- **Two identical full statements**: Rejected — duplication risk, line count waste.
- **Only in safety section**: Rejected — government stakeholders navigating via ToC to "Personas" would miss it (SC-004 requires finding it within 60 seconds of reading the personas section).

---

### RT-006: Existing File Dependency Validation

**Decision**: All files referenced in FR-006 exist in the repository. No broken-link risk at merge time.

**Findings**:

| Referenced Path | Exists? | Notes |
|----------------|---------|-------|
| `docs/disaster-response-hub/architecture.md` | ✅ Yes | Full architecture doc with ASCII diagram |
| `.specify/memory/constitution.md` | ✅ Yes | v1.0.2, ratified 2026-03-02 |
| `.github/workflows/ci.yml` | ✅ Yes | CI pipeline |
| `AMA_Rubric_Asia.md` | ✅ Yes | Evaluation rubric at repo root |
| `capstone.md` | ✅ Yes | Project capstone at repo root |
| `docs/disaster-response-hub/demo/executive-deck.md` | ✅ Yes | Executive presentation |
| `docs/disaster-response-hub/operator-runbooks.md` | ✅ Yes | Operator runbooks |
| `docs/disaster-response-hub/demo/walkthrough.md` | ✅ Yes | Demo walkthrough |
| `specs/` | ✅ Yes | Feature specifications directory |
| `infra/` | ✅ Yes | Bicep IaC templates |
| `apps/` | ✅ Yes | All 4 app directories present |
| `packages/` | ✅ Yes | domain, schemas, ui packages |
| `tests/` | ✅ Yes | 7 test categories |

**No missing dependencies.** SC-007 (all internal links resolve) can be satisfied.

---

### RT-007: Terminology Audit — "Agent" vs "Service" vs "Runtime"

**Decision**: Use "agent" for the 5 AI components, "runtime" for the 3 execution environments, per FR-014 and the Terminology section.

**Findings from existing documentation**:
- `architecture.md` uses "API Service" for the FastAPI component — the README MUST use "API runtime" instead (FR-014 explicitly acknowledges this divergence).
- `architecture.md` uses "Agent Runtime" for `apps/agents/` — consistent with README terminology.
- `architecture.md` uses "Web Client" for `apps/web/` — README should use "Web runtime" for consistency with the three-runtime model.

**Terminology mapping for README**:

| Component | architecture.md Term | README Term (FR-014) |
|-----------|---------------------|---------------------|
| `apps/api` | API Service | API runtime |
| `apps/agents` | Agent Runtime | Agent runtime |
| `apps/web` | Web Client | Web runtime |
| Monitoring Agent | Monitoring Agent | Monitoring Agent |
| Risk Assessment Agent | Risk Assessment Agent | Risk Assessment Agent |
| Evacuation Agent | Evacuation Agent | Evacuation Agent |
| Resource Allocation Agent | Resource Allocation Agent | Resource Allocation Agent |
| Communication Agent | Communication Agent | Communication Agent |

---

### RT-008: Line Count Budget Analysis

**Decision**: Target ~420–480 lines to stay under 500 with margin.

**Budget allocation** (estimated lines per section):

| Section | Est. Lines | Collapsible? | Notes |
|---------|-----------|-------------|-------|
| Title + badges area | 5 | No | Project name, one-liner |
| Table of Contents | 15 | No | 10 sections + formatting |
| Project Overview | 25 | No | FK8, must be concise |
| Agents | 30 | Partially | Summary visible, details collapsible |
| AIIMS Personas & Authority | 30 | No | Table + IC authority callout |
| Architecture Diagram | 25 | No | Mermaid block + brief context |
| Quickstart | 40 | Partially | Commands visible, full prereqs collapsible |
| Repository Structure | 10+35 | Yes | Summary visible, file tree collapsible |
| Technology Stack | 20 | No | Brief table |
| Success Metrics | 15 | No | Bulleted list |
| Contributing | 20 | No | Brief guidelines |
| Documentation Links | 25 | No | Audience-organized links |
| **Total estimate** | **~295 + ~65 collapsed** | | **~360 visible + 65 collapsed = ~425 total** |

The 500-line limit is achievable. NFR-001 excludes blank lines within collapsed `<details>` blocks from the count, providing additional margin.

## Summary of Resolutions

All NEEDS CLARIFICATION items have been resolved:

1. ✅ Mermaid is the diagram format (inline code block, not in `<details>`)
2. ✅ `<details>` blocks require blank-line pattern for GFM rendering
3. ✅ `textstat` is the FK validation tool; threshold is ≤8.0 strict
4. ✅ Prerequisites are split into local dev vs Azure deployment
5. ✅ IC authority lives in AIIMS Personas section with cross-reference
6. ✅ All referenced files exist — no broken links
7. ✅ Terminology mapping is clear: agents (5 AI components), runtimes (3 execution environments)
8. ✅ Line budget is ~425/500 — feasible with margin
