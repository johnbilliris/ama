# Gap-ID Register

**Purpose**: Monorepo-wide, append-only, monotonic register of every gap identifier cited under `specs/`. Satisfies FR-036 and Clarification 8 of `specs/027-spec-hardening/spec.md`.

**Authority**: `.github/CODEOWNERS` entry for `specs/shared/` (the `@johnbilliris/ama-spec-maintainers` team per FR-034).

**Rules** (enforced by `scripts/verify-spec-hardening.ps1`):

1. `gap_id` is unique across the whole register (not just within a category).
2. Within each category prefix, suffixes are strictly monotonic — a missing number fails validation.
3. Rows are never deleted. Status transitions are made in place.
4. `status = Resolved` ⇒ `owning_feature` and `evidence_link` are non-empty.
5. Every Gap ID cited anywhere under `specs/` MUST appear here.

---

## Register

| gap_id | category | short_title | raised_by | raised_in_feature | status | owning_feature | evidence_link |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A-GAP-001 | Assumption | v1 jurisdiction selection rationale unstated | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| A-GAP-002 | Assumption | Asia-region data availability and quality unasserted | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| A-GAP-003 | Assumption | Capstone-vs-solution jurisdiction divergence uncallouted | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| A-GAP-004 | Assumption | Minimum connectivity floor for field operation unstated | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| A-GAP-005 | Assumption | AI/agent quality floor (hallucination, false-positive, multilingual) unstated | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| A-GAP-006 | Assumption | Data residency and sovereignty obligations per target country unstated | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| A-GAP-007 | Assumption | Baseline-exercise availability for SC-004..SC-006 unstated | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| A-GAP-008 | Assumption | Legal / statutory standing of AI-generated recommendations unstated | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| REQ-GAP-001 | Requirement | NFRs scattered across plan.md and not promoted into spec | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| REQ-GAP-002 | Requirement | Accessibility NFR conformance level absent | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| REQ-GAP-003 | Requirement | Privacy NFRs (PII / retention / erasure / residency / cross-border) absent | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| REQ-GAP-004 | Requirement | Security NFRs (authN strength / sessions / keys / threat-model) absent | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| REQ-GAP-005 | Requirement | Performance / freshness NFRs not promoted into spec | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| REQ-GAP-006 | Requirement | Interoperability NFR (CAP 1.2 / EDXL-DE / Sendai) absent | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| REQ-GAP-007 | Requirement | Training & change-management NFR (SC-003 dependency) absent | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| REQ-GAP-008 | Requirement | Medical triage / shelter / utility isolation / SAR FR gap | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| REQ-GAP-009 | Requirement | Misinformation detection FR absent | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| REQ-GAP-010 | Requirement | Audit-retention NFR (duration / format / recoverability) absent | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| PER-GAP-001 | Persona | Persona schema (goals / pains / authority / top-3 tasks) absent | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| PER-GAP-002 | Persona | AIIMS operational personas unvalidated | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| PER-GAP-003 | Persona | Executive personas (Minister / Premier, Mayor) absent | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| PER-GAP-004 | Persona | CALD / affected-community persona archetypes absent | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| PER-GAP-005 | Persona | Adversarial personas (misinfo actor, insider threat) absent | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| PER-GAP-006 | Persona | Accessibility-specific operator personas absent | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| PER-GAP-007 | Persona | Persona SME-validation provenance absent | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| HYP-GAP-001 | Hypothesis | Safety-autonomy balance unfalsifiable | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| HYP-GAP-002 | Hypothesis | Signal trust model unfalsifiable | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| HYP-GAP-003 | Hypothesis | Orchestration approach (deterministic vs LLM-routed) unfalsifiable | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| HYP-GAP-004 | Hypothesis | Mobile delivery under degraded connectivity unfalsifiable | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| HYP-GAP-005 | Hypothesis | Misinformation resilience unfalsifiable | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| HYP-GAP-006 | Hypothesis | Cross-jurisdictional framework portability unfalsifiable | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| SCP-GAP-001 | Scope | v1 Primary Jurisdiction not declared (Australia vs Asia) | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| SCP-GAP-002 | Scope | Deferred-Scope Register for Asia jurisdictions absent | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| SCP-GAP-003 | Scope | In-scope vs out-of-scope hazard list absent | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| SCP-GAP-004 | Scope | Autonomy-boundary table absent | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| SCP-GAP-005 | Scope | Community-signal source enumeration absent | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| SCP-GAP-006 | Scope | Recovery (PPRR) stance unfixed | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| SCP-GAP-007 | Scope | Citizen-facing surface list absent | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| SCP-GAP-008 | Scope | Upstream / downstream integration list absent | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
| SCP-GAP-009 | Scope | Rehearsal content boundary unfixed | J. Reviewer, Principal Architect | 027-spec-hardening | Open | 001-disaster-response-hub | — |
