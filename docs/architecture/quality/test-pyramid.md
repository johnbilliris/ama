---
purpose: Defines the five-tier test pyramid with relative volumes and tooling for the AMA platform so QA Engineers can scope test investment correctly.
personas:
  - Technical-Quality
diagrams:
  - QUAL-01
specs:
  - spec-024
---

# QUAL-01 — Test Pyramid

[→ Architecture index](../README.md)

![QUAL-01: Test Pyramid](test-pyramid.png)

> **Note**: skill-fallback authored — refine before merge.

<!-- spec-cross-ref: spec-024 -->

This view defines the five-tier test pyramid with relative volumes and tooling for the AMA platform so QA Engineers can scope test investment correctly.

## Test Tiers

| Tier | Relative Volume | Tooling | Example Test Target | Notes |
| --- | --- | --- | --- | --- |
| Unit | ~159 tests (~46%) | pytest | Individual agent functions, utility helpers | Fast feedback; no I/O |
| Contract | ~50 tests (~14%) | pytest | API schema contracts, CAP/EDXL payload shapes | Pact-style consumer-driven |
| Integration | ~80 tests (~23%) | pytest | DB reads/writes, external adapter calls | Requires testcontainers |
| Simulation | ~30 tests (~9%) | simulation harness | Multi-agent scenario end-to-end in sandbox | Uses synthetic incident data |
| E2E | ~20 tests (~6%) | Playwright | Full ops-dashboard user journeys | Browser-based; slow |

## FR Notes

- **FR-025**: Five-tier test pyramid documented with volumes and tooling per tier.

## Related Pages

- [Architecture index](../README.md)
- [C4-L3-Agents — Agents Runtime Components](../c4/component-agents.md)
- [EXP-01 — Ops Dashboard User Journey](../accessibility/ops-dashboard-user-journey.md)
