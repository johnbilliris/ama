# Quickstart — Capstone Evidence Pack

**Spec**: [`spec.md`](./spec.md) · **Plan**: [`plan.md`](./plan.md) · **Date**: 2026-05-11

This quickstart walks an operator (Risk Manager, Resilience Planner, RAI Officer, or Capstone Reviewer) through the four most common workflows on the Evidence Pack:

1. **Add a new row to an artefact** (e.g., a new risk row).
2. **Publish an artefact** through the CI publication-gate.
3. **Obtain auditor sign-off** when `manual_row_ratio > 0.5`.
4. **Verify the executive page** renders against the read-only API.

All workflows respect the constitution's append-only audit + AU-residency + human-in-the-loop constraints (NN-1, NN-2). Published rows are **immutable**; corrections are made via dated revision rows that preserve the prior value.

---

## Prerequisites

- Local checkout of `johnbilliris/ama` on a working branch (typically `037-capstone-evidence-pack` or a child branch).
- `pnpm install --frozen-lockfile` and `uv sync` completed.
- Schema dry-run tooling: `python -m evidence_pack_gate --help` returns non-zero exit code on any failed check.

---

## Workflow 1 — Add a new risk row

The Systematic Risk Register lives at `docs/risk-register/`. Each row is a `<RISK-ID>.md` Markdown file *plus* a corresponding entry in `docs/risk-register/risk-register.json` (the JSON sidecar that the schema-check validates).

1. **Create the Markdown row**: `docs/risk-register/RISK-PLATFORM-002.md`. Include front-matter that mirrors the JSON entry one-for-one (id, title, category, likelihood, consequence, treatment, owner, residual scores, next_review_date, back_citations).

2. **Append the JSON entry** to `docs/risk-register/risk-register.json`'s `rows[]` array. Set `provenance.tag` to `automated` if the row is sourced from a tracked telemetry sink, otherwise `manual` with `owner` (named role), `review_cadence`, and `automation_target` (FR-037).

3. **Recompute metadata locally**:

   ```pwsh
   python -m evidence_pack_gate recompute --artefact docs/risk-register/risk-register.json
   ```

   The tool rewrites the `metadata.manual_row_count`, `metadata.total_row_count`, and `metadata.manual_row_ratio` fields in place.

4. **Validate locally**:

   ```pwsh
   python -m evidence_pack_gate validate --artefact docs/risk-register/risk-register.json
   ```

   The output names the schema (`packages/schemas/spec_037/risk-register.schema.json`), confirms link-check, and prints the `manual_row_ratio` against the FR-038 cap.

5. **Open a PR**. The CI job `evidence-pack-publication-gate` runs all four checks (schema → link → cap → sign-off) and blocks merge on any failure.

---

## Workflow 2 — Publish an artefact

Publication happens automatically on merge to `main` if the `evidence-pack-publication-gate` job passed. The publisher service (`apps/api/app/services/governance/evidence_pack_publisher.py`) does the following:

1. Reads the in-repo JSON sidecar.
2. Computes a `publication_id` (UUID v4) and `published_at_utc`.
3. Writes the artefact + metadata to the Cosmos `evidence_pack_artefact_cache` container (partition key `/artefact_id`).
4. Writes the same artefact as an immutable Blob snapshot under `evidence-pack-archive/<artefact_id>/<publication_id>.json`.
5. Appends an audit row to the existing Cosmos audit-timeline container via the existing `audit_writer` pattern (FR-005).
6. Emits two App Insights custom metrics: `evidence_pack.publication.duration_seconds` and `evidence_pack.manual_row_ratio` (dimensions `{ artefact_id, publication_id, environment }`).

The new executive page at `https://app-ama-zo6bb5.azurewebsites.net/governance/executive` reads from the Cosmos cache for sub-200 ms p95 latency.

---

## Workflow 3 — Obtain auditor sign-off (FR-038 override)

If an artefact's `manual_row_ratio` exceeds 0.5 (e.g., the RAI Register at v1, where most posture rows are inherently judgement-based), the publication gate **fails** unless a complete `auditor_signoff` block is present.

1. **Identify the named auditor** with the role appropriate to the artefact (e.g., Compliance Auditor for the RAI Register, Risk Manager for the Risk Register).
2. **Cite the framework basis** that authorises the override — e.g., `ISO/IEC 23894 §7.4 risk evaluation under uncertainty`, or `AIDR Lessons Management 2020 §3.2 expert judgement`.
3. **Add the block** to the artefact's `metadata.auditor_signoff`:

   ```json
   {
     "name": "Jane Doe",
     "role": "Compliance Auditor",
     "signoff_date_utc": "2026-05-15T03:00:00Z",
     "basis": "ISO/IEC 23894 §7.4 risk evaluation under uncertainty"
   }
   ```

4. **Re-run the local gate** (`python -m evidence_pack_gate validate ...`) and re-open the PR. The auditor sign-off is itself audit-logged via the audit-writer when the publish runs (NN-1 human-in-the-loop preserved).

If `manual_row_ratio` later drops to ≤ 0.5, the `auditor_signoff` block MUST be removed from `metadata` (the schema rejects it when not required, preventing stale-override claims).

---

## Workflow 4 — Verify the executive page

1. **Local web preview**: `pnpm --filter @ama/web dev`. Open `http://localhost:3000/governance/executive`.
2. **Sign in** with an Entra account holding any of the spec-035 AppRoles (the page is read-only and all 10 AIIMS AppRoles + system-administrator can read).
3. **Confirm the manual-row ratio strip** at the top of the page renders five values (one per artefact) inside a `aria-live="polite"` region. Toggle a screen reader to hear updates announced.
4. **Confirm the KPI ladder** for each capstone criterion shows ≥ 1 leading + ≥ 1 lagging KPI with owner, target, refresh cadence, and source-of-truth (FR-019/FR-020).
5. **Simulate stale telemetry** by setting the API env var `EVIDENCE_PACK_TELEMETRY_FORCE_STALE=true` and refreshing — the surface MUST display "stale as of <timestamp>" rather than blank or stale-but-fresh-looking values (FR-023).
6. **Run the Playwright smoke**:

   ```pwsh
   pnpm --filter @ama/e2e exec playwright test tests/e2e/web-coverage/governance-executive.spec.ts
   ```

   This includes axe-core (NN-3 WCAG 2.2 AA), keyboard-only navigation, and the live-region announcement assertion.

---

## Read-only API surface

The four endpoints under `/api/governance/evidence-pack/` are documented in [`contracts/openapi.evidence-pack.yaml`](./contracts/openapi.evidence-pack.yaml). All endpoints:

- Require an Entra bearer token (existing JWT/AppRole middleware).
- Return `application/json` matching the artefact envelope schema.
- Return RFC 7807 `application/problem+json` on error.
- Append a tenant-scoped read row to the audit-timeline (FR-005).

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/governance/evidence-pack/artefacts` | List the five artefacts + each artefact's latest `publication_id` and `manual_row_ratio` |
| GET | `/api/governance/evidence-pack/artefacts/{artefact_id}` | Latest published version of an artefact |
| GET | `/api/governance/evidence-pack/artefacts/{artefact_id}/publications/{publication_id}` | A specific historical publication (Blob-backed) |
| GET | `/api/governance/evidence-pack/health` | Gate status + last successful publish per artefact |

---

## Failure modes & recovery

| Symptom | Likely cause | Recovery |
|---|---|---|
| CI gate fails on schema check | A new row omits a required field | Add the field per [`data-model.md`](./data-model.md); re-PR |
| CI gate fails on link check | A back-citation points to a renamed/deleted file | Update the citation; if the target is genuinely gone, file an issue and add `automation_target: "follow-up"` to the row |
| CI gate fails on cap check | `manual_row_ratio > 0.5` and no `auditor_signoff` | Either reduce manual rows or follow Workflow 3 |
| Executive page shows "stale as of …" | Cosmos cache or App Insights unreachable | Page is in graceful-degradation mode (NN-5, FR-023); operator action is to investigate the upstream sink, not the page |
| Cosmos audit-timeline append fails | Throughput limit or transient | The publisher retries with exponential backoff; if it ultimately fails, the publish itself is rolled back (no partial state) |

---

## Where to next

- **`/speckit.tasks`** to generate the dependency-ordered task list from this plan.
- **`/speckit.checklist`** to cut a per-FR review checklist (already noted as ready in spec § Open Clarifications).
