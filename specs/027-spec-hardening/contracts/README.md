# Contracts — Capstone Specification Hardening

**Feature**: 027-spec-hardening

This feature produces no network contracts. The contracts here are **markdown row / file templates** that downstream tasks will copy into the target artefacts. Each template maps 1:1 to an entity in `data-model.md` and satisfies a named functional requirement.

| File | Entity | Satisfies | Target artefact |
| --- | --- | --- | --- |
| [assumption-row.md](./assumption-row.md) | Assumption (E-2) | FR-001 .. FR-003, FR-034 | `specs/001-disaster-response-hub/spec.md § Assumptions` |
| [nfr-row.md](./nfr-row.md) | NFR (E-3) | FR-004 .. FR-013, FR-035 | `specs/001-disaster-response-hub/spec.md § NFRs` |
| [persona-profile.md](./persona-profile.md) | Persona (E-4) | FR-014 .. FR-017 | `specs/001-disaster-response-hub/personas/<persona-id>.md` |
| [hypothesis-row.md](./hypothesis-row.md) | Hypothesis (E-5) | FR-018 .. FR-021 | `specs/001-disaster-response-hub/spec.md § Hypotheses` |
| [evidence-pack-stub.md](./evidence-pack-stub.md) | Evidence Pack (E-6) | FR-020, Clarification 9 | `specs/<owning-feature>/evidence/<HYP-ID>.md` |
| [open-delta-row.md](./open-delta-row.md) | Open Delta (E-9) | FR-032, Clarification 5 | `specs/001-disaster-response-hub/spec.md § Open Deltas` |
| [traceability-row.md](./traceability-row.md) | Traceability Link (E-10) | FR-031, Clarification 10 | `specs/027-spec-hardening/spec.md § Traceability Table` |
| [gap-id-register-row.md](./gap-id-register-row.md) | Gap (E-1) | FR-036, Clarification 8 | `specs/shared/gap-id-register.md` |
| [codeowners-entry.md](./codeowners-entry.md) | — | FR-034, Clarification 6 | `.github/CODEOWNERS` |
