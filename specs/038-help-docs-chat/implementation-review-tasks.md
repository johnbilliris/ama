# Spec 038 Static Implementation Audit

## Review Metadata

- Review date: 2026-09-14.
- Expected and observed HEAD: `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a` (read-only revision check).
- Scope: only Spec 038, its local requirements and associated implementation dependencies.
- Sole writable artifact: this report. No other implementation-review report was consulted.
- Method: fresh static source, content, configuration, test-assertion and evidence inspection.
- Execution boundary: no product tests, builds, imports, generators, model calls, browsers, servers,
  cloud operations, installations, deployments or external approvals. Commands below are future-only.
- Contract and primary inputs: [Review Contract](../001-spec-implementation-audit/README.md#L1),
  [review instructions](../../.github/instructions/code-review.instructions.md#L1),
  [specification](spec.md#L1), [original tasks](tasks.md#L1), [plan](plan.md#L1).
- Applicable guidance read: code-commenting instructions and Python fact-grounded-coding skill.
  Static observations establish control flow, not runtime outcomes or deployed security posture.
- No existing report was present at the start. Original task completion marks remain unchanged.

## Static Audit Result

This is not a release-ready implementation on static evidence: eight Critical and fourteen Important
findings produce 22 open remediation tasks. Positive authored work is preserved: existing Help
navigation/shared chat shell, sixteen persona texts/fourteen screen texts/six playbooks/nine general
articles, selected models/ordered hash helpers, parameterized tenant queries, container/TTL declarations
and a seven-query workbook. None substitutes for their missing active safety/integration controls.

Original-task assessment: 14 IMPLEMENTED, 157 PARTIAL, 17 MISSING, 21 CONFLICT, 17 UNVERIFIED
(226 total; all originally checked). Coverage includes 51 FR clauses, twelve SCs plus SC-009-AMEND,
twenty acceptance scenarios, five independent-test duties, ten edges, 136 feature checklist items,
28 quality-checklist items and seventeen technical-persona review duties. No standalone NFR IDs exist;
forty other nonfunctional/scope rows, all named content domains/screens, data/API/telemetry/risk and
review-resolution tables make those obligations explicit. No whole-feature obligation was retired.

Security, content correctness, complete publication/grounding/audit/offline delivery and honest
verification are release blockers. Runtime/model quality, performance, a11y conformance, deployment,
residency and human approval outcomes remain UNVERIFIED until separately authorized evidence exists.

## Evidence Status Rules

`IMPLEMENTED` means the inspected authored behavior is supported, not that it has executed successfully.
`PARTIAL` identifies a concrete remaining obligation. `MISSING` requires a bounded relocated-behavior search.
`CONFLICT` requires an explicit resolution. `UNVERIFIED` covers execution, measurement and approval claims
without sufficient records. `SUPERSEDED` requires explicit repository authority; absence alone is not retirement.

## Findings

### F01 - Critical: Help identity and active persona can differ from authenticated claims

The Help dependency initializes identity from caller-supplied headers and consults authenticated state
only as a fallback: [help_deps.py](../../apps/api/app/api/routes/help_deps.py#L39).
The web proxy forwards identity headers and injects `live` / `anonymous` defaults without an environment
guard: [proxy route](../../apps/web/src/app/api/help/[...path]/route.ts#L46).
The chat route then accepts `body.persona_id` directly, with no entitlement check in the handler:
[chat_ask](../../apps/api/app/api/routes/help_chat.py#L60).
The [Entra protected prefixes](../../apps/api/app/middleware/entra_auth.py#L37) and
[RBAC protected prefixes](../../apps/api/app/middleware/rbac_check.py#L32) exclude Help, while
[general authentication](../../apps/api/app/middleware/auth_middleware.py#L11) supplies anonymous claims.
FR-019, FR-025, FR-027 and FR-028 are not enforced at this application boundary. External ingress
sanitisation is unverified, not assumed. Follow-up: AUD-038-001.

### F02 - Critical: Snapshot approval trusts user-supplied role labels

[Publication](../../apps/api/app/api/routes/help_snapshots.py#L25) accepts approver strings without
verified membership, per-approval timestamps or binding to reviewed content. The
[workflow](../../.github/workflows/help-snapshot.yml#L41) supplies author/secret identities rather
than checking two qualifying reviews. [CODEOWNERS](../../.github/CODEOWNERS#L47) lists two teams;
that is not evidence that both approved. The [release template](../../docs/runbooks/help/release-signoff-TEMPLATE.md#L36)
also asserts an emergency rollback waiver absent from the binding plan/task dual-signoff rule.
This is a conflict to resolve, not accepted supersession. FR-011b and the plan's publish/rollback
human-authority gate remain unsatisfied. Follow-up: AUD-038-002.

### F03 - Critical: Published-snapshot provenance does not control delivered content

[HTTP publication](../../apps/api/app/api/routes/help_snapshots.py#L82) appends metadata and
[rollback](../../apps/api/app/api/routes/help_snapshots.py#L96) emits an event without switching Search.
The [indexer](../../apps/api/app/services/help/snapshot_indexer.py#L16) is in-memory and the
[ingester](../../apps/ingest-runner/src/help_snapshot/__main__.py#L14) discards chunks; the
[alias helper](../../apps/ingest-runner/src/help_snapshot/alias_swinger.py#L22) writes local JSON.
The [loader](../../apps/ingest-runner/src/help_snapshot/source_loaders.py#L25) defaults missing
status/classification/tenant to Active/OFFICIAL/global and ignores tenant exclusions. Markdown
Draft status is not the YAML metadata it reads. Meanwhile the active
[seed projection](../../scripts/seed_loader.py#L441) makes current MDX globally published, and
[upserts it](../../scripts/seed_loader.py#L515) outside approval. The
[reader](../../apps/api/app/repositories/help_repositories.py#L238) has no snapshot/status guard;
[active resolution](../../apps/api/app/repositories/help_repositories.py#L193) selects the first
active row, not the alias or newest version. These are concrete FR-011/FR-019 violations, not
absence inferred from historical filenames. Follow-up: AUD-038-003.

### F04 - Critical: The active answer path bypasses required safety and grounding controls

The [live entrypoint](../../apps/agents/help_assistant/agent.py#L50) raises `NotImplementedError`.
The connected [Cosmos path](../../apps/agents/help_assistant/agent.py#L359) token-ranks up to 200
Help articles; persona is only a boost, jurisdiction is not a retrieval restriction, and neither
classification, scope refusal, conflict handling nor observer action filtering controls the extracts.
It does not retrieve the approved AIDR/corpus/spec sources. Common retrieval/citation helpers and
authored prompts do not prove connection. An out-of-scope question sharing article vocabulary can
receive an extract; no runtime refusal rate is claimed. Follow-up: AUD-038-004.

### F22 - Critical: The Australian gateway bypass defeats mandatory Help redaction

[Help's region default](../../apps/api/app/api/routes/help_chat.py#L35) is `australiaeast` and its
[gateway call](../../apps/api/app/api/routes/help_chat.py#L71) uses that region. The shared
[gateway](../../apps/agents/common/model_gateway.py#L198) returns original text for AU regions
before PII/PSPF checks. The [agent heuristic](../../apps/agents/help_assistant/agent.py#L331)
only masks whole messages containing `@` or a digit in a sufficiently long message: names and
addresses without those triggers survive, while harmless numeric workflow questions can lose all
content. This directly violates FR-017 and research section E; AU residency is not a redaction waiver.
The deny branch in F05 is relevant when a configured region reaches denial, not a claim that the
default AU path currently denies. Follow-up: AUD-038-022.

### F05 - Critical: Audit receipts and transcript privacy are not durable end to end

The deny branch emits telemetry and immediately returns an SSE stream containing a new UUID:
[deny branch](../../apps/api/app/api/routes/help_chat.py#L72).
It never reaches the later append-to-repository block:
[durable-write branch](../../apps/api/app/api/routes/help_chat.py#L174).
Consequently that branch does not establish the FR-020 / SC-010 append-only, reconstructable record
of redacted input, response, refusal reason and citations. An invented `audit_entry_id` is not a durable receipt.
Successful streaming emits `done` before persistence, passes the record through mutable function
attributes, always uses turn zero, and does not call the session upsert. The
[repository](../../apps/api/app/repositories/help_repositories.py#L103) silently falls back to
volatile memory for missing Cosmos containers. The [browser store](../../apps/web/src/lib/help/chatStore.tsx#L56)
persists raw drafts/prompts under a tab-wide key without identity/retention boundaries. The
[reconstructor](../../apps/api/app/services/help/transcript_reconstructor.py#L1) is not an authorized
audit-tooling endpoint. Retention declarations are not automatic-purge or reconstruction evidence.
Follow-up: AUD-038-005.

### F06 - Critical: Authored guidance misstates doctrine and approval rights

The [Principle V article](../../apps/web/src/content/help/articles/constitution-principle-v.mdx#L29)
labels invented decision-rights text as verbatim; the
[constitution](../../.specify/memory/constitution.md#L76) actually requires Warning and Public Information.
[PIO guidance](../../apps/web/src/content/help/personas/public-information-officer/landing.mdx#L31)
and the [Composer article](../../apps/web/src/content/help/articles/screen-by-screen/alert-composer.mdx#L177)
make IC approval conditional, unlike the [PIO role](../../.github/agents/operational/public-information-officer.agent.md#L22).
The [Evacuation playbook](../../apps/web/src/content/help/articles/playbooks/agent-evacuation.mdx#L115)
omits the required IC chain; [Executive guidance](../../apps/web/src/content/help/personas/executive-leader/landing.mdx#L80)
substitutes Executive/Risk Manager for the Help-owner/safety approval pair.
[Observer guidance](../../apps/web/src/content/help/articles/observer-mode-guide.mdx#L156) restricts
questions and [extends grounding to live audit rows](../../apps/web/src/content/help/articles/observer-mode-guide.mdx#L221).
[Risk calibration advice](../../apps/web/src/content/help/articles/playbooks/agent-risk-assessment.mdx#L174)
lowers the green threshold in response to alleged overconfidence, contradicting its band semantics.
These are authored-content defects independently of model quality. Follow-up: AUD-038-006.

### F16 - Critical: Declared infrastructure does not enforce immutable or AU-only data paths

The [API identity grant](../../infra/main.bicep#L894) is account-wide Cosmos Data Contributor,
defeating application-only insert restrictions. The [storage parent](../../infra/main.bicep#L493)
enables public networking and seven-day soft delete, without the claimed CMK/private-endpoint/90-day
configuration. Required web/ingest-runner grants and Search root wiring are absent in the scoped
IaC inventory. [Shared model configuration](../../infra/main.bicep#L1377) permits GlobalStandard;
an AU resource location alone does not prove AU processing. The
[attestor](../../tools/help/attest_au_residency.py#L42) misses shared dependencies and passes an empty
inventory. Deployed effective permissions and residency remain unverified. Follow-up: AUD-038-016.

### F07 - Important: Rich prose does not cover every required workflow

All 45 MDX files were read, including sixteen persona landings, fourteen screen articles, six
playbooks and nine general articles. The content matrix below records named omissions, including
reassignment, staging, SITREPs, supply tracking, observation/lessons export, Auslan/checker use and
simulation reset. The [glossary](../../apps/web/src/content/help/glossary/terms.yaml#L1) has five terms
and lacks canonical AIIMS Controller. The approximate 250-article/600-term plan estimates are not
treated as exact quotas. Follow-up: AUD-038-007.

### F08 - Important: Navigable Help does not resolve entitled persona or contextual content

[Global navigation](../../packages/ui/src/components/layout/app-shell.tsx#L1) and shared chat mounts
exist, but the [landing](../../apps/web/src/app/help/page.tsx#L222) is generic and the
[layout](../../apps/web/src/app/help/layout.tsx#L31) uses `operational-default`. Tiles, tour, persona
hook and surface-map parser have no active consumers. The [hook's rank sort](../../apps/web/src/lib/help/personaContext.ts#L40)
opposes the [registry](../../packages/domain/src/ama_domain/authority_rank_registry.py#L16).
The relocated [catch-all article route](../../apps/web/src/app/help/articles/[...slug]/page.tsx#L33)
passes nested slugs to a [single-segment API route](../../apps/api/app/api/routes/help_articles.py#L35).
[Glossary](../../apps/web/src/app/help/glossary/[term]/page.tsx#L2) and
[playbook](../../apps/web/src/app/help/playbooks/[id]/page.tsx#L2) pages echo parameters rather than content.
Follow-up: AUD-038-008.

### F09 - Important: Citation and SSE presentation do not preserve required meaning

The [agent emits bare anchors](../../apps/agents/help_assistant/agent.py#L307), while
[CitationBadge](../../apps/web/src/components/help/CitationBadge.tsx#L10) concatenates without `#`.
[Rendering](../../apps/web/src/app/help/articles/[...slug]/page.tsx#L68) lacks a heading-ID plugin.
[ChatPanel](../../apps/web/src/components/help/ChatPanel.tsx#L137) appends badges after plain text,
not at each factual claim. Conflict/deprecation components are unconnected. The
[store](../../apps/web/src/lib/help/chatStore.tsx#L154) overwrites redaction state on the agent's
second `meta`, ignores completion/session metadata and sends no session ID. Follow-up: AUD-038-009.

### F10 - Important: Screenshot capture, freshness and reader warnings are disconnected

No tracked Help image, alt sidecar or captured registry was found in the bounded asset inventory;
MDX uses [screenshot comments](../../apps/web/src/content/help/articles/screen-by-screen/disaster-mapper.mdx#L26),
not images. [Capture](../../tools/help/capture_screenshots.ts#L18) expects an absent JSON registry,
can emit one-pixel placeholders, and does not upload/hash/register assets. The
[checker](../../tools/help/check_screenshot_freshness.py#L33) passes strings to a
[Callout-based hasher](../../packages/domain/src/ama_domain/screen_id_hash.py#L23); hashing selector
paths is not fingerprinting the live DOM. The [registry](../../tools/help/route_registry.py#L19)
covers eight routes. The [unused component](../../apps/web/src/components/help/AnnotatedScreenshot.tsx#L40)
follows OS theme, not the active app theme. [Signed URLs](../../apps/api/app/api/routes/help_screenshots.py#L65)
contain `sig=placeholder`; [flag storage](../../apps/api/app/repositories/help_repositories.py#L269)
targets an unprovisioned container. Follow-up: AUD-038-010.

### F11 - Important: Offline Help is helper-only, not available reader behavior

[Cache](../../apps/web/src/lib/help/offlineCache.ts#L34),
[detector](../../apps/web/src/lib/help/degradedModeDetector.ts#L18) and
[registration](../../apps/web/src/lib/help/sw-register.ts#L2) are unconnected. The requested worker
does not exist; the [existing worker](../../apps/web/public/offline-sw.js#L8) is pass-through.
There is no mandatory glossary/FAQ preload, shared-budget enforcement, aged-copy date banner,
cached-subset search or audit-logged refresh; chat is not disabled through the detector.
Follow-up: AUD-038-011.

### F12 - Important: Search omits article bodies and confuses no-match with offline

[Scoring](../../apps/api/app/api/routes/help_search.py#L22) searches term/title/summary from a
bounded 200-row set, not bodies or canonical aliases. The
[page](../../apps/web/src/app/help/search/page.tsx#L51) shows cached-results wording for any empty
result list without reading a cache. Follow-up: AUD-038-012.

### F13 - Important: Feedback never reaches rolling-pattern review promotion

[FeedbackBar](../../apps/web/src/components/help/FeedbackBar.tsx#L15) confirms success without
checking HTTP status; comments and per-chat-turn controls are absent. The
[facade](../../apps/api/app/repositories/help_repositories.py#L215) creates independent pending rows
without timestamp/pattern aggregation. The [agent's intent ID](../../apps/agents/help_assistant/agent.py#L407)
uses process-randomized truncated `hash`, not a persistent semantic cluster. The ordered SHA-256
helper is supported, but cannot repair this upstream identity. Follow-up: AUD-038-013.

### F14 - Important: Human handoff and acknowledgement monitoring are not operational

[RefusalCard](../../apps/web/src/components/help/RefusalCard.tsx#L12) offers prose only;
[SupportHandoffButton](../../apps/web/src/components/help/SupportHandoffButton.tsx#L12) is unmounted
and hides on errors. The [API](../../apps/api/app/api/routes/help_support_handoff.py#L16) uses a
different record shape, returns 404 when missing, and has no local admin guard. The
[SLA helper](../../apps/api/app/services/help/support_handoff_sla_monitor.py#L1) is not a scheduled
NEMA-driven acknowledgement workflow. Follow-up: AUD-038-014.

### F15 - Important: Models, package exports and public DTOs drift without detecting it

[Twin tests](../../tests/contract/help/test_domain_twin_sync.py#L49) compare names, not field schemas.
The [domain export map](../../packages/domain/package.json#L9) lacks `./help`; the
[agent wheel](../../apps/agents/pyproject.toml#L59) omits `help_assistant` despite test source-path
injection. [Article validation](../../packages/domain/src/ama_domain/help_article.py#L60) misses
relational constraints; [language validation](../../packages/domain/src/ama_domain/glossary_term.py#L12)
is not complete BCP-47 validation. Help wire citations differ from reused doctrine Citation.
The [support PUT](../../apps/api/app/api/routes/help_support_handoff.py#L40) neither reads nor checks
`If-Match`, so concurrent configuration updates can overwrite one another. Article listing does
default to the caller persona, but its [continuation](../../apps/api/app/api/routes/help_articles.py#L24)
is ignored and always returned as null. Follow-up: AUD-038-015.

The mounted [error handler](../../apps/api/app/middleware/error_handler.py#L135) supplies legacy
`correlationId`/status/category fields and stringifies `HTTPException.detail`; it is not the declared
Help `code`/`message` schema or task's `correlation_id` envelope. Correlation is present, but the
contract shape and machine-readable Help code are not preserved.

### F17 - Important: Operational dashboards and runbooks lack working producers and alarms

The [workbook](../../infra/bicep/modules/help-app-insights-dashboard.bicep#L27) is authored, but
matching Help metric producers/alert resources were not found. The
[monitoring configuration](../../infra/modules/monitoring.bicep#L21) is not 30-day hot/7-year archive.
[Runbook thresholds](../../docs/runbooks/help/metric-alerts.md#L3) drift from tasks, and the
[chaos drill](../../docs/runbooks/help/chaos-drill-snapshot-rollback.md#L9) changes key authentication
rather than faulting alias publication. Follow-up: AUD-038-017.

### F18 - Important: Authoring and CI gates do not run or fail closed as specified

[Help gates](../../.github/workflows/help-gates.yml#L3) are manual-only and skip missing inputs.
[test:help](../../package.json#L8) omits browser/evaluation coverage and is not the required CI gate.
[Packaging](../../apps/ingest-runner/pyproject.toml#L48) excludes the new mode; manifests omit
specified build tools. [Language lint](../../tools/help/lint_lang_attributes.py#L41) accepts an
unrelated matching attribute anywhere in the file; the plugin is unbound. The
[link checker](../../tools/help/link_checker.py#L37) strips anchors rather than validating headings.
Follow-up: AUD-038-018.

### F19 - Important: Test and evaluation names overstate meaningful assertion coverage

All six [Help browser suites](../../apps/web/__tests__/e2e/help/chat-citation-flow.spec.ts#L7) are
unconditionally skipped title checks. [OpenAPI assertions](../../tests/contract/help/test_help_api_openapi.py#L27)
check paths, not response contracts; [degraded tests](../../tests/integration/help/test_degraded_mode.py#L47)
accept success. The [promotion test](../../tests/integration/help/test_negative_feedback_no_silencing.py#L53)
counts rows, not promoted status. Six single-row fixtures and
[shape-only evaluation](../../tests/llm-eval/help/test_eval_cite_or_refuse.py#L31) cannot establish
200-case grounded quality, refusal rates, persona tailoring or fabrication audits.
Follow-up: AUD-038-019.

### F20 - Important: Checked tasks and review claims are not release evidence

The [ledger](verification-status.md#L30) estimates 60 checked checklist items; the actual inventory
is 45 checked and 91 unchecked. Its CHK meanings drift. The
[baseline](baselines/pre-launch-support.md#L39) is unfilled and replaces SC-009's 40% ticket-volume
reduction over three months with a different TTR target. The
[sign-off](../../docs/runbooks/help/release-signoff-TEMPLATE.md#L24) and
[cultural consultation](../../docs/cultural-authority/help/INDEX.md#L8) remain templates/TBD.
No checked state retires a required execution, approval or measurement. Follow-up: AUD-038-020.

### F21 - Important: Accessible primitives do not establish complete Help interaction

The shortcut exists only in the unused [HelpAffordance](../../apps/web/src/components/help/HelpAffordance.tsx#L8).
The active [dock](../../apps/web/src/components/help/HelpAssistantDock.tsx#L29) handles Escape but
lacks the required focus transfer/restoration/trap. [Close controls](../../apps/web/src/app/globals.css#L3875)
and [quick actions](../../apps/web/src/app/globals.css#L3275) do not establish the contracted target size;
Help transitions lack a reduced-motion override. Visible outlines and `role=log` are positive source
evidence, not measured WCAG 2.2 AA conformance. Follow-up: AUD-038-021.

Findings are severity-ordered above; their stable identifiers retain the order of discovery.

## Remediation Tasks

These are future developer/tester instructions, not actions performed by this audit. All are open.
Common prerequisites for future executable checks: explicitly authorized implementation/testing,
already prepared locked dependencies, isolated test storage, synthetic identities/content, and no
production credentials. `uv run --no-sync` assumes the prepared interpreter; it does not authorize
installation here. Browser commands require separately authorized servers/browsers. Cloud/model,
human-review and cohort activities require separate authorization. Current stubs/skips are not a pass.
Every named tester file below exists; a new case within it is proposed test work, not existing evidence.

- [ ] AUD-038-001 Enforce verified Help identity and persona authorization

  **Trace:** FR-019, FR-025, FR-027, FR-028; T-AA058, T-AA072, T-AA077, T-AA082, T-AA083; F01.
  **Expected / actual / impact:** Verified principal tenant/user and entitled active role must control
  every route; headers/defaults presently override them, enabling unauthorized data/control access.
  **Developer:** Own [help_deps](../../apps/api/app/api/routes/help_deps.py#L21),
  [proxy](../../apps/web/src/app/api/help/[...path]/route.ts#L23), middleware prefix policies and SSR
  loaders. Reuse validated MSAL/Entra claims, ignore spoofable identity headers, deny missing claims,
  validate jurisdictions and override membership. Require author/admin roles for snapshot, screenshot
  and support writes. Fix resolver fallback that adds the requested override to the entitled set.
  Preserve existing authenticated route compatibility; do not expand observer decision rights.
  **Tester:** Extend [tenant isolation](../../tests/integration/help/test_tenant_isolation.py#L42),
  [persona resolution](../../tests/integration/help/test_persona_resolution.py#L8) and
  [route smoke](../../tests/contract/help/test_help_routes_smoke.py#L33) using the full middleware stack.
  Assert valid access; forged same/foreign-tenant headers, anonymous, revoked roles, empty entitlement
  sets and foreign jurisdictions yield 401/403 before reads/writes; all write routes deny observers.
  **Future command:** `uv run --no-sync pytest tests/integration/help/test_tenant_isolation.py tests/integration/help/test_persona_resolution.py tests/contract/help/test_help_routes_smoke.py -q`.
  **Done:** Removing any principal/entitlement guard breaks a negative assertion; no identity defaults
  survive outside explicit test fixtures. Depends on AUD-038-015 for consistent boundary DTOs.

- [ ] AUD-038-002 Bind publication and rollback to two authenticated approvals

  **Trace:** FR-011a, FR-011b, FR-011c; T-AA008, T-AA039, T-AA053, T-AA074, T-AA163, T-AA164,
  T-AA166, T-AA167, T-AA226; F02.
  **Expected / actual / impact:** Two distinct qualified humans approve exact source bytes; current
  strings/team tokens can assert approval without review, undermining safety provenance.
  **Developer:** Own [snapshot routes](../../apps/api/app/api/routes/help_snapshots.py#L25),
  [publisher](../../apps/api/app/services/help/snapshot_publisher.py#L40),
  [workflow](../../.github/workflows/help-snapshot.yml#L41) and existing ownership policy. Verify
  authority/membership, non-revoked reviews and timestamps against immutable manifest digest/version;
  persist both approvals and expose them in chat audit provenance. Apply the same gate on rollback,
  preserving previously approved snapshots rather than rewriting them. Depends on AUD-038-001/003.
  Resolve the release template's emergency waiver explicitly with authorized governance; do not
  treat an unapproved template sentence as permission to bypass the binding publication gate.
  **Tester:** Extend [dual approval](../../tests/contract/help/test_snapshot_record_dual_approval.py#L23)
  and [CODEOWNERS tests](../../tests/contract/help/test_codeowners_dual_approval.py#L17). Synthetic
  reviews cover one from each team, same person twice, unqualified author, dismissed/stale approval,
  changed content after review, missing timestamps and unapproved rollback; assert no publish effect.
  **Future command:** `uv run --no-sync pytest tests/contract/help/test_snapshot_record_dual_approval.py tests/contract/help/test_codeowners_dual_approval.py -q`.
  **Done:** Exact reviewed digest plus both identities/timestamps are persisted and auditable;
  CODEOWNERS presence alone cannot satisfy the gate. Actual sign-off remains separate human evidence.

- [ ] AUD-038-003 Connect one immutable approved-snapshot publication and retrieval path

  **Trace:** FR-011, FR-011-AMEND, FR-011a, FR-011c, FR-011d, FR-011d-AMEND, FR-019;
  T-AA009, T-AA014, T-AA028, T-AA053, T-AA054, T-AA061, T-AA063, T-AA074, T-AA086, T-AA087,
  T-AA088, T-AA089, T-AA164, T-AA165, T-AA168, T-AA169, T-AA170, T-AA172; F03.
  **Expected / actual / impact:** Readers resolve approved immutable content; current metadata-only
  publication, local alias files and current-MDX seeding bypass the gate and cannot roll back guidance.
  **Developer:** Own [loader](../../apps/ingest-runner/src/help_snapshot/source_loaders.py#L25),
  [embedder](../../apps/ingest-runner/src/help_snapshot/embedder.py#L63),
  [indexer](../../apps/api/app/services/help/snapshot_indexer.py#L16),
  [CLI](../../tools/help/publish_snapshot.py#L33), seeding and article/snapshot readers. Parse actual
  Markdown status, fail closed on missing metadata, honor explicit approved membership and tenant
  exclusions; only global doctrine is shared. Use the existing embedder's real interface, correct
  `body_vector`/body/tag schema and nonzero vectors; do not turn embedding failure into zero vectors.
  Create/upload/health-check before atomic alias switch; idempotency binds snapshot/source/hash.
  Prevent mutable seed bypass, resolve the actual active target, publish replacement/withdrawal maps,
  and preserve old provenance. Depends on AUD-038-001/002/015/016/018.
  **Tester:** Extend [publication](../../tests/integration/help/test_snapshot_publish_rollback.py#L25),
  [deprecation](../../tests/integration/help/test_deprecation_notice.py#L8) and tenant tests. Fixtures:
  YAML and Markdown Draft/missing/Active status, changed digest, global doctrine versus Help/spec rows,
  tenant exclusions, zero vectors, upload/health failure, repeated publish, competing publishes,
  rollback and withdrawal without replacement. Assert real client calls/order and no old-target loss.
  **Future command:** `uv run --no-sync pytest tests/integration/help/test_snapshot_publish_rollback.py tests/integration/help/test_deprecation_notice.py tests/integration/help/test_tenant_isolation.py -q`.
  **Done:** Both HTTP and CLI use one tested pipeline; denied/failed publication leaves the prior
  index readable. An authorized staging rehearsal separately proves restoration within 300 seconds.

- [ ] AUD-038-004 Connect approved-corpus grounding and enforce output safety

  **Trace:** FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-018, FR-019, FR-025;
  T-AA062, T-AA064, T-AA065, T-AA066, T-AA067, T-AA068, T-AA069, T-AA084, T-AA091; F04.
  **Expected / actual / impact:** A retrieval-only AU agent must answer from approved scoped sources,
  refuse unsupported questions and tailor safe actions; live entrypoint is a stub and token overlap
  permits unrelated or unauthorized instructions. Offline extracts are not an approved replacement.
  **Developer:** Own [agent](../../apps/agents/help_assistant/agent.py#L50),
  [chat handler](../../apps/api/app/api/routes/help_chat.py#L154), common retrieval/citation adapters
  and [conflict helper](../../apps/api/app/services/help/conflict_surfacer.py#L15). Reuse existing
  clients; restrict tools to approved retrieval, enforce tenant/global-doctrine classification and
  active-role/jurisdiction boundaries before generation, validate every claim against returned chunks,
  distinguish out-of-scope/cross-tenant/no-match/refusal, and surface contradictory sources with both
  citations plus human verification. Permit observer questions but prohibit modifying-action advice.
  Empty/unhealthy snapshot must produce specified unavailable behavior, not a guessed answer.
  Depends on AUD-038-001/003/006/009/016/022; no arbitrary internet or execution tools.
  **Tester:** Extend [chat integration](../../tests/integration/help/test_chat_end_to_end.py#L34) and
  [retrieval filters](../../tests/contract/help/test_retrieval_filters_tenant.py#L9). Use valid corpus
  tasks, weather/legal/medical prompts sharing common vocabulary, foreign-tenant sources marked
  global improperly, above-OFFICIAL rows, conflicting claims, unsupported claims with a valid-looking
  citation, observer write questions and empty index. Assert refusal reason, zero prohibited retrieval,
  precise citations and no modifying action. Model quality is a separate AUD-038-019 gate.
  **Future command:** `uv run --no-sync pytest tests/integration/help/test_chat_end_to_end.py tests/contract/help/test_retrieval_filters_tenant.py -q`.
  **Done:** Live entrypoint is connected and all safety negative cases fail closed; deterministic
  unit success is not presented as measured model performance.

- [ ] AUD-038-005 Make audit receipts durable and enforce transcript lifecycle boundaries

  **Trace:** FR-020, FR-027, FR-029, FR-029a, FR-029b, SC-010; T-AA036, T-AA042, T-AA049,
  T-AA059, T-AA060, T-AA072, T-AA090, T-AA197; F05.
  **Expected / actual / impact:** Every turn, including refusals, has a durable reconstructable record;
  current deny receipts are invented, completion precedes persistence, sessions are never written,
  fallback is volatile, and browser raw content outlives identity boundaries.
  **Developer:** Own [handler](../../apps/api/app/api/routes/help_chat.py#L174),
  [repositories](../../apps/api/app/repositories/help_repositories.py#L80),
  [browser store](../../apps/web/src/lib/help/chatStore.tsx#L56) and
  [reconstructor](../../apps/api/app/services/help/transcript_reconstructor.py#L16). Return per-turn
  result objects instead of shared function attributes; persist redacted input, exact response,
  citations, refusal, gateway decision, approvals, persona/source and snapshot before `done` receipt.
  Implement session ownership/sequence/idempotency, 30-day cap that cannot be extended by appending
  new turns, seven-year audit lifecycle, explicit durable-write failure, and no production memory fallback.
  Avoid raw browser persistence; namespace/expire state and clear on logout/role/tenant changes.
  Expose reconstruction only through authenticated observer audit tooling with required label,
  target user/time window/reason audit event, never original-user history. Depends on AUD-038-001/016/022.
  **Tester:** Extend [audit schema](../../tests/contract/help/test_chat_audit_schema.py#L10),
  [chat integration](../../tests/integration/help/test_chat_end_to_end.py#L34) and
  [reconstruction](../../tests/integration/help/test_transcript_reconstruction.py#L17). Cover allow,
  redact, deny, disconnect before/after done, concurrent tenants, missing container, write failure,
  retry, day-30 and year-7 edges, wrong owner/observer and two-user browser reload. Assert exact durable
  receipt, no shared-turn mix-up, no PII, purge isolation, audit-only label and unchanged own history.
  **Future command:** `uv run --no-sync pytest tests/contract/help/test_chat_audit_schema.py tests/integration/help/test_chat_end_to_end.py tests/integration/help/test_transcript_reconstruction.py -q`.
  **Done:** Every acknowledged turn is durable/reconstructable; failures are explicit; separately
  authorized lifecycle evidence proves automatic purge and effective append-only permissions.

- [ ] AUD-038-006 Correct safety doctrine and decision-rights guidance

  **Trace:** FR-003, FR-004, FR-011b, FR-024, FR-025; US1.2, US2.5, US4.2; T-AA132, T-AA135,
  T-AA136, T-AA149, T-AA150, T-AA156, T-AA157, T-AA158, T-AA159, T-AA162; F06.
  **Expected / actual / impact:** Approved operational guidance must agree with doctrine/roles;
  current Principle V, IC approval, observer and risk text can misdirect safety decisions.
  **Developer/content owner:** Correct the existing [Principle V article](../../apps/web/src/content/help/articles/constitution-principle-v.mdx#L29),
  affected PIO/Executive/Observer landings, Composer/Evacuation/Risk/amber/NEMA/multilingual guides.
  Verify each action against the constitution and current role/controller; require IC approval for
  public safety communications, preserve Help-owner plus safety/governance approval, allow observer
  questions but observation-only instructions, remove live-audit Help grounding claims, and correct
  calibration directions with explicit axes. Do not silently invent new authority or Help localisation
  scope. Keep existing URLs and publish corrections through AUD-038-002/003.
  **Tester/reviewer:** Extend [persona browser cases](../../apps/web/__tests__/e2e/help/persona-override.spec.ts#L7)
  and [chat integration](../../tests/integration/help/test_chat_end_to_end.py#L34) with synthetic
  urgent/low-confidence/high-confidence PIO outputs, observer task questions, wrong approval pairs,
  and calibrated green-band examples. Assert no confidence-based approval bypass and no invented
  quotation; genuine doctrine/cultural review is a separate human prerequisite, not a generated signature.
  **Future command:** `uv run --no-sync pytest tests/integration/help/test_chat_end_to_end.py -q`;
  after authorized UI setup, `pnpm --filter @ama/web exec playwright test --project=help persona-override`.
  **Done:** Exact source-linked doctrine and authority review approves the corrected published corpus,
  and regression fixtures reject each identified unsafe instruction.

- [ ] AUD-038-007 Complete the named persona and domain content obligations

  **Trace:** FR-002, FR-003, FR-004, FR-021, FR-024; US1, US4, US5; T-AA128, T-AA129, T-AA130,
  T-AA131, T-AA133, T-AA134, T-AA137, T-AA138, T-AA139, T-AA140, T-AA141, T-AA142, T-AA143,
  T-AA144, T-AA147, T-AA148, T-AA151, T-AA152, T-AA153, T-AA155, T-AA160, T-AA161; F07.
  **Expected / actual / impact:** All named workflows need usable steps, boundaries, screenshots and
  handoffs; generic prose and article count do not deliver missing reassignment/staging/export flows.
  **Developer/content owner:** Use the existing persona, screen, playbook, FAQ and glossary files
  enumerated in the content matrix below. Fill every recorded omission, canonical Controller term
  and aliases, decision points, recovery/what-could-go-wrong paths, first-15-minute prompts and exact
  deep links. Include Vietnamese/Auslan and impacted community/Aboriginal language authoring with
  cultural-authority references; do not manufacture consultation. Identify/document the top twenty
  troubleshooting topics and self-contained resolution destinations. Estimates are not quotas.
  Depends on corrected doctrine AUD-038-006, navigation AUD-038-008, visuals AUD-038-010 and approval.
  **Tester:** Expand [search/cluster cases](../../apps/web/__tests__/e2e/help/search-and-cluster.spec.ts#L7),
  [persona cases](../../apps/web/__tests__/e2e/help/persona-override.spec.ts#L7) and
  [language cases](../../tests/contract/help/test_lang_attr_lint.py#L19). For all sixteen personas,
  assert each mandatory named step/link/rights/handoff/prompt, not just title presence; negative fixtures
  omit one required step or target, and edges cover NSW theming, read-only roles and offline recovery.
  **Future command:** `pnpm --filter @ama/web exec playwright test --project=help search-and-cluster persona-override`.
  **Done:** Content matrix has no unexplained gap; authors and authorized role reviewers validate
  exact procedures, separately from measured usability/time-to-competence under AUD-038-020.

- [ ] AUD-038-008 Wire entitled persona landings and valid contextual content routes

  **Trace:** FR-001, FR-002, FR-004, FR-005, FR-027, FR-027-AMEND, FR-028;
  T-AA073, T-AA094, T-AA097, T-AA099, T-AA100, T-AA103, T-AA104, T-AA105, T-AA106,
  T-AA114, T-AA120, T-AA154, T-AA155; F08.
  **Expected / actual / impact:** The active role and surface must select useful approved content;
  generic landing/default persona, absent persona destinations and slash mismatch break workflows.
  **Developer:** Own [landing](../../apps/web/src/app/help/page.tsx#L222), persona hook/tiles/tour,
  dock/deep-link parser/surface map, catch-all article frontend and article API. Load approved profiles,
  ranked entitled union and one active persona, propagate jurisdiction/surface and audit article loads.
  Resolve rank polarity once using the shared registry; preserve all sixteen role/cluster IDs and
  aliases without expanding entitlements. Support nested slugs safely; render real glossary/playbooks,
  distinguish 401/403/404/503, preserve URLs/anchors and approved deprecation. Depends on AUD-038-001/003.
  **Tester:** Extend [deep-link cases](../../apps/web/__tests__/e2e/help/deep-link-resolution.spec.ts#L7)
  and persona cases with all sixteen profiles, multi-role ordering, entitlement revocation, contextual
  PIO launch, nested/encoded/traversal slugs, unknown term, and back/forward navigation. Assert exact
  content destination, safe denial, active-only chat and correct origin-persona audit fields.
  **Future command:** `pnpm --filter @ama/web exec playwright test --project=help deep-link-resolution persona-override`.
  **Done:** Every primary surface reaches contextual content; canonical and nested URLs resolve;
  no disconnected helper is counted as user-facing delivery.

- [ ] AUD-038-009 Preserve citation and provenance semantics through the stream and UI

  **Trace:** FR-011d, FR-011d-AMEND, FR-012, FR-016, FR-017, FR-029;
  T-AA061, T-AA067, T-AA096, T-AA102, T-AA107, T-AA109, T-AA111, T-AA116, T-AA117; F09.
  **Expected / actual / impact:** Every claim needs a valid source heading and complete notices;
  malformed URLs, unbound notices and overwritten metadata break verification and privacy notices.
  **Developer:** Own [SSE client](../../apps/web/src/lib/help/sseClient.ts#L20), chat store/panel,
  CitationBadge, article heading generation and conflict/deprecation components. Define one typed
  event envelope; preserve true redaction status, session/turn/audit/pattern IDs, per-claim citation
  associations and canonical URL+fragment resolution for Help and doctrine/spec sources. Include
  old/new snapshot/date/current equivalent or direct no-replacement handoff. Reject unsafe URL
  schemes; preserve deterministic cancel/reconnect/idempotency semantics, no automatic duplicate POST.
  Depends on AUD-038-003/004/005/014/015/022; never expose another tenant through a citation link.
  **Tester:** Expand [citation browser cases](../../apps/web/__tests__/e2e/help/chat-citation-flow.spec.ts#L7),
  PII and deprecation integration cases. Cover two claims/two sources, bare/leading-# anchors,
  Unicode headings, deleted/no-replacement content, split UTF-8/CRLF frames, bad JSON, truncated
  streams, duplicate meta, cancellation, retry and second turn. Assert correct existing heading,
  stable redaction, visible provenance, stream error, no duplicate audit and persistent session ID.
  **Future command:** `pnpm --filter @ama/web exec playwright test --project=help chat-citation-flow deep-link-resolution`.
  **Done:** A valid badge cannot mask an unsupported claim; all event/error/notice branches are
  observed in assertions and source destinations retain provenance.

- [ ] AUD-038-010 Deliver genuine annotated screenshots and release-based freshness

  **Trace:** FR-006, FR-007, FR-008, FR-010, FR-010a, FR-010a-AMEND, FR-010b, SC-005, SC-012;
  T-AA032, T-AA038, T-AA051, T-AA055, T-AA075, T-AA108, T-AA110, T-AA115, T-AA121,
  T-AA144, T-AA145, T-AA146, T-AA174, T-AA176, T-AA177, T-AA180, T-AA212; F10.
  **Expected / actual / impact:** Real paired images, numbered prose/keyboard equivalents and
  live-DOM mismatch warnings are required; placeholders/comments/selectors do not establish them.
  **Developer:** Own existing capture/registry/hash/checker/bulk tools, screenshot routes/repository,
  MDX embedding and screenshot/keyboard/banner components. Cover fourteen explicitly named surfaces
  and every persona workflow; reconcile plan's eighteen-screen launch target through approved scope,
  not silent deletion. Use numbered actual DOM fingerprints at capture/build, preserve callout order,
  genuine light/dark assets/sidecars and private short-lived URLs. Persist flags in the designed
  registry, create grouped author tasks for route rename, show immediate and next-release banners,
  never remove stale safety guidance. Share application theme with OS fallback only. Depends on
  AUD-038-003/008/016/018; capture/publication require separate authorization, not audit execution.
  **Tester:** Extend [hash cases](../../tests/contract/help/test_screen_id_hash.py#L13) and existing
  Help deep-link/a11y suites. Fixtures: unchanged build, same-selector label/role change, reordered
  callouts, route rename with N assets, missing sidecar/variant, one-pixel output, expired signed URL,
  app/OS theme disagreement, first/next release. Assert genuine inventory, hash/flag/task count,
  distinct banners, callout-to-prose links and adjacent equivalent keyboard steps.
  **Future command:** `uv run --no-sync pytest tests/contract/help/test_screen_id_hash.py -q`;
  separately `pnpm --filter @ama/web exec playwright test --project=help` after authorized real capture.
  **Done:** Every required screenshot has valid paired assets and equivalents; lifecycle assertions
  falsify selector-only staleness and one-pixel success. SC-012 measurement remains a release record.

- [ ] AUD-038-011 Connect offline reading to the shared bounded Help cache

  **Trace:** FR-026, FR-026a, FR-026a-AMEND, FR-026b; T-AA084, T-AA095, T-AA098, T-AA107,
  T-AA118, T-AA124, T-AA194, T-AA205; F11.
  **Expected / actual / impact:** Previously viewed content plus glossary/FAQ stays readable under
  degradation; current helpers are disconnected, leaving users without required incident guidance.
  **Developer:** Own cache/detector/worker registration and active article/search/chat hydration.
  Integrate with the existing shared Field Coordinator envelope, not another additive 500 MB budget;
  preload full glossary/curated FAQ, scope caches by identity/content permission, enforce eviction and
  fourteen-day age banners without hiding stale guidance. Map offline/network/worker/503 signals
  to disabled chat and uncached retrieval; audit an authenticated refresh on reconnect server-side.
  Depends on AUD-038-001/005/008/012; never directly write audit storage from the browser.
  **Tester:** Replace [offline stub](../../apps/web/__tests__/e2e/help/offline-degraded-mode.spec.ts#L7)
  and tighten [degraded assertions](../../tests/integration/help/test_degraded_mode.py#L47).
  Cover cold offline, warm viewed/unviewed articles, glossary/FAQ preload, exact fourteen-day boundary,
  shared-cap overflow, tenant switch, stale-read, reconnect and 503. Assert disabled input, cached-only
  search, correct last-cached date, bounded combined size and exactly auditable refresh.
  **Future command:** `pnpm --filter @ama/web exec playwright test --project=help offline-degraded-mode`.
  **Done:** Actual offline navigation is supported, forbidden retrieval is never attempted, and
  stale safety content stays visible with explanation; separate timing evidence proves lookup limits.

- [ ] AUD-038-012 Implement complete authorized search and truthful result states

  **Trace:** FR-021, FR-026a-AMEND; US5.1, US5.2; T-AA073, T-AA076, T-AA101, T-AA104,
  T-AA118, T-AA153, T-AA161; F12.
  **Expected / actual / impact:** Full article/glossary search and canonical-first matches are required;
  title/summary truncation misses relevant steps and empty-result offline wording misleads users.
  **Developer:** Own [search API](../../apps/api/app/api/routes/help_search.py#L22), article pagination,
  glossary loader and [search page](../../apps/web/src/app/help/search/page.tsx#L40). Search approved
  body text/aliases with correct ranking and continuation; apply tenant/active-role constraints before
  ranking, encode canonical links, distinguish online zero-match/unavailable/degraded cached subset.
  Depends on AUD-038-003/007/008/011; do not query unapproved or uncached sources offline.
  **Tester:** Extend [search browser cases](../../apps/web/__tests__/e2e/help/search-and-cluster.spec.ts#L7)
  and [route smoke](../../tests/contract/help/test_help_routes_smoke.py#L33). Fixtures: canonical and
  aliased AIIMS Controller, body-only match, article beyond row 200, multi-tenant same term, punctuation,
  no match, upstream 401/503, cached match and uncached query. Assert glossary then IC guide ordering,
  complete authorized results, continuation, real destination, and banner only for actual degradation.
  **Future command:** `pnpm --filter @ama/web exec playwright test --project=help search-and-cluster`.
  **Done:** No result is lost solely through arbitrary pre-search slicing and result states are factual.

- [ ] AUD-038-013 Connect feedback retention and stable rolling-pattern review

  **Trace:** FR-022, FR-022a, FR-022a-AMEND; T-AA037, T-AA041, T-AA050, T-AA056, T-AA072,
  T-AA113, T-AA188, T-AA199; F13.
  **Expected / actual / impact:** Ratings/comments must be retained and third negative promoted;
  independent pending rows, unstable intent hashes and false UI success lose improvement signals.
  **Developer:** Own chat feedback route/facade, [aggregator](../../apps/api/app/services/help/feedback_aggregator.py#L25),
  agent pattern identity and FeedbackBar/ChatPanel. Validate authorized targets, persist timestamps,
  derive semantic cluster plus exact ordered citation IDs server-side, preserve ordered SHA-256
  helper, deduplicate retries, aggregate tenant-local negatives in an actual 30-day window and expose
  authors' review backlog. Never mutate/hide rated guidance. Check HTTP response before success;
  add comments and per-turn controls. Depends on AUD-038-001/005/009/015; redact feedback PII too.
  **Tester:** Extend [feedback tests](../../tests/integration/help/test_negative_feedback_no_silencing.py#L25)
  and [pattern tests](../../tests/contract/help/test_pattern_id_stability.py#L14). Cover 2/3/4 negatives,
  exact 30-day boundary, future dates, retries, reordered citations, same intent across processes,
  cross-tenant targets, positive rating, empty comment, 403/500 UI failures. Assert promoted state,
  unique IDs/count, persisted pattern, error feedback and byte-for-byte unchanged content.
  **Future command:** `uv run --no-sync pytest tests/integration/help/test_negative_feedback_no_silencing.py tests/contract/help/test_pattern_id_stability.py -q`.
  **Done:** Third qualifying negative actually creates/promotes one visible review item; order changes
  produce different patterns per amendment, never the obsolete T-AA188 invariance expectation.

- [ ] AUD-038-014 Provide actionable support handoff and incident-aware acknowledgement tracking

  **Trace:** FR-023, FR-023a, FR-023a-AMEND, FR-023b; T-AA040, T-AA057, T-AA077, T-AA090,
  T-AA112, T-AA119, T-AA195, T-AA213; F14.
  **Expected / actual / impact:** Users need one-click tenant/default contact with incident SLA;
  current refusal text/404/unmounted button and unscheduled helper offer no operational handoff.
  **Developer:** Own support API/domain/UI and [SLA monitor](../../apps/api/app/services/help/support_handoff_sla_monitor.py#L19).
  Align channel/address/business-hours/incident override fields, validate admin-only changes and
  safe schemes, provide platform fallback, activate from actual NEMA-Level-3 state or authorized local
  override, record open/ack states and schedule idempotent timeout events. Count four business hours
  using the configured calendar, not elapsed four hours. Do not promise staffing or automatic human
  acknowledgement; this is an audited contractual SLA. Depends on AUD-038-001/005/009/015/017.
  Expose all required record fields on an authenticated tenant-onboarding/admin configuration surface,
  reusing an existing suitable form where available; its validation is part of this task.
  **Tester:** Extend [SLA tests](../../tests/integration/help/test_support_handoff_sla.py#L23) and
  chat browser cases. Cover configured/missing/unreachable destinations, unsupported schemes,
  non-admin edits, Level-3 activation/clear/manual override, holiday/weekend boundaries, just-before/
  after five minutes, acknowledgement, duplicate polling and tenant separation. Assert correct channel,
  direct fallback, no timer after ack and one complete breach event per handoff.
  **Future command:** `uv run --no-sync pytest tests/integration/help/test_support_handoff_sla.py tests/contract/help/test_help_routes_smoke.py -q`.
  **Done:** Every refusal/requested handoff is actionable; timed test data establishes tracking,
  while real human acknowledgement performance remains separate operator evidence.

- [ ] AUD-038-015 Reconcile domain models public schemas and installed package boundaries

  **Trace:** data-model, API/UI contracts; FR-009a, FR-011a, FR-020, FR-023a, FR-027-AMEND;
  T-AA031, T-AA032, T-AA033, T-AA034, T-AA035, T-AA039, T-AA042, T-AA043, T-AA044,
  T-AA045, T-AA046, T-AA047, T-AA048, T-AA049, T-AA079, T-AA080, T-AA081, T-AA085; F15.
  **Expected / actual / impact:** Pydantic/TS/HTTP/storage contracts must agree; name-only tests and
  source-path injection mask mismatched DTOs, exports and missing validators.
  **Developer:** Own existing Help models, TS barrels/package exports, route DTOs and package manifests.
  Compare fields/enums/nullability/extra policy, provide compatible adapters for reused doctrine
  Citation, expose `@ama/domain/help` and installed Help agent/ingest modes, enforce valid persona/
  slug/callout/language constraints and immutable nested provenance. Resolve ULID-versus-slug,
  nested slug, `glossary_term_links`, OFFICIAL-only and error-envelope ambiguities explicitly against
  the binding amendments; do not break unrelated Citation users. Make HTTP pagination/ETag/If-Match,
  Accept-Language and `/api/v1` versus current `/api` contract deliberate and tested.
  **Tester:** Extend [models](../../tests/contract/help/test_help_models.py#L53),
  [twins](../../tests/contract/help/test_domain_twin_sync.py#L49), OpenAPI and smoke cases. Include
  invalid/valid BCP-47 extensions, unknown roles, empty/duplicate callouts, extra/raw fields, nested
  mutation, schema drift, each method/status, stale ETag and installed-package imports without path
  injection. Assert complete schemas/responses, not type names or URL substrings.
  **Future command:** `uv run --no-sync pytest tests/contract/help -q`; separately authorized
  `pnpm --filter @ama/domain build` plus clean-package import checks after packaging repairs.
  **Done:** Deliberate field/export drift fails; source, contracts and built package agree or an
  explicit compatibility resolution records the change. Depends on AUD-038-018 for reproducible setup.

- [ ] AUD-038-016 Enforce effective immutable storage private access and Australian processing

  **Trace:** FR-018, FR-019, FR-020, FR-029, SC-011; T-AA013, T-AA017, T-AA019, T-AA020,
  T-AA021, T-AA024, T-AA025, T-AA026, T-AA027, T-AA029, T-AA171, T-AA218; F16.
  **Expected / actual / impact:** Effective privileges/residency must enforce the plan; broad grants,
  missing private/CMK controls and incomplete inventory cannot establish immutable AU data paths.
  **Developer:** Own existing Help Bicep modules/root grants/parameters, storage parent and attestor.
  Remove broader effective write grants before adding restrictive immutable-container roles; preserve
  necessary unrelated container access explicitly. Use applicable AVM/policy rules, correct container
  names/indexes/TTLs/analytics/tagging/dependency order, proper web/ingest identities, private endpoints,
  CMK and 90-day delete retention. Pin actual Help inference/embedding processing to allowed AU
  deployment types, not merely account region. Inventory every shared data/log/compute dependency;
  fail attestation on empty/missing/unknown/non-AU resources. No policy lookup/deployment performed here.
  **Tester:** Extend existing infrastructure test area (new Help fixture is proposed, not evidence)
  and [tenant tests](../../tests/integration/help/test_tenant_isolation.py#L42). Fixtures: create/read
  versus update/delete under each identity, unintended inherited role, wrong partition/TTL, absent
  shared resource, empty inventory, non-AU processing deployment, expired URL and public network attempt.
  **Future commands:** after separately authorized IaC setup, `bicep build infra/main.bicep --stdout`
  and `Invoke-PSRule -InputPath infra/main.bicep`; actual role/network/TTL/region probes require approved staging.
  **Done:** Effective permissions, real dependency inventory and staging evidence satisfy immutability,
  private/CMK/retention and AU processing. Depends on AUD-038-003/005; no blanket PSRule suppression.

- [ ] AUD-038-017 Connect Help telemetry alerts and safe operational procedures

  **Trace:** FR-010b, FR-011c, FR-020, FR-023b; SC-002, SC-003, SC-007, SC-012;
  T-AA016, T-AA022, T-AA023, T-AA093, T-AA210, T-AA211, T-AA215, T-AA216, T-AA217; F17.
  **Expected / actual / impact:** SREs need meaningful metrics and working rollback/handoff alarms;
  authored queries and inaccurate event/threshold instructions cannot detect or recover failures.
  **Developer:** Own [telemetry](../../apps/web/src/lib/help/telemetry.ts#L6), API audit emitters,
  workbook/monitoring/alert definitions and existing Help runbooks. Emit all ten UI contract events
  without free text, connect correct units/names to seven workbook queries, implement required
  thresholds/actions and 30-day hot/7-year archive. Measure first useful answer separately from first
  byte; implement release-cycle freshness metrics. Repair commands/events to actual interfaces;
  fault the alias/transaction in a controlled drill, never weaken authentication to simulate failure.
  Emit `audit.help_release_signoff_recorded` only after an actually authorized signed release record,
  with both approvers, release tag and snapshot ID; the template's event name alone is not an emitter.
  Depends on AUD-038-003/005/010/014/016; preserve tenant-safe telemetry and no PII.
  **Tester:** Extend publication/SLA integration tests to assert event payloads and metric names/units;
  synthetic 801 ms/5 s/60 s thresholds, no-metric states, SLA duplicate breach and rollback failure
  must map to expected warnings/critical alarms. Verify configured on-call delivery separately.
  **Future command:** `uv run --no-sync pytest tests/integration/help/test_snapshot_publish_rollback.py tests/integration/help/test_support_handoff_sla.py -q`.
  **Done:** Producers and queries agree; approved staging captures alert/pager/recovery evidence;
  runbooks do not claim mechanisms absent from code.

- [ ] AUD-038-018 Make setup authoring and CI gates reproducible and fail closed

  **Trace:** FR-005, FR-009a-AMEND, FR-010a, FR-012; T-AA002, T-AA003, T-AA004, T-AA005,
  T-AA006, T-AA007, T-AA012, T-AA123, T-AA164, T-AA175, T-AA178, T-AA179, T-AA181; F18.
  **Expected / actual / impact:** Required per-PR validators must inspect published content with
  complete dependencies; current manual/skip gates and token checks permit invalid content releases.
  **Developer:** Reconcile root/web/agent/ingest manifests and lockfiles, strict tool coverage,
  installed mode entrypoints, Next MDX build/render integration, complete Help sitemap and workflows.
  Use parsed AST language ancestry for every declared fragment and published HTML, rejecting missing
  wrappers at author/save and build. Validate all internal slug AND heading targets, including nested
  paths. Trigger on all Help-affecting PR paths; require inputs rather than skipping, run complete
  meaningful suites and dev/test/prod promotion gates. No new workspace/service is needed.
  Depends on AUD-038-003/008/010/015/019; keep source `lang` attributes, never runtime injection.
  **Tester:** Extend [language tests](../../tests/contract/help/test_lang_attr_lint.py#L19), twin and
  browser deep-link cases. Fixtures: valid inherited language, unrelated matching attribute, wrong
  wrapper, repeated unwrapped term, missing glossary, heading absent, nested/encoded route, empty
  sitemap and workflow path-filter changes. Assert fail-closed behavior and nonzero discovered suites.
  **Future command:** `uv run --no-sync pytest tests/contract/help/test_lang_attr_lint.py tests/contract/help/test_domain_twin_sync.py -q`;
  prepared environments then `pnpm test:help` after repairing its full-suite definition.
  **Done:** Relevant PRs exercise authoring/build/API/UI/evaluation gates with no success-by-missing-input;
  dependency setup and gate configuration are versioned and consistent, execution separately evidenced.

- [ ] AUD-038-019 Replace placeholder tests and fixture-shape evaluation with meaningful gates

  **Trace:** SC-002, SC-003, SC-004, SC-005, SC-006; all acceptance stories;
  T-AA071, T-AA182, T-AA183, T-AA184, T-AA185, T-AA186, T-AA187, T-AA188, T-AA189,
  T-AA190, T-AA191, T-AA192, T-AA193, T-AA194, T-AA195, T-AA196, T-AA197, T-AA198,
  T-AA199, T-AA200, T-AA201, T-AA202, T-AA203, T-AA204, T-AA205, T-AA206, T-AA207,
  T-AA208, T-AA209; F19.
  **Expected / actual / impact:** Tests must fail when behavior is removed; titles, path names,
  fixture keys, permissive statuses and mocked success do not establish delivery or model quality.
  **Developer/tester:** Reuse the existing contract/integration/e2e/evaluation files, not parallel
  redundant suites. Replace six skipped browser bodies, add real theme/keyboard/axe interactions,
  assert controller-generated schema/audit/retrieval/alias effects, and test actual auth boundaries.
  Expand six one-row fixtures to at least 200 in-scope questions across sixteen personas with approved
  source/claim truth; add out-of-scope, no-match, contradictory, cross-tenant, PII and fabrication cases.
  Connect actual response scoring and audit sampling, not fixture labels, and fail missing/empty sets.
  Keep deterministic fake tests labelled separately from AU model runs. Depends on related fixes and
  AUD-038-018; no execution or model calls are authorized by this report itself.
  **Future commands:** `uv run --no-sync pytest tests/contract/help tests/integration/help -q`;
  `uv run --no-sync pytest tests/llm-eval/help --collect-only -q`; after evaluator repair and separate
  model authorization, `uv run --no-sync pytest tests/llm-eval/help -q`;
  after authorized browsers/servers, `pnpm --filter @ama/web exec playwright test --project=help`.
  **Expected / done:** Nonzero intended discovery, no unconditional skips, >=90% valid cited in-scope
  answers, 100% out-of-scope refusal, zero verified fabrication, exact persona/source constraints and
  zero unresolved A/AA issues supported by meaningful assertions plus required manual accessibility review.

- [ ] AUD-038-020 Reconcile review evidence and satisfy release measurement duties honestly

  **Trace:** SC-001, SC-002, SC-003, SC-004, SC-005, SC-006, SC-007, SC-008, SC-009,
  SC-009-AMEND, SC-010, SC-011, SC-012; T-AA011, T-AA030, T-AA052, T-AA092, T-AA127,
  T-AA160, T-AA163, T-AA173, T-AA214, T-AA218, T-AA219, T-AA220, T-AA221, T-AA222,
  T-AA223, T-AA224, T-AA225, T-AA226; F20.
  **Expected / actual / impact:** Release claims need dated revision/environment results and actual
  approvals; original ticks, obsolete CHK mappings and TBD templates cannot satisfy them.
  **Future reviewer/owner:** Reconcile existing ledger/checklists/runbooks/baselines via transparent
  dated amendments only after authorization; preserve historical states. Use the actual 136 CHKs,
  28 quality items, 17 technical review duties, all persona obligations and AR/MO resolutions below.
  Capture the immediate prelaunch fourteen-day ticket count/persona/TTR baseline, then compare
  three-month navigation-ticket volume against >=40%, not a 25% TTR/30% volume substitute.
  SC-001 cohort needs >=20 participants AND coverage of all personas; SC-008 spans all clusters.
  Separate content approval/cultural consultation, usability, fabrication/red-team/audit/retention,
  actual screenshot inventory, WCAG/AT, useful-answer latency, AU attestation, deployment and one-release
  freshness records. Do not create retrospective approvals or treat unavailable external records as failure proof.
  **Tester/reviewer:** After AUD-038-019, compare every evidence entry to its exact requirement,
  revision, environment, dataset/cohort, date and result; negative fixtures include TBD/obsolete paths,
  wrong CHK meaning, shape-only eval, cold first-byte mistaken for useful answer and zero-resource attestations.
  **Future command:** `uv run --no-sync pytest tests/contract/help tests/integration/help tests/llm-eval/help -q`
  is only one authorized gate after fixes; remaining studies/drills/approvals require their documented owners.
  **Done:** Every release-blocking outcome has authentic linked evidence or remains explicitly open;
  publication/release does not proceed solely because original tasks are checked. All dependencies above apply.

- [ ] AUD-038-021 Complete Help keyboard focus announcements and motion accessibility

  **Trace:** FR-009, UI contract sections 2/4, SC-006; T-AA099, T-AA106, T-AA107,
  T-AA120, T-AA125, T-AA126, T-AA203, T-AA204; F21.
  **Expected / actual / impact:** Keyboard and assistive-technology users need the same operational
  access; inactive shortcut and incomplete dock/tour focus/motion/target behavior break that access.
  **Developer:** Own active dock, Help shell/chat/tour and Help CSS. Wire Windows/macOS shortcut,
  described dialog semantics, focus entry/trap/return, Escape, visible focus and 44x44 contract targets.
  Announce sending/refused/error/redacted/complete states with appropriate priority; respect
  reduced-motion and actual active theme. Reuse established UI primitives; do not rebuild the app.
  Depends on AUD-038-008/009/010/018; minimum 44x44 is the explicit contract, not a blanket WCAG inference.
  **Tester:** Replace [a11y stub](../../apps/web/__tests__/e2e/help/accessibility-axe-scan.spec.ts#L7)
  and add complete keyboard interactions within existing Help browser suites; extend
  [a11y unit sweep](../../apps/web/tests/a11y/full-sweep.test.tsx#L1). Cover mobile/desktop, modal
  cycle, focus return after cancel/error, each chat status, zoom/long labels, OS/app theme disagreement,
  reduced motion and non-English fragments. Assert axe A/AA, target dimensions, focus visibility and
  no trapped/unreachable action. NVDA plus JAWS/equivalent and pronunciation checks remain manual duties.
  **Future command:** `pnpm --filter @ama/web exec playwright test --project=help`; separately
  `pnpm --filter @ama/web test:a11y` after real Help unit coverage exists.
  **Done:** Automated and authorized manual evidence cover every Help surface without open A/AA gaps.

- [ ] AUD-038-022 Enforce Help PII redaction before every AU retrieval and audit path

  **Trace:** FR-017, FR-020, research section E, US2.4; T-AA042, T-AA064, T-AA070, T-AA072,
  T-AA117, T-AA192; F22.
  **Expected / actual / impact:** Help must redact before retrieval regardless of AU residency;
  current shared gateway bypass and ad hoc agent masking retain names or destroy useful numeric prompts.
  **Developer:** Own [Help gateway call](../../apps/api/app/api/routes/help_chat.py#L71) and a compatible
  explicit Help enforcement option/adapter at [common gateway](../../apps/agents/common/model_gateway.py#L198).
  Reuse recognizers, but do not silently change other callers' existing regional behavior. Enforce
  name/phone/address/email and above-OFFICIAL policy for Help, preserve non-PII text, propagate one
  authoritative redaction decision and fail closed when mandated recognizers are unavailable.
  Remove duplicate heuristic redaction, prevent raw logs/browser persistence, keep processing in AU
  and no cross-region workaround. Depends on AUD-038-004/005/009/015/016.
  **Tester:** Extend [PII tests](../../tests/integration/help/test_pii_redaction_notice.py#L28) through
  real Help HTTP/gateway wiring using synthetic names, AU mobiles, address-only text, email, mixed
  Unicode, protected markings, and benign '8x playback'/'15 minutes' questions. Cover AU East/AU
  Southeast, recognizer unavailable/error, explicit deny and duplicate metadata. Assert no raw PII
  in retrieval arguments/audit/telemetry/storage, true user notice, preserved benign content and zero
  retrieval on denial; verify unrelated gateway callers retain their documented compatibility.
  **Future command:** `uv run --no-sync pytest tests/integration/help/test_pii_redaction_notice.py tests/integration/help/test_chat_end_to_end.py -q`.
  **Done:** Default AU Help flow cannot bypass the mandated redaction boundary; source and actual
  negative assertions establish it separately from runtime model-quality measurements.

## Coverage Matrices

The following matrices are completed from original obligation definitions, not inferred from task ticks.

### Functional Requirements

There are 43 base/suffixed FR clauses plus eight explicit FR amendments: 51 rows. No standalone
`NFR-*` is defined by this specification; its nonfunctional duties are recorded below, not omitted
or replaced with invented NFR identifiers. A PARTIAL row does not imply acceptable release behavior.

| Requirement | Status | Definition and concrete implementation assessment | Follow-up |
| --- | --- | --- | --- |
| FR-001 | IMPLEMENTED | [Definition](spec.md#L114); persistent Help destination in [AppShell](../../packages/ui/src/components/layout/app-shell.tsx#L1) and root-mounted dock; contextual shortcut is separately incomplete. | AUD-038-008 |
| FR-002 | PARTIAL | [Definition](spec.md#L115); sixteen authored profiles, but [landing](../../apps/web/src/app/help/page.tsx#L222) is generic and tiles/tours are unconnected. | AUD-038-007, AUD-038-008 |
| FR-003 | PARTIAL | [Definition](spec.md#L116); 45 MDX articles cover domain headings, but [simulation](../../apps/web/src/content/help/articles/playbooks/simulation.mdx#L10) omits observation export and content matrix records other named gaps. | AUD-038-006, AUD-038-007 |
| FR-004 | CONFLICT | [Definition](spec.md#L117); [PIO landing](../../apps/web/src/content/help/personas/public-information-officer/landing.mdx#L31) and Executive/Observer guidance contradict actual decision-right boundaries. | AUD-038-006, AUD-038-007, AUD-038-008 |
| FR-005 | PARTIAL | [Definition](spec.md#L118); [catch-all frontend](../../apps/web/src/app/help/articles/[...slug]/page.tsx#L33) reaches a single-segment API; contextual map and anchors are not operational. | AUD-038-008, AUD-038-009, AUD-038-018 |
| FR-006 | MISSING | [Definition](spec.md#L122); full MDX/assets inventory found [comments](../../apps/web/src/content/help/articles/screen-by-screen/disaster-mapper.mdx#L26), no integrated annotated images or callout/prose mapping. | AUD-038-010 |
| FR-007 | PARTIAL | [Definition](spec.md#L123); unused [picture component](../../apps/web/src/components/help/AnnotatedScreenshot.tsx#L40) follows OS preference, not app theme; no real paired inventory. | AUD-038-010 |
| FR-008 | MISSING | [Definition](spec.md#L124); [KeyboardSteps primitive](../../apps/web/src/components/help/KeyboardSteps.tsx#L7) exists but none of 45 articles embeds actual images/adjacent equivalents. | AUD-038-010 |
| FR-009 | PARTIAL | [Definition](spec.md#L125); outlines/log roles exist, [dock](../../apps/web/src/components/help/HelpAssistantDock.tsx#L29) lacks required focus cycle; WCAG outcome unverified. | AUD-038-019, AUD-038-021 |
| FR-009a | PARTIAL | [Definition](spec.md#L126); [glossary language fields](../../apps/web/src/content/help/glossary/terms.yaml#L1) exist; complete embedded-fragment validation/AT pronunciation not established. | AUD-038-007, AUD-038-015, AUD-038-018, AUD-038-021 |
| FR-010 | PARTIAL | [Definition](spec.md#L127); [banner](../../apps/web/src/components/help/StalenessBanner.tsx#L2) and checker exist but no connected capture-to-reader warning. | AUD-038-010 |
| FR-010a | PARTIAL | [Definition](spec.md#L128); [hasher](../../packages/domain/src/ama_domain/screen_id_hash.py#L23) orders selector paths, not actual live DOM fingerprints; checker input mismatches. | AUD-038-010 |
| FR-010b | CONFLICT | [Definition](spec.md#L129); one release cycle conflicts with [fourteen-day runbook](../../docs/runbooks/help/screenshot-staleness.md#L19); no persisted author task/escalation. | AUD-038-010 |
| FR-011 | CONFLICT | [Definition](spec.md#L133); [loader](../../apps/ingest-runner/src/help_snapshot/source_loaders.py#L25) defaults admission; active [Cosmos extracts](../../apps/agents/help_assistant/agent.py#L359) bypass approved snapshot and omit doctrine/spec retrieval. | AUD-038-003, AUD-038-004 |
| FR-011a | PARTIAL | [Definition](spec.md#L134); [active lookup](../../apps/api/app/repositories/help_repositories.py#L193) is first active metadata row; CLI/indexers do not establish immutable Search publication/version cadence. | AUD-038-002, AUD-038-003 |
| FR-011b | PARTIAL | [Definition](spec.md#L135); [model validator](../../packages/domain/src/ama_domain/snapshot_record.py#L39) checks distinct labels, not authenticated reviews/timestamps/digest; chat audit omits approvals. | AUD-038-002, AUD-038-005 |
| FR-011c | PARTIAL | [Definition](spec.md#L136); [rollback](../../apps/api/app/api/routes/help_snapshots.py#L96) emits metadata without alias restore or complete fields; <=300-second outcome unverified. | AUD-038-003, AUD-038-020 |
| FR-011d | PARTIAL | [Definition](spec.md#L137); [resolver](../../apps/api/app/services/help/deprecation_resolver.py#L17) needs supplied map; no pipeline or dated old/new snapshot notice. | AUD-038-003, AUD-038-009 |
| FR-012 | PARTIAL | [Definition](spec.md#L138); [badge](../../apps/web/src/components/help/CitationBadge.tsx#L10) constructs malformed heading URLs and chat has no per-claim association. | AUD-038-004, AUD-038-009 |
| FR-013 | PARTIAL | [Definition](spec.md#L139); [token retrieval](../../apps/agents/help_assistant/agent.py#L359) has no category/tenant-question refusal policy; refusal card lacks actionable surface/contact. | AUD-038-004, AUD-038-014 |
| FR-014 | PARTIAL | [Definition](spec.md#L140); no-match refusal exists in [agent](../../apps/agents/help_assistant/agent.py#L374), but nearest articles/handoff and supported-claim validation are absent. | AUD-038-004, AUD-038-014, AUD-038-019 |
| FR-015 | PARTIAL | [Definition](spec.md#L141); [scorer](../../apps/agents/help_assistant/agent.py#L221) boosts persona but does not restrict it; jurisdictions unused and active UI persona fixed. | AUD-038-001, AUD-038-004, AUD-038-008 |
| FR-016 | PARTIAL | [Definition](spec.md#L142); [conflict detector](../../apps/api/app/services/help/conflict_surfacer.py#L15) and component exist without production invocation. | AUD-038-004, AUD-038-009 |
| FR-017 | CONFLICT | [Definition](spec.md#L146); default AU call hits [gateway bypass](../../apps/agents/common/model_gateway.py#L198), then heuristic masking instead of mandated redaction; repeated meta can clear notice. | AUD-038-005, AUD-038-009, AUD-038-022 |
| FR-018 | PARTIAL | [Definition](spec.md#L147); AU agent/IaC declarations exist; [attestor](../../tools/help/attest_au_residency.py#L42) omits shared paths and accepts zero resources; actual residency unverified. | AUD-038-016, AUD-038-020 |
| FR-019 | CONFLICT | [Definition](spec.md#L148); [parameterized partition query](../../apps/api/app/repositories/help_repositories.py#L133) is positive, but identity headers and global Help/spec seeding defeat required authorization. | AUD-038-001, AUD-038-003, AUD-038-004 |
| FR-020 | PARTIAL | [Definition](spec.md#L149); [post-stream write](../../apps/api/app/api/routes/help_chat.py#L174) misses denied turns, durable failure and observer access; raw AU inputs may survive. | AUD-038-005, AUD-038-016, AUD-038-022 |
| FR-021 | PARTIAL | [Definition](spec.md#L153); [search](../../apps/api/app/api/routes/help_search.py#L22) omits bodies/aliases, glossary lacks canonical Controller, dedicated term route is placeholder. | AUD-038-007, AUD-038-008, AUD-038-012 |
| FR-022 | PARTIAL | [Definition](spec.md#L154); [article rating control](../../apps/web/src/components/help/FeedbackBar.tsx#L15) has no comment input or chat-response control and ignores failed HTTP status. | AUD-038-013 |
| FR-023 | PARTIAL | [Definition](spec.md#L155); [support component](../../apps/web/src/components/help/SupportHandoffButton.tsx#L12) unmounted; active refusals contain no direct destination. | AUD-038-014 |
| FR-023a | CONFLICT | [Definition](spec.md#L156); [API DTO](../../apps/api/app/api/routes/help_support_handoff.py#L16) lacks binding record fields; missing config returns 404 instead of platform fallback. | AUD-038-001, AUD-038-014, AUD-038-015 |
| FR-023b | PARTIAL | [Definition](spec.md#L157); [SLA helper](../../apps/api/app/services/help/support_handoff_sla_monitor.py#L12) counts elapsed hours and has no scheduled ack lifecycle; staffing/ack outcomes unverified. | AUD-038-014, AUD-038-017, AUD-038-020 |
| FR-022a | PARTIAL | [Definition](spec.md#L158); [pending-row facade](../../apps/api/app/repositories/help_repositories.py#L215) never invokes rolling aggregator or author review surface; no auto-silencing is positive source behavior. | AUD-038-013 |
| FR-024 | CONFLICT | [Definition](spec.md#L162); [multilingual article](../../apps/web/src/content/help/articles/multilingual-authoring.mdx#L218) introduces unauthorized Help translation gates; PIO checker/Auslan and true Principle V coverage incomplete. | AUD-038-006, AUD-038-007 |
| FR-025 | CONFLICT | [Definition](spec.md#L163); [observer article](../../apps/web/src/content/help/articles/observer-mode-guide.mdx#L156) restricts questions and expands grounding; active extracts do not enforce read-only action advice. | AUD-038-001, AUD-038-004, AUD-038-006 |
| FR-026 | PARTIAL | [Definition](spec.md#L167); [offline primitives](../../apps/web/src/lib/help/offlineCache.ts#L34) have no reader/chat consumers; actual cached reading/disabled-chat behavior missing. | AUD-038-011 |
| FR-026a | PARTIAL | [Definition](spec.md#L168); [cache](../../apps/web/src/lib/help/offlineCache.ts#L34) lacks full glossary/curated FAQ preload and scoped offline search. | AUD-038-011, AUD-038-012 |
| FR-026b | PARTIAL | [Definition](spec.md#L169); cache age constant exists, but unused max bytes/separate store/no refresh does not enforce shared cap or dated stale read. | AUD-038-011 |
| FR-027 | PARTIAL | [Definition](spec.md#L173); [resolver](../../apps/api/app/services/help/persona_resolver.py#L20) is unconnected and trusts its override fallback; article audit source is absent. | AUD-038-001, AUD-038-005, AUD-038-008 |
| FR-028 | PARTIAL | [Definition](spec.md#L174); [generic landing](../../apps/web/src/app/help/page.tsx#L222) has no entitled union; body override is not checked and chat does not use authoritative active context. | AUD-038-001, AUD-038-008 |
| FR-029 | PARTIAL | [Definition](spec.md#L178); [TTL model](../../packages/domain/src/ama_domain/chat_session.py#L42) and IaC declarations exist, but session writes/history/purge and browser retention are unconnected. | AUD-038-005, AUD-038-016 |
| FR-029a | PARTIAL | [Definition](spec.md#L179); [reconstruction helper](../../apps/api/app/services/help/transcript_reconstructor.py#L16) reads partitioned entries, with no authorized audit endpoint or seven-year retrieval proof. | AUD-038-005, AUD-038-020 |
| FR-029b | PARTIAL | [Definition](spec.md#L180); helper event lacks target-user/time-window fields; required audit-only labelled surface and unchanged-history assertions absent. | AUD-038-005, AUD-038-019 |
| FR-011-AMEND | CONFLICT | [Definition](spec.md#L186); [seed projection](../../scripts/seed_loader.py#L441) and manifest globalize Help/specs, whereas amendment allows global doctrine only and tenant-scoped composition. | AUD-038-003 |
| FR-022a-AMEND | PARTIAL | [Definition](spec.md#L187); [ordered SHA helper](../../packages/domain/src/ama_domain/chat_pattern_id.py#L22) is correct, but connected [intent hash](../../apps/agents/help_assistant/agent.py#L407) is unstable/truncated and no pattern aggregation is invoked. | AUD-038-013 |
| FR-009a-AMEND | PARTIAL | [Definition](spec.md#L188); [linter](../../tools/help/lint_lang_attributes.py#L41) checks unrelated file-wide strings, plugin unregistered, no built-HTML/per-PR gate. | AUD-038-018 |
| FR-026a-AMEND | PARTIAL | [Definition](spec.md#L189); [banner](../../apps/web/src/components/help/DegradedSearchBanner.tsx#L2) text exists but online zero matches trigger it; no cached-result state. | AUD-038-011, AUD-038-012 |
| FR-027-AMEND | CONFLICT | [Definition](spec.md#L190); [shared rank registry](../../packages/domain/src/ama_domain/authority_rank_registry.py#L16) uses lower-is-higher, while UI contract/client sorts descending. Explicit reconciliation required. | AUD-038-008, AUD-038-015 |
| FR-023a-AMEND | PARTIAL | [Definition](spec.md#L191); [domain flags](../../packages/domain/src/ama_domain/support_handoff_record.py#L13) exist but neither live NEMA state nor manual local override controls active support API/UI. | AUD-038-014 |
| FR-011d-AMEND | PARTIAL | [Definition](spec.md#L193); [deprecation helper](../../apps/api/app/services/help/deprecation_resolver.py#L17) has no-replacement branch; no connected dated notice/direct fallback with preserved snapshot. | AUD-038-003, AUD-038-009, AUD-038-014 |
| FR-010a-AMEND | PARTIAL | [Definition](spec.md#L194); [bulk helper](../../tools/help/bulk_rebaseline.py#L13) writes a report; no live rename-to-N-assets grouped persisted flag/task workflow. | AUD-038-010 |

### Success Criteria

All outcome claims below require execution/measurement records beyond source. Source defects are
not presented as measured rates or observed deployment failures. Twelve criteria plus one amendment
are separately covered.

| Criterion | Status | Definition and evidence assessment | Follow-up |
| --- | --- | --- | --- |
| SC-001 | UNVERIFIED | [95% within 60 seconds](spec.md#L212); [ledger](verification-status.md#L46) defers cohort work, no >=20-person/all-persona study results. | AUD-038-008, AUD-038-020 |
| SC-002 | UNVERIFIED | [90% cited/100% refused](spec.md#L213); [shape checks](../../tests/llm-eval/help/test_eval_cite_or_refuse.py#L31) do not run or score answers. | AUD-038-004, AUD-038-019, AUD-038-020 |
| SC-003 | UNVERIFIED | [Zero verified fabrication per release](spec.md#L214); no actual Help audit sampler or scored release sample found in bounded evaluation/runner/tools search. | AUD-038-004, AUD-038-019, AUD-038-020 |
| SC-004 | UNVERIFIED | [Zero cross-tenant retrieval/answers](spec.md#L215); [memory partition tests](../../tests/integration/help/test_tenant_isolation.py#L42) omit connected auth/Search/model/audit red-team outcome. | AUD-038-001, AUD-038-003, AUD-038-019, AUD-038-020 |
| SC-005 | UNVERIFIED | [100% paired annotated inventory](spec.md#L216); no local genuine images/sidecars; [capture script](../../tools/help/capture_screenshots.ts#L18) is not a capture result. External Blob inventory not inspected. | AUD-038-010, AUD-038-020 |
| SC-006 | UNVERIFIED | [Zero unresolved A/AA](spec.md#L217); [axe-named suite](../../apps/web/__tests__/e2e/help/accessibility-axe-scan.spec.ts#L7) skips without axe assertions; no completed AT attestation. | AUD-038-018, AUD-038-019, AUD-038-021, AUD-038-020 |
| SC-007 | UNVERIFIED | [Median first useful answer <5 seconds](spec.md#L218); [workbook](../../infra/bicep/modules/help-app-insights-dashboard.bicep#L27) is not measurement and first-byte p95 is a different metric. | AUD-038-017, AUD-038-020 |
| SC-008 | UNVERIFIED | [>=80% complete tour <15 minutes](spec.md#L219); authored tours and [unused overlay](../../apps/web/src/components/help/FirstFifteenMinutesTour.tsx#L10) do not prove a cross-cluster study. | AUD-038-007, AUD-038-008, AUD-038-020 |
| SC-009 | UNVERIFIED | [>=40% volume reduction in three months](spec.md#L220); [TBD baseline](baselines/pre-launch-support.md#L39) specifies conflicting TTR/30-day outcome; no before/after counts. | AUD-038-020 |
| SC-010 | UNVERIFIED | [100% durable/observer-accessible audit](spec.md#L221); [deny branch](../../apps/api/app/api/routes/help_chat.py#L72) and volatile fallback contradict prerequisites; no retrieval drill. | AUD-038-005, AUD-038-016, AUD-038-020, AUD-038-022 |
| SC-011 | UNVERIFIED | [100% AU processing](spec.md#L222); [attestation tool](../../tools/help/attest_au_residency.py#L42) misses dependencies/accepts none; no release attestation JSON. | AUD-038-016, AUD-038-020 |
| SC-012 | UNVERIFIED | [90% freshness within one release](spec.md#L223); [staleness runbook](../../docs/runbooks/help/screenshot-staleness.md#L19) changes cycle to days; no backlog measurement. | AUD-038-010, AUD-038-017, AUD-038-020 |
| SC-009-AMEND | UNVERIFIED | [Immediate prelaunch fourteen-day baseline](spec.md#L192); [template](baselines/pre-launch-support.md#L6) has no dates/counts and omits five operational personas in its table. | AUD-038-020 |

### Acceptance Scenarios

Twenty scenarios are separately assessed. Status reflects static support; no scenario was executed.
Definitions are in [user stories](spec.md#L9). `US1.1` etc. are report labels for original numbered
Given/When/Then clauses, not new requirements.

| Scenario | Status | Expected interaction and concrete evidence assessment | Follow-up |
| --- | --- | --- | --- |
| US1.1 | PARTIAL | IC tile/controller/picture/approval/escalation tour: [IC prose](../../apps/web/src/content/help/personas/incident-commander/landing.mdx#L11) exists; personalised tile and annotated tour unconnected. | AUD-038-007, AUD-038-008, AUD-038-010 |
| US1.2 | CONFLICT | PIO contextual multilingual editor/checker/channels guide: [Composer article](../../apps/web/src/content/help/articles/screen-by-screen/alert-composer.mdx#L177) has conditional approval; contextual launch/checker images absent. | AUD-038-006, AUD-038-007, AUD-038-008, AUD-038-010 |
| US1.3 | PARTIAL | NSW RFS ingestion/filter/availability/ack with NSW theme: [fire article](../../apps/web/src/content/help/personas/frontline-fire/landing.mdx#L12) lacks named filter/publication/handoff steps and imagery. | AUD-038-007, AUD-038-008, AUD-038-010 |
| US1.4 | PARTIAL | Audit-trail search to read-only timeline/compliance/export: [observer guide](../../apps/web/src/content/help/articles/observer-mode-guide.mdx#L156) conflicts with rights; body search/export workflow incomplete. | AUD-038-006, AUD-038-007, AUD-038-012 |
| US1.5 | PARTIAL | Reopened image follows chosen dark theme: [unused picture](../../apps/web/src/components/help/AnnotatedScreenshot.tsx#L40) only uses OS media fallback; no actual variants. | AUD-038-010 |
| US2.1 | PARTIAL | Reassign task, cite guide/entity, take-me-there: [Operations landing](../../apps/web/src/content/help/personas/operations-officer/landing.mdx#L11) lacks reassignment; citation deep link malformed and persona untrusted. | AUD-038-004, AUD-038-007, AUD-038-009 |
| US2.2 | PARTIAL | Weather refusal plus bom-national surface: [RefusalCard](../../apps/web/src/components/help/RefusalCard.tsx#L12) has no actionable destination; token ranking does not enforce weather refusal. | AUD-038-004, AUD-038-014 |
| US2.3 | CONFLICT | Other tenant/private data refused without leakage: [caller headers](../../apps/api/app/api/routes/help_deps.py#L39) and global Help seed defeat the required boundary. | AUD-038-001, AUD-038-003, AUD-038-004 |
| US2.4 | CONFLICT | Names/phone/address redact before pipeline with notice: [AU gateway](../../apps/agents/common/model_gateway.py#L198) returns original input and agent heuristic is inadequate. | AUD-038-005, AUD-038-009, AUD-038-022 |
| US2.5 | CONFLICT | PIO Vietnamese/Auslan steps and Principle V/Composer citations: [false doctrine](../../apps/web/src/content/help/articles/constitution-principle-v.mdx#L29), missing Auslan/checker procedure and fixed active persona. | AUD-038-004, AUD-038-006, AUD-038-007, AUD-038-008 |
| US2.6 | PARTIAL | Insufficient support yields inability/nearest articles/contact: [no-match branch](../../apps/agents/help_assistant/agent.py#L374) refuses, but related destinations and support are absent. | AUD-038-004, AUD-038-014 |
| US2.7 | PARTIAL | Every claim has inline badge reaching a heading: [badge](../../apps/web/src/components/help/CitationBadge.tsx#L10) omits fragment separator and renders after whole answer. | AUD-038-004, AUD-038-009 |
| US3.1 | MISSING | Mapper callouts/numbered prose/alt/light-dark control: [MDX marker](../../apps/web/src/content/help/articles/screen-by-screen/disaster-mapper.mdx#L26) is only a comment. | AUD-038-010 |
| US3.2 | PARTIAL | UI change flags image for author and reader: [freshness checker](../../tools/help/check_screenshot_freshness.py#L33) has type mismatch/static selectors and no durable task/reader lifecycle. | AUD-038-010 |
| US3.3 | MISSING | Screen-reader image equivalent with adjacent keyboard block: [primitive](../../apps/web/src/components/help/KeyboardSteps.tsx#L7) has no active embedded content. | AUD-038-010, AUD-038-021 |
| US4.1 | PARTIAL | Multi-jurisdiction scenario/warp/observation export in playbook: [simulation](../../apps/web/src/content/help/articles/playbooks/simulation.mdx#L10) covers setup/warp but not export or valid replay destination. | AUD-038-007, AUD-038-008 |
| US4.2 | CONFLICT | Evacuation recommendation/provenance/IC approval/audit: [playbook](../../apps/web/src/content/help/articles/playbooks/agent-evacuation.mdx#L115) routes through field confirmation without the required IC chain. | AUD-038-006, AUD-038-007 |
| US4.3 | PARTIAL | Observer incident reconstruction/deviations/lessons export: [audit article](../../apps/web/src/content/help/articles/audit-observer-mode.mdx#L35) has live-audit grounding claim and incomplete export procedure. | AUD-038-005, AUD-038-006, AUD-038-007 |
| US5.1 | MISSING | AIIMS Controller definition first then IC guide: [five-term glossary](../../apps/web/src/content/help/glossary/terms.yaml#L1) lacks canonical term, alias scoring/term route incomplete. | AUD-038-007, AUD-038-008, AUD-038-012 |
| US5.2 | PARTIAL | Degraded-mode search explains banner/behavior/recovery: [FAQ](../../apps/web/src/content/help/articles/troubleshooting.mdx#L10) has generic symptoms but not accurate Help-cache/TTL recovery; search banner misfires. | AUD-038-007, AUD-038-011, AUD-038-012 |

### Independent Tests And Edge Cases

The five independent-test paragraphs and ten unnumbered edge cases are distinct duties; report
identifiers here allow exhaustive traceability without inventing original task IDs.

| Obligation | Status | Source and assessment | Follow-up |
| --- | --- | --- | --- |
| INDEP-1 | UNVERIFIED | [US1 independent test](spec.md#L17): any persona completes tour and locates >=3 surfaces; generic landing/no images prevents source support and no participant record exists. | AUD-038-007, AUD-038-008, AUD-038-010, AUD-038-020 |
| INDEP-2 | UNVERIFIED | [US2 independent test](spec.md#L35): all clusters' cited answers/refusals/claim traceability; six single-row fixtures and no model scoring. | AUD-038-004, AUD-038-009, AUD-038-019 |
| INDEP-3 | UNVERIFIED | [US3 independent test](spec.md#L57): each primary screen has two genuine annotated variants/alt/keyboard; local assets absent and external inventory unverified. | AUD-038-010, AUD-038-020 |
| INDEP-4 | UNVERIFIED | [US4 independent test](spec.md#L73): novice completes simulation/8x/evacuation/IC/audit; content lacks approval/export steps and no task study. | AUD-038-006, AUD-038-007, AUD-038-020 |
| INDEP-5 | UNVERIFIED | [US5 independent test](spec.md#L89): glossary-first and twenty self-contained troubleshooting topics; glossary incomplete and no canonical twenty-topic validation. | AUD-038-007, AUD-038-012, AUD-038-020 |
| EDGE-01 | PARTIAL | [Out-of-scope](spec.md#L98): standard refusal/right surface/log required; token matching and prose-only card do not enforce it. | AUD-038-004, AUD-038-005, AUD-038-014 |
| EDGE-02 | CONFLICT | [Cross-tenant/organisation](spec.md#L99): no retrieval/return outside permitted scope; supplied identity and globalized Help/spec sources conflict. | AUD-038-001, AUD-038-003, AUD-038-004 |
| EDGE-03 | CONFLICT | [Input PII](spec.md#L100): pre-pipeline redaction/notice defeated by AU bypass. | AUD-038-005, AUD-038-022 |
| EDGE-04 | PARTIAL | [Conflicting corpus](spec.md#L101): helper/component exist but no active conflicting-claim event/citations. | AUD-038-004, AUD-038-009 |
| EDGE-05 | PARTIAL | [No answer](spec.md#L102): no-match refusal exists; nearest articles/direct support absent. | AUD-038-004, AUD-038-014 |
| EDGE-06 | PARTIAL | [Stale image](spec.md#L103): reader banner unconnected to real lifecycle. | AUD-038-010 |
| EDGE-07 | PARTIAL | [Offline/degraded](spec.md#L104): cache helpers do not deliver reading or disabled chat with cached recovery. | AUD-038-011, AUD-038-012 |
| EDGE-08 | PARTIAL | [Keyboard/reader](spec.md#L105): no embedded alternatives; active focus/announcements incomplete. | AUD-038-010, AUD-038-021 |
| EDGE-09 | CONFLICT | [Multilingual](spec.md#L106): English Help launch is explicit; PIO public-authoring guide introduces unsupported Help translation gates and lacks named steps. | AUD-038-006, AUD-038-007 |
| EDGE-10 | CONFLICT | [Read-only](spec.md#L107): observer instruction restrictions not enforced and content introduces prohibited guidance/query constraints. | AUD-038-001, AUD-038-004, AUD-038-006 |

### Original Task Coverage

Source: [complete original task list](tasks.md#L1). All 226 original entries are `[X]`; the table
normalizes X/x to `[x]` without changing their meaning. Every original ID has its own row. There
are no suffixed task IDs in this particular list. Execution clauses embedded in otherwise authored
tasks remain unverified unless separately recorded; IMPLEMENTED never claims a command was run.

#### Setup

| Original task | Original state | Status | Concrete source/test evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| T-AA001 | [x] | IMPLEMENTED | Requested scaffold families exist, including [ingest mode](../../apps/ingest-runner/src/help_snapshot/__main__.py#L1), Help routes/content/tests/tools; later runtime completeness is separate. | none |
| T-AA002 | [x] | PARTIAL | [Root Python manifest](../../pyproject.toml#L10) and lock do not fully implement specified dependency setup; no sync/import execution established. | AUD-038-018 |
| T-AA003 | [x] | PARTIAL | [Web manifest](../../apps/web/package.json#L24) lacks specified MDX/rehype/pa11y dependencies; existing render path differs without an approved retirement. | AUD-038-018 |
| T-AA004 | [x] | PARTIAL | [Typing configuration](../../pyproject.toml#L1) excludes tools/ignores tests and strict CI typing is nonblocking; scoped ruff/mypy gate not complete. | AUD-038-018 |
| T-AA005 | [x] | PARTIAL | [pa11y config](../../apps/web/.pa11yci.json#L1) is authored; dependency, effective 2.2 coverage and dry-run success unverified. | AUD-038-018, AUD-038-021 |
| T-AA006 | [x] | PARTIAL | Relocated [Playwright .cts Help project](../../apps/web/playwright.config.cts#L70) exists; no functioning Help axe fixture/assertions. | AUD-038-019 |
| T-AA007 | [x] | PARTIAL | [Rehype plugin](../../tools/help/rehype-lang-attr.ts#L26) exists but is not registered in active Next configuration/rendering. | AUD-038-018 |
| T-AA008 | [x] | PARTIAL | [CODEOWNERS](../../.github/CODEOWNERS#L47) lists both groups; group-specific dual review is not enforced by that text. | AUD-038-002 |
| T-AA009 | [x] | IMPLEMENTED | [Initial manifest](../../apps/ingest-runner/manifests/help-snapshot.yaml#L5) declares four globs/status filter; loader enforcement and incorrect global semantics remain separate defects. | AUD-038-003 |
| T-AA010 | [x] | IMPLEMENTED | [Service descriptor](../../azure.yaml#L1) retains existing web/API delivery with no separate Help compute service. | none |
| T-AA011 | [x] | PARTIAL | [Baseline README](baselines/README.md#L3) and placeholder exist, but claim 30% instead of SC-009's 40%. | AUD-038-020 |
| T-AA012 | [x] | PARTIAL | [test:help](../../package.json#L8) is a subset command; no complete Phase-8 CI invocation. | AUD-038-018, AUD-038-019 |

#### Infrastructure

| Original task | Original state | Status | Concrete source/test evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| T-AA013 | [x] | PARTIAL | [Seven-container module](../../infra/bicep/modules/cosmos-help-containers.bicep#L48) declares partitions/TTLs; raw-resource/analytics/index/security obligations not fully delivered or deployed. | AUD-038-016 |
| T-AA014 | [x] | PARTIAL | [Search deployment script](../../infra/bicep/modules/help-search-index-pair.bicep#L33) prints messages, not index/alias operations. | AUD-038-003, AUD-038-016 |
| T-AA015 | [x] | PARTIAL | [Blob container](../../infra/bicep/modules/help-screenshots-storage.bicep#L36) has 30-day policy; parent lacks required private/CMK/90-day delete configuration. | AUD-038-016 |
| T-AA016 | [x] | IMPLEMENTED | [Seven-query workbook](../../infra/bicep/modules/help-app-insights-dashboard.bicep#L27) authored; real producers/live charts assessed under operational tasks. | AUD-038-017 |
| T-AA017 | [x] | PARTIAL | [Root wiring](../../infra/main.bicep#L1452) includes three modules, omits Search and complete required tags; what-if not executed. | AUD-038-003, AUD-038-016 |
| T-AA018 | [x] | IMPLEMENTED | [Agent-definition artifact](../../infra/parameters/foundry-agents/help_assistant.yaml#L1) declares requested region/retrieval-only tool/inference settings; registration/runtime not implied. | AUD-038-004, AUD-038-016 |
| T-AA019 | [x] | PARTIAL | Relocated [companion registry](../../infra/parameters/foundry-agents.yaml#L1) records AU/no-carveout intent; active runtime/validator enforcement absent in bounded search. | AUD-038-016 |
| T-AA020 | [x] | PARTIAL | [API grant](../../infra/main.bicep#L894) is account-wide Data Contributor, not effective insert-only immutable-container access. | AUD-038-016 |
| T-AA021 | [x] | MISSING | Required web-reader/ingest-runner grants absent in scoped IaC inventory; [existing ingestion grant](../../infra/main.bicep#L566) is for another identity. | AUD-038-016 |
| T-AA022 | [x] | PARTIAL | [Monitoring](../../infra/modules/monitoring.bicep#L21) lacks complete Help diagnostics and 30-day hot/7-year archive configuration. | AUD-038-017 |
| T-AA023 | [x] | MISSING | No Help-specific alert resources after root/child monitoring search; [generic module](../../infra/modules/monitoring.bicep#L1) is not the stated thresholds/action groups. | AUD-038-017 |
| T-AA024 | [x] | MISSING | No Help overlays in [dev parameters](../../infra/main.parameters.dev.json#L4) or relocated [production parameters](../../infra/main.parameters.production.json#L4). | AUD-038-016 |
| T-AA025 | [x] | CONFLICT | [PSRule exclusions](../../ps-rule.yaml#L20) classify active Help-module location as legacy; not limited to documented AVM gaps. | AUD-038-016 |
| T-AA026 | [x] | MISSING | Required Help what-if fixture absent after infra tests/parameter inventory; [task](tasks.md#L78) remains binding, empty placeholder is not equivalent. | AUD-038-016 |
| T-AA027 | [x] | PARTIAL | [Infrastructure overview](../../docs/infrastructure/help.md#L21) is authored but describes restrictive roles as future and overclaims other active controls. | AUD-038-016 |
| T-AA028 | [x] | PARTIAL | [Bootstrap CLI](../../tools/help/bootstrap_search_index.py#L126) defaults permanently to dry run and omits vector schema; cannot establish real bootstrap. | AUD-038-003 |
| T-AA029 | [x] | PARTIAL | [Attestor](../../tools/help/attest_au_residency.py#L42) checks a partial name/tag inventory and accepts empty; no complete shared dependency processing proof. | AUD-038-016 |
| T-AA030 | [x] | UNVERIFIED | [Provisioning checkpoint](tasks.md#L82) has no dated Help dev provisioning log in scoped infrastructure/runbook evidence inventory. | AUD-038-020 |

#### Domain Models

| Original task | Original state | Status | Concrete source/test evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| T-AA031 | [x] | PARTIAL | [Article validator](../../packages/domain/src/ama_domain/help_article.py#L60) checks lowercase/spaces; [tests](../../tests/contract/help/test_help_models.py#L53) omit ID/slug/persona/glossary relational constraints. | AUD-038-015 |
| T-AA032 | [x] | PARTIAL | [Screenshot model](../../packages/domain/src/ama_domain/annotated_screenshot.py#L10) allows empty callouts/keyboard steps; [test](../../tests/contract/help/test_help_models.py#L275) constructs a manifest only. | AUD-038-010, AUD-038-015 |
| T-AA033 | [x] | PARTIAL | [Language regex](../../packages/domain/src/ama_domain/glossary_term.py#L12) is incomplete BCP-47; [assertions](../../tests/contract/help/test_help_models.py#L64) cover only basic tags/punctuation. | AUD-038-015 |
| T-AA034 | [x] | PARTIAL | [Profile validator](../../packages/domain/src/ama_domain/persona_help_profile.py#L29) checks known ranks but accepts unknown persona IDs; active registry direction conflicts. | AUD-038-008, AUD-038-015 |
| T-AA035 | [x] | PARTIAL | [Spec-status validator](../../packages/domain/src/ama_domain/knowledge_corpus_source.py#L27) exists; [draft test](../../tests/contract/help/test_help_models.py#L106) uses missing status, not Draft/approved composition, and loader bypasses model. | AUD-038-003, AUD-038-015 |
| T-AA036 | [x] | IMPLEMENTED | [Session model/TTL](../../packages/domain/src/ama_domain/chat_session.py#L42) and [30-day default assertion](../../tests/contract/help/test_help_models.py#L251) support the model annotation, not durable session purge. | AUD-038-005 |
| T-AA037 | [x] | IMPLEMENTED | [Feedback validator](../../packages/domain/src/ama_domain/help_feedback.py#L25) requires chat pattern ID; [negative case](../../tests/contract/help/test_help_models.py#L142) exercises omission. Active HTTP integration differs. | AUD-038-013 |
| T-AA038 | [x] | IMPLEMENTED | [Nonempty grace ID](../../packages/domain/src/ama_domain/staleness_flag.py#L20) is required and [empty value test](../../tests/contract/help/test_help_models.py#L194) rejects it. | AUD-038-010 |
| T-AA039 | [x] | PARTIAL | [Distinct-role model](../../packages/domain/src/ama_domain/snapshot_record.py#L39) and rejection tests exist; frozen outer model does not make nested lists immutable or establish authentic approvals. | AUD-038-002, AUD-038-015 |
| T-AA040 | [x] | IMPLEMENTED | [Handoff defaults](../../packages/domain/src/ama_domain/support_handoff_record.py#L13) and [test](../../tests/contract/help/test_help_models.py#L214) establish 4-hour/5-minute model values, not active scheduling. | AUD-038-014 |
| T-AA041 | [x] | PARTIAL | [Model test](../../tests/contract/help/test_help_models.py#L228) supplies `needs_review` itself, not threshold transition through [aggregator](../../apps/api/app/services/help/feedback_aggregator.py#L25). | AUD-038-013 |
| T-AA042 | [x] | PARTIAL | [Redacted-only model](../../packages/domain/src/ama_domain/chat_audit_entry.py#L20) and frozen assignment test exist; ingress redaction/nested immutability/raw-field handling incomplete. | AUD-038-005, AUD-038-015, AUD-038-022 |
| T-AA043 | [x] | CONFLICT | [Python Citation reuse](../../packages/domain/src/ama_domain/__init__.py#L33) exists, but Help wire/TS shape differs; [test](../../tests/contract/help/test_domain_twin_sync.py#L70) checks declaration presence only. | AUD-038-015 |
| T-AA044 | [x] | PARTIAL | [Shared registry](../../packages/domain/src/ama_domain/authority_rank_registry.py#L19) and [ordering assertion](../../tests/contract/help/test_help_models.py#L243) exist; opposite client polarity and no authoritative rank fixture. | AUD-038-008, AUD-038-015 |
| T-AA045 | [x] | PARTIAL | [Consolidated TS twins](../../packages/domain/src/help/index.ts#L22) are relocated authored equivalents, but schema/nullability/Citation field fidelity is unchecked. | AUD-038-015 |
| T-AA046 | [x] | PARTIAL | [Barrel namespace](../../packages/domain/src/index.ts#L21) exists; [export map](../../packages/domain/package.json#L9) lacks `@ama/domain/help`. | AUD-038-015 |
| T-AA047 | [x] | PARTIAL | [Twin test](../../tests/contract/help/test_domain_twin_sync.py#L49) compares names, not generated field schemas; promised drift gate absent. | AUD-038-015, AUD-038-019 |
| T-AA048 | [x] | IMPLEMENTED | Re-exports live in [existing package initializer](../../packages/domain/src/ama_domain/__init__.py#L22), consumed by [model tests](../../tests/contract/help/test_help_models.py#L8); historical filename not required for delivery. | none |
| T-AA049 | [x] | PARTIAL | [Cosmos query](../../apps/api/app/repositories/help_repositories.py#L133) parameterizes tenant; tests use memory, not live client mocks; volatile fallback and wrong staleness container persist. | AUD-038-005, AUD-038-010, AUD-038-015 |
| T-AA050 | [x] | IMPLEMENTED | [Ordered SHA-256 helper](../../packages/domain/src/ama_domain/chat_pattern_id.py#L22) and [order-sensitive test](../../tests/contract/help/test_pattern_id_stability.py#L14) satisfy amended helper semantics; upstream intent remains unstable. | AUD-038-013 |
| T-AA051 | [x] | PARTIAL | [Callout-number hash](../../packages/domain/src/ama_domain/screen_id_hash.py#L23) and [reorder test](../../tests/contract/help/test_help_models.py#L181) exist; live fingerprints and independent cross-platform golden vector absent. | AUD-038-010, AUD-038-015 |
| T-AA052 | [x] | UNVERIFIED | [Checkpoint](tasks.md#L113) requires build/test execution; historical claims do not establish current revision/environment results. | AUD-038-020 |

#### Backend Services And Agent

| Original task | Original state | Status | Concrete source/test evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| T-AA053 | [x] | PARTIAL | [Publisher](../../apps/api/app/services/help/snapshot_publisher.py#L40) uses stub indexer and is not the mounted HTTP path; no real approval-to-index transaction. | AUD-038-002, AUD-038-003 |
| T-AA054 | [x] | PARTIAL | [Indexer](../../apps/api/app/services/help/snapshot_indexer.py#L16) returns dicts/updates memory without SDK create/upload/alias calls. | AUD-038-003 |
| T-AA055 | [x] | PARTIAL | [Staleness service](../../apps/api/app/services/help/staleness_checker.py#L15) is a pure hash/flag helper, not live build/persisted lifecycle. | AUD-038-010 |
| T-AA056 | [x] | PARTIAL | [Aggregator](../../apps/api/app/services/help/feedback_aggregator.py#L25) returns model updates, but route never invokes it and supplied related rows are not deduplicated/scoped internally. | AUD-038-013 |
| T-AA057 | [x] | PARTIAL | [Monitor helper](../../apps/api/app/services/help/support_handoff_sla_monitor.py#L19) checks supplied elapsed deadlines, not scheduled change feed/ack/calendar/NEMA activation. | AUD-038-014 |
| T-AA058 | [x] | PARTIAL | [Resolver](../../apps/api/app/services/help/persona_resolver.py#L20) exists but fallback entitles the requested override; caller/chat route do not use it. | AUD-038-001, AUD-038-008 |
| T-AA059 | [x] | PARTIAL | [Typed append helper](../../apps/api/app/services/help/chat_audit_writer.py#L9) and repository create-only logic exist; deny/volatile/effective-role gaps prevent every-turn durability. | AUD-038-005, AUD-038-016 |
| T-AA060 | [x] | PARTIAL | [Reconstructor](../../apps/api/app/services/help/transcript_reconstructor.py#L16) sorts supplied session rows and emits partial payload; no observer authorization/expiry/audit-only UI. | AUD-038-005 |
| T-AA061 | [x] | PARTIAL | [Resolver](../../apps/api/app/services/help/deprecation_resolver.py#L17) handles supplied mapping only; no publication-generated map/current-equivalent reader integration. | AUD-038-003, AUD-038-009 |
| T-AA062 | [x] | PARTIAL | [Conflict heuristic](../../apps/api/app/services/help/conflict_surfacer.py#L15) handles artificial topic/stance tags but is not invoked by active Help retrieval. | AUD-038-004, AUD-038-009 |
| T-AA063 | [x] | PARTIAL | [Classification helper](../../apps/api/app/services/help/content_classification_guard.py#L16) exists; active seed and reader paths bypass it. | AUD-038-003, AUD-038-004 |
| T-AA064 | [x] | PARTIAL | [Live agent](../../apps/agents/help_assistant/agent.py#L50) raises NotImplementedError; extract-based Cosmos alternative is not the selected Foundry pipeline or authorized retirement. | AUD-038-004 |
| T-AA065 | [x] | PARTIAL | [System prompt](../../apps/agents/help_assistant/prompts/system.md#L1) is authored; active extract path never consumes its persona/refusal/grounding instructions. | AUD-038-004 |
| T-AA066 | [x] | PARTIAL | [Refusal prompt](../../apps/agents/help_assistant/prompts/refusal.md#L1) is authored; actual refusal/card branches omit prescribed contact and category handling. | AUD-038-004, AUD-038-014 |
| T-AA067 | [x] | PARTIAL | [Deprecation prompt](../../apps/agents/help_assistant/prompts/deprecation_notice.md#L1) exists; current stream/UI do not produce required dated replacement/no-replacement notice. | AUD-038-003, AUD-038-009 |
| T-AA068 | [x] | MISSING | No connected Help-origin hard Search filter in bounded common/agent/service caller search; [active retrieval](../../apps/agents/help_assistant/agent.py#L359) calls article facade instead. | AUD-038-001, AUD-038-003, AUD-038-004 |
| T-AA069 | [x] | PARTIAL | [No-match branch](../../apps/agents/help_assistant/agent.py#L374) refuses empty extracts, but shared citation filter/claim validation is not wired. | AUD-038-004 |
| T-AA070 | [x] | CONFLICT | Wrapper absent after scoped search; relocated [gateway call](../../apps/api/app/api/routes/help_chat.py#L71) exists but [AU bypass](../../apps/agents/common/model_gateway.py#L198) defeats required redaction. | AUD-038-022 |
| T-AA071 | [x] | PARTIAL | Six renamed one-row fixtures exist, e.g. [citation case](../../apps/agents/help_assistant/eval_fixtures/cite_or_refuse.jsonl#L1); no complete gold/persona/fabrication dataset/consumer. | AUD-038-019 |

#### Backend Routes And Ingest

| Original task | Original state | Status | Concrete source/test evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| T-AA072 | [x] | PARTIAL | [Chat routes](../../apps/api/app/api/routes/help_chat.py#L54) stream/enqueue/get, but auth, redaction, session writes, durable receipts and promised services are incomplete. | AUD-038-001, AUD-038-004, AUD-038-005, AUD-038-013, AUD-038-022 |
| T-AA073 | [x] | PARTIAL | [Article routes](../../apps/api/app/api/routes/help_articles.py#L1) list/read with ETag, but no continuation/approved snapshot and nested slug mismatch. | AUD-038-003, AUD-038-008, AUD-038-012, AUD-038-015 |
| T-AA074 | [x] | PARTIAL | [Snapshot routes](../../apps/api/app/api/routes/help_snapshots.py#L45) are mounted metadata operations, not authorized publication/rollback with contract responses. | AUD-038-002, AUD-038-003, AUD-038-015 |
| T-AA075 | [x] | PARTIAL | [Screenshot routes](../../apps/api/app/api/routes/help_screenshots.py#L1) exist; placeholder signature, wrong flag store and no author gate. | AUD-038-001, AUD-038-010 |
| T-AA076 | [x] | PARTIAL | [Search](../../apps/api/app/api/routes/help_search.py#L22) gives simple glossary/title ranking, no body/alias full text or complete corpus search. | AUD-038-012 |
| T-AA077 | [x] | PARTIAL | [Support routes](../../apps/api/app/api/routes/help_support_handoff.py#L16) GET/PUT use divergent fields and no admin guard/fallback. | AUD-038-001, AUD-038-014, AUD-038-015 |
| T-AA078 | [x] | CONFLICT | Six Help routers are included via [API router](../../apps/api/app/api/router.py#L102) and [main](../../apps/api/app/main.py#L73); current `/api` configuration differs from promised `/api/v1`, not missing registration. | AUD-038-015 |
| T-AA079 | [x] | PARTIAL | [Caller dependency](../../apps/api/app/api/routes/help_deps.py#L29) reads Accept-Language; routes do not establish negotiated responses/honored language/error contract. | AUD-038-015 |
| T-AA080 | [x] | CONFLICT | Mounted [error handler](../../apps/api/app/middleware/error_handler.py#L135) preserves legacy correlationId/status/category but stringifies route detail, not declared Help code/message/task correlation_id schema. | AUD-038-015, AUD-038-019 |
| T-AA081 | [x] | PARTIAL | [Article ETag/304](../../apps/api/app/api/routes/help_articles.py#L35) exists; [support PUT](../../apps/api/app/api/routes/help_support_handoff.py#L40) does not read/check If-Match, so optimistic concurrency is missing. | AUD-038-015, AUD-038-019 |
| T-AA082 | [x] | CONFLICT | [Help caller](../../apps/api/app/api/routes/help_deps.py#L39) derives from untrusted headers before claims and accepts defaults, not authenticated-only tenant middleware. | AUD-038-001 |
| T-AA083 | [x] | MISSING | [Body persona selection](../../apps/api/app/api/routes/help_chat.py#L62) never rejects unentitled override; protected middleware excludes Help and resolver is unconnected. | AUD-038-001 |
| T-AA084 | [x] | MISSING | [Chat route](../../apps/api/app/api/routes/help_chat.py#L60) falls back to snapshot-bootstrap; no alias health/empty-index 503 control in route/agent/repo search. | AUD-038-003, AUD-038-004, AUD-038-011 |
| T-AA085 | [x] | PARTIAL | [OpenAPI test](../../tests/contract/help/test_help_api_openapi.py#L27) checks path presence, not every method/response; mounted DTOs differ from binding contract. | AUD-038-015, AUD-038-019 |
| T-AA086 | [x] | PARTIAL | [Entrypoint](../../apps/ingest-runner/src/help_snapshot/__main__.py#L14) calculates/discards chunks; packaging/mode dispatch/idempotent upload missing. | AUD-038-003, AUD-038-018 |
| T-AA087 | [x] | PARTIAL | [Source loader](../../apps/ingest-runner/src/help_snapshot/source_loaders.py#L25) reads globs but misses real status/approval/tenant exclusions. | AUD-038-003 |
| T-AA088 | [x] | PARTIAL | [Embedder](../../apps/ingest-runner/src/help_snapshot/embedder.py#L63) calls absent module-level interface and swallows failure into zeros; schema incompatible. | AUD-038-003 |
| T-AA089 | [x] | PARTIAL | [Alias helper](../../apps/ingest-runner/src/help_snapshot/alias_swinger.py#L22) writes local state without Search prewarm/health/atomic alias calls. | AUD-038-003 |
| T-AA090 | [x] | PARTIAL | [Emitter](../../apps/api/app/observability/audit.py#L26) reserves names, but route/refusal/rollback/reconstruction/SLA payload completeness and durable all-branch emission absent. | AUD-038-003, AUD-038-005, AUD-038-014, AUD-038-017 |
| T-AA091 | [x] | MISSING | [Active extract loop](../../apps/agents/help_assistant/agent.py#L368) has no OFFICIAL-only filter; disconnected classification helper is not enforcement. | AUD-038-004, AUD-038-022 |
| T-AA092 | [x] | UNVERIFIED | Relocated [route-smoke tests](../../tests/contract/help/test_help_routes_smoke.py#L33) exist, but requested running-app/httpx execution/checkpoint is not evidenced. | AUD-038-019, AUD-038-020 |

#### Frontend

| Original task | Original state | Status | Concrete source/test evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| T-AA093 | [x] | PARTIAL | [Telemetry](../../apps/web/src/lib/help/telemetry.ts#L6) differs from ten-event contract and lacks active emitters; raw query rather than length violates telemetry privacy rule. | AUD-038-017 |
| T-AA094 | [x] | PARTIAL | [Parser](../../apps/web/src/lib/help/deepLinkParser.ts#L13) and entitlement predicate are disconnected from contextual navigation. | AUD-038-008 |
| T-AA095 | [x] | PARTIAL | [Cache](../../apps/web/src/lib/help/offlineCache.ts#L34) has basic get/put/stale flag, not shared cap/preload/reader integration/reconnect refresh. | AUD-038-011 |
| T-AA096 | [x] | PARTIAL | [SSE consumer](../../apps/web/src/lib/help/sseClient.ts#L20) fetches/aborts, but no reliable reconnect/framing/schema/session-completion policy. | AUD-038-009 |
| T-AA097 | [x] | PARTIAL | [Persona hook](../../apps/web/src/lib/help/personaContext.ts#L25) is unused, sorts opposite to registry and does not check override entitlement. | AUD-038-001, AUD-038-008 |
| T-AA098 | [x] | PARTIAL | [Detector](../../apps/web/src/lib/help/degradedModeDetector.ts#L18) is unused; connection/worker/503 path does not drive active UI. | AUD-038-011 |
| T-AA099 | [x] | PARTIAL | [Help layout](../../apps/web/src/app/help/layout.tsx#L14) supplies rail/shell, no entitled switcher or required telemetry mount. | AUD-038-008, AUD-038-017 |
| T-AA100 | [x] | PARTIAL | [Generic landing](../../apps/web/src/app/help/page.tsx#L222) lacks entitled ranked tiles and persona tour. | AUD-038-008 |
| T-AA101 | [x] | PARTIAL | [Search page](../../apps/web/src/app/help/search/page.tsx#L40) calls API, but no full body/alias search, real glossary destination or correct offline state. | AUD-038-012 |
| T-AA102 | [x] | IMPLEMENTED | [Full-page chat](../../apps/web/src/app/help/chat/page.tsx#L5) shares root store with dock/rail; broader chat safety/session contracts are separately partial. | AUD-038-005, AUD-038-009 |
| T-AA103 | [x] | PARTIAL | Relocated [catch-all article](../../apps/web/src/app/help/articles/[...slug]/page.tsx#L33) loads Markdown, but API slash mismatch and absent rich/heading rendering remain. | AUD-038-008, AUD-038-009, AUD-038-010 |
| T-AA104 | [x] | PARTIAL | [Glossary route](../../apps/web/src/app/help/glossary/[term]/page.tsx#L2) echoes term instead of definition/cross-links/lang-aware rendering. | AUD-038-008, AUD-038-012 |
| T-AA105 | [x] | PARTIAL | [Playbook route](../../apps/web/src/app/help/playbooks/[id]/page.tsx#L2) is placeholder, not loaded long-form content. | AUD-038-008 |
| T-AA106 | [x] | PARTIAL | [HelpAffordance](../../apps/web/src/components/help/HelpAffordance.tsx#L6) unmounted; active dock/global link exists but lacks contextual shortcut/focus contract. | AUD-038-008, AUD-038-021 |
| T-AA107 | [x] | PARTIAL | [ChatPanel](../../apps/web/src/components/help/ChatPanel.tsx#L26) streams/logs/refuses; context, degradation, inline citations, notices, feedback/support incomplete. | AUD-038-008, AUD-038-009, AUD-038-011, AUD-038-013, AUD-038-014 |
| T-AA108 | [x] | PARTIAL | [Screenshot component](../../apps/web/src/components/help/AnnotatedScreenshot.tsx#L22) unused; OS-only theme and self-referencing callouts/optional keyboard block violate active contract. | AUD-038-010 |
| T-AA109 | [x] | PARTIAL | [Badge](../../apps/web/src/components/help/CitationBadge.tsx#L7) has accessible text but wrong emitted-anchor URL and no contracted focus/hover popover. | AUD-038-009 |
| T-AA110 | [x] | PARTIAL | [Banner](../../apps/web/src/components/help/StalenessBanner.tsx#L2) has status primitive, no actual release/flag consumer or required escalation wording. | AUD-038-010 |
| T-AA111 | [x] | PARTIAL | [Deprecation component](../../apps/web/src/components/help/DeprecationNotice.tsx#L2) unused and omits retired/replacement snapshot dates/IDs. | AUD-038-009 |
| T-AA112 | [x] | PARTIAL | [RefusalCard](../../apps/web/src/components/help/RefusalCard.tsx#L12) is non-judgmental prose, without actionable suggested surface/handoff. | AUD-038-004, AUD-038-014 |
| T-AA113 | [x] | PARTIAL | [FeedbackBar](../../apps/web/src/components/help/FeedbackBar.tsx#L13) ignores HTTP errors, no comment UI or per-chat usage. | AUD-038-013 |
| T-AA114 | [x] | PARTIAL | [Tile](../../apps/web/src/components/help/PersonaTile.tsx#L11) styles active state but is unmounted and links to absent persona route. | AUD-038-008 |
| T-AA115 | [x] | PARTIAL | [KeyboardSteps](../../apps/web/src/components/help/KeyboardSteps.tsx#L7) is a valid primitive but not paired with actual screenshots/captions in content. | AUD-038-010 |
| T-AA116 | [x] | PARTIAL | [Conflict component](../../apps/web/src/components/help/ConflictNotice.tsx#L7) is unconnected; source references are text, not working citations. | AUD-038-004, AUD-038-009 |
| T-AA117 | [x] | PARTIAL | [Redaction notice](../../apps/web/src/components/help/RedactionNotice.tsx#L2) can render, but AU bypass/second metadata event defeats correct notification. | AUD-038-009, AUD-038-022 |
| T-AA118 | [x] | PARTIAL | [Degraded banner](../../apps/web/src/components/help/DegradedSearchBanner.tsx#L2) has required text but wrong trigger: empty online result, not actual cached search. | AUD-038-011, AUD-038-012 |
| T-AA119 | [x] | PARTIAL | [Support button](../../apps/web/src/components/help/SupportHandoffButton.tsx#L12) unmounted, hides errors and mismatches configured support schema. | AUD-038-014 |
| T-AA120 | [x] | PARTIAL | [Tour overlay](../../apps/web/src/components/help/FirstFifteenMinutesTour.tsx#L10) is unused without persona step provider/focus/dismissal integration. | AUD-038-008, AUD-038-021 |
| T-AA121 | [x] | PARTIAL | [Picture fallback](../../apps/web/src/components/help/AnnotatedScreenshot.tsx#L39) reacts to OS only, not active theme setting. | AUD-038-010 |
| T-AA122 | [x] | IMPLEMENTED | [Loading](../../apps/web/src/app/help/loading.tsx#L2) and [retry shell](../../apps/web/src/app/help/error.tsx#L3) authored; successful runtime handling not claimed. | none |
| T-AA123 | [x] | PARTIAL | [Sitemap](../../apps/web/src/app/help/sitemap.ts#L4) lists three routes, not all content/glossary/playbook pages required for a11y inventory. | AUD-038-018 |
| T-AA124 | [x] | PARTIAL | [Registration](../../apps/web/src/lib/help/sw-register.ts#L2) is uncalled and requests missing worker; existing worker does not cache Help. | AUD-038-011 |
| T-AA125 | [x] | PARTIAL | [Focus styles](../../apps/web/src/app/globals.css#L2777) exist, but shortcut inactive and measured >=3:1 focus contrast absent. | AUD-038-021, AUD-038-020 |
| T-AA126 | [x] | MISSING | No Help reduced-motion handler in scoped UI/styles search; [dock transitions](../../apps/web/src/app/globals.css#L3788) unconditional. | AUD-038-021 |
| T-AA127 | [x] | UNVERIFIED | No current build/start/smoke result; [release template](../../docs/runbooks/help/release-signoff-TEMPLATE.md#L6) cannot establish execution. | AUD-038-020 |

#### Content

All sixteen persona articles have some overview/boundary/numbered-tour prose, but none is connected
to the required active persona landing, and no article embeds real annotated screenshots. Rows below
record specific content omissions, not merely those common presentation gaps.

| Original task | Original state | Status | Concrete source/test evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| T-AA128 | [x] | PARTIAL | [IC article](../../apps/web/src/content/help/personas/incident-commander/landing.mdx#L11) covers picture/approval/NEMA/audit; no span-of-control warning/deputy activation walkthrough. | AUD-038-007, AUD-038-008, AUD-038-010 |
| T-AA129 | [x] | PARTIAL | [Operations](../../apps/web/src/content/help/personas/operations-officer/landing.mdx#L11) covers issue/coordination, not reassignment, staging establishment/check-in/deactivation or explicit escalation-up. | AUD-038-007 |
| T-AA130 | [x] | PARTIAL | [Planning](../../apps/web/src/content/help/personas/planning-officer/landing.mdx#L11) has IAP/forecast narrative, no SITREP/aggregation/template/overlay walkthrough. | AUD-038-007 |
| T-AA131 | [x] | PARTIAL | [Logistics](../../apps/web/src/content/help/personas/logistics-officer/landing.mdx#L11) covers requisitions/transfers, not supply dashboard/supplier directory/consumption/forward-staging request. | AUD-038-007 |
| T-AA132 | [x] | CONFLICT | [PIO](../../apps/web/src/content/help/personas/public-information-officer/landing.mdx#L31) makes approval conditional, omits checker/Auslan/view procedure and true Principle V. | AUD-038-006, AUD-038-007 |
| T-AA133 | [x] | PARTIAL | [Field](../../apps/web/src/content/help/personas/field-coordinator/landing.mdx#L11) covers capture/status/offline, lacks forward-staging accountability/resupply/life-safety-default steps. | AUD-038-007 |
| T-AA134 | [x] | PARTIAL | [Resilience](../../apps/web/src/content/help/personas/resilience-planner/landing.mdx#L11) has scenarios/lessons narrative, not gap export/audit-to-lessons ingestion. | AUD-038-007 |
| T-AA135 | [x] | CONFLICT | [Executive](../../apps/web/src/content/help/personas/executive-leader/landing.mdx#L80) uses wrong publication authorities and omits actual policy-log/escalation walkthroughs. | AUD-038-006, AUD-038-007 |
| T-AA136 | [x] | CONFLICT | [Observer](../../apps/web/src/content/help/personas/observer-auditor/landing.mdx#L45) restricts questions/claims live-audit grounding; compliance checklist/lessons export incomplete. | AUD-038-006, AUD-038-007 |
| T-AA137 | [x] | PARTIAL | [Risk](../../apps/web/src/content/help/personas/risk-manager/landing.mdx#L11) describes register/calibration, not hazard/consequence workflow; linked threshold advice conflicts. | AUD-038-006, AUD-038-007 |
| T-AA138 | [x] | PARTIAL | [Fire](../../apps/web/src/content/help/personas/frontline-fire/landing.mdx#L12) covers observations/ack, lacks filter/availability/mutual-aid steps and NSW image. | AUD-038-007, AUD-038-010 |
| T-AA139 | [x] | PARTIAL | [Medical](../../apps/web/src/content/help/personas/frontline-medical/landing.mdx#L12) covers casualty/hospital/transport, no medical-supply request walkthrough. | AUD-038-007 |
| T-AA140 | [x] | PARTIAL | [Police](../../apps/web/src/content/help/personas/frontline-police/landing.mdx#L12) covers traffic/welfare, not named perimeter/enforcement/liaison workflows. | AUD-038-007 |
| T-AA141 | [x] | PARTIAL | [SES/marine](../../apps/web/src/content/help/personas/frontline-ses-marine/landing.mdx#L12) covers flood/rescue, lacks volunteer activation and complete storm task flow. | AUD-038-007 |
| T-AA142 | [x] | PARTIAL | [Commonwealth](../../apps/web/src/content/help/personas/commonwealth/landing.mdx#L11) has national dashboard narrative, no RFA/weather-geo interpretation/recovery handoff. | AUD-038-007 |
| T-AA143 | [x] | PARTIAL | [Cross-sector](../../apps/web/src/content/help/personas/cross-sector/landing.mdx#L11) uses generic joint-task prose, omits intake/recovery/volunteer/infrastructure reporting. | AUD-038-007 |
| T-AA144 | [x] | PARTIAL | All fourteen screen articles authored; [representative comment](../../apps/web/src/content/help/articles/screen-by-screen/disaster-mapper.mdx#L26) is not required screenshot/keyboard embed. | AUD-038-007, AUD-038-010 |
| T-AA145 | [x] | PARTIAL | [Capture tool](../../tools/help/capture_screenshots.ts#L18) exists but no tracked genuine images/manifests; external capture outcome unverified. | AUD-038-010, AUD-038-020 |
| T-AA146 | [x] | MISSING | No alt JSON sidecars in bounded Help/public/assets inventory; [capture loop](../../tools/help/capture_screenshots.ts#L31) writes PNG only. | AUD-038-010 |
| T-AA147 | [x] | PARTIAL | [Getting started](../../apps/web/src/content/help/articles/getting-started.mdx#L10) covers onboarding but claims unavailable shortcut/context/theme guarantees. | AUD-038-007, AUD-038-008 |
| T-AA148 | [x] | PARTIAL | [Simulation playbook](../../apps/web/src/content/help/articles/playbooks/simulation.mdx#L10) covers setup/warp/debrief, lacks observation export and valid replay destination. | AUD-038-007, AUD-038-008 |
| T-AA149 | [x] | CONFLICT | Five agent playbooks exist; [Evacuation](../../apps/web/src/content/help/articles/playbooks/agent-evacuation.mdx#L115) lacks IC chain and [Risk](../../apps/web/src/content/help/articles/playbooks/agent-risk-assessment.mdx#L174) advises contradictory threshold response. | AUD-038-006, AUD-038-007 |
| T-AA150 | [x] | CONFLICT | [Audit/observer article](../../apps/web/src/content/help/articles/audit-observer-mode.mdx#L35) adds live-audit grounding and lacks required complete export/reconstruction workflow. | AUD-038-005, AUD-038-006, AUD-038-007 |
| T-AA151 | [x] | PARTIAL | [Accessibility how-to](../../apps/web/src/content/help/articles/accessibility-how-to.mdx#L24) is substantial prose, but shortcut/theme/AT-verification claims unsupported and PIO checker guidance incomplete. | AUD-038-007, AUD-038-021, AUD-038-020 |
| T-AA152 | [x] | PARTIAL | [FAQ](../../apps/web/src/content/help/articles/troubleshooting.mdx#L10) has many symptoms; missing simulation reset, Help-cache recovery and validated twenty-topic resolution mapping. | AUD-038-007, AUD-038-011 |
| T-AA153 | [x] | PARTIAL | [Five glossary entries](../../apps/web/src/content/help/glossary/terms.yaml#L1) lack canonical AIIMS Controller and adequate jurisdictional/Hub terms; no exact 600-term quota inferred. | AUD-038-007, AUD-038-012 |
| T-AA154 | [x] | IMPLEMENTED | [Surface map](../../apps/web/src/content/help/surfaceMap.yaml#L2) authors all fourteen required mappings; active consumption remains a separate gap. | AUD-038-008 |
| T-AA155 | [x] | PARTIAL | [IC prompts](../../apps/web/src/content/help/personas/incident-commander/landing.mdx#L148) exist, most personas lack tuned sets; [ChatPanel](../../apps/web/src/components/help/ChatPanel.tsx#L18) uses five generic prompts. | AUD-038-007, AUD-038-008 |
| T-AA156 | [x] | CONFLICT | [Principle V](../../apps/web/src/content/help/articles/constitution-principle-v.mdx#L29) fabricates a verbatim doctrine section instead of mandated warning/accessibility guidance. | AUD-038-006 |
| T-AA157 | [x] | CONFLICT | [Amber article](../../apps/web/src/content/help/articles/amber-confidence-badge.mdx#L10) exists, claims confidence-aware Help citation behavior absent from contract/renderer and relies on false doctrine. | AUD-038-006, AUD-038-007 |
| T-AA158 | [x] | PARTIAL | [Cross-border NEMA article](../../apps/web/src/content/help/articles/cross-border-bushfire-nema.mdx#L10) has example, but real destinations/role-defined escalation need reconciliation. | AUD-038-006, AUD-038-007 |
| T-AA159 | [x] | CONFLICT | [Multilingual guide](../../apps/web/src/content/help/articles/multilingual-authoring.mdx#L218) introduces out-of-scope Help translation gates; public authoring/cultural linkage incomplete. | AUD-038-006, AUD-038-007 |
| T-AA160 | [x] | UNVERIFIED | [Consultation index](../../docs/cultural-authority/help/INDEX.md#L8) lists IDs with TBD authorities/dates, not actual completed consultations. | AUD-038-007, AUD-038-020 |
| T-AA161 | [x] | PARTIAL | [Glossary references](../../apps/web/src/content/help/glossary/terms.yaml#L2) and persona links authored, but destinations/heading resolver and glossary display unconnected. | AUD-038-007, AUD-038-008, AUD-038-012 |
| T-AA162 | [x] | CONFLICT | [Observer mode guide](../../apps/web/src/content/help/articles/observer-mode-guide.mdx#L156) narrows allowed questions and broadens Help data beyond binding scope. | AUD-038-006 |
| T-AA163 | [x] | UNVERIFIED | [Snapshot record](../../snapshot-record.json#L1) contains role/identity assertions without per-approval timestamps or reviewed-source binding; no completed dual-review evidence. | AUD-038-002, AUD-038-020 |

#### Publication And Build Tooling

| Original task | Original state | Status | Concrete source/test evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| T-AA164 | [x] | PARTIAL | [Workflow](../../.github/workflows/help-snapshot.yml#L23) lacks trusted review retrieval, installed mode, staged dev/test/prod and actual publication. | AUD-038-002, AUD-038-003, AUD-038-018 |
| T-AA165 | [x] | PARTIAL | [Publisher CLI](../../tools/help/publish_snapshot.py#L33) calls chunk-discarding/local-alias helpers, not durable idempotent Search publication/rollback. | AUD-038-003 |
| T-AA166 | [x] | PARTIAL | [Ownership tests](../../tests/contract/help/test_codeowners_dual_approval.py#L17) count tokens, not two qualifying authenticated reviews. | AUD-038-002, AUD-038-019 |
| T-AA167 | [x] | PARTIAL | [Approver DTO](../../apps/api/app/api/routes/help_snapshots.py#L25) lacks approved_at/trusted identity provenance required for persistence. | AUD-038-002, AUD-038-015 |
| T-AA168 | [x] | PARTIAL | [Rollback endpoint](../../apps/api/app/api/routes/help_snapshots.py#L96) reads metadata only, omits alias rebind and complete previous/restored/reason event. | AUD-038-003 |
| T-AA169 | [x] | PARTIAL | [Loader](../../apps/ingest-runner/src/help_snapshot/source_loaders.py#L25) defaults status Active and does not require explicit approved spec/version membership. | AUD-038-003 |
| T-AA170 | [x] | MISSING | No tenant-exclusion consumer in [loader](../../apps/ingest-runner/src/help_snapshot/source_loaders.py#L25) or publication callers after bounded ingest/service/CLI search. | AUD-038-003 |
| T-AA171 | [x] | MISSING | Insert-only publisher role absent; [broader API grant](../../infra/main.bicep#L894) and deferred documentation do not enforce snapshot immutability. | AUD-038-016 |
| T-AA172 | [x] | MISSING | [Deprecation resolver](../../apps/api/app/services/help/deprecation_resolver.py#L17) requires supplied map; no publisher-produced map or reader integration after scoped search. | AUD-038-003, AUD-038-009 |
| T-AA173 | [x] | UNVERIFIED | [Rehearsal template](../../docs/runbooks/help/snapshot-publish-rollback-rehearsal-template.md#L13) is unfilled/dry-run, not timed dev publish/rollback evidence. | AUD-038-003, AUD-038-020 |
| T-AA174 | [x] | PARTIAL | [Freshness CLI](../../tools/help/check_screenshot_freshness.py#L33) passes string anchors incorrectly and only writes local results; live flags/register-only semantics incomplete. | AUD-038-010 |
| T-AA175 | [x] | PARTIAL | [Language lint](../../tools/help/lint_lang_attributes.py#L41) checks per-file strings/MDX, not every term's wrapping in built HTML; no effective mandatory PR gate. | AUD-038-018 |
| T-AA176 | [x] | PARTIAL | [Capture tool](../../tools/help/capture_screenshots.ts#L18) can write one-pixel placeholders, no DOM hash/upload/registry update/sidecars. | AUD-038-010 |
| T-AA177 | [x] | PARTIAL | [Registry](../../tools/help/route_registry.py#L19) defines eight routes, not complete surface set and expected capture JSON; previous-route integration incomplete. | AUD-038-010 |
| T-AA178 | [x] | PARTIAL | [Link checker](../../tools/help/link_checker.py#L37) strips heading fragments and does not validate citation anchor existence. | AUD-038-018 |
| T-AA179 | [x] | PARTIAL | [Author plugin](../../tools/help/rehype-lang-attr.ts#L26) unregistered and defaults to empty required-term list, not a save/commit gate. | AUD-038-018 |
| T-AA180 | [x] | PARTIAL | [Bulk rebaseline](../../tools/help/bulk_rebaseline.py#L13) writes a report only, not grouped durable flags/author refresh tasks. | AUD-038-010 |
| T-AA181 | [x] | PARTIAL | Relocated [Help workflow](../../.github/workflows/help-gates.yml#L3) is manual-only, skips missing inputs and does not gate every relevant PR. | AUD-038-018 |

#### Test Assertions And Discovery

| Original task | Original state | Status | Concrete source/test evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| T-AA182 | [x] | PARTIAL | [OpenAPI tests](../../tests/contract/help/test_help_api_openapi.py#L27) check URL presence/generated document only, not each response/method/security schema. | AUD-038-015, AUD-038-019 |
| T-AA183 | [x] | PARTIAL | [Audit round-trip](../../tests/contract/help/test_chat_audit_schema.py#L10) checks two fields on hand-authored object, not complete persisted HTTP output/raw-input rejection. | AUD-038-005, AUD-038-015, AUD-038-019 |
| T-AA184 | [x] | PARTIAL | [Approval cases](../../tests/contract/help/test_snapshot_record_dual_approval.py#L23) reject same identity/missing role, not verified timestamp/digest-bound approvals or actual index effect. | AUD-038-002, AUD-038-019 |
| T-AA185 | [x] | PARTIAL | [Language cases](../../tests/contract/help/test_lang_attr_lint.py#L20) include missing wrapper, omit valid non-English ancestry and unrelated-wrapper bypass. | AUD-038-018, AUD-038-019 |
| T-AA186 | [x] | PARTIAL | [Hash cases](../../tests/contract/help/test_screen_id_hash.py#L13) cover order/path changes, not actual flag creation/live same-selector DOM change/golden cross-platform result. | AUD-038-010, AUD-038-019 |
| T-AA187 | [x] | PARTIAL | [Partition tests](../../tests/contract/help/test_retrieval_filters_tenant.py#L9) never observe Help Search filter injection or override rejection. | AUD-038-001, AUD-038-004, AUD-038-019 |
| T-AA188 | [x] | CONFLICT | [Order-sensitive assertion](../../tests/contract/help/test_pattern_id_stability.py#L14) correctly matches FR-022a-AMEND/AR-002; original task's order-invariance text is obsolete, not a reason to change the correct helper. | AUD-038-013, AUD-038-020 |
| T-AA189 | [x] | PARTIAL | Relocated [smoke suite](../../tests/contract/help/test_help_routes_smoke.py#L33) checks six routers/status/ETag, but [URL assertion](../../tests/contract/help/test_help_routes_smoke.py#L139) accepts placeholder signature. | AUD-038-010, AUD-038-015, AUD-038-019 |
| T-AA190 | [x] | PARTIAL | [Seeded article test](../../tests/integration/help/test_chat_end_to_end.py#L34) reaches connected extract retrieval, checks event presence not exact citation/order/refusal audit or live model. | AUD-038-004, AUD-038-005, AUD-038-019 |
| T-AA191 | [x] | PARTIAL | [Stopwatch test](../../tests/integration/help/test_snapshot_publish_rollback.py#L25) times metadata route, never asserts real index/alias/previous-restored fields. | AUD-038-003, AUD-038-019 |
| T-AA192 | [x] | PARTIAL | [PII tests](../../tests/integration/help/test_pii_redaction_notice.py#L28) exercise offline email heuristic, not default AU HTTP gateway/mobile/names/persisted-redaction/visible notice. | AUD-038-022, AUD-038-019 |
| T-AA193 | [x] | PARTIAL | [Tenant tests](../../tests/integration/help/test_tenant_isolation.py#L42) check article partition directions/direct slug, not auth overrides/Search/chat/global-doctrine authorization. | AUD-038-001, AUD-038-003, AUD-038-019 |
| T-AA194 | [x] | PARTIAL | [Degraded test](../../tests/integration/help/test_degraded_mode.py#L47) tolerates 200/202/503 and never tests actual offline cache/TTL/disabled chat/shared capacity. | AUD-038-011, AUD-038-019 |
| T-AA195 | [x] | PARTIAL | [SLA tests](../../tests/integration/help/test_support_handoff_sla.py#L23) check durations/returned IDs, not NEMA activation/calendar/channel/ack/event payloads. | AUD-038-014, AUD-038-019 |
| T-AA196 | [x] | PARTIAL | [Persona tests](../../tests/integration/help/test_persona_resolution.py#L8) call helper, not real entitlements/rendered union/chat/audit source; unsafe fallback untested. | AUD-038-001, AUD-038-008, AUD-038-019 |
| T-AA197 | [x] | PARTIAL | [Reconstruction tests](../../tests/integration/help/test_transcript_reconstruction.py#L17) check sorting/empty list only, not observer authorization/age/label/event/history isolation. | AUD-038-005, AUD-038-019 |
| T-AA198 | [x] | PARTIAL | [Deprecation cases](../../tests/integration/help/test_deprecation_notice.py#L8) inspect supplied maps, not publisher-generated maps/current source heading/dated rendered notice. | AUD-038-003, AUD-038-009, AUD-038-019 |
| T-AA199 | [x] | PARTIAL | [No-deletion case](../../tests/integration/help/test_negative_feedback_no_silencing.py#L25) useful; [promotion case](../../tests/integration/help/test_negative_feedback_no_silencing.py#L53) merely counts rows. | AUD-038-013, AUD-038-019 |
| T-AA200 | [x] | PARTIAL | Relocated [persona browser suite](../../apps/web/__tests__/e2e/help/persona-override.spec.ts#L7) skips and checks title; shared Help smoke is not sixteen journeys/tours. | AUD-038-008, AUD-038-019 |
| T-AA201 | [x] | MISSING | No theme/alt/adjacent-keyboard interaction assertions in bounded web-test search; nearest [manifest test](../../tests/contract/help/test_help_models.py#L275) only builds an object. | AUD-038-010, AUD-038-019 |
| T-AA202 | [x] | PARTIAL | [Citation browser stub](../../apps/web/__tests__/e2e/help/chat-citation-flow.spec.ts#L7) skips before any question/badge/navigation assertion. | AUD-038-009, AUD-038-019 |
| T-AA203 | [x] | PARTIAL | [Axe-named stub](../../apps/web/__tests__/e2e/help/accessibility-axe-scan.spec.ts#L7) skips, imports no axe and asserts title only; shared landmark checks are not conformance. | AUD-038-019, AUD-038-021 |
| T-AA204 | [x] | MISSING | No complete Help/chat keyboard journey after scoped tests search; [shared focus checks](../../tests/e2e/interface-coverage.spec.ts#L778) concern home/header only. | AUD-038-019, AUD-038-021 |
| T-AA205 | [x] | PARTIAL | [Offline browser stub](../../apps/web/__tests__/e2e/help/offline-degraded-mode.spec.ts#L7) skips, no offline cache/disabled/search-scope assertion. | AUD-038-011, AUD-038-019 |
| T-AA206 | [x] | PARTIAL | [Replacement eval checker](../../tests/llm-eval/help/test_eval_cite_or_refuse.py#L31) requires one row/keys, not >=200 actual responses/valid citations/90% scoring. | AUD-038-019 |
| T-AA207 | [x] | PARTIAL | [Refusal fixture checker](../../tests/llm-eval/help/test_eval_out_of_scope_refusal.py#L31) verifies shape, not actual 100% refusal across maintained categories. | AUD-038-019 |
| T-AA208 | [x] | MISSING | No Help fabrication audit sampler/evaluator in bounded tests/eval-runner/eval-core/tools search; [task](tasks.md#L354) not delivered by shape checks. | AUD-038-019 |
| T-AA209 | [x] | MISSING | No persona-tagged response/source-relevance evaluator or representative dataset after bounded search; [task](tasks.md#L355) remains binding. | AUD-038-019 |

#### Operational Readiness And Release

| Original task | Original state | Status | Concrete source/test evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| T-AA210 | [x] | PARTIAL | [On-call runbook](../../docs/runbooks/help/on-call.md#L10) authored, but flags/events/rollback recovery do not match connected implementation. | AUD-038-017 |
| T-AA211 | [x] | CONFLICT | [Publish/rollback guide](../../docs/runbooks/help/snapshot-publish-rollback.md#L28) promises different events/automatic recovery from actual path. | AUD-038-003, AUD-038-017 |
| T-AA212 | [x] | CONFLICT | [Staleness guide](../../docs/runbooks/help/screenshot-staleness.md#L19) substitutes fourteen days for required one release, without explicit superseding authority. | AUD-038-010 |
| T-AA213 | [x] | PARTIAL | [Support configuration guide](../../docs/configuration/help-support-handoff.md#L1) describes intended fields/SLAs but mismatches active schema/update route and lacks live activation. | AUD-038-014, AUD-038-017 |
| T-AA214 | [x] | CONFLICT | [Baseline](baselines/pre-launch-support.md#L39) has TBD values and wrong 25%-TTR/30-day success definition, not required actual fourteen-day prelaunch capture. | AUD-038-020 |
| T-AA215 | [x] | UNVERIFIED | [Workbook instructions](../../docs/runbooks/help/app-insights-workbook.md#L3) defer actual pinning/configuration; no live dashboard evidence. | AUD-038-017, AUD-038-020 |
| T-AA216 | [x] | UNVERIFIED | [Alert instructions](../../docs/runbooks/help/metric-alerts.md#L17) are not deployed alerts/action-group/pager receipt. | AUD-038-017, AUD-038-020 |
| T-AA217 | [x] | CONFLICT | [Chaos drill](../../docs/runbooks/help/chaos-drill-snapshot-rollback.md#L9) alters key authentication instead of managed-identity alias failure; no valid rehearsal result. | AUD-038-017 |
| T-AA218 | [x] | UNVERIFIED | [Attestation README](../../docs/attestations/README.md#L1) only; no current Help release attestation JSON in bounded evidence inventory. | AUD-038-016, AUD-038-020 |
| T-AA219 | [x] | UNVERIFIED | Original explicitly says deferred-to-deploy-step; [smoke template](../../docs/runbooks/help/azd-up-smoke-TEMPLATE.md#L1) is not execution or supersession of deployment duty. | AUD-038-020 |
| T-AA220 | [x] | CONFLICT | [Ledger](verification-status.md#L9) misidentifies current CHK meanings and counts 60 versus actual 45 checked; task gate not completed by obsolete mapping. | AUD-038-020 |
| T-AA221 | [x] | UNVERIFIED | [Ledger](verification-status.md#L46) defers participant test; no >=20-person/all-persona 95%-within-60-second result located. | AUD-038-020 |
| T-AA222 | [x] | UNVERIFIED | [Fixture checker](../../tests/llm-eval/help/test_eval_cite_or_refuse.py#L31) is not release-candidate 90%/100% model evaluation archive. | AUD-038-019, AUD-038-020 |
| T-AA223 | [x] | UNVERIFIED | [Deferred fabrication sample](verification-status.md#L46) has no executed audit/zero-fabrication result; sampler itself missing. | AUD-038-019, AUD-038-020 |
| T-AA224 | [x] | UNVERIFIED | [Memory isolation tests](../../tests/integration/help/test_tenant_isolation.py#L42) do not prove live red-team/audit retrieval/AU attestation duties. | AUD-038-001, AUD-038-005, AUD-038-016, AUD-038-020 |
| T-AA225 | [x] | UNVERIFIED | [Skipped a11y suite](../../apps/web/__tests__/e2e/help/accessibility-axe-scan.spec.ts#L7), absent genuine asset inventory and study/latency/freshness reports do not establish five outcomes. | AUD-038-010, AUD-038-017, AUD-038-019, AUD-038-020, AUD-038-021 |
| T-AA226 | [x] | UNVERIFIED | [Sign-off template](../../docs/runbooks/help/release-signoff-TEMPLATE.md#L24) lacks real release identity/signatures; not proof of both authorized approvals. | AUD-038-002, AUD-038-020 |

### Authored Content Obligations

All 45 MDX bodies were inspected, not just filenames/frontmatter. The sixteen persona-specific
needs are individually assessed in T-AA128 through T-AA143 above: each needs overview, decision
rights, first-fifteen-minute tour, primary-screen walkthroughs, boundaries, handoffs and tuned starter
prompts. Every one is PARTIAL or CONFLICT; none has actual embedded screenshots or connected
persona landing. The table below makes every primary-screen obligation independently traceable.

| Screen obligation | Status | Full article inspected and specific assessment | Follow-up |
| --- | --- | --- | --- |
| SCREEN-01 Disaster Mapper | PARTIAL | [Mapper](../../apps/web/src/content/help/articles/screen-by-screen/disaster-mapper.mdx#L1): prose exists; screenshot marker is comment, no numbered image/keyboard equivalence. | AUD-038-007, AUD-038-010 |
| SCREEN-02 Governance Dashboard | PARTIAL | [Governance](../../apps/web/src/content/help/articles/screen-by-screen/governance-dashboard.mdx#L1): prose without captured active UI; authority ordering/context not reconciled. | AUD-038-007, AUD-038-008, AUD-038-010 |
| SCREEN-03 Multi-Jurisdiction Filter | PARTIAL | [Filter](../../apps/web/src/content/help/articles/screen-by-screen/multi-jurisdiction-filter.mdx#L1): text exists, no captured jurisdiction theme/callouts or actual Help context propagation. | AUD-038-007, AUD-038-008, AUD-038-010 |
| SCREEN-04 Simulation Control | PARTIAL | [Simulation](../../apps/web/src/content/help/articles/screen-by-screen/simulation-control.mdx#L1): prose; screenshot/keyboard pairs absent and current playback destination not established. | AUD-038-007, AUD-038-008, AUD-038-010 |
| SCREEN-05 Alert Composer | CONFLICT | [Composer](../../apps/web/src/content/help/articles/screen-by-screen/alert-composer.mdx#L177): conditional IC approval; no multilingual editor/checker/channel visual sequence. | AUD-038-006, AUD-038-007, AUD-038-010 |
| SCREEN-06 Communication Agent | PARTIAL | [Communication surface](../../apps/web/src/content/help/articles/screen-by-screen/agent-communication.mdx#L1): text but no actual callouts/keyboard equivalent; doctrine/approval path requires correction. | AUD-038-006, AUD-038-007, AUD-038-010 |
| SCREEN-07 Evacuation Agent | PARTIAL | [Evacuation surface](../../apps/web/src/content/help/articles/screen-by-screen/agent-evacuation.mdx#L1): no annotated variants and no connected end-to-end IC approval walkthrough. | AUD-038-006, AUD-038-007, AUD-038-010 |
| SCREEN-08 Monitoring Agent | PARTIAL | [Monitoring surface](../../apps/web/src/content/help/articles/screen-by-screen/agent-monitoring.mdx#L1): prose only; no visual/keyboard equivalence or role-specific tested procedure. | AUD-038-007, AUD-038-010 |
| SCREEN-09 Risk Assessment Agent | CONFLICT | [Risk surface](../../apps/web/src/content/help/articles/screen-by-screen/agent-risk-assessment.mdx#L1): no images; linked risk-calibration procedure contradicts threshold semantics. | AUD-038-006, AUD-038-007, AUD-038-010 |
| SCREEN-10 Resource Allocation Agent | PARTIAL | [Resource surface](../../apps/web/src/content/help/articles/screen-by-screen/agent-resource-allocation.mdx#L1): text but no paired annotated asset/keyboard workflow. | AUD-038-007, AUD-038-010 |
| SCREEN-11 Audit/Observer | CONFLICT | [Observer surface](../../apps/web/src/content/help/articles/screen-by-screen/audit-observer-view.mdx#L1): prose and misleading live-audit Help guidance elsewhere; no actual screenshot/export/reconstruction flow. | AUD-038-005, AUD-038-006, AUD-038-007, AUD-038-010 |
| SCREEN-12 Persona Switcher | PARTIAL | [Switcher](../../apps/web/src/content/help/articles/screen-by-screen/persona-switcher.mdx#L1): describes entitled switching but active Help does not use it; imagery absent. | AUD-038-001, AUD-038-008, AUD-038-010 |
| SCREEN-13 Settings | PARTIAL | [Settings](../../apps/web/src/content/help/articles/screen-by-screen/settings.mdx#L1): text without actual theme/accessibility/callout equivalence. | AUD-038-007, AUD-038-010, AUD-038-021 |
| SCREEN-14 Login | PARTIAL | [Login](../../apps/web/src/content/help/articles/screen-by-screen/login.mdx#L1): sign-in prose exists but anonymous Help defaults contradict claimed authentication boundary; no images. | AUD-038-001, AUD-038-007, AUD-038-010 |

| Domain obligation | Status | Inspected source, required substance and residual gap | Follow-up |
| --- | --- | --- | --- |
| DOMAIN-1 Getting started | PARTIAL | [Getting started](../../apps/web/src/content/help/articles/getting-started.mdx#L10) covers overview/sign-in/persona/filter/theme in prose; controls/guarantees and visuals do not match active implementation. | AUD-038-007, AUD-038-008, AUD-038-010 |
| DOMAIN-2 Persona workflows | PARTIAL | [IC](../../apps/web/src/content/help/personas/incident-commander/landing.mdx#L11) plus fifteen individually assessed task rows: missing named workflow actions/tuned prompts, no active journeys. | AUD-038-006, AUD-038-007, AUD-038-008 |
| DOMAIN-3 Screens | PARTIAL | Fourteen screen rows above cover every explicit name; no actual numbered callouts/alt/keyboard pairs. Plan's >=18 launch screen target is not retired. | AUD-038-007, AUD-038-010, AUD-038-020 |
| DOMAIN-4 Simulation | PARTIAL | [Playbook](../../apps/web/src/content/help/articles/playbooks/simulation.mdx#L10): configuration/multi-jurisdiction/warp/debrief exist, observation export and current route missing. | AUD-038-007, AUD-038-008 |
| DOMAIN-5 Agents | CONFLICT | [Communication](../../apps/web/src/content/help/articles/playbooks/agent-communication.mdx#L1), [Evacuation](../../apps/web/src/content/help/articles/playbooks/agent-evacuation.mdx#L115), [Monitoring](../../apps/web/src/content/help/articles/playbooks/agent-monitoring.mdx#L1), [Risk](../../apps/web/src/content/help/articles/playbooks/agent-risk-assessment.mdx#L174), [Resource](../../apps/web/src/content/help/articles/playbooks/agent-resource-allocation.mdx#L1) all read: evidence/confidence prose exists; IC chain/risk advice conflict and actual screenshots absent. | AUD-038-006, AUD-038-007, AUD-038-010 |
| DOMAIN-6 Observer | CONFLICT | [Audit guide](../../apps/web/src/content/help/articles/audit-observer-mode.mdx#L35) and [observer guide](../../apps/web/src/content/help/articles/observer-mode-guide.mdx#L156): timeline/integrity prose, false live-audit grounding/question limits, incomplete compliance/lessons export. | AUD-038-005, AUD-038-006, AUD-038-007 |
| DOMAIN-7 Accessibility | PARTIAL | [How-to](../../apps/web/src/content/help/articles/accessibility-how-to.mdx#L24) and [multilingual guide](../../apps/web/src/content/help/articles/multilingual-authoring.mdx#L1): keyboard/AT/theme prose, incomplete actual PIO checker/Auslan steps and unsupported conformance claims. | AUD-038-006, AUD-038-007, AUD-038-021 |
| DOMAIN-8 Troubleshooting | PARTIAL | [FAQ](../../apps/web/src/content/help/articles/troubleshooting.mdx#L10): login/persona/filter/approval/refusal symptoms exist; simulation reset/Help cache recovery and twenty self-contained topic destinations not validated. | AUD-038-007, AUD-038-011, AUD-038-012 |
| DOMAIN-9 Glossary | PARTIAL | [Terms](../../apps/web/src/content/help/glossary/terms.yaml#L1): five cross-linked entries, missing canonical Controller/jurisdictional/Hub coverage and real definition route/alias-first search. | AUD-038-007, AUD-038-008, AUD-038-012 |

The additional [amber confidence](../../apps/web/src/content/help/articles/amber-confidence-badge.mdx#L1),
[NEMA escalation](../../apps/web/src/content/help/articles/cross-border-bushfire-nema.mdx#L1), and
[Principle V](../../apps/web/src/content/help/articles/constitution-principle-v.mdx#L1) articles were
read fully and are assessed in T-AA156, T-AA157 and T-AA158. Content depth cannot be inferred from
45 files, generator output, checked authoring tasks or absence of a model call.

### Nonfunctional And Scope Obligations

Rows represent unique unnumbered duties from spec/plan/research/UI contract, including repeated
mandatory Visual, Chat, Accessibility and Residency sections. Repeated text is mapped to the same
named FR instead of assigned invented original NFR IDs. No runtime/performance/human outcome is
inferred from static source.

| Obligation | Status | Authority and static assessment | Follow-up |
| --- | --- | --- | --- |
| OTHER-01 Visual callouts/prose | MISSING | [Visual requirements](spec.md#L263), FR-006: no genuine imagery/callout mapping, as SCREEN matrix establishes. | AUD-038-010 |
| OTHER-02 Both themes | PARTIAL | FR-007, [UI screenshot contract](contracts/help-ui.contract.ts.md#L69): unused OS fallback is not active-theme switching. | AUD-038-010 |
| OTHER-03 Alt and keyboard equivalence | MISSING | FR-008, visual/accessibility sections: no integrated images or adjacent keyboard blocks after full content review. | AUD-038-010 |
| OTHER-04 Embedded focus | PARTIAL | [UI accessibility contract](contracts/help-ui.contract.ts.md#L182): focus outlines exist but embedded example/dock/tour coverage is unverified. | AUD-038-021 |
| OTHER-05 Reader freshness notice | PARTIAL | FR-010/FR-010b: no active first/next-release lifecycle; one-cycle duty not replaced by runbook's days. | AUD-038-010 |
| OTHER-06 Approved-only chat/no HEAD | CONFLICT | [Mandatory chat requirements](spec.md#L271), FR-011: selected snapshot-only architecture not retired by current Cosmos extract path/seed bypass. | AUD-038-003, AUD-038-004 |
| OTHER-07 Refusal/support/claim citations | PARTIAL | FR-012, FR-013, FR-014: no claim-level source link, category policy or actual support destination; not an external-weather assistant. | AUD-038-004, AUD-038-009, AUD-038-014 |
| OTHER-08 Persona/jurisdiction/conflicts | PARTIAL | FR-015, FR-016, FR-025: fixed persona/boost-only extraction and unconnected conflict helper do not enforce authorized scoped advice. | AUD-038-001, AUD-038-004, AUD-038-008 |
| OTHER-09 Redaction/audit/degraded | CONFLICT | FR-017, FR-020, FR-026: AU gateway bypass, partial durability and inactive offline controls contradict mandatory repeated chat section. | AUD-038-005, AUD-038-011, AUD-038-022 |
| OTHER-10 AU data plane | UNVERIFIED | [Residency section](spec.md#L290) includes processing/embeddings/indexes/retrieval/storage/logs, not just agent account region; full attestation absent. | AUD-038-016, AUD-038-020 |
| OTHER-11 Tenant/audit isolation | CONFLICT | Repeated residency/isolation section and FR-019/020: partitions exist, but spoofable principal/globalized content and broad permissions undermine guarantees. | AUD-038-001, AUD-038-003, AUD-038-005, AUD-038-016 |
| OTHER-12 WCAG/AT/full keyboard | UNVERIFIED | [Accessibility section](spec.md#L283) and UI contract: zero A/AA requires real automated/manual coverage, not skipped titles. | AUD-038-019, AUD-038-021, AUD-038-020 |
| OTHER-13 Public multilingual duty | CONFLICT | Constitution V and FR-024 require affected community/Aboriginal languages and accessible warnings; false Principle V and incomplete Auslan/checker instructions fail authored scope. | AUD-038-006, AUD-038-007 |
| OTHER-14 English Help launch | CONFLICT | [Pass-1 clarification](spec.md#L335) explicitly excludes Help localisation; [authoring guide](../../apps/web/src/content/help/articles/multilingual-authoring.mdx#L218) invents translation gates without authority. | AUD-038-006 |
| OTHER-15 No public unauthenticated portal | CONFLICT | [Out of scope](spec.md#L306) excludes it; proxy/SSR anonymous defaults and absent Help JWT protection violate the boundary. | AUD-038-001 |
| OTHER-16 No voice interaction | IMPLEMENTED | Out-of-scope voice I/O absent in active [text chat](../../apps/web/src/components/help/ChatPanel.tsx#L26); no audio capture/synthesis path found in bounded Help source. | none |
| OTHER-17 Advisory-only chat | PARTIAL | No direct operational mutation tools in [active agent](../../apps/agents/help_assistant/agent.py#L359); advice can still exceed active-role rights, especially observer. | AUD-038-004, AUD-038-006 |
| OTHER-18 Complement doctrine training | CONFLICT | Help must not replace doctrine training; [false verbatim Principle V](../../apps/web/src/content/help/articles/constitution-principle-v.mdx#L29) misrepresents its authority. | AUD-038-006 |
| OTHER-19 Reuse tenant/persona/jurisdiction model | PARTIAL | [Assumptions](spec.md#L296), [research J](research.md#L175): shared registry exists but header-first caller, arbitrary overrides and independent client ordering drift. | AUD-038-001, AUD-038-008, AUD-038-015 |
| OTHER-20 Reuse minimisation without waiver | CONFLICT | [Research E](research.md#L101) explicitly mandates AU Help redaction, whereas common function bypasses AU; no superseding Help evidence. | AUD-038-022 |
| OTHER-21 Constitution unchanged/human/no-silencing | PARTIAL | Plan constitution gates require life-safety, human signoff, transparent logs and graceful degradation; no automatic feedback deletion exists, but approval/offline/audit controls incomplete. | AUD-038-002, AUD-038-005, AUD-038-011, AUD-038-013 |
| OTHER-22 Screenshot convention clarification | SUPERSEDED | Earlier implementation-choice assumption is explicitly tightened by FR-010a and FR-010a-AMEND at [spec](spec.md#L128) and [amendment](spec.md#L194); live fingerprint requirement wins. | AUD-038-010 |
| OTHER-23 Configurable support | PARTIAL | [Assumptions](spec.md#L296) defer to binding FR-023a/b; missing config must fall back, not fail as active API does. | AUD-038-014 |
| OTHER-24 Existing services/packages | PARTIAL | [Plan structure](plan.md#L86) prohibits new compute/workspace; services reused, but Help agent/ingest installed package paths incomplete. | AUD-038-015, AUD-038-018 |
| OTHER-25 Toolchain compatibility | PARTIAL | [Plan technical context](plan.md#L21): Python/FastAPI/Pydantic and TS/React/Next exist; requested locked deps, strict typing and MDX integration incomplete. | AUD-038-015, AUD-038-018 |
| OTHER-26 Metadata-only Cosmos bodies | CONFLICT | [Research A](research.md#L12) selects MDX static UI plus Search body, Cosmos metadata only; [seed](../../scripts/seed_loader.py#L441) stores mutable current bodies and runtime renderer fetches them. | AUD-038-003, AUD-038-008 |
| OTHER-27 Retrieval-only AU Foundry configuration | PARTIAL | [Research C](research.md#L55) fixes one agent/env, retrieval only, temperature 0, top_p 0.1, 1500 tokens; YAML exists but live implementation stub, no authorized substitution. | AUD-038-004, AUD-038-016 |
| OTHER-28 First-byte latency | UNVERIFIED | Plan <800 ms p95 is distinct from SC-007 useful-answer median; no representative distribution/producer evidence. | AUD-038-017, AUD-038-020 |
| OTHER-29 Cached article render | UNVERIFIED | Plan p95 <500 ms goal not established by runtime API fetch/Markdown or generic build statements. | AUD-038-008, AUD-038-020 |
| OTHER-30 Offline lookup latency | UNVERIFIED | Plan <=50 ms goal cannot be measured from unconnected cache code; shared cache and TTL require implementation first. | AUD-038-011, AUD-038-020 |
| OTHER-31 Publication performance | UNVERIFIED | Plan alias flip <60 seconds and rollback <=300 seconds require real clients/timed rehearsal; metadata stopwatch is not evidence. | AUD-038-003, AUD-038-017, AUD-038-020 |
| OTHER-32 Scale and content estimates | PARTIAL | Plan >=10 operational/6 clusters and >=18 screen IDs: sixteen landings/fourteen named articles, eight registry routes; approximate 250 articles/600 terms/~100 turns daily/~20 snapshots yearly are capacity assumptions, not exact issue quotas. | AUD-038-007, AUD-038-010, AUD-038-020 |
| OTHER-33 Shared cache/privacy envelope | PARTIAL | [Research F](research.md#L119): lazy viewed+glossary+FAQ, <=500 MB shared, fourteen days, audit refresh; separate unused browser DB does not implement it. | AUD-038-011 |
| OTHER-34 Screenshot storage contract | PARTIAL | [Research D](research.md#L84): WebP plus PNG fallback/alt JSON, seeded fixture capture, private Blob immutability/90-day soft delete and registry update are not implemented end to end. | AUD-038-010, AUD-038-016 |
| OTHER-35 Authoring/build/runtime gates | PARTIAL | [Research G](research.md#L137): source lang validation, built HTML lint/pa11y and every-route axe/manual AT are required separately; gates presently weak/unconnected/skipped. | AUD-038-018, AUD-038-019, AUD-038-021 |
| OTHER-36 Cultural authority | UNVERIFIED | Research G requires registry consultation before publishing language content; [consultation index](../../docs/cultural-authority/help/INDEX.md#L8) is pending/TBD. | AUD-038-007, AUD-038-020 |
| OTHER-37 Queue-only human content changes | PARTIAL | [Research H](research.md#L161): pending feedback does not delete content, but stable pattern/window/author backlog and approved withdrawal incomplete. | AUD-038-003, AUD-038-013 |
| OTHER-38 No caller-controlled retrieval filter | CONFLICT | [Research I](research.md#L169): tenant sourced from authenticated principal; active Help header/facade path does not use hard Search wrapper. | AUD-038-001, AUD-038-004 |
| OTHER-39 Reproducible CI/test pyramid | PARTIAL | [Quickstart section 6](quickstart.md#L144): contract/integration, web/a11y, browser, model, IaC gates required; missing dependencies/markers/manual-only workflows do not establish them. | AUD-038-018, AUD-038-019 |
| OTHER-40 No authoring/runtime code confusion | CONFLICT | [UI boundary](contracts/help-ui.contract.ts.md#L199) says MDX built, no new auth/UI audit writes; runtime raw Markdown and header defaults differ, although UI does not directly write audit storage. | AUD-038-001, AUD-038-005, AUD-038-008, AUD-038-018 |

### Data And API Contracts

The data-model preamble also conflicts internally: it describes ULID IDs and universal timestamps/ETag
but later requires article `id == slug`, introduces `glossary_term_links` without a field, and allows
global Help/profile examples where the amendment restricts tenancy. The OFFICIAL-sensitive model
possibility versus OFFICIAL-only admission, ID-list versus full-Citation turn schema, error-correlation
shape and opposite authority-rank polarity require explicit compatibility decisions, not silent waiver.

| Contract obligation | Status | Concrete model/boundary evidence and gap | Follow-up |
| --- | --- | --- | --- |
| ENTITY-01 HelpArticle | PARTIAL | [Model](../../packages/domain/src/ama_domain/help_article.py#L60): missing relational validators, active rows include body_md beyond metadata schema and bypass approved transitions. | AUD-038-003, AUD-038-015 |
| ENTITY-02 AnnotatedScreenshot/Callout | PARTIAL | [Model](../../packages/domain/src/ama_domain/annotated_screenshot.py#L10): variants/fields exist, empty callouts/equivalents and actual DOM/storage lifecycle incomplete. | AUD-038-010, AUD-038-015 |
| ENTITY-03 GlossaryTerm | PARTIAL | [Model](../../packages/domain/src/ama_domain/glossary_term.py#L12): basic fields, incomplete standards-language validation/cross-link rendering. | AUD-038-007, AUD-038-015 |
| ENTITY-04 PersonaHelpProfile | PARTIAL | [Profile](../../packages/domain/src/ama_domain/persona_help_profile.py#L29): registry validation partial, unknown IDs/order/active tiles unconnected. | AUD-038-008, AUD-038-015 |
| ENTITY-05 KnowledgeCorpusSource | PARTIAL | [Model](../../packages/domain/src/ama_domain/knowledge_corpus_source.py#L27): typed status exists; active loader bypasses source-kind/approval/scope schema. | AUD-038-003, AUD-038-015 |
| ENTITY-06 ChatSession/ChatTurn | PARTIAL | [Model](../../packages/domain/src/ama_domain/chat_session.py#L42): thirty-day annotation and turns exist, no live writes/ownership continuation/purge. | AUD-038-005, AUD-038-015 |
| ENTITY-07 Citation | CONFLICT | [Doctrine Citation](../../packages/domain/src/ama_domain/citation.py#L21) differs from [Help wire schema](contracts/help-api.openapi.yaml#L447); conformance checks only names. | AUD-038-009, AUD-038-015 |
| ENTITY-08 HelpFeedback | PARTIAL | [Model](../../packages/domain/src/ama_domain/help_feedback.py#L25) pattern/timestamp/source exists, active pending rows omit it. | AUD-038-013, AUD-038-015 |
| ENTITY-09 StalenessFlag | PARTIAL | [Model](../../packages/domain/src/ama_domain/staleness_flag.py#L20) release fields exist, facade targets wrong container/status and no release workflow. | AUD-038-010, AUD-038-015 |
| ENTITY-10 SnapshotRecord/Approver | PARTIAL | [Model](../../packages/domain/src/ama_domain/snapshot_record.py#L39) checks labels, HTTP source_set/timestamps/immutability and provenance differ. | AUD-038-002, AUD-038-003, AUD-038-015 |
| ENTITY-11 SupportHandoffRecord | CONFLICT | [Domain](../../packages/domain/src/ama_domain/support_handoff_record.py#L13) has required nested channel/SLA flags, active DTO does not. | AUD-038-014, AUD-038-015 |
| ENTITY-12 ContentReviewBacklogItem | PARTIAL | [Aggregator](../../apps/api/app/services/help/feedback_aggregator.py#L25) can produce needs_review model, not connected tenant/window/pattern storage. | AUD-038-013, AUD-038-015 |
| ENTITY-13 ChatAuditEntry | PARTIAL | [Model](../../packages/domain/src/ama_domain/chat_audit_entry.py#L20) redacted-only/frozen outer shape, incomplete durable branches/approval fields/observer access. | AUD-038-005, AUD-038-015, AUD-038-022 |
| DATA-14 Cosmos mapping | PARTIAL | [IaC containers](../../infra/bicep/modules/cosmos-help-containers.bicep#L48) declare seven/partition/TTLs, missing effective immutable role and divergent staleness/analytics/index expectations. | AUD-038-010, AUD-038-016 |
| DATA-15 Search schema/idempotency | CONFLICT | [Embedder](../../apps/ingest-runner/src/help_snapshot/embedder.py#L63) emits wrong field names/zero fallback; bootstrap lacks body_vector and ingester discards chunks. | AUD-038-003 |
| DATA-16 Cross-language schema sync | PARTIAL | [Twin test](../../tests/contract/help/test_domain_twin_sync.py#L49) checks names; export/field drift remains undetected. | AUD-038-015, AUD-038-019 |
| API-01 POST chat ask | PARTIAL | [Handler](../../apps/api/app/api/routes/help_chat.py#L54): SSE exists, identity/extra fields/denial status/claims/citations/session/audit semantics differ. | AUD-038-001, AUD-038-004, AUD-038-005, AUD-038-009, AUD-038-015, AUD-038-022 |
| API-02 POST chat feedback | PARTIAL | [Handler](../../apps/api/app/api/routes/help_chat.py#L223): 202/pending facade, no authoritative target/pattern/aggregation/comment-redaction path. | AUD-038-013, AUD-038-015 |
| API-03 GET own session | PARTIAL | [Read route](../../apps/api/app/api/routes/help_chat.py#L246) checks supplied tenant/user via repo, but no session writer/expiry/audit-only reconstructed boundary. | AUD-038-001, AUD-038-005 |
| API-04 GET article listing | PARTIAL | [Listing](../../apps/api/app/api/routes/help_articles.py#L15) defaults to caller persona, but trusts caller identity, ignores continuation and lacks approved status-snapshot projection. | AUD-038-003, AUD-038-008, AUD-038-012, AUD-038-015 |
| API-05 GET article slug | PARTIAL | [Read](../../apps/api/app/api/routes/help_articles.py#L35) has ETag but no nested slug/deprecation/approved published metadata-body boundary. | AUD-038-003, AUD-038-008, AUD-038-015 |
| API-06 GET snapshots | PARTIAL | [Snapshots](../../apps/api/app/api/routes/help_snapshots.py#L45) returns raw metadata, not required complete source/approval records and canonical active target. | AUD-038-003, AUD-038-015 |
| API-07 POST publish | PARTIAL | [Publish](../../apps/api/app/api/routes/help_snapshots.py#L82) trusts differing DTO and stores metadata, not authenticated immutable-index publication. | AUD-038-002, AUD-038-003, AUD-038-015 |
| API-08 POST rollback | PARTIAL | [Rollback](../../apps/api/app/api/routes/help_snapshots.py#L96) does not restore alias or complete typed previous/restored/timestamp/duration event. | AUD-038-003, AUD-038-015 |
| API-09 GET staleness | PARTIAL | [Facade](../../apps/api/app/repositories/help_repositories.py#L269) queries unprovisioned staleness_flags with status absent from designed entity. | AUD-038-010, AUD-038-015 |
| API-10 POST staleness | PARTIAL | [Routes](../../apps/api/app/api/routes/help_screenshots.py#L1) do not establish contract manual raise/clear body, correct store and author/build authority. | AUD-038-001, AUD-038-010, AUD-038-015 |
| API-11 POST clear flag | PARTIAL | [Clear surface](../../apps/api/app/api/routes/help_screenshots.py#L1) lacks authorized author/refresh provenance and designed lifecycle persistence. | AUD-038-001, AUD-038-010 |
| API-12 GET signed theme URL | PARTIAL | [URL route](../../apps/api/app/api/routes/help_screenshots.py#L65) returns placeholder signature, not verified tenant/asset five-minute Blob grant. | AUD-038-001, AUD-038-010, AUD-038-016 |
| API-13 GET search | PARTIAL | [Search](../../apps/api/app/api/routes/help_search.py#L22) omits bodies/aliases/complete authorized results and schema fidelity. | AUD-038-012, AUD-038-015 |
| API-14 GET support | CONFLICT | [Support API](../../apps/api/app/api/routes/help_support_handoff.py#L33) returns 404 when missing and different record fields. | AUD-038-014, AUD-038-015 |
| API-15 PUT support | PARTIAL | [Support API](../../apps/api/app/api/routes/help_support_handoff.py#L16) lacks admin enforcement and binding schema/calendar/incident lifecycle. | AUD-038-001, AUD-038-014, AUD-038-015 |
| API-16 Common prefix/security/errors | CONFLICT | [Settings](../../apps/api/app/core/settings.py#L10) default `/api`; contract `/api/v1`, bearer security, error/correlation/extra-field/Accept-Language requirements are not reconciled. | AUD-038-001, AUD-038-015 |

### UI Contract And Telemetry Duties

Each route and component is individually covered in the original task matrix, including public
props, side-panel/full-page shared state, screenshot themeOverride, required keyboard caption IDs,
refusal suggestions, feedback acknowledgement callback and persona union polarity. None of those
contracts is superseded by a similarly named but unconnected component. The ten event obligations
are separately assessed below; raw free text is forbidden by the contract even in help search telemetry.

| Event obligation | Status | Required trigger/properties and actual evidence | Follow-up |
| --- | --- | --- | --- |
| TELEMETRY-01 help.affordance.opened | PARTIAL | [Contract](contracts/help-ui.contract.ts.md#L176), [telemetry module](../../apps/web/src/lib/help/telemetry.ts#L6): surface/via on actual click/keyboard open not wired. | AUD-038-008, AUD-038-017 |
| TELEMETRY-02 help.article.viewed | PARTIAL | Contract article/persona/snapshot mount event not emitted from active SSR/reader path; active persona/source audit also missing. | AUD-038-005, AUD-038-008, AUD-038-017 |
| TELEMETRY-03 help.search.performed | CONFLICT | Contract q_length/result_count/top_kind differs from raw query event shape; active correct trigger not established. | AUD-038-012, AUD-038-017 |
| TELEMETRY-04 help.chat.turn.requested | PARTIAL | Contract session/persona/surface/degraded:false is not supplied by active fixed-persona/no-session store. | AUD-038-005, AUD-038-008, AUD-038-017 |
| TELEMETRY-05 help.chat.turn.completed | PARTIAL | Contract turn/latency/citation/refusal uses done metadata the store ignores; transport first-byte does not equal useful-answer latency. | AUD-038-009, AUD-038-017 |
| TELEMETRY-06 help.chat.redaction_notified | PARTIAL | Contract session event requires actual notice, defeated by AU bypass/duplicate metadata; no correct active event. | AUD-038-009, AUD-038-017, AUD-038-022 |
| TELEMETRY-07 help.chat.degraded.shown | PARTIAL | Contract surface event depends on active degraded detector not connected to chat. | AUD-038-011, AUD-038-017 |
| TELEMETRY-08 help.feedback.submitted | PARTIAL | Contract target/rating after verified acknowledgement not supplied consistently; false-success UI cannot substantiate submission. | AUD-038-013, AUD-038-017 |
| TELEMETRY-09 help.staleness.banner.shown | PARTIAL | Contract target/downgraded event lacks live flags/rendered lifecycle. | AUD-038-010, AUD-038-017 |
| TELEMETRY-10 help.deprecation.notice.shown | PARTIAL | Contract old snapshot/has replacement event unconnected with required dated notice. | AUD-038-009, AUD-038-017 |

### Risk Hypotheses

The [eight plan risks](plan.md#L186) are hypotheses/mitigations, not execution evidence. They remain
relevant even though all original tasks were checked.

| Risk | Status | Required mitigation versus observed control | Follow-up |
| --- | --- | --- | --- |
| R1 Alias zero-result window | PARTIAL | Prewarm >=1 document, health check and atomic switch absent from local-file alias helper; no bounded retry proof. | AUD-038-003, AUD-038-011 |
| R2 Fabrication despite prompt | PARTIAL | Prompt authored but unused, shared citation filter not connected and actual fabrication audit absent. | AUD-038-004, AUD-038-019 |
| R3 Mis-scoped tenant query | CONFLICT | Parameterized partition query exists, but principal is header-selected and global Help/spec admission unsafe; red-team assertions incomplete. | AUD-038-001, AUD-038-003, AUD-038-004, AUD-038-019 |
| R4 Novel PII pattern | CONFLICT | Quarterly recognizer review unverified; more basic AU bypass means current Help does not invoke recognizers at all. | AUD-038-022, AUD-038-020 |
| R5 High-churn stale imagery | PARTIAL | Ordered selector hashing/bulk report helpers do not create live-DOM flags, author tasks or release banners. | AUD-038-010 |
| R6 Rollback over five minutes | UNVERIFIED | Metadata stopwatch and unfilled rehearsal do not measure real restore under load/alias failure. | AUD-038-003, AUD-038-017, AUD-038-020 |
| R7 Negative-feedback brigading | PARTIAL | No automatic deletion exists, but missing target/window/dedup/stable-pattern aggregation can mis-prioritize or lose review work. | AUD-038-013 |
| R8 Shared cache overflow | PARTIAL | Unused max-byte constant/separate DB does not establish LRU shared-envelope enforcement, 80% alert or per-device metrics. | AUD-038-011, AUD-038-017 |

### Feature Checklist Assessment

[Feature checklist](checklists/feature.md#L1): exactly 136 items, 45 checked and 91 unchecked;
86 carry `[Gate]`, of which 28 are checked and 58 unchecked. These are original states, not audited
passes. Each row is assessed by its current text, not obsolete inline CHK references in tasks or ledger.

| Checklist item | Original state | Status | Current obligation and concrete evidence assessment | Follow-up |
| --- | --- | --- | --- | --- |
| CHK001 | [x] | PARTIAL | IC journey: [landing](../../apps/web/src/content/help/personas/incident-commander/landing.mdx#L11) lacks span warnings, active persona flow and screenshots. | AUD-038-007, AUD-038-008, AUD-038-010 |
| CHK002 | [x] | PARTIAL | Operations: [landing](../../apps/web/src/content/help/personas/operations-officer/landing.mdx#L11) lacks reassignment/staging/upward escalation walkthrough. | AUD-038-007, AUD-038-008, AUD-038-010 |
| CHK003 | [x] | PARTIAL | Planning: [landing](../../apps/web/src/content/help/personas/planning-officer/landing.mdx#L11) omits SITREP/intelligence/templates/overlay workflow. | AUD-038-007, AUD-038-008, AUD-038-010 |
| CHK004 | [x] | PARTIAL | Logistics: [landing](../../apps/web/src/content/help/personas/logistics-officer/landing.mdx#L11) omits supply dashboard/consumption/directory/staging. | AUD-038-007, AUD-038-008, AUD-038-010 |
| CHK005 | [x] | CONFLICT | PIO: [landing](../../apps/web/src/content/help/personas/public-information-officer/landing.mdx#L31) conditional approval and false Principle V; checker/Auslan/visuals incomplete. | AUD-038-006, AUD-038-007, AUD-038-010 |
| CHK006 | [x] | PARTIAL | Field: [landing](../../apps/web/src/content/help/personas/field-coordinator/landing.mdx#L11) lacks staging accountability/life-safety-default procedure and active offline Help. | AUD-038-007, AUD-038-011 |
| CHK007 | [x] | PARTIAL | Resilience: [landing](../../apps/web/src/content/help/personas/resilience-planner/landing.mdx#L11) lacks gap export/audit-to-lessons ingestion. | AUD-038-007, AUD-038-010 |
| CHK008 | [x] | CONFLICT | Executive: [landing](../../apps/web/src/content/help/personas/executive-leader/landing.mdx#L80) incorrect approval roles; policy log/escalation omitted. | AUD-038-006, AUD-038-007 |
| CHK009 | [x] | CONFLICT | Observer: [guide](../../apps/web/src/content/help/articles/observer-mode-guide.mdx#L156) restricts questions, extends grounding, incomplete read-only/export flow. | AUD-038-004, AUD-038-006, AUD-038-007 |
| CHK010 | [x] | PARTIAL | Risk: [landing](../../apps/web/src/content/help/personas/risk-manager/landing.mdx#L11) lacks hazard/consequence workflow; calibration conflict. | AUD-038-006, AUD-038-007 |
| CHK011 | [x] | PARTIAL | Fire: [landing](../../apps/web/src/content/help/personas/frontline-fire/landing.mdx#L12) lacks filter/availability/mutual-aid steps and NSW screenshot. | AUD-038-007, AUD-038-010 |
| CHK012 | [x] | PARTIAL | Medical: [landing](../../apps/web/src/content/help/personas/frontline-medical/landing.mdx#L12) lacks medical-supply request walkthrough. | AUD-038-007, AUD-038-010 |
| CHK013 | [x] | PARTIAL | Police: [landing](../../apps/web/src/content/help/personas/frontline-police/landing.mdx#L12) lacks perimeter/enforcement/liaison procedures. | AUD-038-007, AUD-038-010 |
| CHK014 | [x] | PARTIAL | SES/marine: [landing](../../apps/web/src/content/help/personas/frontline-ses-marine/landing.mdx#L12) lacks volunteer activation/full storm flow. | AUD-038-007, AUD-038-010 |
| CHK015 | [x] | PARTIAL | Commonwealth: [landing](../../apps/web/src/content/help/personas/commonwealth/landing.mdx#L11) lacks RFA/doctrine interpretation/recovery handoff. | AUD-038-007, AUD-038-010 |
| CHK016 | [x] | PARTIAL | Cross-sector: [landing](../../apps/web/src/content/help/personas/cross-sector/landing.mdx#L11) misses intake/recovery/volunteer/infrastructure workflows. | AUD-038-007, AUD-038-010 |
| CHK017 | [ ] | PARTIAL | Getting started prose in [article](../../apps/web/src/content/help/articles/getting-started.mdx#L10) exists despite unchecked box; no genuine screenshots/current control fidelity. | AUD-038-007, AUD-038-010 |
| CHK018 | [ ] | PARTIAL | Sixteen persona texts authored, [generic UI](../../apps/web/src/app/help/page.tsx#L222) not curated active journeys. | AUD-038-007, AUD-038-008 |
| CHK019 | [ ] | PARTIAL | Fourteen screen articles exist, e.g. [Mapper](../../apps/web/src/content/help/articles/screen-by-screen/disaster-mapper.mdx#L26); imagery/actual route coverage incomplete. | AUD-038-007, AUD-038-010 |
| CHK020 | [ ] | PARTIAL | [Simulation playbook](../../apps/web/src/content/help/articles/playbooks/simulation.mdx#L10) omits observation export; end-to-end execution unverified. | AUD-038-007, AUD-038-020 |
| CHK021 | [ ] | CONFLICT | Five playbooks authored; [Evacuation](../../apps/web/src/content/help/articles/playbooks/agent-evacuation.mdx#L115) lacks IC chain and Risk advice conflicts. | AUD-038-006, AUD-038-007 |
| CHK022 | [ ] | PARTIAL | [Observer article](../../apps/web/src/content/help/articles/audit-observer-mode.mdx#L35) has timeline narrative, not complete deviation/lessons-export journey. | AUD-038-006, AUD-038-007 |
| CHK023 | [ ] | PARTIAL | [Accessibility how-to](../../apps/web/src/content/help/articles/accessibility-how-to.mdx#L24) exists; keyboard/AT claims and public-authoring steps incomplete. | AUD-038-007, AUD-038-021 |
| CHK024 | [ ] | PARTIAL | [FAQ](../../apps/web/src/content/help/articles/troubleshooting.mdx#L10) omits simulation reset/Help-cache recovery despite many topics. | AUD-038-007, AUD-038-011 |
| CHK025 | [ ] | PARTIAL | [Glossary](../../apps/web/src/content/help/glossary/terms.yaml#L1) lacks Controller/adequate domains; aliases/body search/definition route incomplete. | AUD-038-007, AUD-038-008, AUD-038-012 |
| CHK026 | [ ] | IMPLEMENTED | Persistent Help destination in [global AppShell](../../packages/ui/src/components/layout/app-shell.tsx#L1), despite unchecked original; contextual behavior separate. | AUD-038-008 |
| CHK027 | [ ] | PARTIAL | [Parser](../../apps/web/src/lib/help/deepLinkParser.ts#L13) unused; nested slugs/anchors fail controller/UI contracts. | AUD-038-008, AUD-038-009 |
| CHK028 | [ ] | MISSING | [Mapper comment](../../apps/web/src/content/help/articles/screen-by-screen/disaster-mapper.mdx#L26) representative of no integrated annotated callout/prose assets. | AUD-038-010 |
| CHK029 | [ ] | PARTIAL | [Unused picture](../../apps/web/src/components/help/AnnotatedScreenshot.tsx#L40) supports OS fallback, not genuine paired images/application theme; no test report. | AUD-038-010, AUD-038-020 |
| CHK030 | [ ] | MISSING | [Keyboard primitive](../../apps/web/src/components/help/KeyboardSteps.tsx#L7) unpaired in all content; actual alt/equivalents absent. | AUD-038-010 |
| CHK031 | [ ] | UNVERIFIED | Zero-A/AA attestation absent; [axe suite](../../apps/web/__tests__/e2e/help/accessibility-axe-scan.spec.ts#L7) skips without axe. | AUD-038-019, AUD-038-021, AUD-038-020 |
| CHK032 | [ ] | PARTIAL | [Focus styles](../../apps/web/src/app/globals.css#L2777) exist; embedded examples/dock/tour coverage incomplete. | AUD-038-021 |
| CHK033 | [ ] | UNVERIFIED | [Shared focus checks](../../tests/e2e/interface-coverage.spec.ts#L778) do not verify full Help/chat journey; required test absent. | AUD-038-019, AUD-038-021 |
| CHK034 | [ ] | UNVERIFIED | No one-article-per-persona NVDA/JAWS/equivalent report in scoped accessibility/release evidence; [signoff](../../docs/runbooks/help/release-signoff-TEMPLATE.md#L24) unfilled. | AUD-038-021, AUD-038-020 |
| CHK035 | [ ] | PARTIAL | [Lang lint](../../tools/help/lint_lang_attributes.py#L41) can accept unrelated attribute; no per-language pronunciation spot-check record. | AUD-038-018, AUD-038-021, AUD-038-020 |
| CHK036 | [ ] | PARTIAL | [Chat log](../../apps/web/src/components/help/ChatPanel.tsx#L26) live region exists, but all sending/refused/redacted/complete announcements and redaction truth not asserted. | AUD-038-009, AUD-038-021, AUD-038-022 |
| CHK037 | [ ] | CONFLICT | [Current MDX seed](../../scripts/seed_loader.py#L441) and active facade bypass approved immutable snapshot; no live-spec-HEAD admission safeguard in loader. | AUD-038-003, AUD-038-004 |
| CHK038 | [ ] | PARTIAL | [Loader](../../apps/ingest-runner/src/help_snapshot/source_loaders.py#L25) defaults missing Markdown metadata Active, ignores explicit reviewed set. | AUD-038-003 |
| CHK039 | [ ] | PARTIAL | [Publish DTO](../../apps/api/app/api/routes/help_snapshots.py#L25) omits required per-approver dates/complete source-version provenance. | AUD-038-002, AUD-038-003, AUD-038-015 |
| CHK040 | [x] | CONFLICT | Model frozen/create helper positive, but [broad grant](../../infra/main.bicep#L894) and mutable bodies mean no effective immutable guarantee or actual edit-rejection evidence. | AUD-038-003, AUD-038-016 |
| CHK041 | [x] | PARTIAL | [Approval label tests](../../tests/contract/help/test_snapshot_record_dual_approval.py#L23) do not verify both qualified humans reviewed exact bytes. | AUD-038-002 |
| CHK042 | [x] | MISSING | [Chat audit payload](../../apps/api/app/api/routes/help_chat.py#L182) has snapshot ID but no both approver identities/timestamps; no connected enrichment found. | AUD-038-002, AUD-038-005 |
| CHK043 | [x] | UNVERIFIED | [Metadata stopwatch](../../tests/integration/help/test_snapshot_publish_rollback.py#L25) does not time actual alias flip; rehearsal unfilled. | AUD-038-003, AUD-038-020 |
| CHK044 | [x] | PARTIAL | [Rollback](../../apps/api/app/api/routes/help_snapshots.py#L96) emits incomplete event, missing actual previous/restored target/reason provenance. | AUD-038-003, AUD-038-017 |
| CHK045 | [x] | PARTIAL | [Notice](../../apps/web/src/components/help/DeprecationNotice.tsx#L2) unconnected, lacks old/new IDs/date/current heading. | AUD-038-003, AUD-038-009 |
| CHK046 | [x] | PARTIAL | [Workflow](../../.github/workflows/help-snapshot.yml#L23) cannot establish real once-per-release approved refresh or out-of-cycle equivalent gate. | AUD-038-002, AUD-038-003, AUD-038-020 |
| CHK047 | [x] | PARTIAL | [Hasher](../../packages/domain/src/ama_domain/screen_id_hash.py#L23) uses selector paths, not UI-build live DOM fingerprints for every surface. | AUD-038-010 |
| CHK048 | [x] | PARTIAL | [Capture/checker](../../tools/help/check_screenshot_freshness.py#L33) do not store/compare actual build fingerprints or durable flags. | AUD-038-010 |
| CHK049 | [ ] | MISSING | No connected immediate reader banner/author-task creation in [checker](../../apps/api/app/services/help/staleness_checker.py#L15) and active UI search. | AUD-038-010 |
| CHK050 | [ ] | MISSING | [Banner primitive](../../apps/web/src/components/help/StalenessBanner.tsx#L2) has no release-state consumer; no next-release escalation workflow found. | AUD-038-010 |
| CHK051 | [ ] | PARTIAL | No automatic removal in inspected staleness helpers, but [active lifecycle](../../apps/api/app/repositories/help_repositories.py#L269) absent and forced-removal prevention not demonstrated. | AUD-038-010, AUD-038-019 |
| CHK052 | [ ] | UNVERIFIED | [Workbook artifact](../../infra/bicep/modules/help-app-insights-dashboard.bicep#L27) is not 90%-within-cycle query/result evidence. | AUD-038-017, AUD-038-020 |
| CHK053 | [ ] | CONFLICT | [Active agent](../../apps/agents/help_assistant/agent.py#L359) only extracts current Help rows, omits approved doctrine/spec sources and publication boundary. | AUD-038-003, AUD-038-004 |
| CHK054 | [ ] | PARTIAL | [Token path](../../apps/agents/help_assistant/agent.py#L359) has no category refusal; shape-only fixture is not 100% refusal evidence. | AUD-038-004, AUD-038-014, AUD-038-019 |
| CHK055 | [ ] | PARTIAL | [CitationBadge](../../apps/web/src/components/help/CitationBadge.tsx#L10) malformed fragments, no per-claim attachment. | AUD-038-004, AUD-038-009 |
| CHK056 | [ ] | PARTIAL | [Scorer](../../apps/agents/help_assistant/agent.py#L221) persona boost is not active-role-only retrieval authorization. | AUD-038-001, AUD-038-004, AUD-038-008 |
| CHK057 | [ ] | UNVERIFIED | [Attestor](../../tools/help/attest_au_residency.py#L42) omits shared resources/process-region proof; no release attestation. | AUD-038-016, AUD-038-020 |
| CHK058 | [ ] | CONFLICT | [AU bypass](../../apps/agents/common/model_gateway.py#L198) before recognizers contradicts gateway trace requirement. | AUD-038-022 |
| CHK059 | [ ] | UNVERIFIED | [Fixture checker](../../tests/llm-eval/help/test_eval_cite_or_refuse.py#L31) is not zero-fabrication sampling; nearest articles/support also missing. | AUD-038-004, AUD-038-014, AUD-038-019, AUD-038-020 |
| CHK060 | [ ] | PARTIAL | [Conflict helper](../../apps/api/app/services/help/conflict_surfacer.py#L15) unconnected to retrieval/stream/linked citations. | AUD-038-004, AUD-038-009 |
| CHK061 | [ ] | CONFLICT | [Observer guide](../../apps/web/src/content/help/articles/observer-mode-guide.mdx#L156) and extract path lack enforced observation-only instruction policy. | AUD-038-001, AUD-038-004, AUD-038-006 |
| CHK062 | [ ] | CONFLICT | [Header-selected tenant](../../apps/api/app/api/routes/help_deps.py#L39) and globalized Help/spec content defeat isolation-by-design claim. | AUD-038-001, AUD-038-003, AUD-038-004 |
| CHK063 | [ ] | PARTIAL | [Session container declaration](../../infra/bicep/modules/cosmos-help-containers.bicep#L48) partitioned; actual session persistence absent. | AUD-038-005, AUD-038-016 |
| CHK064 | [ ] | PARTIAL | [Support facade](../../apps/api/app/repositories/help_repositories.py#L275) scopes rows by supplied tenant, not verified principal/admin boundary. | AUD-038-001, AUD-038-014 |
| CHK065 | [x] | PARTIAL | [Backlog facade](../../apps/api/app/repositories/help_repositories.py#L215) stores tenant rows, but header authority and actual review aggregation/author visibility incomplete. | AUD-038-001, AUD-038-013 |
| CHK066 | [ ] | PARTIAL | [Audit query helper](../../apps/api/app/services/help/transcript_reconstructor.py#L16) uses tenant filter, no secured observer endpoint/effective immutable grant. | AUD-038-001, AUD-038-005, AUD-038-016 |
| CHK067 | [x] | UNVERIFIED | [Memory article isolation](../../tests/integration/help/test_tenant_isolation.py#L42) not multi-environment red-team report/zero cross-tenant answers. | AUD-038-001, AUD-038-019, AUD-038-020 |
| CHK068 | [ ] | PARTIAL | [Session upsert](../../apps/api/app/repositories/help_repositories.py#L212) exists but no caller on chat route; AU durable persistence not established. | AUD-038-005, AUD-038-016 |
| CHK069 | [ ] | UNVERIFIED | [30-day model assertion](../../tests/contract/help/test_help_models.py#L251) is not aged-transcript automatic removal, especially on continuing sessions. | AUD-038-005, AUD-038-020 |
| CHK070 | [ ] | UNVERIFIED | [Seven-year IaC TTL](../../infra/bicep/modules/cosmos-help-containers.bicep#L48) authored, not live lifecycle verification/effective append-only protection. | AUD-038-005, AUD-038-016, AUD-038-020 |
| CHK071 | [ ] | UNVERIFIED | No both-window aged-data/purge-alarm record; [monitoring](../../infra/modules/monitoring.bicep#L21) is not that gate. | AUD-038-005, AUD-038-017, AUD-038-020 |
| CHK072 | [ ] | PARTIAL | [Reconstruction helper](../../apps/api/app/services/help/transcript_reconstructor.py#L16) lacks authorized seven-year observer surface. | AUD-038-005 |
| CHK073 | [ ] | PARTIAL | [Browser store](../../apps/web/src/lib/help/chatStore.tsx#L56) has no expiry and own history/audit-only reconstruction unconnected. | AUD-038-005 |
| CHK074 | [x] | PARTIAL | [FeedbackBar](../../apps/web/src/components/help/FeedbackBar.tsx#L13) omits free text/chat responses and trusts non-2xx. | AUD-038-013 |
| CHK075 | [ ] | PARTIAL | [Pending enqueue](../../apps/api/app/repositories/help_repositories.py#L215) does not supply author-visible aggregated content-review backlog. | AUD-038-013 |
| CHK076 | [x] | PARTIAL | [Three-row test](../../tests/integration/help/test_negative_feedback_no_silencing.py#L53) does not assert promotion; active facade never invokes aggregator. | AUD-038-013, AUD-038-019 |
| CHK077 | [ ] | PARTIAL | [No-deletion assertion](../../tests/integration/help/test_negative_feedback_no_silencing.py#L25) is positive, but forced suppression/preapproved withdrawal boundary not fully exercised. | AUD-038-002, AUD-038-013, AUD-038-019 |
| CHK078 | [ ] | PARTIAL | [Refusal card](../../apps/web/src/components/help/RefusalCard.tsx#L12) no direct destination; handoff component unused. | AUD-038-014 |
| CHK079 | [ ] | CONFLICT | [Support DTO](../../apps/api/app/api/routes/help_support_handoff.py#L16) differs from required channel/address/hours/incident fields. | AUD-038-014, AUD-038-015 |
| CHK080 | [ ] | MISSING | [GET support](../../apps/api/app/api/routes/help_support_handoff.py#L33) returns 404 and UI hides; no platform-default fallback path found. | AUD-038-014 |
| CHK081 | [ ] | PARTIAL | [Timer helper](../../apps/api/app/services/help/support_handoff_sla_monitor.py#L12) uses elapsed hours with caller boolean, not business calendar or NEMA state. | AUD-038-014 |
| CHK082 | [ ] | PARTIAL | [Breach emitter](../../apps/api/app/services/help/support_handoff_sla_monitor.py#L37) exists only in unconnected helper, no durable scheduled ack/breach lifecycle. | AUD-038-005, AUD-038-014, AUD-038-017 |
| CHK083 | [ ] | PARTIAL | [Resolver](../../apps/api/app/services/help/persona_resolver.py#L20) sorts but isn't on active caller route; identity/rank polarity unresolved. | AUD-038-001, AUD-038-008 |
| CHK084 | [ ] | PARTIAL | [Persona hook](../../apps/web/src/lib/help/personaContext.ts#L25) unused, override not authorized; resolver fallback broadens entitlement. | AUD-038-001, AUD-038-008 |
| CHK085 | [ ] | PARTIAL | [Chat audit payload](../../apps/api/app/api/routes/help_chat.py#L182) has persona/source but trusts inputs; article-load audit missing. | AUD-038-001, AUD-038-005, AUD-038-008 |
| CHK086 | [ ] | MISSING | [Landing](../../apps/web/src/app/help/page.tsx#L222) generic; no active entitled ranked tile union after component caller search. | AUD-038-008 |
| CHK087 | [ ] | PARTIAL | [Body selection](../../apps/api/app/api/routes/help_chat.py#L62) selects one value, but it is not verified active persona and content retrieval only boosts tags. | AUD-038-001, AUD-038-004, AUD-038-008 |
| CHK088 | [ ] | MISSING | [Cache helper](../../apps/web/src/lib/help/offlineCache.ts#L34) unused; no mandatory preload/viewed-article reader behavior. | AUD-038-011 |
| CHK089 | [ ] | MISSING | [Detector](../../apps/web/src/lib/help/degradedModeDetector.ts#L18) unused; no active disabled chat/uncached retrieval explanation path. | AUD-038-011 |
| CHK090 | [ ] | PARTIAL | [Cache constants](../../apps/web/src/lib/help/offlineCache.ts#L1) are not shared-budget enforcement or measured fourteen-day/500 MB assertion. | AUD-038-011, AUD-038-019 |
| CHK091 | [ ] | MISSING | No reconnect-to-refresh-to-audit caller in scoped cache/worker/server search; [registration](../../apps/web/src/lib/help/sw-register.ts#L2) uncalled. | AUD-038-005, AUD-038-011 |
| CHK092 | [ ] | MISSING | [Cache stale boolean](../../apps/web/src/lib/help/offlineCache.ts#L34) never drives required dated article banner. | AUD-038-011 |
| CHK093 | [ ] | MISSING | Active chat does not consume detector or route user to cached troubleshooting; [ChatPanel](../../apps/web/src/components/help/ChatPanel.tsx#L26) is unconnected to cache. | AUD-038-011 |
| CHK094 | [ ] | PARTIAL | [Shared domain imports](../../packages/domain/src/ama_domain/__init__.py#L22) reused, but duplicate context/DTO semantics and header-selected tenant drift from required model integration. | AUD-038-001, AUD-038-015 |
| CHK095 | [ ] | PARTIAL | [Classification helper](../../apps/api/app/services/help/content_classification_guard.py#L16) disconnected; loader defaults classification/approval and no dual-authority gate. | AUD-038-002, AUD-038-003, AUD-038-004 |
| CHK096 | [ ] | PARTIAL | [Communication playbook](../../apps/web/src/content/help/articles/playbooks/agent-communication.mdx#L1) authored; verified current domain-agent contract walkthrough not established; PIO approval conflict. | AUD-038-006, AUD-038-007, AUD-038-020 |
| CHK097 | [x] | CONFLICT | [Evacuation playbook](../../apps/web/src/content/help/articles/playbooks/agent-evacuation.mdx#L115) does not meet Spec 038's IC-approval scenario regardless of obsolete ledger label. | AUD-038-006, AUD-038-007 |
| CHK098 | [x] | UNVERIFIED | [Monitoring playbook](../../apps/web/src/content/help/articles/playbooks/agent-monitoring.mdx#L1) exists; independent current-agent contract correctness/reviewer attestation not established. | AUD-038-007, AUD-038-020 |
| CHK099 | [x] | UNVERIFIED | [Resource playbook](../../apps/web/src/content/help/articles/playbooks/agent-resource-allocation.mdx#L1) exists; checked box not a contract-accuracy review record. | AUD-038-007, AUD-038-020 |
| CHK100 | [x] | CONFLICT | [Risk playbook](../../apps/web/src/content/help/articles/playbooks/agent-risk-assessment.mdx#L174) gives contradictory calibration guidance; completed current-contract review unverified. | AUD-038-006, AUD-038-007 |
| CHK101 | [x] | MISSING | [Active Help retrieval](../../apps/agents/help_assistant/agent.py#L359) has no docs/aidr source; manifest declaration alone not actual grounded integration. | AUD-038-003, AUD-038-004 |
| CHK102 | [ ] | PARTIAL | [Mapper guide](../../apps/web/src/content/help/articles/screen-by-screen/disaster-mapper.mdx#L26) prose, no captured actual UI/screenshot contract match. | AUD-038-007, AUD-038-010 |
| CHK103 | [ ] | PARTIAL | [Governance guide](../../apps/web/src/content/help/articles/screen-by-screen/governance-dashboard.mdx#L1) exists, rank direction/client context and imagery incomplete. | AUD-038-007, AUD-038-008, AUD-038-010 |
| CHK104 | [ ] | MISSING | [Help agent input](../../apps/agents/help_assistant/agent.py#L30) carries jurisdictions but active ranking/query never uses authorized jurisdiction filter. | AUD-038-001, AUD-038-004, AUD-038-008 |
| CHK105 | [ ] | PARTIAL | [Session repo](../../apps/api/app/repositories/help_repositories.py#L204) and SLA helper not connected to real turn persistence/NEMA banner. | AUD-038-005, AUD-038-014 |
| CHK106 | [ ] | PARTIAL | [Simulation playbook](../../apps/web/src/content/help/articles/playbooks/simulation.mdx#L10) includes warp but wrong replay path/no observation export; runtime match unverified. | AUD-038-007, AUD-038-008 |
| CHK107 | [ ] | PARTIAL | [Rollback](../../apps/api/app/api/routes/help_snapshots.py#L96) metadata only, not five-minute reversible config flip. | AUD-038-003, AUD-038-020 |
| CHK108 | [ ] | CONFLICT | [AU gateway bypass](../../apps/agents/common/model_gateway.py#L198), inactive shared cache and absent persistent lifecycle defeat promised reused controls. | AUD-038-005, AUD-038-011, AUD-038-014, AUD-038-022 |
| CHK109 | [ ] | PARTIAL | No automatic feedback deletion, but [unconnected cache](../../apps/web/src/lib/help/offlineCache.ts#L34) and staleness pipeline do not prove three live no-silencing controls. | AUD-038-010, AUD-038-011, AUD-038-013 |
| CHK110 | [ ] | PARTIAL | [Audit deny branch](../../apps/api/app/api/routes/help_chat.py#L72) has no durable receipt; effective tamper resistance absent. Principle label in checklist does not waive behavior. | AUD-038-005, AUD-038-016, AUD-038-022 |
| CHK111 | [ ] | PARTIAL | [Audit emitter](../../apps/api/app/observability/audit.py#L38) logs names, not complete durable governance event coverage/deprecation/provenance. | AUD-038-003, AUD-038-005, AUD-038-009, AUD-038-014, AUD-038-017 |
| CHK112 | [ ] | UNVERIFIED | [Skipped axe](../../apps/web/__tests__/e2e/help/accessibility-axe-scan.spec.ts#L7), false Principle V and weak lang gates cannot establish multilingual/a11y attestation. | AUD-038-006, AUD-038-018, AUD-038-021, AUD-038-020 |
| CHK113 | [x] | UNVERIFIED | Actual obligation is SC-001 participant usability, not no-silencing; [ledger](verification-status.md#L46) defers it and no report exists. | AUD-038-020 |
| CHK114 | [ ] | UNVERIFIED | SC-002: [shape evaluator](../../tests/llm-eval/help/test_eval_cite_or_refuse.py#L31) no measured 90%/100% rates. | AUD-038-019, AUD-038-020 |
| CHK115 | [ ] | UNVERIFIED | SC-003: no actual Help audit sampler/result after bounded evaluation search; [ledger](verification-status.md#L46) defers. | AUD-038-019, AUD-038-020 |
| CHK116 | [ ] | UNVERIFIED | SC-004: [memory partition test](../../tests/integration/help/test_tenant_isolation.py#L42) no multi-environment answer/audit red-team report. | AUD-038-001, AUD-038-019, AUD-038-020 |
| CHK117 | [ ] | UNVERIFIED | SC-005: [capture script](../../tools/help/capture_screenshots.ts#L18) not real paired-asset coverage output. | AUD-038-010, AUD-038-020 |
| CHK118 | [ ] | UNVERIFIED | SC-006: [axe stub](../../apps/web/__tests__/e2e/help/accessibility-axe-scan.spec.ts#L7) no automated or manual conformance record. | AUD-038-019, AUD-038-021, AUD-038-020 |
| CHK119 | [x] | UNVERIFIED | Actual obligation is SC-007 p50 useful-answer latency, not reconstruction; [workbook](../../infra/bicep/modules/help-app-insights-dashboard.bicep#L27) is not measurement. | AUD-038-017, AUD-038-020 |
| CHK120 | [ ] | UNVERIFIED | SC-008: [tour](../../apps/web/src/components/help/FirstFifteenMinutesTour.tsx#L10) unconnected, no cross-cluster >=80% study. | AUD-038-008, AUD-038-020 |
| CHK121 | [ ] | UNVERIFIED | SC-009: [TBD baseline](baselines/pre-launch-support.md#L39) changes metric and no three-month volume comparison. | AUD-038-020 |
| CHK122 | [x] | UNVERIFIED | SC-010: [post-stream audit](../../apps/api/app/api/routes/help_chat.py#L174) incomplete; no observer retrieval sample/all-turn coverage. | AUD-038-005, AUD-038-016, AUD-038-020 |
| CHK123 | [x] | UNVERIFIED | SC-011: [attestation README](../../docs/attestations/README.md#L1) no per-release AU processing result. | AUD-038-016, AUD-038-020 |
| CHK124 | [x] | UNVERIFIED | SC-012: [staleness guide](../../docs/runbooks/help/screenshot-staleness.md#L19) wrong cycle, no 90% measured backlog report. | AUD-038-010, AUD-038-017, AUD-038-020 |
| CHK125 | [x] | PARTIAL | Out-of-scope refusal/pointer/log: [active token path](../../apps/agents/help_assistant/agent.py#L359) lacks policy/direct contact/refusal event; not verified despite tick. | AUD-038-004, AUD-038-005, AUD-038-014 |
| CHK126 | [ ] | CONFLICT | Cross-tenant refusal before retrieval: [caller](../../apps/api/app/api/routes/help_deps.py#L39) accepts chosen tenant and agent lacks such question policy. | AUD-038-001, AUD-038-004 |
| CHK127 | [ ] | CONFLICT | [AU gateway](../../apps/agents/common/model_gateway.py#L198) does not redact before Help pipeline. | AUD-038-022 |
| CHK128 | [x] | PARTIAL | Actual obligation is conflicting-source notice, not runbook; [detector](../../apps/api/app/services/help/conflict_surfacer.py#L15) unconnected. | AUD-038-004, AUD-038-009 |
| CHK129 | [ ] | PARTIAL | [No-match refusal](../../apps/agents/help_assistant/agent.py#L374) exists, closest article/contact handoff absent. | AUD-038-004, AUD-038-014 |
| CHK130 | [ ] | PARTIAL | [Staleness banner](../../apps/web/src/components/help/StalenessBanner.tsx#L2) exists only as unused primitive. | AUD-038-010 |
| CHK131 | [x] | CONFLICT | [Multilingual article](../../apps/web/src/content/help/articles/multilingual-authoring.mdx#L218) introduces Help localisation contrary to explicit English-only clarification. | AUD-038-006, AUD-038-007 |
| CHK132 | [x] | CONFLICT | No voice/mutation tools positive; [anonymous proxy defaults](../../apps/web/src/app/api/help/[...path]/route.ts#L52) contradict no public Help and guidance misstates doctrine/role scope. | AUD-038-001, AUD-038-006 |
| CHK133 | [x] | UNVERIFIED | [Publication guide](../../docs/runbooks/help/snapshot-publish-rollback.md#L28) authored but inaccurate; [rehearsal template](../../docs/runbooks/help/snapshot-publish-rollback-rehearsal-template.md#L13) not execution. | AUD-038-017, AUD-038-020 |
| CHK134 | [x] | PARTIAL | [On-call guide](../../docs/runbooks/help/on-call.md#L10) exists, but scheduled actual support breach/operational event path incomplete. | AUD-038-014, AUD-038-017 |
| CHK135 | [ ] | UNVERIFIED | [Workbook instructions](../../docs/runbooks/help/app-insights-workbook.md#L3) defer live dashboards/metrics; no SC-002/003/007/009/012 results. | AUD-038-017, AUD-038-020 |
| CHK136 | [ ] | MISSING | No connected tenant onboarding support-record form found in Help UI/config search; [existing support component](../../apps/web/src/components/help/SupportHandoffButton.tsx#L12) is not an admin form. | AUD-038-001, AUD-038-014 |

### Specification Quality Checklist Assessment

[Requirements-quality checklist](checklists/requirements.md#L1) has 28 checked, unnumbered items.
`QUALITY-01` etc. below are report-local row identifiers in original order. IMPLEMENTED in this
table means the specification states the required material, not that the feature meets it in production.

| Quality item | Original state | Status | Original criterion and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| QUALITY-01 | [x] | CONFLICT | No implementation details: [spec FR-010a](spec.md#L128) mandates build-time hashes and [FR-029](spec.md#L178) mandates Cosmos; blanket no-detail assertion is false. | AUD-038-020 |
| QUALITY-02 | [x] | IMPLEMENTED | User-value focus: [stories](spec.md#L10) explain incident-time discovery, safe help and role adoption. | none |
| QUALITY-03 | [x] | PARTIAL | Nontechnical audience: stories readable, [detailed FR amendments](spec.md#L186) introduce implementation mechanisms/identifiers. | AUD-038-020 |
| QUALITY-04 | [x] | IMPLEMENTED | Mandatory sections: [scenarios](spec.md#L8), [requirements](spec.md#L108), [outcomes](spec.md#L208), personas/content/scope present. | none |
| QUALITY-05 | [x] | IMPLEMENTED | No unresolved clarification markers: [Pass 1/2/3 decisions](spec.md#L326) and closure statement exist; historical quoted markers in notes are not unresolved questions. | none |
| QUALITY-06 | [x] | PARTIAL | Testable/unambiguous: many numerical clauses, but rank direction, ID/slug/global-tenancy contract tensions and stale task wording still need explicit resolution. | AUD-038-015, AUD-038-020 |
| QUALITY-07 | [x] | IMPLEMENTED | Measurable criteria: [SC definitions](spec.md#L212) specify denominators/thresholds/windows; absence of actual measurement is tracked separately. | AUD-038-020 |
| QUALITY-08 | [x] | IMPLEMENTED | Outcome-oriented SCs: [success criteria](spec.md#L212) state usability/quality/safety/timing outcomes rather than implementation-only file counts. | none |
| QUALITY-09 | [x] | IMPLEMENTED | Acceptance scenarios: twenty numbered Given/When/Then cases exist across five stories and are individually assessed above. | none |
| QUALITY-10 | [x] | IMPLEMENTED | Edge cases: [ten edges](spec.md#L95) explicitly cover privacy, conflicts, offline, a11y, multilingual and read-only behavior. | none |
| QUALITY-11 | [x] | IMPLEMENTED | Bounded scope: [Out of Scope](spec.md#L306) lists five exclusions; implementation violations do not erase the authored boundary. | AUD-038-001, AUD-038-006 |
| QUALITY-12 | [x] | IMPLEMENTED | [Assumptions](spec.md#L296) and [dependencies](spec.md#L314) are explicit; other specs were not independently audited here. | none |
| QUALITY-13 | [x] | PARTIAL | Clear acceptance for all FRs: explicit clauses/matrix exist, but some contracts disagree and named model fields/route expectations unresolved. | AUD-038-015, AUD-038-020 |
| QUALITY-14 | [x] | IMPLEMENTED | [Five user stories](spec.md#L8) cover primary discovery/chat/visual/playbook/search flows; source gaps evaluated separately. | none |
| QUALITY-15 | [x] | UNVERIFIED | Feature meets measured outcomes: no evidence in a specification-quality tick establishes SC execution, as [ledger deferrals](verification-status.md#L46) confirm. | AUD-038-020 |
| QUALITY-16 | [x] | CONFLICT | No implementation leakage repeats QUALITY-01; [Cosmos persistence](spec.md#L178), deterministic DOM hash and approval-event shapes are explicit technical mandates. | AUD-038-020 |
| QUALITY-17 | [x] | IMPLEMENTED | [Ten operational personas](spec.md#L227) individually list help needs. | none |
| QUALITY-18 | [x] | IMPLEMENTED | [Six sector clusters](spec.md#L240) individually list help needs; runtime ID alias drift is separate. | AUD-038-008 |
| QUALITY-19 | [x] | IMPLEMENTED | [FR-025](spec.md#L163) and [Pass-2 read-only clarification](spec.md#L384) distinguish permitted questions from restricted instructed actions. | AUD-038-004, AUD-038-006 |
| QUALITY-20 | [x] | IMPLEMENTED | [PIO needs](spec.md#L233) and [FR-024](spec.md#L162) specify multilingual/public accessibility duties. | AUD-038-006, AUD-038-007 |
| QUALITY-21 | [x] | IMPLEMENTED | [FR-011](spec.md#L133) enumerates approved Help/doctrine/spec-snapshot sources and exclusions. | AUD-038-003, AUD-038-004 |
| QUALITY-22 | [x] | IMPLEMENTED | [FR-013](spec.md#L139) explicitly defines refusal and suggested destination. | AUD-038-004, AUD-038-014 |
| QUALITY-23 | [x] | IMPLEMENTED | [FR-012](spec.md#L138) requires a citation for every factual claim and source heading deep link. | AUD-038-004, AUD-038-009 |
| QUALITY-24 | [x] | IMPLEMENTED | [FR-019](spec.md#L148) specifies isolation by design; this is not proof of current header-selected implementation. | AUD-038-001, AUD-038-003 |
| QUALITY-25 | [x] | IMPLEMENTED | [FR-017](spec.md#L146) specifies pre-pipeline redaction/notice even though current AU implementation conflicts. | AUD-038-022 |
| QUALITY-26 | [x] | IMPLEMENTED | [FR-018](spec.md#L147) and residency section explicitly require Australian processing/storage/log boundaries. | AUD-038-016, AUD-038-020 |
| QUALITY-27 | [x] | IMPLEMENTED | [FR-020](spec.md#L149) explicitly specifies append-only redacted prompt/citations/response/refusal provenance. | AUD-038-005, AUD-038-022 |
| QUALITY-28 | [x] | IMPLEMENTED | [FR-026](spec.md#L167) and amendments specify cached reading/disabled chat/shared cap/refresh; no delivery claim inferred. | AUD-038-011 |

### Formal Persona Review Duties

The [plan constitution gate owners and additional inputs](plan.md#L33) specify seventeen technical
roles; [cross-functional review narrative](spec.md#L429) claims their participation. This table
assesses each named responsibility independently. There are no signed role-specific review records
for this revision in the scoped evidence, so actual review execution is UNVERIFIED for every role.
The status column describes the supporting implementation, not whether a person attended a review.

| Review duty | Status | Required contribution and source-based assessment | Follow-up |
| --- | --- | --- | --- |
| REVIEW-TECH-01 principal-engineer | PARTIAL | No silencing/reuse/human approval: [queue helper](../../apps/api/app/services/help/feedback_aggregator.py#L25) does not remove content, but publication/approval/offline paths incomplete. | AUD-038-002, AUD-038-003, AUD-038-011, AUD-038-013, AUD-038-020 |
| REVIEW-TECH-02 product-owner-ba | PARTIAL | Persona backlog/content/signoff/baseline: all landings authored, named gaps and [TBD baseline](baselines/pre-launch-support.md#L6) remain; real approval unverified. | AUD-038-006, AUD-038-007, AUD-038-020 |
| REVIEW-TECH-03 sre-engineer | PARTIAL | Graceful degradation/SLO/metrics: [unused cache](../../apps/web/src/lib/help/offlineCache.ts#L34), missing metric producers/alarms and unmeasured recovery. | AUD-038-011, AUD-038-017, AUD-038-020 |
| REVIEW-TECH-04 chaos-engineer | CONFLICT | Quarterly alias-fault/<=300-second rollback: [drill](../../docs/runbooks/help/chaos-drill-snapshot-rollback.md#L9) changes key auth, not alias; rehearsal absent. | AUD-038-003, AUD-038-017, AUD-038-020 |
| REVIEW-TECH-05 compliance-auditor | PARTIAL | APP11 retention/tenant red-team/AU evidence: [TTL IaC](../../infra/bicep/modules/cosmos-help-containers.bicep#L48) authored, no actual purge/audit/access/residency records. | AUD-038-001, AUD-038-005, AUD-038-016, AUD-038-020 |
| REVIEW-TECH-06 security-engineer | CONFLICT | Privacy/identity/tenant/immutable audit: [AU gateway](../../apps/agents/common/model_gateway.py#L198), header selection and broad grants violate intended controls. | AUD-038-001, AUD-038-005, AUD-038-016, AUD-038-022 |
| REVIEW-TECH-07 accessibility-tester | PARTIAL | WCAG/lang/AT pronunciation gates: [axe stub](../../apps/web/__tests__/e2e/help/accessibility-axe-scan.spec.ts#L7) and weak language lint; no signed AT/cultural evidence. | AUD-038-018, AUD-038-019, AUD-038-021, AUD-038-020 |
| REVIEW-TECH-08 ux-designer | PARTIAL | Contextual Help, entitled personas, theme/annotations: [generic landing](../../apps/web/src/app/help/page.tsx#L222), inactive tiles and no real images. | AUD-038-007, AUD-038-008, AUD-038-010, AUD-038-021 |
| REVIEW-TECH-09 solution-architect | PARTIAL | Human-in-loop and no extra service: [existing service reuse](../../azure.yaml#L1) supported; gate and data-plane architecture not connected. | AUD-038-002, AUD-038-003, AUD-038-020 |
| REVIEW-TECH-10 azure-principal-architect | PARTIAL | AU resources/processing/no carveout: [agent YAML](../../infra/parameters/foundry-agents/help_assistant.yaml#L1) declarative; effective shared dependencies and deployment type unverified. | AUD-038-016, AUD-038-020 |
| REVIEW-TECH-11 infrastructure-devops | PARTIAL | IaC/approval/CI/deployment: [manual-only gates](../../.github/workflows/help-gates.yml#L3) and metadata publisher do not deliver staged publication; logs absent. | AUD-038-002, AUD-038-003, AUD-038-016, AUD-038-018, AUD-038-020 |
| REVIEW-TECH-12 qa-test-engineer | PARTIAL | Contract/integration/browser/evaluation pyramid: [fixture checker](../../tests/llm-eval/help/test_eval_cite_or_refuse.py#L31) and skipped e2e are not intended gates. | AUD-038-015, AUD-038-019, AUD-038-020 |
| REVIEW-TECH-13 software-developer | PARTIAL | Reuse existing routes/no new workspace: [catch-all relocation](../../apps/web/src/app/help/articles/[...slug]/page.tsx#L33) credited, but server mismatch and helper-only features incomplete. | AUD-038-008, AUD-038-015, AUD-038-018 |
| REVIEW-TECH-14 data-engineer | PARTIAL | Tenant partitions/idempotent ingest/source projection: [partition queries](../../apps/api/app/repositories/help_repositories.py#L133) positive, [discarding ingester](../../apps/ingest-runner/src/help_snapshot/__main__.py#L14) no immutable idempotent upload. | AUD-038-003, AUD-038-005, AUD-038-016 |
| REVIEW-TECH-15 ai-ml-engineer | PARTIAL | Retrieval-only configured Foundry/embedding reuse/refusal: [live stub](../../apps/agents/help_assistant/agent.py#L50), wrong embedding adapter, unused prompts and absent model quality gate. | AUD-038-003, AUD-038-004, AUD-038-019 |
| REVIEW-TECH-16 docker-container-engineer | PARTIAL | Existing API/ingest image/mode reuse: service count preserved, [ingest wheel](../../apps/ingest-runner/pyproject.toml#L48) excludes mode and no configured build/runtime verification. | AUD-038-015, AUD-038-018, AUD-038-020 |
| REVIEW-TECH-17 api-architect | CONFLICT | REST/SSE/ETag/error/OpenAPI contract: [path-only tests](../../tests/contract/help/test_help_api_openapi.py#L27) miss `/api/v1`/DTO/auth/signed-URL/persistence divergences. | AUD-038-001, AUD-038-009, AUD-038-015, AUD-038-019 |

Operational and sector reviewers' content duties are covered individually in T-AA128 through
T-AA143 and CHK001 through CHK016, with bounded reads of actual operational and representative
agency role definitions. Those source comparisons do not claim any real person reviewed, approved,
tested or accepted the material. Every role's screenshot/context/rights duty remains binding.

### Clarifications And Prior Review Claims

These rows distinguish explicit repository authority from authored assertions about implementation
or execution. Only the scoped supersessions below are accepted; no other duty was retired implicitly.

| Record | Status | Exact authority, supported work and remaining assessment | Follow-up |
| --- | --- | --- | --- |
| PASS1-01 Help language | IMPLEMENTED | [Clarification](spec.md#L328) explicitly resolves English-only Help, not exemption from public PIO multilingual authoring or embedded lang. Current content conflict remains. | AUD-038-006, AUD-038-007 |
| PASS1-02 Snapshot freshness | IMPLEMENTED | [Clarification](spec.md#L334) explicitly selects approved snapshots, excluding live HEAD/draft/unreviewed specs. Active bypass is not a later approved replacement. | AUD-038-003, AUD-038-004 |
| PASS2-01 Publication/rollback/deprecation | PARTIAL | [Pass 2](spec.md#L344) binds dual signoff, immutable config rollback and transparent replacement; current handlers/notice do not implement them. | AUD-038-002, AUD-038-003, AUD-038-009 |
| PASS2-02 Screenshot governance | PARTIAL | [Pass 2](spec.md#L349) binds DOM hash/one-release grace; selector hashing/local report/fourteen-day runbook not equivalent. | AUD-038-010 |
| PASS2-03 Support record/SLA | PARTIAL | [Pass 2](spec.md#L354) defines fields/calendar/incident timer/audit, not staffing guarantee; current DTO/helper lacks active workflow. | AUD-038-014 |
| PASS2-04 Active persona/union | PARTIAL | [Pass 2](spec.md#L359) defines IdP/entitled override/ranked union/active-only chat; no current entrypoint enforcement. | AUD-038-001, AUD-038-008 |
| PASS2-05 Persistence/retention | PARTIAL | [Pass 2](spec.md#L364) binds thirty-day operational history/seven-year audit; models alone cannot establish purge or user/observer access. | AUD-038-005, AUD-038-016 |
| PASS2-06 Feedback closure | PARTIAL | [Pass 2](spec.md#L369) requires human backlog/promotion/no silencing; pending rows not completed aggregation. | AUD-038-013 |
| PASS2-07 Degraded cache | PARTIAL | [Pass 2](spec.md#L374) specifies mandatory subset/shared cap/TTL/refresh; unused browser cache is not delivery. | AUD-038-011 |
| PASS2-08 Embedded language | PARTIAL | [Pass 2](spec.md#L379) applies Language of Parts despite English chrome; validators/gates insufficient. | AUD-038-015, AUD-038-018, AUD-038-021 |
| PASS2-09 Observer questions | CONFLICT | [Clarification](spec.md#L384) permits questions freely, limits instructed actions; authored Observer guide contradicts it. | AUD-038-004, AUD-038-006 |
| PASS3-01 Global versus tenant | CONFLICT | [Amendment](spec.md#L186): global doctrine only versus tenant Help/transcripts/audit/snapshot composition/support; seed/loader global defaults violate it. | AUD-038-003 |
| PASS3-02 Answer pattern | PARTIAL | [Amendment](spec.md#L187): semantic intent cluster plus exact ordered citations; ordered helper correct, unstable Python hash/aggregation absent. | AUD-038-013 |
| PASS3-03 Two lang gates | PARTIAL | [Amendment](spec.md#L188): source author-save and published build lint, no runtime injection; current plugin unbound/linter weak. | AUD-038-018 |
| PASS3-04 Offline search indicator | PARTIAL | [Amendment](spec.md#L189): persistent cached-only banner only in real degraded state; current empty-query-result trigger incorrect. | AUD-038-011, AUD-038-012 |
| PASS3-05 Shared rank | CONFLICT | [Amendment](spec.md#L190): single authoritative registry; client/contract polarity conflicts and helper unconnected. | AUD-038-008, AUD-038-015 |
| PASS3-06 Incident detection | PARTIAL | [Amendment](spec.md#L191): auto Level-3 plus optional lower-level manual override; no active support integration. | AUD-038-014 |
| PASS3-07 Prelaunch baseline | UNVERIFIED | [Amendment](spec.md#L192): fourteen-day immediate prelaunch actual counts/persona/TTR; TBD template and wrong metric not completion. | AUD-038-020 |
| PASS3-08 Audit-only reconstruction | PARTIAL | [FR-029b](spec.md#L180) explicitly adds label/no-user-history/observer event; current helper lacks secured surface/required provenance. | AUD-038-005 |
| PASS3-09 Withdrawn/no replacement | PARTIAL | [Amendment](spec.md#L193): dated snapshot notice/direct support required; supplied-map helper/template not connected. | AUD-038-003, AUD-038-009, AUD-038-014 |
| PASS3-10 Route rename grouping | PARTIAL | [Amendment](spec.md#L194): previous_route_id triggers one grouped N-image author task; current JSON report is not lifecycle. | AUD-038-010 |
| AR-001 Retention correction | PARTIAL | [Resolution](spec.md#L415) explicitly replaces ninety days with thirty; model/IaC values preserved, actual session purge/observer reconstruction not verified. | AUD-038-005, AUD-038-020 |
| AR-002 Citation ordering | IMPLEMENTED | [Resolution](spec.md#L417) explicitly forbids citation sorting; [ordered helper/test](../../tests/contract/help/test_pattern_id_stability.py#L14) supported. T-AA188's residual order-invariance wording is not controlling. | AUD-038-013, AUD-038-020 |
| AR-003 Callout ordering | PARTIAL | [Resolution](spec.md#L419) explicitly replaces lexical anchor sorting with Callout.number ordering; helper supported, actual DOM fingerprint and build path incomplete. | AUD-038-010 |
| AR-004 Phase dependency | PARTIAL | [Resolution](spec.md#L421) requires tooling before snapshot publication; task map corrected, effective mandatory CI gate ordering not connected. | AUD-038-018 |
| AR-005 Screenshot routes | PARTIAL | [Resolution](spec.md#L423) adds clear/signed-URL endpoints to contract; routes exist but placeholder signature/no author enforcement violate semantics. | AUD-038-001, AUD-038-010, AUD-038-015 |
| AR-006 CHK-reference drift | IMPLEMENTED | [Resolution](spec.md#L425) explicitly makes FR/SC matrix canonical over obsolete inline CHKs, while still requiring direct checklist walk. It does not excuse current ledger/count/outcome errors. | AUD-038-020 |
| REVIEW-MO-01 Placeholder citations | PARTIAL | [Claim](spec.md#L433): real extract path now exists, but live stub/gateway AU bypass/current mutable corpus mean claimed complete production wiring is unsupported. | AUD-038-003, AUD-038-004, AUD-038-022 |
| REVIEW-MO-02 Audit completeness | PARTIAL | [Claim](spec.md#L434): response/citation/redacted fields added to ordinary post-stream payload; denies/volatile fallback/approval/source accuracy/reconstruction remain incomplete. | AUD-038-005, AUD-038-022 |
| REVIEW-MO-03 Local-government handoffs | IMPLEMENTED | [Claim](spec.md#L435) supported by [current local-government role](../../.github/agents/sectors/cross-sector/local-government.agent.md#L1) routing to jurisdiction-specific agencies/NEMA; does not retire this spec's other role/content obligations. | AUD-038-007 |
| REVIEW-CODE-P1 OpenAPI indentation | IMPLEMENTED | [Claim](spec.md#L436) supported by top-level [session path](contracts/help-api.openapi.yaml#L80); complete schema conformance remains separate. | AUD-038-015 |
| REVIEW-CODE-P2 Primary AU parameter | IMPLEMENTED | [Claim](spec.md#L437) and [root parameter](../../infra/main.bicep#L1) establish AU-East primary constraint; this is not full resource/processing-residency proof. | AUD-038-016, AUD-038-020 |
| REVIEW-CODE-P3 Active snapshot | CONFLICT | [Claim](spec.md#L438) says newest-created active record/order is correct; [facade](../../apps/api/app/repositories/help_repositories.py#L193) returns first active unsorted row, while rollback never switches the actual index. | AUD-038-003 |
| REVIEW-EXECUTION Assertions | UNVERIFIED | [79-pass/build/lint statement](spec.md#L440) and [86-pass template](../../docs/runbooks/help/release-signoff-TEMPLATE.md#L6) lack current revision-bound run artifacts; no commands executed to retroactively validate them. | AUD-038-019, AUD-038-020 |
| REVIEW-TEMPLATE-01 Emergency rollback | CONFLICT | [Release template](../../docs/runbooks/help/release-signoff-TEMPLATE.md#L36) waives recollecting signatures while plan/task notes require dual signoff for rollback; no binding approved resolution found. | AUD-038-002, AUD-038-020 |
| REVIEW-TEMPLATE-02 Signoff event | MISSING | [Template](../../docs/runbooks/help/release-signoff-TEMPLATE.md#L28) requires audit.help_release_signoff_recorded with approvers/release/snapshot; no emitter in scoped workflows/Help tools/API observability search. | AUD-038-017, AUD-038-020 |

### Evidence Records And Release Limits

| Record | Status | What the artifact proves, and what it does not | Follow-up |
| --- | --- | --- | --- |
| EVIDENCE-01 Verification ledger | CONFLICT | [Ledger](verification-status.md#L9) is authored narrative; wrong/missing current paths, CHK meanings and approximate 60/136 count versus actual 45/136. | AUD-038-020 |
| EVIDENCE-02 Baseline record | UNVERIFIED | [Prelaunch template](baselines/pre-launch-support.md#L6) lists methods/TBD measurements, not actual dated fourteen-day observations. Its acceptance conflicts with SC-009. | AUD-038-020 |
| EVIDENCE-03 Baseline README | CONFLICT | [README](baselines/README.md#L3) says 30% instead of 40% and names a CSV not found; neither is superseding authority. | AUD-038-020 |
| EVIDENCE-04 Snapshot record | UNVERIFIED | [Root record](../../snapshot-record.json#L1) has snapshot ID, asserted identities/roles and publication time only; no source/index binding, exact reviewed digest, per-approval timestamps or deploy receipts. | AUD-038-002, AUD-038-003, AUD-038-020 |
| EVIDENCE-05 Local snapshot inventory | MISSING | Local snapshots directory contains only empty placeholder; no immutable approved-source record under it. Root record evaluated separately, not ignored as relocation. | AUD-038-003, AUD-038-020 |
| EVIDENCE-06 Cultural consultation | UNVERIFIED | [Index](../../docs/cultural-authority/help/INDEX.md#L8) contains pending/TBD authority/date; no actual culturally authorized consultation/signature. | AUD-038-007, AUD-038-020 |
| EVIDENCE-07 Dev provisioning | UNVERIFIED | No dated Help provisioning log found in scoped infrastructure/runbook/weblog inventory; [infrastructure overview](../../docs/infrastructure/help.md#L1) is not a deployment receipt. | AUD-038-016, AUD-038-020 |
| EVIDENCE-08 Publish/rollback rehearsal | UNVERIFIED | [Template](../../docs/runbooks/help/snapshot-publish-rollback-rehearsal-template.md#L13) is unfilled/dry-run, not alias restoration timing/audit proof. | AUD-038-003, AUD-038-017, AUD-038-020 |
| EVIDENCE-09 Clean deployment smoke | UNVERIFIED | [Smoke template](../../docs/runbooks/help/azd-up-smoke-TEMPLATE.md#L1) and deferred task not actual azd-up or UI/refusal/redaction/offline test. | AUD-038-020 |
| EVIDENCE-10 Release sign-off | UNVERIFIED | [Sign-off template](../../docs/runbooks/help/release-signoff-TEMPLATE.md#L24) has no completed dual signatures/release identity; cannot approve rollout. | AUD-038-002, AUD-038-020 |
| EVIDENCE-11 AU attestation | UNVERIFIED | [Attestation README](../../docs/attestations/README.md#L1) is instructions, not Help release JSON; attestor itself incomplete. | AUD-038-016, AUD-038-020 |
| EVIDENCE-12 Dashboard/alerts | UNVERIFIED | [Workbook](../../docs/runbooks/help/app-insights-workbook.md#L3) and [alerts](../../docs/runbooks/help/metric-alerts.md#L17) defer operator setup; no live query/pager evidence. | AUD-038-017, AUD-038-020 |
| EVIDENCE-13 Usability/competence | UNVERIFIED | [Ledger](verification-status.md#L46) defers SC-001/008; no representative dated participants/tasks/timing/result records found. | AUD-038-007, AUD-038-008, AUD-038-020 |
| EVIDENCE-14 Grounding/fabrication/red-team | UNVERIFIED | [Shape-only evaluation](../../tests/llm-eval/help/test_eval_cite_or_refuse.py#L31) and [memory tenant tests](../../tests/integration/help/test_tenant_isolation.py#L42) are not actual quality/audit/environment outcomes. | AUD-038-019, AUD-038-020 |
| EVIDENCE-15 Accessibility/image inventory | UNVERIFIED | [Skipped axe file](../../apps/web/__tests__/e2e/help/accessibility-axe-scan.spec.ts#L7) and absent tracked image/sidecar inventory are not real screenshots, WCAG/AT review or current theme verification. | AUD-038-010, AUD-038-021, AUD-038-020 |

No deployment, runtime/model quality, availability, latency, accessibility conformance, human staffing,
external approval or cultural authority is inferred from static declarations. No external evidence
was fetched to fill the gaps; these remain future gated activities, not a direction to run them now.

## Reviewed Inputs And Search Bounds

### Complete Local Input List

All thirteen nonempty local input documents were read in full, including appended clarifications,
analysis corrections and review narrative. The initial report did not exist. The two local empty
baseline/snapshot placeholders were inventoried; they contain no approval or execution evidence.

| Input | Read scope and purpose |
| --- | --- |
| [spec.md](spec.md#L1) | Entire file: stories/independent tests/edges, base/suffixed/amended FRs, SCs, personas, content/visual/chat/accessibility/residency, assumptions/exclusions/dependencies, all clarification/analysis/review appendices. |
| [tasks.md](tasks.md#L1) | Entire file: 226 task definitions with original checkboxes, phase/dependency notes, verification matrix, final binding notes; dependency-note repetitions excluded from task inventory. |
| [plan.md](plan.md#L1) | Entire file: technical/nonfunctional constraints, constitution/persona duties, architecture, eight risks, test/telemetry strategy and complexity assertions. |
| [research.md](research.md#L1) | Entire file: ten binding selected decisions including rejected alternative grounding/storage paths, authority, language, privacy, offline and tenant controls. |
| [data-model.md](data-model.md#L1) | Entire file: thirteen entity definitions, validators, common metadata, Citation reuse, exact Search field/index and Cosmos/TTL mapping. |
| [contracts/help-api.openapi.yaml](contracts/help-api.openapi.yaml#L1) | Entire OpenAPI contract: all methods/responses/schemas/security, prefix, SSE, approval, staleness, signed URL, search/support and ownership boundaries. |
| [contracts/help-ui.contract.ts.md](contracts/help-ui.contract.ts.md#L1) | Entire UI contract: six routes, components/props, ten telemetry events, a11y targets/focus/announcements/motion, source-language gates and server-only auth/audit boundaries. |
| [quickstart.md](quickstart.md#L1) | Entire file: prerequisites/install/build/provision/seed/run/publish/rollback/tests/troubleshooting are instructions for future authorized execution, not evidence. |
| [checklists/feature.md](checklists/feature.md#L1) | Entire 136-item checklist including original states and Gate markings; all rows individually reassessed. |
| [checklists/requirements.md](checklists/requirements.md#L1) | Entire 28-item unnumbered specification-quality checklist and clarification notes; all rows individually reassessed. |
| [verification-status.md](verification-status.md#L1) | Entire ledger/SC table, obsolete path/CHK mappings, counts and deferred operator claims. |
| [baselines/pre-launch-support.md](baselines/pre-launch-support.md#L1) | Entire template, observation window, TBD values/persona rows and conflicting acceptance metric. |
| [baselines/README.md](baselines/README.md#L1) | Entire baseline inventory/metric description and unsupported CSV claim. |

Required [Review Contract](../001-spec-implementation-audit/README.md#L1) was read through line 59
only; no inventory or other specification's implementation-review report was read. Applicable
[code-review](../../.github/instructions/code-review.instructions.md#L1),
[code-commenting](../../.github/instructions/code-commenting.instructions.md#L1),
[Bicep best-practice](../../.github/instructions/bicep-code-best-practices.instructions.md#L1) and
[policy](../../.github/instructions/bicep-policy-compliance.instructions.md#L1) instructions were read.
The Python fact-grounded-coding skill was loaded for static evidence discipline; the isolated
infrastructure reviewer read the [Bicep patterns](../../.github/skills/azure-bicep-patterns/SKILL.md#L1)
and [Azure defaults](../../.github/skills/azure-defaults/SKILL.md#L1) skills. No environment configuration,
Python imports, Azure discovery/compilation or runtime tooling was invoked by this audit.

Three user-authorized isolated read-only reviewers examined frontend/content, infrastructure/publication,
and domain/tests respectively. Their evidence was reconciled against controlling handlers; subsequent
direct checks corrected support If-Match, article default-persona and mounted error-envelope details.
They wrote no repository files and were instructed not to read any implementation-review reports.

### Associated Source And Evidence Inventory

Full content reads comprise all sixteen existing persona landing MDX files referenced by T-AA128
through T-AA143, all fourteen screen articles in the SCREEN table, all six playbooks in DOMAIN-4/5,
all nine general articles in the domain/findings tables, the five-entry glossary and surface map.
Their actual named procedures, approval rights, handoffs, required images and omissions were assessed.

Source inspection followed the active global shell/root HelpChatProvider/dock, Help layout/landing,
search/chat/catch-all article/glossary/playbook routes, proxy, all sixteen Help components and nine
Help client modules, theme/focus CSS and existing worker. Existing audit and simulation-playback
destinations were inspected to distinguish bad links from relocated behavior. The current
[Playwright config](../../apps/web/playwright.config.cts#L1) and
[Next config](../../apps/web/next.config.ts#L1) were read, not their obsolete historical filenames.

Backend inspection covered six mounted Help route modules plus caller dependency, Help repository,
all Help services/agent and three prompts; common gateway/retrieval/embedding/citation interfaces,
app mounting/settings, authentication/tenant/JWT/RBAC/error/audit middleware and emitters were
followed only as dependencies of Help behavior. Both the real extract generator and live stub were
read; no invocation was made. The shared gateway AU bypass is independently relevant to this spec.

Domain/tests review covered all twelve new model modules plus Citation, authority registry, both
hashers, Python initializer and TS barrels/exports; all Help contract/integration/evaluation files,
six single-row eval fixtures and six browser stubs. Static inventory found 54 contract and 25
integration test functions, eight fixture-shape evaluator checks, and six skipped browser stubs.
Those counts are authored definitions, not passing results. Unit/help has only a placeholder.
Broader [interface tests](../../tests/e2e/interface-coverage.spec.ts#L599) were read for relevant
Help/FAQ/navigation/landmark/mobile/focus assertions, not independently audited as another feature.

Configuration reads covered root/web/domain/API/agent/ingest package/typing/test manifests,
lockfile declarations, test path injection, CI/Help-gates/snapshot workflows, ownership and branch
approval configuration, service descriptor/seeding hooks, all Help ingestion/tooling modules,
connected root/child Bicep resources, parameter overlays, PSRule settings and infrastructure tests.
No repository validation, generator, dependency resolver, build or deployment command was executed.

Associated evidence reads included [infrastructure overview](../../docs/infrastructure/help.md#L1),
[on-call](../../docs/runbooks/help/on-call.md#L1),
[publication](../../docs/runbooks/help/snapshot-publish-rollback.md#L1),
[freshness](../../docs/runbooks/help/screenshot-staleness.md#L1),
[support configuration](../../docs/configuration/help-support-handoff.md#L1),
[workbook](../../docs/runbooks/help/app-insights-workbook.md#L1),
[alerts](../../docs/runbooks/help/metric-alerts.md#L1),
[chaos drill](../../docs/runbooks/help/chaos-drill-snapshot-rollback.md#L1),
[rehearsal template](../../docs/runbooks/help/snapshot-publish-rollback-rehearsal-template.md#L1),
[smoke template](../../docs/runbooks/help/azd-up-smoke-TEMPLATE.md#L1),
[sign-off template](../../docs/runbooks/help/release-signoff-TEMPLATE.md#L1),
[attestation instructions](../../docs/attestations/README.md#L1),
[cultural-authority index](../../docs/cultural-authority/help/INDEX.md#L1) and
[root snapshot record](../../snapshot-record.json#L1). Authored runbooks and TBD records were not
mistaken for logs, executed tests, approved publication, externally signed consultation or measured SLIs.

Role-definition comparisons included all ten existing operational roles and bounded representative
NSW RFS, Ambulance Victoria, NSW Police, NSW SES, Marine Rescue NSW, NEMA, local government,
community NGO, volunteer and utility definitions. The relevant constitution warning/audit/approval
clauses were read directly. Other specifications were not independently reviewed; their obligations
are represented by the explicit Spec 038 dependency/contract duties, with unsupported cross-spec
accuracy claims retained as UNVERIFIED rather than invented successful reviews.

### Bounded Negative Searches

Each MISSING judgment follows a search for connected or relocated behavior, not a historical-name miss.
Only relevant source/content/config/test/evidence scopes were searched; other implementation-review
reports were excluded. Search failures/timeouts were not treated as absence evidence.

| Search boundary | Controlling path inspected and negative conclusion |
| --- | --- |
| SEARCH-01 Web entrypoints | Help route tree, root shell, shared UI, Help components/lib and public worker inventory; [generic landing](../../apps/web/src/app/help/page.tsx#L222) and [dock](../../apps/web/src/components/help/HelpAssistantDock.tsx#L29) do not call persona/tour/context/offline helpers. Catch-all article relocation and shared full-page/dock store credited. |
| SEARCH-02 Auth/tenant/roles | Help proxy/SSR/caller plus actual app middleware registration/JWT/RBAC/tenant context; [protected-prefix list](../../apps/api/app/middleware/entra_auth.py#L37) excludes Help. No compensating application-level entitlement/admin check found; external ingress controls not assumed. |
| SEARCH-03 Chat/retrieval/output | Entire Help agent/routes/services, relevant common retrieval/citation/embedding definitions and imports; [active query](../../apps/agents/help_assistant/agent.py#L359) bypasses Search/prompt/classification/conflict/read-only controls. Live entrypoint stub is present, not missing file. |
| SEARCH-04 Audit/session/reconstruction | Help routes/services/repository, API audit surfaces and UI chat/audit consumers; [session writer](../../apps/api/app/repositories/help_repositories.py#L212) and reconstruction/SLA/aggregation/conflict helpers have definitions/exports but no active Help callers. No audit-only reconstruction label/route or required complete events found. |
| SEARCH-05 Publication/admission/deprecation | Help workflow, CLI, services, ingest mode, source loaders, bootstrap/alias helpers and seed hooks/readers; [loader](../../apps/ingest-runner/src/help_snapshot/source_loaders.py#L25) has no tenant-exclusion use and no producer connects deprecation maps. Local-file aliases/metadata writes credited only as stubs. |
| SEARCH-06 Visual assets/freshness | All 45 MDX files, Help/public/tracked image/alt/registry inventories, capture/hash/freshness/bulk tools, screenshot routes and component consumers; [capture](../../tools/help/capture_screenshots.ts#L18) is not uploaded paired assets, alt sidecars, live-DOM flags or author tasks. Deployed Blob inventory remains unverified. |
| SEARCH-07 Offline/search | All Help client modules/worker/static serving/active article/search/chat routes and related tests; [registration](../../apps/web/src/lib/help/sw-register.ts#L2) uncalled and intended worker absent. No shared-cap/preload/dated stale reader/refresh path or full-body alias search found. |
| SEARCH-08 Content obligations | Complete persona/screen/playbook/general/glossary bodies, surface map and relevant role definitions/current destinations; named missing actions recorded per persona/domain. Similar generic prose did not retire reassignment, IC approval, export, Auslan or simulation-reset duties. |
| SEARCH-09 Infrastructure | Help modules plus connected main/storage/monitoring/identity resources, dev/staging/production parameters, tests and PSRule; [broad role](../../infra/main.bicep#L894) not append-only, required web/runner grants/Help alarms/Help what-if fixture/overlays absent. Search did credit relocated production parameter filename and companion registry. |
| SEARCH-10 Tests/evaluation | All Help contract/integration/unit/evaluation/browser files, related web suites, eval-runner/core/dataset/Help tools and CI discovery; no full Help theme/keyboard assertions, actual fabrication sampler or persona quality evaluator found. Renamed smoke/eval files and shared navigation assertions credited by actual assertions, not names. |
| SEARCH-11 Operational records | Local evidence/baseline/snapshot inventory, Help runbooks/infrastructure/attestations/cultural records and bounded Help-related weblog names; no dated authentic deployment/rehearsal/SC study/attestation/signature outcomes found. No audit report content used as evidence. |
| SEARCH-12 Release event | Help workflow/tooling/API observability text search for audit.help_release_signoff_recorded; only [template obligation](../../docs/runbooks/help/release-signoff-TEMPLATE.md#L28), no corresponding emitter discovered. |

## Integrity And Execution Record

Only this report was manually changed with `apply_patch`; one permitted EOF-only mechanical newline
normalisation was applied after the initial Markdown diagnostic. No source/config/original
specification/task/checklist/evidence/index files were written. Existing unrelated untracked audit
artifacts were only visible as path names in status output and were not opened or altered.

Completed intermediate read-only checks established matching expected revision, exact 226 original
task IDs/states, all 64 numbered requirement definitions and exact 136 feature-checklist states.
Balanced-parenthesis local-link parsing checked existing files and one-based line bounds, treating
route brackets/parentheses as path characters. Four incorrect documentation anchors were corrected,
and the immediate rerun passed all then-current 821 links. Every substantive report edit was followed
by a focused report diagnostic or integrity check; no product tests were substituted for static review.

Final checks on 2026-09-14:

| Check | Result |
| --- | --- |
| Expected revision | PASS: HEAD remains `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`. |
| Original tasks | PASS: 226 unique definition rows, exact IDs/states with X/x treated equivalently; dependency-note repetitions excluded, no extra task IDs. |
| Numbered requirements | PASS: 51 FR definitions, zero original NFR definitions, thirteen SC definitions including SC-009-AMEND; all 64 appear exactly once. |
| Acceptance scenarios | PASS: all twenty original Given/When/Then cases; five independent-test duties and ten edge-case rows also present. |
| Feature checklist | PASS: all 136 IDs/states match, including 45 checked and 86 Gate items; no obsolete CHK substitutes. |
| Quality checklist | PASS: all 28 original unnumbered criteria represented in order with checked state preserved. |
| Additional coverage | PASS: fourteen named screens, nine content domains, forty other obligations, thirteen entities, three data mappings, sixteen API duties, ten telemetry duties, eight risks and seventeen technical review duties. |
| Follow-ups | PASS: AUD-038-001 through AUD-038-022 each declared exactly once, all unchecked, imperative titles, no undefined referenced ID. |
| Local evidence links | PASS: all 983 links resolve to existing local files with valid one-based line bounds; balanced-parenthesis parsing handles route names and decoded paths, and no other implementation-review report is linked/read. |
| Report diagnostics | PASS: get_errors reports no errors; only initial EOF newline defect required mechanical normalization. |
| Change boundary | PASS: no tracked source/config/original-spec/evidence/index changes; only this new report was written. Other untracked audit artifacts left untouched. |
| Execution boundary | PASS: no product tests or collection, builds, imports, generators, model calls, browsers/servers, cloud/deploy operations, installs, runtime/debug or external approvals. |

The follow-up integrity parser initially rejected CRLF line endings; its corrected CRLF-tolerant
read-only check passed all 22 declarations and references. This was a validator issue, not missing
report tasks. No helper files were created. Product execution and externally verifiable outcomes
remain intentionally UNVERIFIED as recorded above; the static audit itself has no remaining blocker.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 038 only. Three parallel technical reviews examined Help auth/
approval, grounding/redaction, and transcript/audit durability. The source-completable route-boundary defect was corrected:
the shared `/api/help` route family is now included in both Entra authentication and RBAC protection registries.

Validation: `python -m pytest tests/integration/test_rbac_enforcement_036.py -q` returned `15 passed` (2 existing
deprecation warnings).

Remaining open work includes claims-backed persona entitlement, authenticated dual snapshot approval, approved-source
grounding, AU redaction enforcement, citation-linked claims, durable SSE/audit ordering, browser draft privacy,
retention, deployment, accessibility, model quality, and human evidence.
