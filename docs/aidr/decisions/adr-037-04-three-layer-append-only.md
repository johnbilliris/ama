# ADR-037-04 — Three-layer append-only audit (git + Cosmos + Blob immutability)

**Date**: 2026-05-11
**Status**: Accepted
**Spec**: [`specs/037-capstone-evidence-pack/`](../../../specs/037-capstone-evidence-pack/) — PD-037-04, FR-005

## Context

Spec-037 artefacts are intended to be regulator-facing evidence. Auditors need confidence that a published row cannot be silently altered. Git history alone is mutable by force-push and rebase, so a single-layer "evidence in git" guarantee is insufficient.

## Decision

Every published artefact is appended to **three independent append-only layers** at publication time:

1. **Git history** — the in-repo Markdown + JSON pair (PR-merged commit on `main`).
2. **Cosmos audit-timeline** — an append-only row in the existing audit-timeline container in `cosmos-ama-zo6bb5/disaster-hub` (NN-2-clean payload: actor `oid`, no PII).
3. **Blob immutability policy snapshot** — a per-publish JSON snapshot tagged with `publication_id` and `manual_row_ratio` in the new `evidence-pack-archive` container in the existing storage account in `rg-ama`. The container has a time-based immutability policy (`spec037ArchiveRetentionDays`, default 7 years) with `allowProtectedAppendWrites: true`.

Reads of an artefact whose `manual_row_ratio > 0.5` also append to layer 2.

## Rationale

- A single layer (git) is force-push-mutable; three layers give tamper-evidence auditors can verify independently.
- Cosmos audit-timeline is the established AMA pattern (`apps/api/app/services/simulation/audit_writer.py`); reuse honours QG-1 and PD-037-06.
- Blob immutability matches the spec-030 audit-archive precedent (7-year time-based retention).
- AU-East residency for all three layers honours NN-1.

## Alternatives Considered

- **Git only** — rejected: force-push-mutable; auditors cannot verify a snapshot independent of repo state.
- **Cosmos only** — rejected: Cosmos backups can be restored; immutability is policy- not storage-enforced.
- **Blob only** — rejected: loses developer-facing edit-and-PR workflow that the spec depends on.
- **Four layers (add Key Vault signing certificate)** — deferred to a future spec; FR-029 export does not currently require cryptographic provenance beyond what Blob immutability provides.

## Consequences

- Two child resources are added to `infra/main.bicep` (1 Cosmos container + 1 Blob container with immutability policy). Zero net-new top-level resources (PD-037-06, SC-009).
- `evidence_pack.publication.duration_seconds` is the SLO for the three-layer publish.
- Corrections happen via dated revision rows tagged `revises: <prior_publication_id>`; there is no `Unpublish` state (data-model.md § State machine).
