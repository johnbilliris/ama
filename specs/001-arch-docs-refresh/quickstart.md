# Quickstart: Adding a New Architecture Diagram

**Audience**: contributors adding a diagram to `docs/architecture/`  
**Spec refs**: FR-006, FR-007, FR-008, FR-021(a,d), FR-022  
**Branch**: `001-arch-docs-refresh`

---

## Overview

Every diagram in `docs/architecture/` is an **atomic pair**: a Draw.io XML source file (`.drawio`)
plus a PNG raster export (`.png`) in the same directory. CI will fail if either half of the pair is
missing, or if the `.drawio` file has changed without a corresponding PNG re-export (detected via
SHA256 hash manifest).

This quickstart walks through the end-to-end process: author → export → embed → hash update → CI
pass.

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Draw.io desktop | ≥ 24.x | https://github.com/jgraph/drawio-desktop/releases |
| `sha256sum` | any | Pre-installed on Linux/macOS; use `Get-FileHash` on Windows (see Step 4) |
| Git | ≥ 2.40 | Pre-installed |

Optional: The `drawio-mcp-diagramming` project skill (GitHub Copilot MCP integration) can generate
initial diagram XML that you then refine in Draw.io desktop.

---

## Step 1 — Author the `.drawio` Source

1. Open **Draw.io desktop** (or use the `drawio-mcp-diagramming` Copilot skill to generate a
   starter).

2. Identify the correct **subdirectory** for your diagram:

   | View type | Subdir |
   |-----------|--------|
   | C4 levels 1–4 | `docs/architecture/c4/` |
   | Sequence flows | `docs/architecture/sequence/` |
   | AIIMS operational | `docs/architecture/operational/` |
   | Data flows, tenancy | `docs/architecture/data/` |
   | Security, compliance | `docs/architecture/security/` |
   | CI/CD, Azure topology | `docs/architecture/deployment/` |
   | WAF, ADR index | `docs/architecture/governance/` |
   | Quality, test taxonomy | `docs/architecture/quality/` ← **NEW** (Amendment 1 — QUAL-01) |
   | Accessibility, UX journeys | `docs/architecture/accessibility/` |

   > **Amendment 1 (2026-05-11)**: Six new diagrams were added — RISK-01 and OPS-03 go in
   > `operational/`; SECTOR-05 goes in `data/`; BUILD-01 goes in `c4/`; QUAL-01 goes in the new
   > `quality/` subdir; EXP-01 goes in `accessibility/`. All six use the standard diagram-pair
   > contract (`.drawio` + PNG + hash manifest entry) — no new CI steps or contract files required.

3. Name the file using lowercase kebab-case: e.g., `my-new-view.drawio`

4. **Azure services** MUST use the Azure shape stencils (FR-008):
   - In Draw.io: `Extras → Edit Diagram` or use the shape search panel
   - Search for `azure` in the shape library; enable the **Azure** stencil pack if not visible
   - Azure shapes are under `Search Shapes` → type the service name (e.g., "Cosmos DB")

5. **Actuation diagrams** (any diagram where the system takes a real-world action) MUST mark every
   human approval checkpoint with a distinct visual treatment (FR-009):
   - Recommended: a yellow swim-lane labelled "Human Approval Gate" around the approval step
   - Alternatively: a red-bordered diamond or hexagon shape labelled "👤 Human Gate"
   - Every actuation sequence (SEQ-01 through SEQ-03, SEQ-05) must have at least one such marker

6. Save the file to the correct subdir, e.g.:

   ```
   docs/architecture/c4/my-new-view.drawio
   ```

---

## Step 2 — Export the PNG

1. In Draw.io desktop, with your diagram open:
   - **File → Export As → PNG…**
   - Set resolution to **150 DPI** (recommended for GitHub Markdown rendering)
   - Set background colour to **white** (`#FFFFFF`)
   - Enable **"Fit page"** to avoid white borders
   - Save to the **same directory** as the `.drawio` file, with the **same base name**:
     ```
     docs/architecture/c4/my-new-view.png
     ```

2. Verify the PNG renders correctly: open it in a browser or image viewer. Check that:
   - Azure shapes are legible at 150 DPI
   - Human-in-the-loop markers are visible
   - Labels are not truncated

---

## Step 3 — Create the Markdown Page

Every diagram pair must be accompanied by an architecture page (FR-003). Create the page in the
same subdirectory:

```
docs/architecture/c4/my-new-view.md
```

Use this template:

```markdown
# [Page Title]

> **Purpose**: [One sentence — what question does this page answer?]  
> **Persona clusters**: [Operational | Sector | Technical-Architecture | Technical-Build | Technical-Quality | Technical-Experience]  
> **Spec refs**: spec-NNN, spec-MMM  
> **[→ Architecture index](../README.md)**

## Diagram

![My New View — [short description]](my-new-view.png)

*[Optional: one-paragraph narrative explaining the key elements of the diagram.]*

## Key Elements

- **[Element A]**: [description]
- **[Element B]**: [description]

## WAF Pillar Notes

| Pillar | Notes |
|--------|-------|
| Reliability | [if relevant] |
| Security | [if relevant] |
| Cost Optimisation | [if relevant] |
| Operational Excellence | [if relevant] |
| Performance Efficiency | [if relevant] |

## Related Pages

- [C4 System Context](system.md) — spec-001
- [ADR Index](../adr/README.md)
```

**Markdownlint notes**: The existing `.markdownlint.jsonc` already allows:
- Long image path lines (`line-length: false`)
- HTML comments for spec cross-refs (`MD033: false`)
- Repeated heading names across sibling sections (`MD024: siblings_only`)

No additional per-page exceptions are needed.

---

## Step 4 — Update the Hash Manifest

After exporting the PNG, update `docs/architecture/.diagram-hashes` to record the current SHA256
of your new `.drawio` file. **This step must be done last**, after the final PNG export.

### Linux / macOS

```bash
cd docs/architecture
find . -name '*.drawio' | sort | xargs sha256sum \
  | sed 's|  \./|  |' \
  > .diagram-hashes
```

### Windows (PowerShell)

```powershell
Set-Location docs/architecture
Get-ChildItem -Recurse -Filter '*.drawio' |
  Sort-Object FullName |
  ForEach-Object {
    $hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower()
    $rel  = $_.FullName.Replace($PWD.Path + '\', '').Replace('\', '/')
    "$hash  $rel"
  } | Set-Content .diagram-hashes -Encoding UTF8
```

Verify the manifest was updated:

```bash
sha256sum --check docs/architecture/.diagram-hashes
# Expected output: all entries: OK
```

---

## Step 5 — Update the Index

Add your new page to `docs/architecture/README.md` under the appropriate persona cluster section.
For example, under `### Technical — Architecture`:

```markdown
- [My New View](c4/my-new-view.md) — [one-line description] — spec-NNN
```

---

## Step 6 — Cite the Spec(s)

At least one architecture page must cite each spec number 001–037 (FR-011). Ensure your page
includes an explicit spec reference. You can use inline text or an HTML comment:

```markdown
<!-- spec-cross-ref: spec-022 -->
```

The `check_spec_cross_refs.py` script looks for the pattern `spec-NNN` (hyphen, 3 digits) anywhere
in `.md` files under `docs/architecture/`.

---

## Step 7 — Run CI Checks Locally (optional but recommended)

```bash
# Markdown lint
npx markdownlint-cli2 "docs/architecture/**/*.md"

# PNG ↔ .drawio pairing
find docs/architecture -name '*.png' | while read p; do
  base="${p%.png}"
  [ ! -f "${base}.drawio" ] && echo "MISSING .drawio for: $p"
done

# Hash manifest
cd docs/architecture && sha256sum --check .diagram-hashes && cd -

# Spec cross-reference coverage
python tools/lint/check_spec_cross_refs.py

# Known-gaps registry
python tools/lint/check_known_gaps.py
```

---

## Step 8 — Commit and Push

```bash
git add docs/architecture/c4/my-new-view.drawio \
        docs/architecture/c4/my-new-view.png \
        docs/architecture/c4/my-new-view.md \
        docs/architecture/.diagram-hashes \
        docs/architecture/README.md
git commit -m "docs: add my-new-view diagram (spec-NNN)"
git push
```

The `docs-arch` CI job will run on your PR and verify all checks pass.

---

## Common Failure Modes

| CI Failure | Cause | Fix |
|-----------|-------|-----|
| `FAIL: PNG without .drawio sibling` | PNG committed but `.drawio` was not | Commit the `.drawio` source file |
| `FAIL: .drawio without .png sibling` | `.drawio` committed but PNG was not exported | Export PNG via Draw.io and commit it |
| `sha256sum: FAILED` | `.drawio` was edited but PNG not re-exported; manifest not updated | Re-export PNG, then re-run Step 4 to regenerate `.diagram-hashes` |
| `markdownlint` error | Markdown rule violation | Run `npx markdownlint-cli2` locally; fix reported violations |
| `FAIL: spec-NNN not cited` | New page does not cite a required spec | Add `spec-NNN` citation to the page |
| `FAIL: Follow-up Task Ref is TBD` | Added a known-gaps row without a real task ref | Replace `TBD` with a GitHub issue number or `tasks.md` anchor |

---

## If You Are Deferring a Diagram

If a diagram cannot be completed in the current iteration, add an entry to
`docs/architecture/known-gaps.md` instead of leaving it undone silently:

```markdown
| MY-DIAG-01 | [Description of what is missing] | tasks.md#my-diag-01 | 2026-MM-DD | Open |
```

The `check_known_gaps.py` script will verify the `Follow-up Task Ref` is non-empty. If the deferred
diagram was in the SC-007 inventory, the spec cross-ref check will still pass because the known-gaps
entry serves as the formal deferral record.

---

## Using the `drawio-mcp-diagramming` Skill (optional)

The project-level `drawio-mcp-diagramming` Copilot skill can generate a starter `.drawio` XML file
from a natural-language description. Use it as follows:

1. In GitHub Copilot Chat, invoke the skill with a prompt such as:
   > "Create a Draw.io sequence diagram for the alert authoring → human approval → publication
   > flow, using Azure shape stencils, with a human approval swim-lane."

2. The skill returns Draw.io XML. Paste it into Draw.io desktop via `Extras → Edit Diagram`.

3. Review for accuracy: the MCP output may not perfectly reflect the actual system. Adjust shapes,
   labels, and relationships as needed before exporting.

4. Continue from **Step 2** above.
