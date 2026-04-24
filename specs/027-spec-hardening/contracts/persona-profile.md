# Template: Persona profile

Satisfies FR-014 .. FR-017. Copy into `specs/001-disaster-response-hub/personas/<persona-id>.md` (one file per persona). Alternatively, for brevity, inline the same front-matter + sections as a block under `## Personas` in spec 001.

## Required front-matter (YAML)

```yaml
---
persona_id: PER-###
display_name: <e.g. "Incident Controller (State-level)">
aiims_function: Control | Intelligence | Planning | Operations | Logistics | Public Information | Non-AIIMS-Community | Non-AIIMS-Governance
role_basis: <citation — AIIMS-5, AIDR handbook, etc.>
jurisdiction_scope: v1-primary | deferred | national
authority_scope: <single sentence — what the persona may authorise unilaterally; what requires countersign>
validated_by:
  - { name: "<Name>", role: "SME | practitioner | proxy", date: YYYY-MM-DD }
  # Must include at least one entry with role = "SME" OR "practitioner"
representative_scenarios:
  - <link to scenario in spec 001 or rehearsal library>
accessibility_needs: <single sentence OR "Not applicable — operator persona">
---
```

## Required sections

1. `## Goals` — what the persona is trying to accomplish within the platform.
2. `## Decisions they own` — the operational decisions this persona makes.
3. `## Information they need` — the signal / intelligence inputs this persona relies on.
4. `## Constraints` — legal, jurisdictional, accessibility, or safety constraints on the persona.
5. `## Handoffs` — upstream and downstream role interactions.
6. `## Evidence of validation` — paragraph naming the SME / practitioner / proxy that validated the profile and the date.

## Validation rules

1. `aiims_function ∈ {Control, Intelligence, Planning, Operations, Logistics, Public Information}` must have at least one persona (SC-004).
2. `validated_by` must include at least one entry with `role ∈ {SME, practitioner}` (FR-016 — proxy alone is insufficient).
3. CALD, accessibility-impaired, and tourist archetypes must each have at least one persona profile (FR-015(c)(d)(e)).
4. `authority_scope` must name both unilateral authority and countersign-required authority — one-sided authority statements fail validation.
