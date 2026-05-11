# spec-038 CHK Verification Status (T-AA220)

> Walk of `checklists/feature.md` CHK001–CHK136. An item is ticked only
> when **codebase evidence** is linkable (test file, audit emit site,
> module). Items that require participants, live telemetry, real
> screenshots, or running infrastructure are marked
> **[deferred-to-operator]** and must be verified at release sign-off.

## Code-evidence ticks

| CHK | Evidence |
|---|---|
| CHK001-CHK010 (operational persona landing + chat wiring) | `apps/web/src/app/help/persona/[id]/page.tsx`, `apps/api/app/services/help/persona_resolver.py`, `tests/integration/help/test_persona_resolution.py` |
| CHK011-CHK016 (sector cluster landings) | `apps/web/src/app/help/cluster/[id]/page.tsx`, persona fixtures in `data/help/personas/` |
| CHK017-CHK030 (article structure / 5 sections / workflow) | `tools/help/generate_phase5_content.py`, MDX files under `data/help/articles/` |
| CHK040-CHK048 (a11y / lang attr) | `tests/contract/help/test_lang_attr_lint.py`, `tools/help/lint_lang_attributes.py`, `tools/help/rehype_lang_attr.ts` |
| CHK045-CHK046 (PII redaction notice) | `tests/integration/help/test_pii_redaction_notice.py`, `apps/agents/help_assistant/agent.py` |
| CHK065 (snapshot dual-approval) | `tests/contract/help/test_snapshot_record_dual_approval.py`, `tests/contract/help/test_codeowners_dual_approval.py` |
| CHK067 (deprecation notice) | `tests/integration/help/test_deprecation_notice.py`, `apps/api/app/services/help/deprecation_resolver.py` |
| CHK074 (screen_id_hash determinism) | `tests/contract/help/test_screen_id_hash.py`, `packages/domain/src/ama_domain/screen_id_hash.py` |
| CHK076 (staleness backlog grace) | `docs/runbooks/help/screenshot-staleness.md`, `tools/help/check_screenshot_freshness.py` |
| CHK097-CHK101 (tenant isolation) | `tests/integration/help/test_tenant_isolation.py`, `tests/contract/help/test_retrieval_filters_tenant.py` |
| CHK113 (no auto-silencing) | `tests/integration/help/test_negative_feedback_no_silencing.py`, `apps/api/app/services/help/feedback_aggregator.py` |
| CHK119 (transcript reconstruction audit) | `tests/integration/help/test_transcript_reconstruction.py`, `apps/api/app/services/help/transcript_reconstructor.py` |
| CHK122-CHK125 (support handoff config + SLA) | `docs/configuration/help-support-handoff.md`, `tests/integration/help/test_support_handoff_sla.py` |
| CHK128 (incident response runbook) | `docs/runbooks/help/on-call.md` |
| CHK131-CHK134 (persona resolution / authority rank) | `tests/integration/help/test_persona_resolution.py`, `packages/domain/src/ama_domain/authority_rank_registry.py` |
| CHK139-CHK142 (degraded mode) | `tests/integration/help/test_degraded_mode.py`, `apps/web/src/lib/help/degradedModeDetector.ts` |

Approximate **code-evidence count: 60 / 136**.

## Deferred-to-operator (76)

The remaining items require one or more of:
- ≥20 participants for SC-001 task-based usability test (CHK176-CHK183).
- Live App Insights telemetry (CHK150-CHK155, SC-007).
- Real screenshots captured via Playwright on a deployed environment
  (CHK070-CHK075, T-AA176).
- Live azd-deployed environment (most "verified" tags).
- Quarterly chaos drill execution (CHK runbook items).

These MUST be walked at release sign-off (T-AA226) by the help-content
owner and a safety/governance lead, and the corresponding CHK rows
ticked in `checklists/feature.md` at that time.

## SC verification table (T-AA221–T-AA225)

| SC | Status | Evidence / Plan |
|---|---|---|
| SC-001 | [deferred-to-operator] | ≥20 participant usability test post-deploy. |
| SC-002 | partial code-evidence | LLM-eval harness wired at `tests/llm-eval/help/`; gate run against deployed Foundry agent. |
| SC-003 | [deferred-to-operator] | Fabrication audit on `chat_audit_log` sample post-launch. |
| SC-004 | code-evidence | `test_tenant_isolation.py`, retrieval filter hard-coded in `apps/agents/common/retrieval_client.py`. |
| SC-005 | partial | Screenshot inventory generator wired; live capture runbook authored. |
| SC-006 | partial | a11y stubs in `apps/web/__tests__/e2e/help/accessibility-axe-scan.spec.ts`; needs Playwright browsers. |
| SC-007 | [deferred-to-operator] | App Insights workbook `help-slis`, see `docs/runbooks/help/app-insights-workbook.md`. |
| SC-008 | [deferred-to-operator] | Participant 15-min tour completion test. |
| SC-009-AMEND | template captured | `specs/038-help-docs-chat/baselines/pre-launch-support.md`. |
| SC-010 | code-evidence | Append-only enforced in `apps/api/app/repositories/help_repositories.py::APPEND_ONLY`. |
| SC-011 | code-evidence + runbook | `docs/attestations/README.md`, AU region asserts in Bicep. |
| SC-012 | code-evidence | Staleness check `tools/help/check_screenshot_freshness.py`. |
