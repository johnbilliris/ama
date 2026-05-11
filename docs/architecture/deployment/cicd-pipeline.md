---
purpose: CI/CD pipeline diagram showing what-if and plan gates, manual approval steps, and deployment targets for all environments.
personas:
  - Technical-Build
diagrams:
  - DEPLOY-01
specs:
  - spec-017
  - spec-029
---

# DEPLOY-01 — CI/CD Pipeline

[→ Architecture index](../README.md)

<!-- spec-cross-ref: spec-017 -->
<!-- spec-cross-ref: spec-029 -->

![DEPLOY-01 — CI/CD Pipeline](./cicd-pipeline.png)

## Stages

| Stage | Control |
| --- | --- |
| GitHub PR | Source change enters the gated pipeline |
| Quality Gate | Verifies checks before infrastructure change review |
| What-If | Surfaces plan output before approval |
| Manual Approval | Human release authority approves promotion |
| Deploy Dev / Staging / Prod | Container Apps targets receive the approved release |
