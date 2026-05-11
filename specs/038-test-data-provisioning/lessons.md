# Spec 038 — Lessons Learned

**Author:** spec-038 implementation pass (Phases 1–7)
**Date:** 2026-05-11
**Branch:** `038-test-data-provisioning`

---

## What worked

- **Two-Path Rule as a primary design constraint.** Treating "static
  reference data goes through `seed_loader`; live-stream data lives only
  under `apps/api/app/services/simulation/`" as a non-negotiable design
  rule (rather than a guideline) made every subsequent decision easy.
  Manifest categories, import-linter contracts, simulator-isolation
  lint, and the manifest path↔category mapping all fell out of it
  naturally, and the Phase 7 composite `test_two_path_rule_full.py`
  proves all three layers stay green together.

- **Manifest-as-single-source-of-truth.** A single canonical
  `docs/test-data/manifest.json` validated by JSON Schema turned every
  ad-hoc question ("which personas does X serve?", "which entries are
  PII-bearing?") into a one-line `jq` query. The auto-rendered
  `MANIFEST.md` removes the staleness risk.

- **Canonical NDJSON + SHA-256 sidecar.** The Phase 5 decision (CL-4) to
  define "byte-identical" precisely as "same canonical NDJSON bytes,
  verified by SHA-256 stream digest" means we can lock fixtures with a
  single sidecar file and detect drift with a single test
  (`test_replay_digest_sidecar_regression.py`, Phase 7). 21 fixtures,
  one regression gate.

- **Persona rosters as code.** Encoding the 68-persona inventory as
  `PERSONA_ROSTERS: dict[str, list[str]]` in
  `tools/lint/build_test_data_manifest.py` (rather than a YAML file)
  means it can be imported by both the manifest builder and the
  coverage report — single source of truth, type-checked by import.

- **TDD on lints.** Writing `test_simulator_isolation_lint.py`,
  `test_manifest_lint_detects_missing_entry.py`, etc. *before* the
  lints themselves caught two false-negative classes (string match
  inside docstrings; symlinked path normalisation) that would otherwise
  have shipped silently.

---

## What surprised us

- **`simulator_not_imported_by_production` masking bug.** During
  Phase 5, the import-linter contract reported KEPT even though
  production code was importing simulator modules. Root cause: an
  outdated `forbidden_modules` glob in `pyproject.toml` that didn't
  cover the new `apps/api/app/services/simulation/feeds/` subpackage.
  The Phase 7 composite test (`test_two_path_rule_full.py`) now asserts
  the contract is KEPT *and* the string-grep lint is clean — defence in
  depth so a single misconfiguration cannot mask a violation.

- **Windows cp1252 subprocess output.** The `lint-imports` CLI emits
  Unicode box-drawing characters that PowerShell's default cp1252 codec
  cannot decode, causing `UnicodeDecodeError` in pytest's reader thread.
  Fix: every Phase 7 subprocess call uses
  `encoding="utf-8", errors="replace"`. Worth adding to the project's
  test conventions.

- **Demo scenarios needed explicit `seed=42`.** The simulator CLI
  defaults to `seed=0` (with a `UserWarning`), but the committed demo
  fixtures were generated with `seed=42`. Phase 7 regression test
  pins this explicitly. A future improvement: bake the seed into each
  scenario's manifest entry so `--check` can read it back without
  CLI guesswork.

- **Manifest entry count growth.** Started Phase 1 expecting ~60
  manifest entries; landed on 134 by Phase 6. The auto-walk + per-file
  classification approach scales well, but `MANIFEST.md` (rendered) is
  now ~140 KB and arguably needs collapsing per category for
  reviewability.

- **Indigenous denylist as test-data artefact.** Initially the
  `indigenous_denylist.txt` was treated as "tooling" and excluded from
  the manifest. Phase 4 reclassified it as a `category=mock` entry
  (it *is* a test artefact — a denylist that test data is checked
  against). This meant the file itself carries `cultural_review_required`
  and an SPDX licence, which is the right model.

---

## Pre-existing issues observed (NOT spec-038 scope)

- `lint-imports` currently reports the `seed_not_imported_by_runtime`
  contract as KEPT, but a pre-existing pattern in `apps/agents/*` uses
  `from packages.domain.src.domain.seed import …` for **type-only**
  imports under `TYPE_CHECKING`. The contract correctly tolerates these
  (they don't run at runtime) but a future cleanup could move the
  shared types into a dedicated `packages/domain/types/` module so the
  intent is explicit. Tracked as a follow-up; not blocking.

- `MANIFEST.md` rendering uses GitHub-flavoured Markdown tables. On
  some viewers (notably PyPI metadata renderers) the wide tables wrap
  ugly. Consider a `--render-format=html` option for downstream
  embedding. Not urgent.

- `scripts/generators/*.py` use a mix of `print(record)` and structured
  output. Consistent JSON-Lines stdout would simplify chained
  generators-into-loaders. Tracked separately.

---

## Post-merge follow-ups

| # | Item | Owner / next step |
|---|---|---|
| 1 | Bake per-scenario `seed` into manifest so `replay --check` can self-discover. | Spec 039 candidate. |
| 2 | Add `MANIFEST.md` per-category sub-files for reviewability. | Doc-only; queue for next docs sprint. |
| 3 | Move shared seed types to `packages/domain/types/` to remove TYPE_CHECKING-only imports from agents. | Refactor PR; non-blocking. |
| 4 | Generators: standardise on JSON-Lines stdout with `--out -` convention. | Devex backlog. |
| 5 | Add a CI step that runs `persona_coverage_report.py --strict` on every PR (currently the underlying test runs, but the human-readable report only runs on demand). | Trivial CI addition; defer to next CI hardening pass. |
| 6 | Consider extracting the Two-Path Rule composite test into a reusable lint that other specs can depend on. | After Spec 039 ships. |

---

## Numbers at a glance

- **Phases:** 7
- **Tasks:** 117 planned (T001–T167 with gaps); ~117 completed
- **Tests:** 255 contract+unit (`tests/{contract,unit}/spec038`) + 64+ integration touching spec-038 surfaces
- **Lints:** 5 in `tools/lint/` + import-linter (5 contracts) + ruff
- **Manifest:** 134 entries · 5 categories · 68/68 personas · 8/8 domain groups
- **Replay fixtures:** 21 (13 simulator-feed + 8 demo)
- **Multilingual locales:** 6 active + 2 Indigenous placeholders
