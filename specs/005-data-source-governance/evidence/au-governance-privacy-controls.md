# AU Governance Privacy Control Map (AUD-025)

## Status

- Overall status: UNVERIFIED
- Owner approvals required: data owner, legal owner, security owner
- Scope: spec 005 governance registry and governance dashboard export seam

## Control Summary

- APP collection/minimization controls are mapped to governance mutation paths.
- Governance payload classifier now covers `/api/data-sources` and `/api/governance`.
- Actor identifiers are pseudonymized for governance audit/response surfaces when an email subject is presented.
- Assessment free text (`explanation`, `conditions`, `gaps`) is classified before persistence with fail-closed behavior.
- Governance export seam blocks non-AU country activation by default and enforces legal-hold constraints for history exports.

## Country Activation Gates

- AU: active with transfer default deny-unless-approved.
- PH: default-deny until MoU + DPIA + sovereign authorization.
- JP: default-deny until MoU + DPIA + sovereign authorization.
- BD: default-deny until MoU + DPIA + sovereign authorization.

## Retention and Lawful Access

- Retention schedule: UNVERIFIED pending legal/data-owner approval.
- Historical export requires `legal_hold=true`.
- Mixed-scope export is denied to prevent cross-scope leakage.

## Bounded Carve-Out

- Foundry bounded carve-out remains unchanged.
- This control map does not authorize non-AU governance storage or transfer.
