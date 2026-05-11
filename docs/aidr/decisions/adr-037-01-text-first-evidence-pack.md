# ADR-037-01 — Text-first evidence pack (Markdown + JSON sidecar)

**Date**: 2026-05-11
**Status**: Accepted
**Spec**: [`specs/037-capstone-evidence-pack/`](../../../specs/037-capstone-evidence-pack/) — PD-037-01

## Context

Spec-037 publishes five durable evidence artefacts (Risk Register, Adoption Roadmap, Executive KPI Surface, Responsible AI Register, Feature-Value Ledger + Tradeoff Log). The team needed a representation that:

- is auditor-friendly (regulators read Markdown, not OpenTelemetry traces)
- is machine-validatable (`evidence-pack-publication-gate` CI job)
- preserves provenance via git history (NN-2)
- requires no net-new infrastructure (PD-037-06, SC-009)

## Decision

Each artefact is a **Markdown + JSON sidecar pair** committed under `docs/` (and `specs/shared/` for the Feature-Value Ledger). The JSON sidecar is validated against a JSON Schema (draft 2020-12) under `packages/schemas/spec_037/`. Pydantic v2 models under `packages/domain/src/domain/models/evidence_pack/` mirror the schemas for runtime use by the FastAPI surface.

## Rationale

- Text-first matches the "evidence in git" principle inherited from spec-035 + spec-036.
- The JSON sidecar enables the executive page (`apps/web/src/app/governance/executive/`) and the four publication-gate checks without parsing Markdown.
- JSON Schema 2020-12 is the same dialect used by `signal-envelope.schema.v2.json`, `spec_035/`, and `spec_036/` — no tooling change.

## Alternatives Considered

- **OpenAPI as the primary contract** — rejected: artefacts themselves are the contract; OpenAPI for the read API is a thin layer on top.
- **YAML-only artefacts** — rejected: harder to validate at scale, breaks parity with spec-035/036 layout.
- **Bespoke per-artefact schema flavours** — rejected: increases drift surface; mirroring the established `spec_03X/` layout costs nothing.

## Consequences

- The Tradeoff Log (T060) lists this ADR with `synthesised_tension: "none"`.
- Any sixth evidence artefact in a future spec MUST follow this same pattern (extend `_DEFAULT_ARTEFACT_ROOTS` in `scripts/evidence_pack_gate/gate.py`).
