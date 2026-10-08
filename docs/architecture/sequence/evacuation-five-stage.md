---
purpose: Answers "where does a human gate the loop during evacuation?" — five-stage AIIMS evacuation flow with human-in-the-loop approval gate on actuation.
personas:
  - Operational
diagrams:
  - SEQ-03
specs:
  - spec-010
  - spec-019
---

# SEQ-03 — Evacuation Five-Stage Flow

[→ Architecture index](../README.md)

![SEQ-03: Evacuation Five-Stage Flow](evacuation-five-stage.png)

This page shows the constitutional five-stage evacuation lifecycle (Decision, Warning, Withdrawal, Shelter, Return) and highlights where a human decision gates actuation.

## Human Approval Gate

The human approval gate sits between the generated evacuation recommendation and the actuation step. Operators validate scope, timing, public messaging, and jurisdictional authority before any movement order is issued.

## FR Notes

- **FR-009**: the actuation path includes a distinct human approval marker before evacuation instructions are actioned.
- **FR-010c**: the canonical five stages are Decision, Warning, Withdrawal, Shelter, and Return.

## Stage semantics

- Preparation is a precondition activity and not one of the five evacuation lifecycle stages.
- Shelter-in-place and re-entry are explicit alternatives governed by incident conditions and authority directives.
- Recovery can overlap with late response operations; handover does not imply immediate shutdown of response coordination.

## Related Pages

- [Architecture index](../README.md)
- [SEQ-04 — Recovery Transition](recovery-transition.md)
