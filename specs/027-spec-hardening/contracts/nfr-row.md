# Template: NFR row

Satisfies FR-004 .. FR-013, FR-035. Copy into the `## NFRs` table of `specs/001-disaster-response-hub/spec.md`.

## Column order

`nfr_id | category | statement | target | basis | drafter | sme_countersigner | privacy_reviewer | standard_reference | measurement_method`

## Row template

```markdown
| NFR-### | <enum> | <non-prose statement> | <number + units OR enum> | <citation> | <Name, Role> | <Name, Role> | <Name, Role OR "N/A"> | <standard reference OR "—"> | <how measured in production> |
```

## Allowed `category` values

`Performance`, `Reliability`, `Security`, `Privacy`, `Accessibility`, `Interoperability`, `Observability`, `Data-Residency`, `Cost`.

## Examples

```markdown
| NFR-004 | Performance | Read-side API p95 latency, excluding model latency. | ≤ 500 ms | Internal SRE benchmark on Azure Container Apps (2026-04); aligns with national EM dashboard UX studies. | C. Nguyen, Staff Engineer | M. Ross, Principal SRE | N/A | — | Azure Monitor `requests` metric p95 over 7-day rolling window. |
| NFR-006 | Data-Residency | All operational and audit data is stored and processed within Australian Azure regions. | Australia East (primary) + Australia Southeast (DR) | Privacy Act 1988 (Cth); constitution §Non-Negotiable-2; internal Data Residency Policy v3.1. | C. Nguyen, Staff Engineer | M. Ross, Principal SRE | J. Patel, Privacy Counsel | — | Azure Policy assignment `allowed-locations` with daily compliance scan. |
| NFR-009 | Interoperability | Public alert payloads conform to CAP 1.2 and are distributable via EDXL-DE 2.0 envelopes. | 100% of outbound public alerts | OASIS CAP 1.2; OASIS EDXL-DE 2.0; Australia AWS requirements. | C. Nguyen, Staff Engineer | M. Ross, Principal SRE | N/A | CAP 1.2; EDXL-DE 2.0 | Contract test suite in `apps/api/tests/contract/alerts_cap_test.py`. |
```

## Validation rules

1. `category ∈ {Privacy, Security, Data-Residency}` ⇒ `privacy_reviewer ≠ "N/A"`.
2. `category ∈ {Interoperability, Accessibility}` ⇒ `standard_reference` is non-empty.
3. `target` parses as number-with-units, bounded enum, or "100%"/"0%" — prose targets fail validation.
4. `measurement_method` names a runtime-observable mechanism (metric, contract test, Azure Policy, etc.).
