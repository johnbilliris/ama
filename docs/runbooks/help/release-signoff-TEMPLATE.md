# Release Sign-Off — spec-038 In-Product Help Documentation & Grounded Chat Assistant (TEMPLATE)

> FR-011b dual-approval gate. Fill at release time; commit signed copy.

## Release info
- Release tag: TBD
- Date: TBD (UTC)
- Snapshot id: TBD
- Bicep build: clean (`az bicep build` on every help module)
- Pytest: 86/86 passing (contract + integration + unit + llm-eval)
- Ruff: clean
- TypeScript: `tsc --noEmit` clean on `apps/web`

## Pre-launch gates
- [ ] T-AA219 `azd up` smoke captured at `docs/runbooks/help/azd-up-smoke-{date}.log`
- [ ] T-AA221 SC-001 task-based usability test (≥20 participants)
- [ ] T-AA222 SC-002 LLM-eval gates against live Foundry agent
- [ ] T-AA223 SC-003 fabrication audit sample
- [ ] T-AA224 SC-004 + SC-010 + SC-011 verification
- [ ] T-AA225 SC-005..008 + SC-012 verification
- [ ] T-AA218 AU-residency attestation at `docs/attestations/help-{release}.json`
- [ ] T-AA220 CHK001–CHK136 walked; code-evidence ticks recorded; deferred items signed off

## Approvers (FR-011b — both required; must be distinct identities)
- [ ] **Help content owner** — name / IdP id / signature ts: ________
- [ ] **Safety lead OR Governance lead** — name / IdP id / signature ts: ________

## Sign-off audit
On commit, the workflow MUST emit:
```
audit.help_release_signoff_recorded
```
with both approver identities, release tag, and snapshot id.

## Rollback authority
If post-launch monitoring trips a Sev1 alert (see
`docs/runbooks/help/metric-alerts.md`), on-call may execute rollback
without re-collecting both signatures (FR-011c emergency procedure).
Post-incident review must record the rollback in a follow-up sign-off.
