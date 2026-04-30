# Sensitive-Content Classification Taxonomy

**Purpose**: define every class of content that the platform treats as sensitive, the detection mechanism, and the default action when detected.
**Consumed by**: `apps/agents/common/safety/classification.py` (Stream 2 task T209), `infra/policies/foundry_carveout.rego` (Stream 4 task T412), the model gateway, and the audit trail.

| Class | Detector | Default action on non-AU transit | Default action on AU storage |
|---|---|---|---|
| **PII (personal identifiers)** | Microsoft Presidio v2 + custom AU patterns (Medicare, TFN, driver's licence, passport) | redact (high-confidence: deny) | hash-redact in logs (FR-O05) |
| **PII (location)** | Reverse-geocode + named-entity recognition for residential addresses | redact | allow if tenant-scoped + audit-logged |
| **PSPF marking — OFFICIAL: Sensitive** | Regex + zero-shot classifier | **deny** | allow inside AU tenant; restrict viewer roles |
| **PSPF marking — PROTECTED** | Regex + zero-shot classifier | **deny** | allow only for IncidentCommander/Executive roles; audit-logged |
| **PSPF marking — SECRET / TOP SECRET** | Regex (strict) | **deny** | **deny** (refuse storage) |
| **Operator/responder identifiers** | Pattern set (badge IDs, employee numbers, LEID) | redact (high-confidence: deny) | allow inside AU tenant |
| **Victim/casualty identifiers** | NER + pattern set (names + medical record numbers) | **deny** | allow only with explicit tenant approval; never to public alerts |
| **ATSI community identifiers** | Curated pattern set agreed with community liaisons | **deny** | allow with cultural-protocol flag set |
| **Classified location coordinates** | Geo-bounding box matched against classified-asset registry | **deny** | allow with tenant access control |
| **Critical infrastructure schematics** | Document classifier (CNN over building diagrams) | **deny** | allow with auditor approval |

## Detection action codes

- **redact** — replace the matched token with `[REDACTED:<class>]` and continue.
- **deny** — refuse the action; emit `shadow.classification.denied` (or `gateway.classification.denied`) audit event with class + count of redactions; return no model output for this turn.
- **allow** — pass through unchanged.
- **hash-redact** — replace with `sha256(value)[:12]` so logs preserve correlation but not the underlying value.

## Override path

A documented override header (`X-Foundry-Carveout-Override: <case_id>`) is permitted only when `case_id` matches an approval record in Cosmos `carveout_overrides`. Each override is page-routed to the Security Engineer.

## Review cadence

Quarterly review by Compliance Auditor + Security Engineer; classifier rules versioned alongside `packages/prompts/` (per ADR-035 review cadence).

## References

- Constitution Non-Negotiable #2 (Data sovereignty + Foundry carve-out)
- Australian PSPF: <https://www.protectivesecurity.gov.au/>
- ADR-033 — Phi shadow boundary
- Microsoft Presidio: <https://github.com/microsoft/presidio>

---
*Author: Security Engineer + Compliance Auditor + AI/ML Engineer personas via spec-032 Stream-0. Date: 2026-04-30.*
