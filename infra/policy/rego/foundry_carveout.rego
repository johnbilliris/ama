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

deny_foundry_carveout[msg] {
    deployment := input.deployments[_]
    count(deployment.approver_identities) < 2
    msg := sprintf("FR-RAG-CV-01 violation: deployment %v has fewer than 2 approver_identities.", [deployment.model_name])
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
