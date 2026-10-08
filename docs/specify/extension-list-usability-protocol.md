# Extension List External Usability Protocol

## Scope

This protocol governs the external human study for SC-001 and SC-006. The
study is conducted only by an authorized study team using pre-provisioned,
authorized Australian Azure evidence and audit stores. It is never conducted
locally, in CI, from this repository, or by the CLI implementation. Repository
fixtures are synthetic and are not participant records or study outcomes.

The study measures whether representative adult CLI users can identify
installed and enabled extensions and understand that listing does not install,
remove, enable, disable, or repair extensions. Collection is limited to those
purposes. Results must not be reused for identity, employment, health,
profiling, marketing, or unrelated product research.

## Notice And Consent

Before eligibility screening or collection, the study team provides the
approved notice version, purpose, collected closed fields, storage location,
retention period, access controls, withdrawal process, incident contact, and
the limits of deletion under an approved legal hold. Explicit consent is
recorded for every included or excluded person before any task exposure. A
person who declines or withdraws is not disadvantaged and is not replaced
using identity-derived matching.

## Identity And Collection

Participant identifiers are independently random pseudonyms generated without
names, contact details, employer, account identifiers, precise location, or
other identity-derived input. Recruitment records and the re-identification key
remain separate from study evidence with separately authorized access.
Participant evidence contains no names, direct identifiers, free-text fields,
medical details, command output, repository paths, or unstructured notes.

Reviewer records contain only a random `reviewer_identifier`, the closed role
`privacy` or `research-governance`, review timestamp, decision `approved` or
`rejected`, and reason `study-verified` or `study-rejected`. Accommodations use
only the approved generic category codes; no reason, diagnosis, or free text is
collected.

## Eligibility, Cohorts, And Allocation

Eligible participants are adults who use a CLI monthly and have no prior
exposure to this feature. The final included cohort contains exactly 20 unique
pseudonyms: 10 novices with zero to two Spec Kit workflows in the prior six
months and no extension-management experience, and 10 experienced users with
at least five workflows and extension-management experience. The unclassified
three-to-four-workflow gap is ineligible.

Within each stratum, deterministic allocation uses
`sha256-seeded-stratified-order-v1`: sort eligible pseudonyms, order by the
SHA-256 of `<seed>:<stratum>:<participant_id>` with pseudonym as tie-breaker,
then assign declared task variants round-robin. The seed is study-specific,
random, and contains no identity material.

An unavailable required accommodation or a documented technical interruption
may exclude a participant only before task exposure. The record uses a closed
reason code and generic unavailable-accommodation codes. Replacement is a
distinct eligible participant in the same stratum and receives the next valid
deterministic allocation. Post-exposure outcomes are retained in the included
cohort and are never replaced to improve results. Requested accommodations are
provided without changing the measured task.

## Storage, Access, And Audit

Evidence and action audit records are written only to authorized AU-resident
Azure stores with public access disabled, private networking, encryption in
transit and at rest, and named least-privilege study-team access. Access and
lifecycle actions are recorded in an immutable audit ledger. The study team
verifies the authorized storage boundary before collection and finalization.
No participant or reviewer payload is written to a workstation, repository,
GitHub, CI artifact, console transcript, or local cache.

## Retention, Withdrawal, And Incidents

The reviewed evidence records a deletion deadline no later than 90 days after
review. At the deadline, study evidence and separated linkage material are
verified deleted unless a documented authorized legal hold is active. A legal
hold preserves only the required records, remains audited, and triggers deletion
when released.

Before de-identification or aggregation, withdrawal causes collection to stop
and all linkable study evidence to be deleted and audited. After irreversible
de-identification, the notice explains which aggregate data can no longer be
linked for deletion. Suspected loss, unauthorized access, disclosure, or
re-identification triggers immediate collection suspension, access revocation,
evidence preservation under incident controls, notification to the privacy and
security contacts, assessed breach response, documented remediation, and an
audited decision before any restart.

## Finalization

Finalization validates schema and cross-record semantics before an authorized
pseudonymous reviewer records a closed decision and reason. Study lifecycle
validity is independent of outcome thresholds: a reviewed, schema-valid,
semantically consistent failed study remains valid retained evidence. SC-001
and SC-006 threshold results are reported separately and never alter cohort,
privacy, retention, or review validity.