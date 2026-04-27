package identity_consistency

# T008b — Static consistency check between infra/IDENTITY.md and the rest
# of the repository. Counterpart to the runtime topology assertion in
# .github/workflows/_reusable/setup-oidc-azure.yml (T005).
#
# Input contract (assembled by the conftest driver):
#   input.identity      = parsed YAML front-matter from infra/IDENTITY.md
#   input.parameters    = {dev: <bicepparam_obj>, staging: ..., production: ...}
#   input.codeowners    = raw text content of .github/CODEOWNERS
#
# Per ADR-029-01 (research.md §R17) and §R16 dual-topology decision.

# (a) Topology A declared but parameter files do not have 3 distinct sub IDs
deny[msg] {
    input.identity.subscription_topology == "A"
    sub_ids := {input.parameters[env].subscriptionId | env := input.parameters[_]}
    count(sub_ids) < 3
    msg := sprintf(
        "identity_consistency_topology_a_collapse: subscription_topology=A but only %d distinct subscription IDs declared across dev/staging/production parameter files (must be 3, per research.md §R16)",
        [count(sub_ids)],
    )
}

# (b) Topology B declared but parameter files have differing sub IDs
deny[msg] {
    input.identity.subscription_topology == "B"
    sub_ids := {input.parameters[env].subscriptionId | env := input.parameters[_]}
    count(sub_ids) > 1
    msg := sprintf(
        "identity_consistency_topology_b_split: subscription_topology=B but %d distinct subscription IDs declared across dev/staging/production parameter files (must be 1, per research.md §R16)",
        [count(sub_ids)],
    )
}

# (c.1) handle_mode=team but CODEOWNERS contains user-style @<single>-handles for posture files
deny[msg] {
    input.identity.codeowners_handle_mode == "team"
    contains(input.codeowners, "@johnbilliris")
    msg := "identity_consistency_handle_mode_mismatch_team: codeowners_handle_mode=team declared in IDENTITY.md but .github/CODEOWNERS still contains user-form handle @johnbilliris (per ADR-029-01 the org-mode mapping must use @org/<team> handles)"
}

# (c.2) handle_mode=user but CODEOWNERS contains team-style @org/<team> handles
deny[msg] {
    input.identity.codeowners_handle_mode == "user"
    regex.match(`@[A-Za-z0-9_-]+/[A-Za-z0-9_-]+`, input.codeowners)
    msg := "identity_consistency_handle_mode_mismatch_user: codeowners_handle_mode=user declared in IDENTITY.md but .github/CODEOWNERS contains org/team-form handle (per ADR-029-01 user-owned repos cannot reference team handles)"
}

# (d) production_reviewers_mode=individual_union but union exceeds GitHub Environments cap of 6
deny[msg] {
    input.identity.production_reviewers_mode == "individual_union"
    union_size := count(input.review_set)
    union_size > 6
    msg := sprintf(
        "identity_consistency_reviewer_cap_breach: production_reviewers_mode=individual_union with %d distinct reviewers exceeds the GitHub Environments hard cap of 6 (per ADR-029-01 / research.md §R17). Migrate to org mode (production_reviewers_mode=scim_team) or reduce membership.",
        [union_size],
    )
}
