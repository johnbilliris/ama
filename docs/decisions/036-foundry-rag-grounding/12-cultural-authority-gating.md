# ADR 12 — Cultural-Authority Gating (Constitution VI-C)

**FR**: FR-RAG-CA-01, FR-RAG-CA-02, FR-RAG-CA-03, FR-RAG-CA-04, FR-RAG-CA-05
**Cluster**: A2 — Cultural Authority (Constitution VI-C)
**Persona memo citation**: `personas-input/r3-sectors-territories.md` §"Indigenous-liaison and cultural-authority"; `personas-input/r3-sectors-commonwealth.md` §"NEMA + AFAC + AIATSIS sign-off"
**Approver**: HUMAN-IN-LOOP — NEMA + AFAC + ≥3 Indigenous community representatives (per FR-RAG-CA-05)
**Date**: 2026-05-08
**Status**: Stub — body authored in `/speckit.implement` (Phase F-A2 task)

## Stub placeholder

> Detailed rationale to land in implement-phase task `T-A2-ADR12` (planned). This stub exists per spec 036 Assumption **A11** so that `tasks.md` and downstream FR cross-references can resolve to a real path during `/speckit.plan` review without 404s. Body authoring follows the Phase E ADR convention (T118–T126) and is gated by FR-RAG-CA-05 governance sign-off.

## Skeleton (to be filled in `/speckit.implement`)

- **Context** — Constitution VI-C non-negotiable; Sacred Site protocols, Indigenous-language corpus, ALT/APY consent gates; `culturalAuthorityRegistry` Cosmos container schema (`{operator_id, land_council_id, granted_at, expires_at, granted_by_authority, scope, signature, revocation_reason}`).
- **Decision** — Post-retrieval, in-process gate inside `RetrievalService.retrieve()` (between AI Search round-trip and Foundry inference), per Pass 2 Q-P2-02. Gate is `feature.cultural_authority_gate.enabled` Locked-on in prod (Pass 2 Q-P2-08, A12 class taxonomy); disable permitted only for `environment=test` chaos runs and OPA-blocked at flag-flip time.
- **Fail-closed semantics** — Pass 1 Q-P1-01: when registry unreachable, suppress Sacred Site / Indigenous protocol matches and emit `cultural_authority_registry_unavailable` audit event; non-protected chunks remain retrievable so the agent does not silence (Constitution Principle I).
- **Provisioning** — Cosmos container created empty by amend-loop deploy; populated HUMAN-IN-LOOP per FR-RAG-CA-05 before production go-live; SC-014 verifies sign-offs at CD time.
- **Consequences** — Preserves Constitution VI-C enforcement at the canonical retrieval seam; preserves FR-RAG-IDX-08 single-shared-index economics; cost is one additional in-process per-call gate (estimated ≤5ms p95 on cold registry-cache miss, ~100µs warm).

## Cross-references

- Cluster A2 in `specs/036-foundry-rag-grounding/spec.md` Session 3.
- Pass 1 Q-P1-01, Pass 2 Q-P2-01/Q-P2-02/Q-P2-08 in `specs/036-foundry-rag-grounding/spec.md` Sessions 4 + 5.
- Schema in `specs/036-foundry-rag-grounding/contracts/cultural-authority-registry.schema.json`.
- Plan phase `F-A2` in `specs/036-foundry-rag-grounding/plan.md`.
