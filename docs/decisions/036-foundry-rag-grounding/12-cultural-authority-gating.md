# ADR 12 — Cultural-Authority Gating (Constitution VI-C)

**FR**: FR-RAG-CA-01, FR-RAG-CA-02, FR-RAG-CA-03, FR-RAG-CA-04, FR-RAG-CA-05
**Cluster**: A2 — Cultural Authority (Constitution VI-C)
**Persona memo citation**: `personas-input/r3-sectors-territories.md` §"Indigenous-liaison and cultural-authority"; `personas-input/r3-sectors-commonwealth.md` §"NEMA + AFAC + AIATSIS sign-off"
**Approver**: HUMAN-IN-LOOP — NEMA + AFAC + ≥3 Indigenous community representatives (per FR-RAG-CA-05)
**Date**: 2026-05-08
**Status**: Accepted — body authored 2026-05-15 (Phase F-A2)

## Context

Constitution Principle VI-C is a **non-negotiable**: Sacred Site protocols, Indigenous-language corpora, and ALT/APY consent gates must never be surfaced to operators who lack a current, signed cultural-authority delegation. Spec 036 retrieves these chunks from the same shared AI Search index that serves all other handbook content (FR-RAG-IDX-08), so the gate cannot be enforced at the index layer without sharding the corpus and breaking the single-index economics chosen in ADR 11.

The persona memos (`personas-input/r3-sectors-territories.md` § "Indigenous-liaison and cultural-authority"; `personas-input/r3-sectors-commonwealth.md` § "NEMA + AFAC + AIATSIS sign-off") and out-of-scope item OOS-8 mandate a registry of operator → land-council → scope → expiry mappings that fronts every retrieval response. Pass 1 Q-P1-01 settled fail-closed semantics; Pass 2 Q-P2-02 settled the gate's *seam* (post-retrieval, in-process) over four alternatives (pre-retrieval filter, AI Search security trim, Foundry tool-call gate, Front-Door route).

## Decision

1. **Seam**: a post-retrieval, in-process gate inside `RetrievalService.retrieve()` between the AI Search round-trip and Foundry inference. Implementation lives at `apps/api/app/services/retrieval_service.py` (the canonical retrieval seam, T193–T199).
2. **Registry**: a new `culturalAuthorityRegistry` Cosmos container in Australia East, partition key `/operator_id`, schema per `contracts/cultural-authority-registry.schema.json` (T193 + T197). Container is provisioned empty; population is HUMAN-IN-LOOP (T202).
3. **Indigenous-language corpus**: a separate Cosmos container with the same access-control model; body content is HUMAN-IN-LOOP (T203).
4. **Cache**: 5-minute TTL in-process cache of registry rows by `(operator_id, scope)`; no Redis/external cache because revocation events must take effect within `2 × cache_ttl` ≤ 10 min (Pass 1 Q-P1-04).
5. **Feature flag**: `feature.cultural_authority_gate.enabled` is **Locked-on** in production (A12 flag-class taxonomy, Pass 2 Q-P2-08). The flag may be disabled only for `environment=test` chaos runs; OPA `foundry_carveout.rego` blocks any production flip via the same line-29 environment-discriminator extended in F-A4.
6. **Fail-closed semantics**: when the registry is unreachable, suppress all chunks tagged `protected_indigenous` or `sacred_site_protocol` and emit a `cultural_authority_registry_unavailable` audit record. Non-protected chunks remain retrievable so the agent does not silence overall (Constitution Principle I).
7. **CD gate**: SC-014 (`tools/lint/check_cultural_authority_signoffs.py`) verifies `granted_by_authority`, `signature`, and `granted_at` are non-null for every active row at deploy time.

## Rationale

- **Why post-retrieval, in-process?** AI Search security trims operate on per-document ACLs but cannot represent time-bound, scope-bound delegations without an order-of-magnitude blow-up in indexed metadata. A Foundry tool-call gate would run *after* the model has already read the chunk, violating the "never surface" requirement. Front-Door routing cannot inspect chunk-level metadata. The in-process seam is the only place where (a) retrieval has happened, (b) the chunk metadata is fully resolved, and (c) the agent has not yet seen the content.
- **Why a 5-minute cache TTL?** The registry is small (≤ 10⁴ rows in steady state), so a longer TTL has no cost benefit; a shorter TTL costs Cosmos RUs without a measurable freshness gain since revocations are rare. 5 minutes pairs with the 10-minute revocation-propagation budget settled in Q-P1-04.
- **Why locked-on?** The constitution clause is non-negotiable; making the flag Reversible would create a path for accidental disablement during incident response and weaken the audit story.
- **Why fail-closed for protected only?** Globally fail-closed on registry unavailability would cause cascading silences under the perfectly normal operational pattern of Cosmos throttling under burst load. Scoping the closure to protected tags preserves Principle I (no silent agent) while preserving VI-C (no protected exposure without authority).

## Consequences

**Positive**
- Constitution VI-C is enforced at the canonical retrieval seam; future agents and surfaces inherit the gate by construction.
- Single-index economics (FR-RAG-IDX-08) preserved: ≤ 1 additional 5 ms p95 on cold cache miss, ≈ 100 µs warm.
- Audit trail is uniform — every gated denial emits a single shape independently of the upstream cause.

**Negative / mitigations**
- Cold-start penalty on the first request after each pod restart (≤ 5 ms). Mitigated by a startup pre-warm against the 100 most-recent operators.
- Registry must be populated by external authority sign-off before production go-live. Tracked as T202 + a CD gate (SC-014).
- Revocation latency up to 10 minutes (2 × TTL). Acceptable per Q-P1-04; emergency revocation can bypass via an `force_invalidate_cache` admin endpoint.

## Cross-references

- Cluster A2 in `specs/036-foundry-rag-grounding/spec.md` Session 3.
- Pass 1 Q-P1-01, Pass 2 Q-P2-01 / Q-P2-02 / Q-P2-08 in spec.md Sessions 4 + 5.
- Schema in `specs/036-foundry-rag-grounding/contracts/cultural-authority-registry.schema.json`.
- Tasks T193–T203; HUMAN-IN-LOOP gate at T202 + T203.
- Plan phase F-A2 in `specs/036-foundry-rag-grounding/plan.md`.
- Implementation: `apps/api/app/services/retrieval_service.py`, `apps/api/app/services/cultural_authority.py`.

