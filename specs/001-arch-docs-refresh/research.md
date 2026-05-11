# Research: Comprehensive Architectural Documentation & Diagrams Refresh

**Branch**: `001-arch-docs-refresh` | **Phase**: 0 — Outline & Research  
**Generated**: 2026-05-11

---

## Research Questions & Decisions

### RQ-01 — Diagram Authoring Toolchain

**Question**: Which toolchain produces `.drawio` + PNG pairs that pass CI, render Azure shapes
correctly, and are maintainable by the project?

**Decision**: Draw.io desktop / `drawio-mcp-diagramming` project skill

**Rationale**: The spec explicitly mandates `.drawio` source files (FR-006) and Azure shape stencils
(FR-008). The project already has the `drawio-mcp-diagramming` skill installed at the project level
(per `SKILL.md`), providing a consistent, auditable authoring path. Draw.io's XML format is git-diff
friendly. PNG export is performed from within Draw.io (File → Export As → PNG) or via the MCP tool;
the result is a raster image suitable for GitHub Markdown rendering without a build step.

**Alternatives considered**:
- Mermaid (built into GitHub Markdown): Rejected — does not support Azure shape stencils (FR-008);
  mermaid PNGs cannot be version-controlled as a `.drawio` source (FR-006). The pre-existing `c4/`
  docs already use Mermaid; those files are updated with front-matter only and do not need to be
  migrated to Draw.io.
- PlantUML: Rejected — same stencil limitation; requires a build server for PNG generation.
- Structurizr: Rejected — additional SaaS dependency; not in the existing toolchain.

---

### RQ-02 — PNG Staleness Detection

**Question**: How do we detect that a `.drawio` file was updated but the PNG was not re-exported?
File modification timestamps are unreliable after `git clone`.

**Decision**: SHA256 hash manifest at `docs/architecture/.diagram-hashes`

**Rationale**: Per spec clarification Q3 and FR-021(d): timestamps are unreliable (all files share
the clone timestamp). A SHA256 manifest is git-stable, reproducible, and CI-cacheable. The manifest
records the SHA256 of each `.drawio` file at PNG-export time. If the `.drawio` hash diverges from the
manifest entry, the build fails. This gives auditors a version-of-record for each diagram source.

**Manifest format** (resolved, see contracts/diagram-manifest-format.md):
```
sha256  c4/system.drawio
sha256  c4/container.drawio
```
Sorted by relative path; generated/updated by the contributor after each PNG export.

**Alternatives considered**:
- Git modification timestamps: Rejected — unreliable post-clone.
- CI-side PNG re-generation + diff: Rejected — requires Draw.io CLI in the runner image, adding a
  heavyweight dependency and CI time. The hash approach is leaner.

---

### RQ-03 — Link Checking Tool

**Question**: Which link checker runs in the GitHub Actions `ubuntu-latest` runner with no new
permanent devDependency?

**Decision**: `lychee` (installed via apt/cargo in the CI runner setup step)

**Rationale**: `lychee` is fast (async Rust), supports relative file:// links, configurable timeout,
and can be scoped to `docs/architecture/**/*.md`. It is available as an apt package (`lychee`) or a
pre-compiled binary download, requiring only a one-line install step in the CI job. It handles anchor
links (`#section`) which are common in architecture index pages.

**Known risk**: False positives on spec deep-links (e.g., `specs/036-*/spec.md#fr-rag-cv-01`) — these
are repo-internal relative paths. Mitigation: configure lychee with `--include 'docs/architecture'`
to scope internal-link checking to the architecture directory only; external URLs with transient
failures use `--max-retries 2`.

**Alternatives considered**:
- `markdown-link-check` (npm): Available but slower (sequential); requires Node.js which is already
  present in the runner. Fallback option if `lychee` is unavailable.
- `linkcheck` (Python): Less maintained; no async support.

---

### RQ-04 — Markdown Lint Invocation

**Question**: How does the `docs-arch` CI job invoke markdownlint without adding a workspace
devDependency?

**Decision**: `npx markdownlint-cli2 "docs/architecture/**/*.md"` — no new workspace devDependency

**Rationale**: Per spec clarification Q3 and FR-022: `npx` downloads `markdownlint-cli2` on demand
(cached by the Actions runner). The existing `.markdownlint.jsonc` ruleset at repo root already
includes `line-length: false`, `MD033: false`, and `MD024: siblings_only` — these relaxations cover
the patterns common in diagram-heavy pages (long image paths, HTML comment annotations, repeated
headings in sibling sections). No per-path exceptions are needed for architecture pages.

**Rule coverage check** (verified against existing `.markdownlint.jsonc`):
- Long `![diagram](path/to/diagram.png)` lines: covered by `line-length: false`
- `<!-- spec-cross-ref: spec-022 -->` HTML comments: covered by `MD033: false`
- Multiple `## Purpose` or `## Diagrams` headings across siblings: covered by `MD024: siblings_only`

---

### RQ-05 — Spec Cross-Reference Coverage (001–037)

**Question**: Which spec numbers 001–037 are confirmed shipped vs archived/duplicate, and how do
they map to architecture pages?

**Finding**: 37 spec numbers in scope. Based on directory inspection:
- Active spec directories found: 001, 010, 015, 017, 019, 020, 024, 025, 028, 029, 030, 036+
- Multiple `036-*` directories observed (spec assumption: treated as one shipped spec for counting;
  duplication noted in known-gaps registry as DUPE-036).
- Specs without a dedicated architecture home are handled via known-gaps registry entries (not
  forced citations).

**Spec-to-view mapping** (preliminary; finalised by the implementation phase):

| Spec range | Primary view home | Secondary citations |
|---|---|---|
| 001–009 (foundation infra, initial platform) | C4 L1 + L2, deployment/ | governance/ |
| 010 (monitoring agent) | C4-L3-Agents, sequence/alert-approval | data/ |
| 015 (performance benchmarks) | governance/waf-pillar-mapping | security/sli-slo-model |
| 017 (CD pipeline) | deployment/cicd-pipeline | deployment/azure-resource-topology |
| 019 (AIDR additional guidances) | operational/aiims-system-context | sequence/* |
| 020 (disaster mapper UI) | c4/component-web | accessibility/wcag-coverage |
| 022 (jurisdiction filter, cited in spec) | data/jurisdiction-filter | data/multi-jurisdiction-tenancy |
| 024 (simulation control chat) | c4/component-agents | sequence/ |
| 025 (agent spec compliance) | c4/component-agents | governance/ |
| 028 (capstone alignment) | governance/waf-pillar-mapping | README.md |
| 029 (progressive delivery pipeline) | deployment/cicd-pipeline | security/au-residency |
| 030 (LLM eval framework) | c4/component-agents | governance/ |
| 035 (middleware and offline) | c4/component-ingest | deployment/ |
| 036 (Foundry RAG grounding) | security/au-residency-data-classification | adr/ |
| 037 (to be resolved at implementation) | known-gaps entry if no home found | — |

**Decision**: `tools/lint/check_spec_cross_refs.py` walks `specs/*/` and asserts each spec number
001–037 (excluding archived entries listed in `docs/architecture/known-gaps.md`) is cited in at
least one architecture page. The known-gaps registry is the escape valve for specs with no natural
home.

---

### RQ-06 — Pre-existing Document Integration Strategy

**Question**: How do the six pre-existing architecture documents integrate with the new structure?
Can they remain in place?

**Decision**: Keep in place; update front-matter only; add redirect banners pointing to the index
and (where applicable) to the superseding page.

| Pre-existing file | Location | Action |
|---|---|---|
| `c4/system.md` | `docs/architecture/c4/system.md` | UPDATED: add front-matter `[→ index](../README.md)` + add `system.drawio` / `system.png` siblings |
| `c4/container.md` | `docs/architecture/c4/container.md` | UPDATED: same front-matter treatment + diagram pair |
| `sequence/monitoring-risk-comms.md` | `docs/architecture/sequence/` | UPDATED: front-matter only; page already serves a valid sequence view |
| `capacity-model.md` | `docs/architecture/capacity-model.md` (root) | UPDATED: front-matter banner; known-gaps migration entry CAP-MIG-01 |
| `cosmos-partitioning.md` | `docs/architecture/cosmos-partitioning.md` (root) | UPDATED: front-matter banner linking to `deployment/cosmos-partitioning.md`; known-gaps entry COSM-MIG-01 |
| `spec-035-middleware-and-offline.md` | `docs/architecture/spec-035-middleware-and-offline.md` (root) | UPDATED: front-matter banner; known-gaps entry MDW-MIG-01 |

**Rationale**: Moving files risks breaking external references and the `rag-optout-binding-lint` CI
step (which resolves paths in `docs/decisions/036-foundry-rag-grounding/`). Prior-spec convention
favours backward compatibility (spec assumption, clarification Q5).

---

### RQ-07 — ADR Navigation Index vs Canonical ADR Store

**Question**: Should `docs/architecture/adr/README.md` be a file store or a navigation cross-reference?

**Decision**: Navigation cross-reference only. Canonical ADR home remains `docs/decisions/{spec-id}/`.

**Rationale**: Per spec clarification Q2: moving the existing 20+ spec-036 ADRs from
`docs/decisions/036-foundry-rag-grounding/` would break the `rag-optout-binding-lint` CI step,
all existing spec-036 cross-references, and the constitution's footnote pattern. The
`docs/architecture/adr/README.md` is a Markdown table linking each ADR by number, title, status,
date, and motivating spec.

---

### RQ-08 — Foundry Carve-out Zone Diagram Label

**Question**: Should SEC-01 (AU-Residency diagram) hard-code non-AU region names or use a
mechanism-zone label?

**Decision**: Mechanism-zone label: `"Permitted Non-AU Foundry Inference Zone (registry-gated; zero active non-AU entries)"`

**Rationale**: Per spec clarification Q4 and FR-016: `infra/parameters/foundry-carveout.yaml`
confirms zero active non-AU entries — all three production Foundry deployments (`gpt-4o-mini`,
`gpt-4o`, `text-embedding-3-large`) are in `australiaeast`. Hard-coding non-AU region names would be
factually incorrect and misleading to auditors. The mechanism-zone label accurately reflects current
operational state and the registry-driven nature of the carve-out (constitution NN-2 v1.2.0).

---

### RQ-09 — `docs-arch` CI Job: Placement and Triggers

**Question**: Should `docs-arch` be a new workflow file or a job in the existing `ci.yml`?

**Decision**: New job `docs-arch` inside `.github/workflows/ci.yml`, same triggers as `quality` job
(push to `main`/`dev`/`staging`/`production`; PR to `main`), no path filtering.

**Rationale**: Per spec clarification Q5 and spec assumption: a separate workflow file would allow
docs changes to bypass required PR checks. No path filtering ensures spec cross-reference correctness
is checked on every PR, not just those touching `docs/architecture/`.

**Job does not `needs: [quality]`** — it runs in parallel to avoid adding latency to the critical
path of the existing quality job.

---

### RQ-10 — WCAG Coverage Map: Diagram or Text?

**Question**: Does the `accessibility/wcag-coverage.md` page require a diagram pair?

**Decision**: Text-only page (table format); no diagram pair required.

**Rationale**: WCAG 2.2 coverage is best expressed as a structured table mapping success criteria
to implementation status per component. It is not in the 26-diagram SC-007 inventory. A Draw.io
diagram adds no clarity over a Markdown table for this content. The page does not trigger the
PNG-without-drawio CI check because it contains no `.png` embeds.

---

### RQ-11 — Bicep Module Dependency Graph (deferred)

**Question**: Should the Bicep module dependency graph be hand-authored or auto-generated?

**Decision**: Deferred. Known-gaps entry `BICEP-DEP-01` created.

**Rationale**: Per spec note in SC-007: "requires tooling to generate from `infra/bicep/`". A
hand-authored graph would drift immediately; auto-generation requires either a custom Python script
parsing HCL/Bicep or a third-party tool. Neither is in scope for this feature iteration. The
`check_spec_cross_refs.py` script will not count this as a missing citation; the known-gaps entry
provides the follow-up track.

---

## Risk Register

| Risk ID | Description | Likelihood | Impact | Mitigation |
|---------|-------------|------------|--------|------------|
| RSK-01 | `drawio-mcp` tool unavailable in CI (not installed) | Medium | High | Draw.io diagrams are authored offline/locally and committed as source; CI only validates the hash manifest, not re-renders diagrams |
| RSK-02 | Azure stencil version drift (shape library updates) | Low | Medium | Pin Draw.io version in quickstart.md; note stencil version in diagram file comments |
| RSK-03 | `lychee` false positives on spec deep-links (anchor fragments) | Medium | Low | Scope lychee to `docs/architecture/` only; add `.lychee.toml` exclude patterns for known deep-link patterns; fallback to `markdown-link-check` |
| RSK-04 | Hash manifest churn on diagram rebuilds (every export changes hash) | High | Low | Document in quickstart.md that manifest must be updated after every PNG export; CI failure message references quickstart step |
| RSK-05 | Two `036-*` spec directories cause double-counting in cross-ref script | Medium | Low | `check_spec_cross_refs.py` uses directory-name prefix deduplication; known-gaps entry DUPE-036 |
| RSK-06 | Spec numbers in 001–037 range with no architecture home force spurious citations | Medium | Medium | Known-gaps registry is the canonical escape valve; CI check reads exclusion list from registry |

---

## Resolution Summary

All `NEEDS CLARIFICATION` items from the Technical Context are resolved:

| Item | Resolution |
|------|-----------|
| Diagram toolchain | Draw.io + drawio-mcp-diagramming skill (RQ-01) |
| Staleness detection | SHA256 hash manifest (RQ-02) |
| Link checker | lychee (RQ-03) |
| Markdown lint invocation | npx markdownlint-cli2, no new devDependency (RQ-04) |
| Spec inventory 001–037 | Mapped to views; known-gaps for orphans (RQ-05) |
| Pre-existing docs | Keep in place, front-matter update (RQ-06) |
| ADR canonical location | docs/decisions/ canonical; adr/README.md nav-index only (RQ-07) |
| FR-016 Foundry label | Mechanism-zone label, zero active non-AU entries (RQ-08) |
| CI job placement | Job in ci.yml, no path filter (RQ-09) |
| WCAG diagram | Text-only, no diagram pair (RQ-10) |
| Bicep dep graph | Deferred, known-gaps entry (RQ-11) |

---

## Amendment 1 Notes (2026-05-11)

One-line decision + rationale per new FR, per spec clarification session 2026-05-11 (Amendment 1).

| FR | Decision | Rationale |
|----|----------|-----------|
| **FR-024** — PPRR phase-overlay diagram (OPS-03) | Author OPS-03 in `operational/` using constitution §PPRR Lifecycle as the source; no new CI gate required | All existing `docs-arch` checks (pair, hash, lint, spec-ref) cover OPS-03 mechanically; content correctness (agent × phase alignment) verified by human reviewer citing constitution §PPRR Lifecycle in the PR description |
| **FR-025** — Test pyramid diagram (QUAL-01, corrected to 5-tier) | Author QUAL-01 in new `quality/` subdir with unit as base tier (~159 files); five tiers: unit → contract → integration → simulation → e2e; pytest primary for all except web e2e (Playwright) | FR-025 originally stated "four-tier" omitting unit — the largest tier (159 files) and constitutionally mandated (§Quality Gates "unit tests before merge"); corrected in Amendment 1 Q3; a pyramid without unit as base would be topologically incorrect and contradict the constitution |
| **FR-026** — Ops dashboard user-journey diagram (EXP-01) | Author EXP-01 in `accessibility/` tracing one canonical incident-active user journey; perception/comprehension/action callouts; success-criteria → component traceability | Technical-Experience persona = accessibility + WCAG + end-user interaction patterns (spec clarification Q1 Session 2026-05-11); `accessibility/` already holds wcag-coverage.md; no separate `experience/` subdir warranted for a single diagram (minimum viable directory surface principle) |
