# Phase 0 Research: Capstone Specification Hardening

**Feature**: 027-spec-hardening
**Date**: 2026-04-24
**Status**: complete

This document records the design-time research performed to resolve the unknowns in the Technical Context of `plan.md`. Each topic is captured as a Decision / Rationale / Alternatives Considered triple, per the Spec-Kit plan template.

---

## R-1. Monotonic Gap-ID register location and format (FR-036)

**Decision**: Seed `specs/shared/gap-id-register.md` as a single markdown table with columns `Gap ID | Category | Short title | Raised by | Raised in (feature) | Status | Owning feature | Evidence link`. IDs are allocated in strict monotonic order using the category prefix (A-GAP-###, REQ-GAP-###, PER-GAP-###, HYP-GAP-###, SCP-GAP-###) and padded to three digits. A withdrawn ID is never reused; a new ID is allocated if the underlying concern resurfaces. The register is append-only: rows are never deleted, only updated in-place.

**Rationale**: Clarification 8 requires monorepo-wide monotonicity and no renumbering. A flat markdown table is the cheapest format that GitHub renders, supports diff review, and can be lint-checked by a small script. A single file avoids the cross-directory race condition of per-feature registers. Zero-padded three-digit suffixes keep file sorts stable up to 999 per category, which exceeds the forecast over the capstone lifetime.

**Alternatives considered**:

- *Per-feature registers*: rejected because the contradiction sweep (FR-032) spans features, and per-feature scopes make it structurally impossible to detect cross-feature reuse.
- *JSON / YAML register*: rejected because the dominant consumer is human review in PRs, not tooling; markdown is already the native format of every neighbouring artefact.
- *GitHub Issues as register*: rejected because issues are mutable, can be deleted, and are not versioned with the specs they describe.

## R-2. Evidence Pack file layout and location (FR-020, Clarification 4, Clarification 9)

**Decision**: One file per hypothesis at `specs/<owning-feature>/evidence/<HYP-ID>.md`. The file is created at hypothesis creation time with status = *Not tested* and is never deleted; subsequent status transitions overwrite the file in place while preserving prior content under a `## History` section.

Each file has a required front-matter block (YAML) and required markdown sections:

```yaml
---
hypothesis_id: HYP-###
owning_feature: 001-disaster-response-hub
status: Not tested | Under validation | Validated | Invalidated | Withdrawn
last_reviewed: YYYY-MM-DD
drafter: "Name, Role"
countersigner: "Name, Role"
---
```

Required sections: `## Statement`, `## Falsification Criteria`, `## Method`, `## Evidence`, `## Decision`, `## History`.

**Rationale**: Clarification 9 mandates that stubs exist from creation. Placing files next to the owning feature's spec preserves locality; a single file per hypothesis avoids merge conflicts when multiple reviewers edit evidence concurrently. The history section supports audit replay without git-log spelunking. YAML front-matter lets the verification script read status and signatures without parsing prose.

**Alternatives considered**:

- *Single per-feature evidence.md with all hypotheses inside*: rejected because every update churns one file, generating merge conflicts and making per-hypothesis ownership harder.
- *Evidence stored outside `specs/`* (e.g., `data/evidence/`): rejected because reviewers expect spec-supporting artefacts co-located with the spec.
- *Evidence stored only as Open Delta rows*: rejected because Open Deltas are transient, while validated evidence must persist with the spec forever.

## R-3. Status-transition authority — CODEOWNERS mechanism (FR-034, Clarification 6)

**Decision**: Add an entry `specs/001-disaster-response-hub/ @<spec-maintainer-team>` to `.github/CODEOWNERS`. The team handle (not an individual) is used so that the authority survives personnel change. Status transitions on Assumptions, Hypotheses, and Personas require both a drafter signature and a countersignature from a CODEOWNERS team member, recorded in the row as `drafter: Name, Role` and `countersigner: Name, Role`. GitHub enforces that CODEOWNERS review is required for the PR; the row fields record the human names for audit.

**Rationale**: Clarification 6 designated CODEOWNERS as the canonical maintainer mechanism. Using a team handle rather than individuals (a) avoids stale owners when a person leaves and (b) preserves the dual-control property at all times. The row-level name capture preserves the audit trail even if the CODEOWNERS file is later edited.

**Alternatives considered**:

- *Individual owners*: rejected — fragile over time, conflicts with the organisational intent to distribute accountability.
- *GitHub branch protection without CODEOWNERS*: rejected — branch protection enforces *that* someone reviews but not *which* team, and Clarification 6 explicitly named CODEOWNERS.
- *GitHub "review teams" feature without CODEOWNERS*: rejected — same visibility gap; not all repos in the org configure review teams.

## R-4. Traceability Table canonical location (FR-031, Clarification 10)

**Decision**: The canonical Traceability Table lives at the bottom of `specs/027-spec-hardening/spec.md` under `## Traceability Table`. Spec 001 carries a single pointer row in its `## Changelog` section of the form:

```markdown
| 2026-04-24 | capstone-hardening-ingest | See [specs/027-spec-hardening/spec.md#traceability-table](../027-spec-hardening/spec.md#traceability-table) for the gap-to-requirement mapping. |
```

Table columns: `Gap ID | Gap short title | Category | Resolved by (FR / §) | Evidence Pack | Status`.

**Rationale**: Clarification 10 settled this unambiguously: the change record is 027, therefore the table belongs with the change record, and duplication is avoided. The pointer from spec 001 preserves discoverability for readers who start there.

**Alternatives considered**:

- *Canonical in spec 001*: rejected — would make 027 a pointer-only record and defeat the point of a dedicated hardening spec.
- *Canonical in both (duplicated)*: rejected — duplication creates drift risk and violates FR-031.
- *Canonical in a third file (e.g., `specs/shared/traceability.md`)*: rejected — weakens the "one change, one spec" locality principle of Spec-Kit.

## R-5. Open Deltas handoff to downstream features (FR-032, Clarification 5)

**Decision**: The `## Open Deltas` subsection lives in `specs/001-disaster-response-hub/spec.md` (where the contradiction was detected) and is kept in sync with the canonical row in the 027 Traceability Table. Every row carries a `target-feature` field naming the feature that must settle the delta; a delta is considered settled only when the targeted feature's own `spec.md` records the resolution. The plan-phase prerequisite is enforced by a verification script (Phase 2 task): `/speckit.plan` for a targeted feature must fail if any Open Delta row still has status ≠ *Resolved* and `target-feature` equal to the running feature's ID.

**Rationale**: Clarification 5 required deltas to be settled before `/speckit.plan` on the owning follow-on feature. A scripted gate is the only way to enforce the ordering without placing trust in reviewer memory; a `target-feature` field is the minimum metadata to make the gate tractable.

**Alternatives considered**:

- *Deltas kept only in 027*: rejected — the planner of the target feature would have to cross-read another spec to discover blocking work. Co-locating in spec 001 keeps the work visible where contradictions were observed.
- *Deltas enforced by PR template checklist only*: rejected — relies on reviewer diligence; scripted enforcement meets the non-negotiable audit bar.
- *Deltas allowed to remain open at plan time if flagged in plan.md*: rejected — Clarification 5 explicitly rules this out.

## R-6. NFR drafting authority chain (FR-035, Clarification 7)

**Decision**: Every NFR row in spec 001 carries four required fields in addition to the numeric target: `basis` (citation), `drafter` (name + role), `sme_countersigner` (name + role), and `privacy_reviewer` (name + role; required only when the NFR covers privacy, legal, or data-sharing concerns; `"N/A"` otherwise). The numeric target is normative only when all required signatures are present.

**Rationale**: Clarification 7 required basis citation + drafter + domain SME countersign, plus privacy reviewer for privacy/legal NFRs. Making the signatures a structural part of the row (not an attached note) means the verification script can check completeness by parsing the row. `"N/A"` is an explicit allowed value to distinguish *no privacy concern* from *unfilled*.

**Alternatives considered**:

- *Signatures in a separate appendix table*: rejected — introduces a second thing to keep in sync with the NFR table.
- *Signatures via PR approvals only*: rejected — loses the ability to audit a single spec file years later without GitHub metadata.
- *Privacy reviewer always required*: rejected — forces an artificial reviewer on purely technical NFRs (e.g., p95 latency), diluting accountability.

## R-7. Markdown lint and link-check tooling

**Decision**: Use `markdownlint-cli2` (already a dev dependency of the repo's `pnpm` workspace) with the existing `.markdownlint.jsonc` configuration. Add relative-link verification via `markdown-link-check` run only against the files this feature authors or amends; external links are not checked by this feature.

**Rationale**: Keeps tooling consistent with the rest of the repo; avoids introducing a new linter. Restricting link-check to relative links avoids flakiness from external-site availability and satisfies the constitution's Quality Gates requirement without introducing a new failure mode.

**Alternatives considered**:

- *`remark-lint`*: rejected — would introduce a second Markdown linter into the repo.
- *Vale prose linter*: rejected — scope creep; prose style is not the concern of 027.

## R-8. AIIMS persona enumeration basis

**Decision**: Persona roster for FR-015 is drawn from AIIMS-5 (2022) role families — Control, Intelligence, Planning, Operations, Logistics, Public Information — supplemented by non-AIIMS archetypes required by the constitution's Principle VI (Evacuation) and Non-Negotiable #3 (Privacy): vulnerable-population archetypes (CALD, accessibility-impaired, tourist), and the AIDR-aligned Resilience Planner and Auditor roles. Validation (FR-016) requires SME / practitioner / proxy review with name, role, and date recorded in the persona profile.

**Rationale**: AIIMS-5 is the operative Australian interoperability framework cited by the constitution (Principle II-A). AIDR is the complementary recovery and resilience reference. The vulnerable-population archetypes are required to operationalise Principle VI and the Ten Warning Principles (accessibility, CALD communities, transient populations).

**Alternatives considered**:

- *ICS-100 (US)*: rejected — wrong jurisdiction; constitution mandates AIIMS.
- *AIIMS-4*: rejected — superseded.
- *Persona list without external framework basis*: rejected — fails FR-015's "cited role basis" requirement.

## R-9. Scope of "v1 Primary Jurisdiction" and deferred jurisdictions (FR-022)

**Decision**: v1 Primary Jurisdiction is declared explicitly in spec 001 § Scope as one named Australian state or territory (to be filled by the content owner during the Phase 2 amendment tasks, defaulting to NSW for alignment with the capstone scenario). Deferred jurisdictions are listed in a Deferred-Scope Register with the fields `jurisdiction | reason deferred | target feature | re-evaluation trigger`. No jurisdictional claim is left implicit.

**Rationale**: Clarification 1 scoped 027 to spec 001 only; Clarification 5 requires that deferred work is tracked with an explicit target. NSW is the default candidate because the capstone scenario references a bushfire in NSW's Blue Mountains; the content owner may override during amendment.

**Alternatives considered**:

- *All Australian states in v1*: rejected — contradicts FR-026 (feasibility realism) and the spec's resource constraints.
- *No jurisdictional scoping at v1*: rejected — would reintroduce the SCP-GAP cluster this feature is meant to close.

## R-10. Hazard list enumeration (FR-024)

**Decision**: v1 in-scope hazards are the four capstone-named hazards — bushfire, flood, cyclone, severe storm — each with a one-sentence operational definition and a link to the corresponding AIDR Handbook. CBRN, pandemic, space weather, and cyber-physical cascading hazards are listed as out-of-scope with written rationale and a `re-evaluation trigger`. The list lives in spec 001 § Scope / Hazard List as a single markdown table.

**Rationale**: Matches the capstone.md domain scenarios and the constitution's Principle III multi-hazard mandate without smuggling in hazards the platform has not been designed for. AIDR Handbook references satisfy the constitution's II-B AIDR alignment.

**Alternatives considered**:

- *Parametric hazard model (any hazard fits v1)*: rejected — collides with FR-024's explicit-enumeration requirement and creates untestable scope.
- *In-scope hazards listed without definitions*: rejected — fails FR-024's "operational definition" clause.

---

## Closed items

All items in the Technical Context's "NEEDS CLARIFICATION" bucket were resolved either by the 10 clarifications already integrated into `spec.md` or by the nine decisions above. There are no outstanding research threads at the close of Phase 0.
