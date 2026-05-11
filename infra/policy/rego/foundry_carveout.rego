# Spec 036 — Foundry carve-out OPA policy (T025, FR-RAG-CV-01..04)
#
# Mirrors the JSON-Schema enforcement in
# ``infra/parameters/foundry-carveout.schema.json`` so OPA can refuse a Bicep
# what-if dump whose effective ``foundry-carveout.yaml`` would deploy a model
# without the carve-out approval. Loaded by ``conftest`` for unit-tests and by
# the CD ``verify-carveout.ps1`` step (T026) for live deploys.
package main

# Allow-list of Australian regions for FR-RAG-CV-04 data-residency.
au_regions := {"australiaeast", "australiasoutheast"}

# A registry row is well-formed when it carries a non-placeholder approver
# duo, both data-minimisation flags, and an AU region.
deny_foundry_carveout[msg] {
    deployment := input.deployments[_]
    not deployment.data_minimisation_required
    msg := sprintf("FR-RAG-CV-03 violation: deployment %v missing data_minimisation_required.", [deployment.model_name])
}

deny_foundry_carveout[msg] {
    deployment := input.deployments[_]
    not deployment.classification_filter_required
    msg := sprintf("FR-RAG-CV-03 violation: deployment %v missing classification_filter_required.", [deployment.model_name])
}

# Spec 036 F-A4 (T152) — environment-aware approver-count quorum
# (FR-RAG-CV-01; SC-016; Plan §F-A4.1).
#
# `prod`             → count(approver_identities) >= min_approvers_prod (default 3)
# `dev` or `staging` → count(approver_identities) >= min_approvers_dev  (default 2)
#
# Schema mirror: `infra/parameters/foundry-carveout.schema.json` (registry-root
# `min_approvers_prod` + `min_approvers_dev`; per-row `environment` enum).
# Spec contract mirror: `specs/036-foundry-rag-grounding/contracts/foundry-cv.schema.json`.

# Default floors when the registry omits the keys (preserves spec-032 behaviour).
default_min_approvers_prod := 3
default_min_approvers_dev := 2

min_approvers_prod := input.min_approvers_prod {
    input.min_approvers_prod
} else := default_min_approvers_prod

min_approvers_dev := input.min_approvers_dev {
    input.min_approvers_dev
} else := default_min_approvers_dev

# prod row → require >= min_approvers_prod (default 3).
deny_foundry_carveout[msg] {
    deployment := input.deployments[_]
    lower(deployment.environment) == "prod"
    count(deployment.approver_identities) < min_approvers_prod
    msg := sprintf(
        "FR-RAG-CV-01 violation: deployment %v has fewer than %v approver_identities (prod requires >= %v).",
        [deployment.model_name, min_approvers_prod, min_approvers_prod],
    )
}

# dev / staging row → require >= min_approvers_dev (default 2).
deny_foundry_carveout[msg] {
    deployment := input.deployments[_]
    env := lower(deployment.environment)
    env != "prod"
    env != ""
    count(deployment.approver_identities) < min_approvers_dev
    msg := sprintf(
        "FR-RAG-CV-01 violation: deployment %v has fewer than %v approver_identities (dev/staging requires >= %v).",
        [deployment.model_name, min_approvers_dev, min_approvers_dev],
    )
}

# Backward-compat: rows missing the `environment` field (legacy spec-032
# registries) still get the dev floor — the discriminator MUST be added at the
# next CD apply per Pass 2 Q-P2-03.
deny_foundry_carveout[msg] {
    deployment := input.deployments[_]
    not deployment.environment
    count(deployment.approver_identities) < min_approvers_dev
    msg := sprintf(
        "FR-RAG-CV-01 violation: deployment %v has fewer than %v approver_identities (no environment set; treating as dev/staging).",
        [deployment.model_name, min_approvers_dev],
    )
}

deny_foundry_carveout[msg] {
    deployment := input.deployments[_]
    approver := deployment.approver_identities[_]
    contains(approver, "<")
    msg := sprintf("FR-RAG-CV-01 violation: deployment %v approver %q is a placeholder.", [deployment.model_name, approver])
}

deny_foundry_carveout[msg] {
    deployment := input.deployments[_]
    approver := deployment.approver_identities[_]
    contains(lower(approver), "todo")
    msg := sprintf("FR-RAG-CV-01 violation: deployment %v approver %q is a placeholder.", [deployment.model_name, approver])
}

deny_foundry_carveout[msg] {
    deployment := input.deployments[_]
    region := lower(deployment.region)
    not au_regions[region]
    msg := sprintf("FR-RAG-CV-04 violation: deployment %v region %v is outside Australian data-residency boundary.", [deployment.model_name, deployment.region])
}

deny_foundry_carveout[msg] {
    not input.reviewer_quorum
    msg := "FR-RAG-CV-01 violation: reviewer_quorum must be >= 2."
}

deny_foundry_carveout[msg] {
    input.reviewer_quorum < 2
    msg := sprintf("FR-RAG-CV-01 violation: reviewer_quorum=%v is below the required minimum of 2.", [input.reviewer_quorum])
}
