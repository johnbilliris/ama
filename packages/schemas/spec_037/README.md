# `spec_037` schemas (runtime mirror)

These six JSON Schema (draft 2020-12) files are a **byte-identical mirror** of the
canonical schema files committed under
`specs/037-capstone-evidence-pack/contracts/*.schema.json`.

The runtime copy here is what the Pydantic v2 models under
`packages/domain/src/domain/models/evidence_pack/` and the FastAPI routes under
`apps/api/app/api/routes/governance/evidence_pack.py` load. The canonical copy
under `specs/.../contracts/` is the source of truth for the contract; this mirror
is for runtime use.

## Mirror policy

- **Canonical path**: `specs/037-capstone-evidence-pack/contracts/*.schema.json`
- **Runtime mirror**: `packages/schemas/spec_037/*.schema.json` (this directory)
- The two sets MUST be byte-identical. The CI publication-gate (T046,
  `scripts/evidence_pack_gate/`) asserts equality. If they diverge, regenerate
  the mirror via:
  ```pwsh
  Get-ChildItem specs/037-capstone-evidence-pack/contracts -Filter '*.schema.json' | ForEach-Object {
    Copy-Item $_.FullName -Destination (Join-Path 'packages/schemas/spec_037' $_.Name) -Force
  }
  ```

## Schemas

| File | Artefact |
|---|---|
| `risk-register.schema.json` | Artefact 1 — Systematic Risk Register |
| `adoption-roadmap.schema.json` | Artefact 2 — Adoption Roadmap |
| `executive-kpi-surface.schema.json` | Artefact 3 — Executive KPI Surface |
| `responsible-ai-register.schema.json` | Artefact 4 — Responsible AI Register |
| `feature-value-ledger.schema.json` | Artefact 5 — Feature-Value Ledger + Tradeoff Log |
| `publication-gate-metadata.schema.json` | Cross-cutting publication-gate metadata |

Citations: RES-01, PD-037-01, FR-009 (`specs/037-capstone-evidence-pack/`).
