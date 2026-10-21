# Review Ledger — specs/004-actor-github-agents

## Purpose

This ledger records review evidence classes for this feature without retroactively asserting historical execution that is not evidenced.

## Evidence Classes

| Class | Definition | Automation level |
| --- | --- | --- |
| Structural review | Static checks on document shape, links, identifiers, and contract-required headings/fields. | Automatable |
| Secret-content/source inspection | Static source-text inspection for prohibited content indicators (secrets/PII/live payload patterns) without runtime scanners. | Automatable |
| Semantic review | Human interpretation of requirement meaning, scope boundaries, and claim correctness beyond structure. | Human-led |
| Live evaluation | Executed scenario/test/survey/timed exercises with run artefacts and measured outcomes. | Human + execution evidence |
| Formal signoff | Named approver attestation with authority scope and date. | Human-only |

## Ledger Entries

| Date (UTC) | Scope | Class | Method | Checked artefacts | Outcome | Limitations | Reviewer | Approval evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-15 | AUD-023/AUD-024/AUD-025 truth-correction and scaffolding | Structural review | Static file update + feature-scoped lint rules | `spec.md`, `plan.md`, `checklists/requirements.md`, `implementation-review-tasks.md`, `evidence/HYP-042.md`, `specs/shared/gap-id-register.md` | Complete for documentation truth-correction scope | Does not prove historical T038-T042 execution and does not constitute live evaluation/signoff | GitHub Copilot (orchestrated remediation) | None |
| 2026-09-15 | FR-010 compatibility check in current static corpus | Secret-content/source inspection | Source-only textual inspection findings carried forward from scoped review context | `.github/agents/**` static text references in feature review context | No prohibited payload identified in cited static findings | Not a rerun of historical scanners and not equivalent to original T042 execution artefact | GitHub Copilot (source inspection only) | None |
| 2026-09-15 | Constitutional and measurable-claim restatement | Semantic review | Claim-by-claim dispositioning in checklist and plan gate restatement | `checklists/requirements.md`, `plan.md` | Claims reclassified as Supported/Unverified/Incorrect as written where applicable | Requires later human acceptance review for final signoff | GitHub Copilot (draft reviewer) | None |
| 2026-09-15 | SC-003..SC-006 and persona validation outcomes | Live evaluation | Not executed in this remediation | N/A | Unverified | External measurement and participant/SME involvement required | N/A | None |
| 2026-09-15 | Amendment approval for validated persona/consultation claims | Formal signoff | Not executed in this remediation | N/A | Unverified | Named SME/practitioner and authority_scope countersign still required | N/A | None |
