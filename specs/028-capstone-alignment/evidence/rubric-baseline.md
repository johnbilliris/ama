# AMA Rubric — Pre-feature Baseline (T002)

**Rubric source**: `C:\code\ama\AMA_Rubric_Asia.md`
**Snapshot taken**: 2026-04-25T00:40:13+10:00
**Grader**: `ama-rubric-grader` skill — structural assessment derived from `spec_inventory` SQL table populated in T001.
**Run ID**: `028-T002-baseline-2026-04-25`
**Frozen reference for**: SC-009 composite gate (Δmean across the 5 target criteria ≥ +1 AND per-criterion Δ ≥ 0).

The five target criteria below correspond to the rubric rows tied to Assumptions / Requirements / Personas / Hypotheses / Scope. Scores are integer 1..5 (1 = absent, 5 = exemplary).

## Criterion 1 — Define assumptions

**Score**: 2 / 5

**Rationale**: 17 of 27 spec.md files contain a `## Assumptions` section header (count from inventory). However, the contents are inconsistent: most are bullet lists without explicit ASM-NNN identifiers, no `[RISK]`/`[DECISION]` tagging taxonomy from spec 027, and no `linked_gaps:` cross-references. 10 specs have no Assumptions section at all (`001`, `003`, `004`, `005`, `006`, `007`, `009`, `011`, `012`, `024`, `027`). The capstone tension between AU-only data residency (constitution NON-NEGOTIABLE #2) and capstone Asia framing is nowhere captured as a `[RISK]` assumption. Baseline grade band: **Developing**.

## Criterion 2 — Expand requirements

**Score**: 3 / 5

**Rationale**: All 27 specs follow the speckit FR/SC convention; quality is heterogeneous. The Asia-framed capstone success metrics (`LIVES_SAVED`, `RESPONSE_SPEED`, `EVAC_LEAD_TIME`, `LOGISTICS_EFFICIENCY`, `ECONOMIC_LOSS_REDUCTION`) are not all surfaced as SCs across the portfolio: spec 001 carries a partial set; spec 015 (performance benchmarks) does not yet map every metric to a benchmark scenario. Per-country PII regimes (PH RA 10173, JP APPI, BD ICT/DPA 2023) are not enumerated as deferred requirements in spec 005. Multilingual language-pack requirement (FR-006) is implicit in spec 008 but not encoded as a deferred FR. Baseline grade band: **Developing**.

## Criterion 3 — Identify personas

**Score**: 1 / 5

**Rationale**: Only **1 of 27** spec.md files (`001-disaster-response-hub`) contains a `## Personas` section. The repo carries a persona-profile schema (`specs/027-spec-hardening/contracts/persona-profile.md`) and an actor-github-agents framework (spec 004) but no spec under `specs/NNN-*/spec.md` wires personas to spec-027 taxonomy via cross-references. Non-AU personas (PH/JP/BD operators, citizens, regulators) are entirely absent. Baseline grade band: **Absent**.

## Criterion 4 — Form hypotheses

**Score**: 1 / 5

**Rationale**: Only **1 of 27** spec.md files (`001-disaster-response-hub`) contains a `## Hypotheses` section. No spec carries the FR-018 statement format (`If <condition> then <observable>`) with linked falsification criteria and evidence stubs. Zero `evidence/HYP-*.md` stubs exist anywhere in the portfolio. The five capstone metrics × four cohorts (AU-v1, PH, JP, BD) traceability table is absent — no `specs/shared/capstone-metric-trace.md` file. Baseline grade band: **Absent**.

## Criterion 5 — Shape scope boundaries

**Score**: 2 / 5

**Rationale**: Only **3 of 27** specs carry a `## Out of Scope` (or hyphenated `## Out-of-Scope`) section: `013-root-readme`, `014-azure-openai-integration`, `015-performance-benchmarks`, `024-simulation-control-chat`, plus `028-capstone-alignment` itself (the feature spec). Most agent specs (008..012) and dashboard specs (020..023) defer no explicit capstone-country scope. Cross-spec overlaps (spec 006 FR-024 vs spec 008; spec 018 escalation timeout vs spec 008; recovery across 001/018/011) are silent — no `supersedes` / `defers-to` / `authoritative for` rules exist anywhere in the portfolio. Meta vs capstone-critical-path partitioning is not surfaced. Baseline grade band: **Developing**.

## Composite baseline

| Criterion | Baseline score |
| --- | --- |
| 1. Define assumptions | 2 |
| 2. Expand requirements | 3 |
| 3. Identify personas | 1 |
| 4. Form hypotheses | 1 |
| 5. Shape scope boundaries | 2 |
| **Mean** | **1.8** |

**Composite band**: Developing.

**SC-009 gate target (post-feature)**:

- Δmean ≥ +1 ⇒ post-feature mean must be ≥ 2.8.
- Per-criterion Δ ≥ 0 ⇒ no criterion may regress.

## Notes

- This baseline is the **frozen reference** for SC-009; it MUST NOT be re-computed retroactively. Post-feature snapshot at `evidence/rubric-post-feature.md` is the comparator (T063).
- The structural counts are reproducible: re-run the inventory PowerShell snippet in T001 against the pre-feature commit (HEAD before spec 028's authoring tasks land) to verify.
