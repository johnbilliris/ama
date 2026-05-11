# ADR-037-03 — Manual-evidence cap (per-artefact ≤ 0.5 with auditor sign-off override)

**Date**: 2026-05-11
**Status**: Accepted
**Spec**: [`specs/037-capstone-evidence-pack/`](../../../specs/037-capstone-evidence-pack/) — PD-037-03, FR-038, SC-011

## Context

Spec-037's Clarification 4 asked: when an artefact requires data not yet produced by automated telemetry sinks (FR-037 manual stub rows), how do we prevent the pack from degenerating into a free-text "trust me" artefact while not disabling the inherently judgement-heavy RAI Register?

Three options were considered:
1. No cap — accept any ratio
2. Fleet-wide cap (e.g., median across artefacts ≤ 0.5)
3. Per-artefact cap with named-auditor sign-off override

## Decision

**Per-artefact cap at `manual_row_ratio ≤ 0.5` for v1**. Artefacts exceeding the cap MUST carry a complete `auditor_signoff` block in metadata: `{ name, role, signoff_date_utc, basis }` where `basis` cites the AIDR / ISO / NIST framework reference authorising the override. The CI publication gate (`evidence-pack-publication-gate`) enforces this — artefacts violating both conditions fail the build.

## Rationale

- Matches the `Validated` / `Deferred` / `Unresolved` precedent in `specs/shared/capstone-metric-trace.md`.
- Preserves NN-1 human-in-the-loop: an over-cap publish requires a named human to take responsibility.
- Does not disable the RAI Register, which is inherently judgement-heavy at v1 (most posture rows derive from human review of spec 030's evaluation outputs, not from real-time telemetry).
- Applies the AIDR M&E Framework + ISO/IEC 42001 §6.1 risk-acceptance pattern.

## Alternatives Considered

- **No cap** — rejected: degenerates the pack to a free-text artefact and breaks SC-002/SC-011.
- **Fleet-wide cap** — rejected: hides per-artefact deficiencies (a low-ratio Risk Register would mask a high-ratio RAI Register).
- **Hard cap with no override** — rejected: blocks RAI publish at v1 since most rows are inherently judgement-based.

## Consequences

- The `manual_row_ratio` is recomputed server-side at publish time (RES-05), emitted as App Insights custom metric `evidence_pack.manual_row_ratio`, and re-validated by the gate — clients never trust the declared value.
- Sign-off basis strings are scanned for ISO/AIDR/NIST references during gate runs (≥ 8 chars enforced by schema; PR review enforces semantic alignment).
- Reads of an over-cap artefact are themselves audit-logged (T035, NN-2-clean payload).
