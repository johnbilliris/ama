# Spec 038 — Terraform parity follow-up (T-Z07)

Per Research D10: Terraform mirrors of spec-035/037 modules are not yet
present in `infra/terraform/`. The Bicep module
`infra/bicep/modules/evidence-harness.bicep` is the canonical source.

A follow-up issue should be filed to add a Terraform mirror at
`infra/terraform/modules/evidence-harness.tf` once the wider AMA
Terraform parity stream lands. Until then, deployments use Bicep
exclusively (`infra/bicep/main.bicep` `enableEvidenceHarness=true`).

> See `infra/bicep/modules/evidence-harness.bicep` for the reference
> implementation and `specs/040-success-criteria/research.md` D10 for the
> parity decision rationale.
