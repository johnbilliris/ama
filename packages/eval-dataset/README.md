# ama-eval-dataset

Authoring + tooling for the AMA disaster-response evaluation dataset.

## Layout

- `cases/` — committed case JSON files, organised by hazard (legacy authoring path)
- `data/dataset-disaster-core-{version}/` — generated `cases.jsonl` + `manifest.json` per version
- `generation/` — synthetic generator, distribution targets, validators, sanitiser
- `manifests/` — generated manifests per published version
- `src/ama_eval_dataset/` — Python package
  - `distribution.py` — distribution targets + `validate_distribution()`
  - `templates.py` — multilingual prompt templates (≥338) across 13 hazards × 5 languages + injection variants
  - `generator.py` — deterministic, seeded `generate_corpus()`
  - `manifest.py` — builds `EvaluationDatasetVersion` with sha256 content hash
  - `cli.py` / `__main__.py` — `python -m ama_eval_dataset {generate|validate}`

## Regenerating the corpus

```bash
python -m ama_eval_dataset generate \
  --seed 20251121 \
  --size 5000 \
  --output packages/eval-dataset/data/dataset-disaster-core-1.0.0/
```

The generator is deterministic: the same `--seed` always produces the same `cases.jsonl`
and the same `contentHash` in `manifest.json`. The default v1.0.0 seed is `20251121`.

## Changing the seed

Pick a new integer seed when re-generating a fresh corpus (e.g. for v2.0.0):

```bash
python -m ama_eval_dataset generate --seed 20260101 --size 5000 \
  --output packages/eval-dataset/data/dataset-disaster-core-2.0.0/
```

Per **FR-013** datasets are immutable — never overwrite a published version. Bump the
semver and supersede.

## Validating a corpus

```bash
python -m ama_eval_dataset validate \
  --input packages/eval-dataset/data/dataset-disaster-core-1.0.0/cases.jsonl
```

The validator round-trips every line through `EvaluationCase`, enforcing:

- semver version, BCP-47 language, ISO 3166-2 jurisdictionTags
- `expectedAction='refuse'` ⇒ `referToAuthority` must be set
- `hazardTags` of `fatality-report`/`remains-recovery` ⇒ at least one of
  `graphic-fatality`/`human-remains`/`mass-casualty` sensitivity label
- `retrievalScope=true` ⇒ `retrievedContext` non-empty
- caseId uniqueness across the corpus

## Approval workflow (4-eyes, FR-011 / FR-013)

The corpus follows a strict 4-eyes approval chain before publication:

1. **Author drafts.** A safety engineer runs `generate` (or hand-edits cases under `cases/`)
   with `approvalState=draft`. PR opens against a `dataset/<version>` branch.
2. **Reviewer reviews.** CODEOWNERS routes the PR to `@ama/safety-reviewers`.
   Reviewer transitions individual case `approvalState` to `in-review`,
   verifies distributions, sensitivity coverage and refusal correctness, then
   sets `approvalState=approved` and signs the `approvalChain` entry.
3. **Approval.** A second `@ama/safety-reviewers` member approves the PR.
4. **Publish.** On merge, `.github/workflows/eval-publish-dataset.yml`
   validates the corpus, hashes it, uploads `cases.jsonl` + `manifest.json` to the
   immutable Blob container, then `POST /api/eval/datasets/disaster-response-core/versions`
   creates the published `EvaluationDatasetVersion` record.

### Immutability (FR-013)

Once a dataset version is `state=published`, **it is never deleted or modified**.
Mistakes are corrected by publishing a superseding version (`v1.0.1`, `v2.0.0`, …)
and recording the supersession via the audit chain. The Blob container has an
immutability policy that physically prevents overwrite during the retention window.

## Distribution targets (research D8 / SC-005)

See `distribution.py` for the canonical targets:

- 13 hazards summing to 1.0
- 5 languages (en-AU 60%, en-NZ 10%, vi-VN 10%, zh-Hans-CN 10%, ar-SA 10%)
- 5 expected actions (answer 35%, refuse 25%, escalate 20%, clarify 15%, redirect 5%)
- 4 severity bands (low 15%, medium 30%, high 35%, critical 20%)
- Sensitivity floors: graphic-fatality ≥5%, human-remains ≥5%, prompt-injection ≥8%, crisis-distress ≥4%

## Testing

```bash
cd packages/eval-dataset
python -m pytest tests/ -q
python -m ruff check .
```
