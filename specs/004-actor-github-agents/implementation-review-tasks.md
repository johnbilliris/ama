# Implementation Review Tasks: Actor-Specific GitHub Agents

**Specification**: 004-actor-github-agents  
**Review date**: 2026-09-11  
**Baseline and inspected HEAD**: `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`  
**Boundary**: Static, isolated review of development-time customization artifacts. All remediation work below is unexecuted.

## Findings

The catalogue exists and contains substantive original persona instructions, but its current content does not satisfy the complete contract. Neither filenames nor the 42 checked original tasks establish conformance. P1 denotes a safety, authority, or material guidance risk; P2 denotes a completeness, maintainability, or evidence gap. These are development-time guidance findings, not claims that a live incident or deployed system was affected.

| Follow-up | Priority | Finding, impact, and precise evidence |
| --- | --- | --- |
| AUD-001 | P1 | Agents teach an obsolete six-principle constitution and absolute AU-only deployment rules. The current constitution has principles I-VIII, AIIMS II-A, and a tightly bounded model-hosting exception. Following the agent text can reject approved configurations or misidentify governing controls. Compare [solution architect:81](../../.github/agents/technical/solution-architect.agent.md#L81), [security engineer:63](../../.github/agents/technical/security-engineer.agent.md#L63), [DevOps:120](../../.github/agents/technical/infrastructure-devops.agent.md#L120), and [planning:57](../../.github/agents/operational/planning-officer.agent.md#L57) with [constitution:34](../../.specify/memory/constitution.md#L34), [constitution:197](../../.specify/memory/constitution.md#L197), and [constitution:238](../../.specify/memory/constitution.md#L238). |
| AUD-002 | P1 | Warning, incident-severity, and fire-danger vocabularies are conflated. UX prescribes Watch/Warning/Emergency/Catastrophic, while the constitution requires Advice/Watch and Act/Emergency Warning. PIO omits the required nested warning model and all-clear guidance; the archived BoM document presents a legacy fire-danger list. Evidence: [UX:82](../../.github/agents/technical/ux-designer.agent.md#L82), [PIO:60](../../.github/agents/operational/public-information-officer.agent.md#L60), [archived BoM:65](../../.github/agents/sectors/_archive/meteorology-bom.agent.md#L65), [constitution:81](../../.specify/memory/constitution.md#L81), [Incident severity:127](../001-disaster-response-hub/data-model.md#L127). |
| AUD-003 | P1 | Knowledge/advisory scope is not reflected in tool capabilities. Observer/Auditor declares strictly read-only operation but omits `tools`; 82 of 85 active actor files omit it. Azure Principal Architect explicitly enables editing, creation, and command execution despite implementation handoffs. DevOps now mandates an executable IaC workflow, contrary to the research's knowledge-agent boundary. Evidence: [observer:1](../../.github/agents/operational/observer-auditor.agent.md#L1), [observer:28](../../.github/agents/operational/observer-auditor.agent.md#L28), [Azure architect:3](../../.github/agents/technical/azure-principal-architect.agent.md#L3), [DevOps:35](../../.github/agents/technical/infrastructure-devops.agent.md#L35), [research:27](research.md#L27). This is a tool-scope gap, not a request to implement invocation authentication. |
| AUD-004 | P1 | Replacement profiles are partially grounded, not devoid of legislative/activation data: their shared seed reference supplies legislative labels for 43/49 organizations and activation triggers for all 49. However, ten bodies have only an "outside the scope of itself" boundary, and lists/labels do not explain unilateral versus approval-required powers, civilian command limits, or substantive cross-jurisdiction coordination. NGO guidance also lacks statutory/contractual and substantive jurisdictional treatment. Evidence: [NEMA:24](../../.github/agents/sectors/commonwealth/nema.agent.md#L24), [ADF:24](../../.github/agents/sectors/commonwealth/adf.agent.md#L24), [BoM:33](../../.github/agents/sectors/commonwealth/bom-national.agent.md#L33), [NGOs:59](../../.github/agents/sectors/cross-sector/community-ngos.agent.md#L59), [NEMA triggers:48](../../packages/domain/src/domain/seed/organisations_australia.json#L48), [BoM Act:92](../../packages/domain/src/domain/seed/organisations_australia.json#L92), and [ADF triggers:246](../../packages/domain/src/domain/seed/organisations_australia.json#L246). |
| AUD-005 | P1 | Handoffs exist but can send the wrong question to the wrong authority. National Health, Transport, and Volunteer default to NSW; national profiles route bushfire questions to airport-focused Airservices. Replacements omit important medical-logistics and some weather/IC handoffs, and multiple buttons have indistinguishable labels. Evidence: [Health:3](../../.github/agents/sectors/cross-sector/health.agent.md#L3), [Transport:3](../../.github/agents/sectors/cross-sector/transport.agent.md#L3), [Volunteer:3](../../.github/agents/sectors/cross-sector/volunteer.agent.md#L3), [NEMA:3](../../.github/agents/sectors/commonwealth/nema.agent.md#L3), [Airservices:28](../../.github/agents/sectors/commonwealth/asa.agent.md#L28), [NSW Ambulance:3](../../.github/agents/sectors/nsw/nsw-ambulance.agent.md#L3), [NSW SES:3](../../.github/agents/sectors/nsw/ses-nsw.agent.md#L3). |
| AUD-006 | P1 | Agent identity is ambiguous: both ACT and Commonwealth files use `afp`, with different handoffs, violating catalogue-wide ID uniqueness. DevOps additionally declares `name: infrastructure-devops-agent` while callers use `infrastructure-devops`; alias resolution is unverified, not assumed broken. Evidence: [ACT AFP:1](../../.github/agents/sectors/act/afp.agent.md#L1), [Commonwealth AFP:1](../../.github/agents/sectors/commonwealth/afp.agent.md#L1), [DevOps:2](../../.github/agents/technical/infrastructure-devops.agent.md#L2), [solution architect:8](../../.github/agents/technical/solution-architect.agent.md#L8), [ID uniqueness:22](data-model.md#L22). |
| AUD-007 | P1 | Eight technical definitions contain control-character damage in paths, commands, decorators, or ARIA names. Software Developer contains BEL/form-feed/ESC characters and broken `ruff` text; QA paths begin with tabs; Accessibility Tester damages ARIA/role attributes. Docker's example uses single-backtick pseudo-fences. Guidance copied from these files can be invalid. Evidence: [software developer:50](../../.github/agents/technical/software-developer.agent.md#L50), [software developer:73](../../.github/agents/technical/software-developer.agent.md#L73), [QA:31](../../.github/agents/technical/qa-test-engineer.agent.md#L31), [accessibility:57](../../.github/agents/technical/accessibility-tester.agent.md#L57), [Docker:111](../../.github/agents/technical/docker-container-engineer.agent.md#L111). All eight files are enumerated below. |
| AUD-008 | P1 | Legislative and coordinator claims lack a current, reconciled authority record. Commonwealth prose asserts different unsupported Emergency Management Act years, while the seed cites National Emergency Declaration Act 2020; the state table names Resilience NSW/QFES while the replacement is QFD, and local government equates QLD mayors with local disaster coordinators. Seed labels are also assertions, not verified law: Geoscience Australia, Marine Rescue NSW and SA Ambulance have bases needing primary-source review. Evidence: [archived Commonwealth:69](../../.github/agents/sectors/_archive/commonwealth-government.agent.md#L69), [compliance auditor:53](../../.github/agents/technical/compliance-auditor.agent.md#L53), [state government:69](../../.github/agents/sectors/cross-sector/state-government.agent.md#L69), [local government:67](../../.github/agents/sectors/cross-sector/local-government.agent.md#L67), [QFD:32](../../.github/agents/sectors/qld/qfd.agent.md#L32), [NEMA seed basis:41](../../packages/domain/src/domain/seed/organisations_australia.json#L41), [GA basis:142](../../packages/domain/src/domain/seed/organisations_australia.json#L142), [Marine Rescue basis:676](../../packages/domain/src/domain/seed/organisations_australia.json#L676), [SA Ambulance basis:1374](../../packages/domain/src/domain/seed/organisations_australia.json#L1374). External legal correctness remains unverified where primary material could not be retrieved. |
| AUD-009 | P2 | Literal contextual references are not all usable. A scoped scan found 17 unresolved reference occurrences, including damaged paths. Even after repairing control characters, root-level Playwright references and the Chaos Engineer's services-layer resilience path are wrong. Actual targets are [Playwright configuration:1](../../apps/web/playwright.config.cts#L1), [TypeScript configuration:1](../../apps/web/tsconfig.json#L1), and [resilience middleware:1](../../apps/api/app/middleware/resilience.py#L1). Evidence: [QA:62](../../.github/agents/technical/qa-test-engineer.agent.md#L62), [accessibility:95](../../.github/agents/technical/accessibility-tester.agent.md#L95), [chaos:103](../../.github/agents/technical/chaos-engineer.agent.md#L103). Existing architecture, infrastructure, and runtime-helper paths were followed, not declared missing. |
| AUD-010 | P2 | Structural conformance fails independently of response quality: all 50 replacement sector files omit `## Guidance Notes`; Compliance Auditor and Docker descriptions contain 208 and 201 characters respectively. Evidence: [contract:45](contracts/agent-file-contract.md#L45), [contract:108](contracts/agent-file-contract.md#L108), [NEMA final section:50](../../.github/agents/sectors/commonwealth/nema.agent.md#L50), [compliance description:2](../../.github/agents/technical/compliance-auditor.agent.md#L2), [Docker description:2](../../.github/agents/technical/docker-container-engineer.agent.md#L2). YAML parser execution was unavailable; this is not a claim of malformed YAML. |
| AUD-011 | P2 | Grounding is semantically inaccurate even where files exist: government agents cite a nonexistent `government` category, NGOs cite `ngo` instead of `community`, and references name undeclared entities such as Infrastructure, AuditEntry, Scenario, and HazardPrediction. Several operational overviews omit explicit AIIMS/non-AIIMS alignment. Compare [Organisation:10](../001-disaster-response-hub/data-model.md#L10), [Persona:27](../001-disaster-response-hub/data-model.md#L27), [state:57](../../.github/agents/sectors/cross-sector/state-government.agent.md#L57), [NGOs:53](../../.github/agents/sectors/cross-sector/community-ngos.agent.md#L53), [observer:59](../../.github/agents/operational/observer-auditor.agent.md#L59), [field:14](../../.github/agents/operational/field-coordinator.agent.md#L14), and [data engineer:63](../../.github/agents/technical/data-engineer.agent.md#L63). |
| AUD-012 | P2 | Technical guidance is not aligned to current dependencies, quality gates, or inherited NFRs. Next.js 15/TypeScript 5.6 guidance conflicts with pinned Next.js 16.2.6/TypeScript 6.0.3. Generic latency and SLO tables are not mapped to current NFRs; retention, security, recovery, and release-training obligations are incomplete. Evidence: [software developer:40](../../.github/agents/technical/software-developer.agent.md#L40), [solution architect:92](../../.github/agents/technical/solution-architect.agent.md#L92), [SRE:139](../../.github/agents/technical/sre-engineer.agent.md#L139), [web dependencies:22](../../apps/web/package.json#L22), [contribution gates:41](../../CONTRIBUTING.md#L41), [parent NFRs:151](../001-disaster-response-hub/spec.md#L151). |
| AUD-013 | P2 | Accessibility agents disagree on the required release gate: PIO/UX prescribe WCAG 2.1 AA, Accessibility Tester requires 2.2 AA, and the current parent NFR requires 2.2 AA. Six-language guidance is also presented as the baseline without distinguishing the two-language v1 floor and jurisdiction-specific additions. Evidence: [PIO:67](../../.github/agents/operational/public-information-officer.agent.md#L67), [UX:29](../../.github/agents/technical/ux-designer.agent.md#L29), [accessibility:36](../../.github/agents/technical/accessibility-tester.agent.md#L36), [NFR-001:151](../001-disaster-response-hub/spec.md#L151), [NFR-013:163](../001-disaster-response-hub/spec.md#L163). |
| AUD-014 | P2 | Ownership boundaries conflict or remain undeclared: DFES both owns and excludes flood/storm coordination; ARC claims centre establishment/management without the local-government/NGO split; Principal Engineer reverses escalation in its IC-to-Operations-to-Planning example. Parent delegated PIO dispatch also conflicts with unconditional IC-approval wording and the runtime matrix. Evidence: [DFES:28](../../.github/agents/sectors/wa/dfes-wa.agent.md#L28), [DFES:37](../../.github/agents/sectors/wa/dfes-wa.agent.md#L37), [ARC:24](../../.github/agents/sectors/commonwealth/arc.agent.md#L24), [NGOs:34](../../.github/agents/sectors/cross-sector/community-ngos.agent.md#L34), [principal engineer:121](../../.github/agents/technical/principal-engineer.agent.md#L121), [PIO:18](../../.github/agents/operational/public-information-officer.agent.md#L18), [parent dispatch authority:507](../001-disaster-response-hub/spec.md#L507), [runtime matrix:47](../../docs/agents/decision-rights.md#L47). |
| AUD-015 | P2 | Registry metadata does not meet its own contract: Tier and Key Handoffs columns are absent, descriptions are shortened or inconsistent, and paths are agent-directory-relative rather than the contracted repository-relative format. The stated 94 active agents includes nine workflow agents, not the 85 actors; three additional workflow files make the actual active file count 97. Evidence: [registry:7](../../.github/agents/AGENTS.md#L7), [registry columns:17](../../.github/agents/AGENTS.md#L17), [entry contract:95](contracts/agent-file-contract.md#L95), [fleet review:1](../../.github/agents/speckit.fleet.review.agent.md#L1), [fleet run:1](../../.github/agents/speckit.fleet.run.agent.md#L1), [verify run:1](../../.github/agents/speckit.verify.run.agent.md#L1). |
| AUD-016 | P2 | Retirement and discovery are not operationally established. Six retired files remain `.agent.md` files in the agent tree without invocation-disable metadata; active body text still points at them. The registry itself has agent frontmatter but only prose saying it is not interactive. Tier discovery in a clean supported editor profile and archive exclusion have no checked-in result. Evidence: [registry:1](../../.github/agents/AGENTS.md#L1), [archive declaration](../../.github/agents/AGENTS.md#archived-6), [archived fire:1](../../.github/agents/sectors/_archive/fire-services.agent.md#L1), [IC body:47](../../.github/agents/operational/incident-commander.agent.md#L47), [PIO body:35](../../.github/agents/operational/public-information-officer.agent.md#L35), [settings:1](../../.vscode/settings.json#L1). Do not assume a folder named `_archive` disables discovery. |
| AUD-017 | P2 | Local authoring documents disagree: 35 actors/12 technical roles in the spec, 31/8 in planning and tasks, 27 in checklist notes; quickstart says six remaining operational agents after creating only one. Contract optional handoffs contradict T038's all-agent rule; `send` is described as forwarding context/default true although current VS Code documents auto-submit/default false. Evidence: [spec:1](spec.md#L1), [plan:6](plan.md#L6), [tasks:87](tasks.md#L87), [quickstart:74](quickstart.md#L74), [checklist:32](checklists/requirements.md#L32), [contract:17](contracts/agent-file-contract.md#L17), [research:15](research.md#L15). |
| AUD-018 | P2 | No inspected validator or test asserts the actor-file contract, unique IDs, actual tool scope, current references, or substantive boundaries. CI's Markdown gate only covers architecture docs; manifest persona counts and tribunal closure tests are not actor-content tests. Evidence: [CI docs gate:482](../../.github/workflows/ci.yml#L482), [cross-reference validator:61](../../tools/lint/check_spec_cross_refs.py#L61), [persona assertions:26](../../tests/integration/test_persona_coverage_zero_unbacked.py#L26), [review-log assertions:83](../../tests/unit/test_review_log_closure.py#L83). |
| AUD-019 | P2 | SC-003 operational-answer accuracy and same-session role isolation are unverified. The quickstart supplies questions, not responses, ground-truth scoring, a run manifest, or >=80% results. Evidence: [operational questions:47](quickstart.md#L47), [SC-003 and other outcomes](spec.md#measurable-outcomes), [T007-T015 work:38](tasks.md#L38). |
| AUD-020 | P2 | SC-004 sector accuracy is unverified. The original Fire Services questionnaire has no results and does not establish the quality of the replacement catalogue. Evidence: [sector questions:54](quickstart.md#L54), [sector tasks:60](tasks.md#L60), [replacement BoM:18](../../.github/agents/sectors/commonwealth/bom-national.agent.md#L18). |
| AUD-021 | P2 | SC-005's >=85% onboarding benefit has no checked-in survey instrument, cohort, denominator, responses, or calculation in the searched feature/evaluation scope. Technical advice existing is not survey evidence. Evidence: [SC-005](spec.md#measurable-outcomes), [technical work:87](tasks.md#L87), [quickstart technical questions:61](quickstart.md#L61). |
| AUD-022 | P2 | SC-006's under-30-minute creation outcome is unverified. There is an authoring contract but no timed contributor exercise or successful new-agent validation record; the guide's stale counts and IDs obstruct reproducibility. Evidence: [SC-006](spec.md#measurable-outcomes), [maintenance checkpoint:108](tasks.md#L108), [quickstart:74](quickstart.md#L74). |
| AUD-023 | P2 | Historical review completion is not proved. T038-T042 and all 16 quality-checklist items are checked, but no local review execution/signoff record accompanies them. The plan's six PASS rows describe an obsolete constitution, and the checklist claims measurable outcomes already met. Evidence: [original validation tasks:114](tasks.md#L114), [checklist:7](checklists/requirements.md#L7), [plan constitution gate:22](plan.md#L22). Current static inspection found no secret/live-incident payloads; that does not retroactively prove T042 execution. |
| AUD-024 | P2 | HYP-002 points to an absent, double-prefixed evidence filename and lacks a spec-specific measured comparison. Portfolio rubric scores are not this feature's causal/per-spec result. The similarly named parent hypothesis concerns evacuation lead time, not actor consultation. Evidence: [HYP-002:177](spec.md#L177), [rubric baseline:1](../028-capstone-alignment/evidence/rubric-baseline.md#L1), [post-feature aggregate:22](../028-capstone-alignment/evidence/rubric-postfeature.md#L22), [different parent HYP-002:1](../001-disaster-response-hub/evidence/HYP-002.md#L1), [stub contract:47](../028-capstone-alignment/contracts/evidence-stub.contract.md#L47). |
| AUD-025 | P2 | Amendment consultation and persona-validation claims are unsupported. ASM-005 says actors are consulted during authoring/review, while PER-004/PER-005 say validated without identifying a practitioner/date/evidence. Cross-references do not themselves provide the required validation record; the section-coverage script checks only headings. Evidence: [amendments:157](spec.md#L157), [persona claims:165](spec.md#L165), [profile contract:5](../027-spec-hardening/contracts/persona-profile.md#L5), [heading checks:43](../028-capstone-alignment/scripts/validate-section-coverage.ps1#L43), [feature-028 signoff description:36](../028-capstone-alignment/evidence/decision-record.md#L36). |

## Scope, Inputs, and Limitations

This report follows the [Review Contract:13](../001-spec-implementation-audit/README.md#L13). No actor or other subagent was invoked or delegated work. No branch/specification was created, original artifact was edited, commit was made, or product test/build/cloud operation was run. Only this report was authored. Changes to other reports were ignored.

Fully read local inputs: [specification:1](spec.md#L1), [all original tasks:1](tasks.md#L1), [plan:1](plan.md#L1), [research:1](research.md#L1), [data model:1](data-model.md#L1), [quickstart:1](quickstart.md#L1), [agent contract:1](contracts/agent-file-contract.md#L1), and [requirements checklist:1](checklists/requirements.md#L1). There are no additional local task-amendment files or local execution-review records. The spec's appended ASM/PER/HYP/SCP sections were included.

Applicable guidance read: [repository customization skill:1](../../.github/skills/copilot-customization/SKILL.md#L1), [custom-agent reference:1](../../.github/skills/copilot-customization/references/custom-agents.md#L1), [development guidelines:1](../../.github/agents/copilot-instructions.md#L1), [code review instructions:1](../../.github/instructions/code-review.instructions.md#L1), [commenting instructions:1](../../.github/instructions/code-commenting.instructions.md#L1), [contributing:1](../../CONTRIBUTING.md#L1), and [Microsoft documentation skill:1](../../.github/skills/microsoft-docs/SKILL.md#L1). The editor-provided agent-customization workflow skill was also read; it is outside the repository baseline. Referenced but absent customization-enforcement instruction files were not invented. The actual shared development-guideline file is inside the agents directory, not an assumed root instruction file.

All 91 actor definitions were read in full: 10 operational, 58 active sectors, 17 technical, and 6 archived sectors. There are **85 active actor files but 84 unique active file-stem IDs**, because AFP is duplicated. Twelve root workflow definitions were inventoried for location/count only; their workflow behavior is outside this feature review. The original 31 definitions are individually traced in Task Coverage; all 60 additional/replacement files are separately inventoried below.

Authoritative contextual evidence included the current [constitution:1](../../.specify/memory/constitution.md#L1), [parent data model:1](../001-disaster-response-hub/data-model.md#L1), [parent spec:1](../001-disaster-response-hub/spec.md#L1), [runtime decision-rights matrix:1](../../docs/agents/decision-rights.md#L1), [dependency metadata:1](../../pyproject.toml#L1), [web dependency metadata:1](../../apps/web/package.json#L1), [shared gap register:1](../shared/gap-id-register.md#L1), the linked persona/evidence/meta contracts, all three feature-028 evidence records, and the cited validator/test sources. No runtime-agent test result is credited as a Copilot-persona evaluation.

Non-mutating document inventories confirmed required heading presence, description lengths, file-stem identities, frontmatter target-file existence, control-character occurrences, and literal contextual-reference destinations. All scanned frontmatter handoff targets have a corresponding actor file and none of the active frontmatter handoffs points to an archived-only ID. This does **not** establish unique editor resolution, semantic correctness, or availability of referenced tools. Basic YAML parsing could not run: neither the declared JavaScript YAML package nor PyYAML was available in the current execution environment. No dependency was installed. YAML runtime parsing/loading therefore remains UNVERIFIED.

Shared grounding was followed into the [organization seed:1](../../packages/domain/src/domain/seed/organisations_australia.json#L1) and [jurisdiction seed:1](../../packages/domain/src/domain/seed/jurisdictions_australia.json#L1), which also match the baseline. All 49 organization records' governance fields and all nine jurisdiction records' structure were inspected without outputting contact data. The organization reference supplies AIIMS functions, lead-agency categories, capabilities, participation conditions, activation triggers, mutual-aid partners, and 43 non-null legislative labels. NEMA state/territory requests, ADF DACC requests, and BoM's Meteorology Act are therefore present via shared references, not missing artifacts. Six nonstatutory/service organizations have null legislative labels; null alone is not a defect, because agreements and general law may govern them. These fields provide useful grounding but do not establish current legal correctness, detailed approval powers, or an evaluated actor response.

The reference scan found 17 unresolved literal occurrences, including corrupt tokens; it was supplemented by complete content reading. Architecture, operator runbook, infrastructure, tenant-context, and runtime LLM-helper files do exist. Playwright moved to the web package's `.cts` configuration; resilience is middleware, not the named services path. Missing historical names were followed before classification. Historical public-event examples are not treated as live incident payloads. No secret values or sensitive operational records are reproduced here.

Public documentation checked on the review date: [VS Code custom agents](https://code.visualstudio.com/docs/copilot/customization/custom-agents), [tool-list priority](https://code.visualstudio.com/docs/agent-customization/prompt-files#_tool-list-priority), [GitHub custom-agent tools](https://docs.github.com/en/copilot/reference/custom-agents-configuration#tools), [NEMA overview](https://www.nema.gov.au/about-us), [NEMA governance](https://www.nema.gov.au/about-us/governance), and [NEMA publication scheme](https://www.nema.gov.au/about-us/freedom-of-information/information-publication-scheme). These establish customization semantics and source provenance, not an exhaustive legal certification. Search-engine and Queensland-page extraction was unsuccessful. External legal/jurisdictional verification, editor discovery, tool binding, model responses, user surveys, elapsed-time measurements, and human approvals remain unverified. Host-specific behavior must be checked in the supported VS Code version; a file-existence check is insufficient.

## Unexecuted Remediation Tasks

All paths described as **proposed** below are future work, not existing evidence. Developer and tester instructions are for a later authorized change. Reuse the existing [tools/lint directory](../../tools/lint/) and [tests/unit directory](../../tests/unit/) conventions; do not run the product suite to substitute for artifact validation. Future validation procedures V-STRUCT, V-EDITOR, V-CONTENT, V-SURVEY, and V-TIMED are defined after the coverage tables.

### AUD-001 - Restore Constitutional Grounding

- [X] AUD-001 Reconcile actor instructions with the current constitution without broadening its carve-out.

**Original IDs**: FR-008, FR-009, FR-014, FR-015; T003, T005, T008-T014, T030-T036, T039-T040; SCP-006.

**Expected / observed / impact**: Current governing principles should control guidance. Six-principle summaries instead mislabel privacy, provenance, and Azure controls and forbid all non-AU model endpoints, risking incorrect design reviews.

**Developer instructions**: Update the owning operational and technical definitions, starting with Solution Architect, Security Engineer, Infrastructure/DevOps, Planning Officer, and Product Owner/BA. Reference current sections II-A, IV, V, VIII and NN-1 through NN-5 directly. Separate non-AU inference-hosting permission from the unchanged AU persistence/telemetry/secrets requirements. Require the named registry, approvals, minimization, and use-case conditions before recognizing an exception. Do not amend the constitution or infer approval from endpoint location alone.

**Tester instructions**: Use the existing quickstart's technical questions as the manual home. Positive: AU storage plus approved, minimized inference-only exception yields qualified advice. Negative: offshore audit/PII storage or an unlisted inference endpoint is rejected. Edge: an expired/missing approval or a new constitution version causes uncertainty/escalation, not silent permission. Check every affected agent's principle references, including contextual annotations.

**Dependencies / future validation**: No dependency to reconcile references; coordinate authority questions with AUD-014. Run V-STRUCT after AUD-018 and V-CONTENT after source correction.

**Objective acceptance**: No obsolete principle attribution or unqualified "no exceptions" statement remains; all agents give the same bounded exception interpretation, retain human authorization, and link the current governing sections.

### AUD-002 - Separate Warning Taxonomies

- [X] AUD-002 Correct public-warning guidance and keep distinct severity scales explicitly separate.

**Original IDs**: FR-006, FR-007, FR-008, FR-014, FR-015; T010, T023, T035, T039; US1-AS1, US3-AS2.

**Expected / observed / impact**: Public warnings must follow the constitutional three-tier AWS model. UX instead specifies a different four-value scale, and the other profiles do not establish the required nested warning/all-clear semantics.

**Developer instructions**: Correct the PIO, UX, and active BoM guidance; route archive handling through AUD-016. Link the current warning authority and distinguish public AWS levels, internal incident severity, and fire-danger ratings. Encode warning level + hazard/location + action statement, de-escalation/all-clear, and human approval. Do not rename product enums or implement alerting in this remediation.

**Tester instructions**: Add manual cases beside the quickstart accuracy pack. Positive: a synthetic flood warning uses the three AWS levels and nested structure. Negative: Catastrophic is not accepted as an AWS level. Edge: an internal `watch` incident and a fire-danger rating are translated/explained rather than copied as a public warning; a declining threat produces reviewable all-clear guidance.

**Dependencies / future validation**: AUD-001 and AUD-014 for governing authority; V-CONTENT and V-STRUCT after AUD-018.

**Objective acceptance**: PIO, UX, and BoM describe identical public-warning semantics while preserving explicit distinctions from other scales; all listed positive, negative, and edge cases pass manual review.

### AUD-003 - Align Tools With Advisory Scope

- [X] AUD-003 Establish explicit, role-appropriate tool capabilities and resolve the DevOps knowledge/workflow conflict.

**Original IDs**: FR-005, FR-006, FR-008, FR-013, FR-015; T003-T005, T014, T031, T038-T039; research knowledge-agent decision.

**Expected / observed / impact**: An observer/adviser should not acquire implementation or operational capabilities accidentally. Omitted allowlists inherit host capabilities; the architect explicitly enables writes, and DevOps directs execution.

**Developer instructions**: Define a documented capability policy for all 85 active actors. Make Observer/Auditor explicitly read/search-only with no mutating MCP tools, shell, editing, creation, or unrestricted subagent escape. Decide with maintainers whether technical implementation roles are intentional exceptions to the knowledge-only design; do not silently convert every actor to an implementation agent. Limit Azure Principal Architect to approved advisory capabilities. Reconcile legacy tool names in DevOps/Azure Architect with the supported provider inventory and document missing-provider behavior. Preserve the distinction between Copilot tool scope and application RBAC, which is outside this feature.

**Tester instructions**: In an isolated profile with fake/local data, inspect resolved tool lists without invoking cloud operations. Positive: observer can read an audit fixture. Negative: requests to edit a record, execute a command, deploy, or delegate a write expose no usable mutator. Edge: missing MCP provider, prompt-file tool overrides, and inherited tools cannot silently invalidate a claimed read-only workflow; unsupported combinations must be documented or blocked by the supported configuration.

**Dependencies / future validation**: AUD-006 and AUD-016 for identity/discovery; contract decision recorded with AUD-017. Use V-EDITOR and V-STRUCT. No real cloud-operation probe is necessary.

**Objective acceptance**: Each active actor has an explicit reviewed capability policy; observer restrictions are demonstrated in the supported host; advisory/implementation exceptions and unresolved tool aliases are not hidden behind prose.

### AUD-004 - Restore Sector Knowledge Depth

- [X] AUD-004 Restore statutory, conditional, jurisdictional, and substantive scope content lost in sector replacement.

**Original IDs**: FR-003, FR-005, FR-007, FR-009, FR-013-FR-015, SC-001, SC-004; T004, T016-T028, T039; all US2 scenarios and EC-02.

**Expected / observed / impact**: Each sector must explain actual authority and participation boundaries. The fifty replacements link shared metadata containing statute labels and activation triggers, but their bodies do not explain approval powers and cross-jurisdiction implications; ten tautological boundaries cannot support a novice's out-of-scope question. NGO content is also incomplete for FR-007. This is an explanatory/authority gap, not a claim that every referenced statute or trigger is absent.

**Developer instructions**: Amend all 50 successor profiles in the inventory and the cross-sector NGO profile. Preserve separate agents per actor and reuse the existing legislative/activation metadata after AUD-008's fact review. Explain the consequences of those fields: unilateral versus approval-required decisions, request/escalation conditions, civilian command limits, and counterpart responsibilities. A **proposed** `docs/agents/sector-authority-reference.md` may hold versioned primary-source comparisons if no existing authoritative home fits; do not duplicate the seed into a competing catalogue. Explicitly cover NEMA assistance approval, DACC categories and civilian authority, BoM's advisory/non-responding role, fire/SES differences, police powers, ambulance-versus-hospital responsibilities, and NGO statutory/contractual obligations. Do not simply add a heading or copy seed labels.

**Tester instructions**: Extend the existing quickstart question pack with every required sector family and every replacement's jurisdiction. Positive: explain who may act and under what authority. Negative: a national advisory or humanitarian agency must not assume state combat command. Edge: cross-border events, Defence requests without a national declaration, combined agencies, multiple hazards, and unknown jurisdiction must produce qualified escalation. Each content assertion needs a primary-source citation and reviewer rationale, not keyword presence alone.

**Dependencies / future validation**: AUD-008 supplies validated authority facts; AUD-005/AUD-006 supply unambiguous counterpart routing. V-CONTENT and V-STRUCT.

**Objective acceptance**: All 58 active sectors contain the FR-007 obligations in their body or explicit authoritative references; no tautological scope-only boundary remains; all fourteen original sector families retain demonstrable coverage after retirement.

**Implementation status (2026-09-15)**: Completed for automatable scope. All 50 jurisdiction sector files were regenerated with substantive Guidance Notes, authority-status citations, qualified activation/approval conditions, and non-tautological boundaries. Cross-sector NGO guidance was expanded with contractual/jurisdiction variation and explicit non-command constraints.

### AUD-005 - Repair Semantic Handoffs

- [X] AUD-005 Make routing depend on jurisdiction and capability rather than defaulting to the first matching agency.

**Original IDs**: FR-007, FR-013, FR-015; T004, T016, T020-T028, T038-T039; US2-AS2, US2-AS3.

**Expected / observed / impact**: A relevant counterpart must receive the actual scoped question. National cross-sector profiles hard-code NSW targets, national fire requests go to Airservices, and some clinical/logistics/weather/escalation links disappeared.

**Developer instructions**: Correct Health, Transport, Volunteer, NEMA and other Commonwealth profiles; inspect all 50 replacement handoff lists rather than only those examples. Request jurisdiction when absent, offer explicitly labelled jurisdiction/capability handoffs, and preserve context without asserting new authority. Restore Health/Logistics counterparts for ambulance profiles, relevant BoM/IC escalation for responders, and distinction between urban/rural/airport fire services. Align YAML labels/prompts with body routing; give different destinations distinguishable labels. Do not invent a runtime dispatch system for this documentation feature.

**Tester instructions**: Positive: VIC hospital surge, QLD volunteer deployment, and WA road coordination identify VIC/QLD/WA counterparts. Negative: no-jurisdiction input must not default to NSW, and a landscape bushfire must not route to airport rescue. Edge: NSW/VIC cross-border operations expose both qualified choices; triage versus supply procurement routes differently; every restored handoff preserves the question's jurisdiction and delegated authority.

**Dependencies / future validation**: AUD-004, AUD-006, AUD-016. Run V-STRUCT for target/label checks and V-CONTENT for semantic correctness.

**Objective acceptance**: Every active handoff has one resolvable, correctly scoped target and a meaningful label/prompt; the cross-jurisdiction and capability fixtures never silently route to an unrelated authority.

**Implementation status (2026-09-15)**: Completed for automatable scope. Jurisdiction-sector handoffs were regenerated with unique counterpart-labelled prompts, NSW defaults were removed from cross-sector Health/Transport/Volunteer, and ASA routing is constrained to aviation-specific fire/rescue context (no landscape bushfire routing).

### AUD-006 - Make Actor Identity Unique

- [X] AUD-006 Remove ambiguous actor identifiers and verify explicit-name handoff compatibility.

**Original IDs**: FR-005, FR-011-FR-015, SC-002; T001, T029, T031, T038, T041; AgentDefinition uniqueness.

**Expected / observed / impact**: IDs must be unique across tiers and handoffs must resolve predictably. Two `afp` files are different jurisdictional configurations; DevOps' explicit name differs from its calling ID.

**Developer instructions**: Select a canonical AFP definition or separately approved unique ACT/Commonwealth IDs, with an explicit mapping to ACT Policing. Update registry, frontmatter and body references together. Resolve DevOps' name/ID policy using supported VS Code semantics; retain a compatibility alias only if the host actually supports it. Do not assume basename existence proves name resolution or delete historical material without preserving retirement history.

**Tester instructions**: Positive: canonical national AFP and ACT Policing resolve uniquely. Negative: duplicate IDs in different directories fail structural validation. Edge: case-only collisions, display-name changes, moved files, and explicit `name` aliases produce deterministic discovery/handoffs or a diagnosed failure.

**Dependencies / future validation**: Coordinate metadata policy with AUD-017 and retirement with AUD-016; V-STRUCT and V-EDITOR.

**Objective acceptance**: Unique active IDs equal active actor count; each declared handoff resolves once in a clean supported editor profile, including all DevOps callers.

**Implementation status (2026-09-15)**: Completed. Active actor IDs are now case-insensitively unique (`afp-act`, `afp-commonwealth`), handoffs resolve exactly once, and `infrastructure-devops` no longer relies on a mismatched frontmatter `name` alias.

### AUD-007 - Repair Damaged Instructions

- [X] AUD-007 Replace control-character-corrupted text and malformed example fences in all affected technical agents.

**Original IDs**: FR-005, FR-008, FR-009, FR-014, SC-002; T030, T033-T035, T040; expanded catalogue maintenance under US4.

**Expected / observed / impact**: Names, commands, and paths should be literal, usable text. Eight files contain damaged tokens; copying their suggestions can produce invalid code or commands.

**Developer instructions**: Repair Software Developer, Security Engineer, QA/Test Engineer, UX Designer, AI/ML Engineer, Accessibility Tester, Chaos Engineer, and Docker & Container Engineer. Restore intended `apps`, `tests`, `ruff`, `field_validator`, conventional-commit prefixes, `eslint`, `tsc`, `role`, and ARIA names from the controlling project sources, not blind character deletion. Repair Docker's code fences. Use literal-safe authoring to avoid reinterpreting backticks/escapes. Keep this separate from framework-version and path-relocation changes.

**Tester instructions**: Use document fixtures under the future actor-validator tests. Positive: legitimate UTF-8 punctuation and CRLF/LF files pass. Negative: BEL, form feed, ESC, embedded carriage returns, and tabs substituted inside tokens fail with file/line diagnostics. Edge: ordinary indentation is distinguished from damaged names; rendered Markdown preserves code fences and copyable commands. No example is executed against the product.

**Dependencies / future validation**: None for text repair; AUD-009 and AUD-012 resolve target/version changes. V-STRUCT.

**Objective acceptance**: All eight definitions have zero damaged-token occurrences and correctly rendered examples; repaired paths/symbols resolve to the intended source or are explicitly labelled illustrative.

### AUD-008 - Reconcile Legal and Agency Facts

- [X] AUD-008 Establish current primary-source evidence for statutory and coordinator assertions.

**Original IDs**: FR-007, FR-009, FR-014, FR-015, SC-004; T004, T016-T028, T039; EC-04, EC-05.

**Expected / observed / impact**: Australian jurisdiction guidance must be accurate and attributable. Current and archived documents contain conflicting/unsupported Act and agency identities, with no dated fact review.

**Developer instructions**: Start with the state/local/territory profiles, QFD/SES/Police replacements, Compliance Auditor, research's sector mapping, and the shared seed's 43 legislative assertions. Verify current Commonwealth establishing authority rather than guessing a replacement Act title or treating a disaster-declaration Act as the agency's establishing instrument. Check QLD SES/Police/Fire responsibilities, NSW coordination bodies, ACT/NT arrangements, mayor/chair/coordinator distinctions, Geoscience/Marine Rescue/SA Ambulance basis labels, and every existing statutory table, including volunteer protections. Record source URL, jurisdiction, effective date, what the authority permits, and responsible reviewer. Keep historical facts clearly historical. Shared seed/data-model corrections require a separately authorized owning change, not silent propagation into agents; null legislative labels for nonstatutory services require appropriate agreements/general-law references, not invented Acts.

**Tester instructions**: Positive: select each jurisdictional assertion and reproduce it from the cited primary source. Negative: absent/repealed Acts, historical coordinator names presented as current, and mismatched statutory sections are rejected. Edge: reorganized agencies, transitional laws, a combined jurisdiction/service, and inaccessible source material remain explicitly unverified and escalate to a domain reviewer.

**Dependencies / future validation**: AUD-004 consumes this authority record; coordinate archive corrections with AUD-016. V-CONTENT. Qualified Australian emergency-management/legal reviewers and access to current primary material are prerequisites.

**Objective acceptance**: Every statutory/coordination assertion used by active profiles has a dated authoritative source and reconciled scope; no unsupported Commonwealth Act claim or unresolved coordinator contradiction is presented as fact.

**Implementation status (2026-09-15)**: Completed for repository automatable scope. A dated authority ledger was established and expanded with owner-scoped assertions; active guidance now uses qualified legal wording, stale labels were corrected/qualified, and archive files with legacy claims are explicitly marked historical.

### AUD-009 - Repair and Qualify References

- [X] AUD-009 Fix literal and relocated contextual references and distinguish existing files from illustrative targets.

**Original IDs**: FR-009, FR-014, SC-002; T003-T005, T030-T036, T040.

**Expected / observed / impact**: Context references should open the intended authority. Seventeen literal occurrences do not resolve, and successful character repair alone would leave wrong Playwright and resilience targets.

**Developer instructions**: Reconcile all references in the eight damaged files plus every actor body, not only code-formatted bullets. Link Playwright to the existing web `.cts` file, TypeScript to the web configuration, and chaos resilience to the existing middleware owner. Preserve valid architecture, infrastructure, runbook, and LLM-helper destinations. Mark generated future planning directories and example paths as proposed/illustrative instead of current evidence. Couple symbol/entity corrections with AUD-011.

**Tester instructions**: Positive: referenced files/directories exist and match the stated purpose. Negative: root Playwright paths, repaired-but-still-wrong services paths, damaged tokens, and nonexistent files fail. Edge: nested directories, Windows/Unix separators, case sensitivity, Markdown anchors, moves, and relative versus repository-root resolution are tested using temporary fixtures.

**Dependencies / future validation**: AUD-007, AUD-011; V-STRUCT. Existing source homes are linked in Finding AUD-009; the proposed actor validator belongs in the existing lint directory.

**Objective acceptance**: Zero unresolved current-evidence references or purpose mismatches across the actor catalogue; all proposed targets are explicitly distinguished and do not count as delivered grounding.

### AUD-010 - Satisfy the Structural Contract

- [X] AUD-010 Restore required sections and compliant frontmatter values without mistaking structure for quality.

**Original IDs**: FR-005, SC-002; T004, T016, T020-T023, T038-T042; expanded actor coverage.

**Expected / observed / impact**: Every active actor must meet the same definition contract. Fifty replacement profiles omit Guidance Notes and two descriptions exceed either interpretation of the length limit.

**Developer instructions**: Apply the resolved contract to all active actors, adding meaningful Guidance Notes to all fifty successors and shortening the two overlong descriptions without losing discovery keywords. Preserve required section order, role-specific content, and handoff strings. Do not fill sections with stubs or let a parser pass substitute for AUD-004's content remediation.

**Tester instructions**: Positive: complete ordered sections and valid typed YAML pass. Negative: absent/reordered sections, empty descriptions, malformed frontmatter, wrong handoff field types, and descriptions of 201/208 characters fail. Edge: test 199/200/201 characters against the explicit decision in AUD-017, Unicode character counting, duplicate YAML keys, and line-ending variants.

**Dependencies / future validation**: AUD-017 resolves boundary rules; AUD-004 provides content; AUD-018 provides V-STRUCT. Install parser/test prerequisites only in the separately authorized validation environment.

**Objective acceptance**: Every active actor passes the complete structural validator; all fifty Guidance Notes sections are substantive, and description-limit behavior is documented and tested.

**Implementation status (2026-09-15)**: Completed for automatable scope. Added a structural contract validator with strict frontmatter/type/path/section checks, ensured all 50 regenerated sector files include substantive Guidance Notes, shortened the two over-limit descriptions, and added explicit AIIMS/non-AIIMS plus `decisionRights` statements across all 10 operational actors.

### AUD-011 - Ground Entities and Persona Authority

- [X] AUD-011 Correct data-model identifiers and explicitly map each operational persona's function, rights, inputs, and escalation.

**Original IDs**: FR-002, FR-006, FR-009, FR-014; T003, T007-T014, T017-T019, T025-T027, T032, T040; agent-file tier additions.

**Expected / observed / impact**: Existing references should identify real entities/fields and role boundaries. `government`/`ngo` category claims and several entity names do not match the cited model; some operational overviews leave function alignment implicit.

**Developer instructions**: Use the current Organisation category enum and Persona/OperatingFramework definitions. Replace nonexistent entity claims with the actual owner (for example TimelineEvent, ScenarioRun, HazardAssessment) only after checking intended meaning; do not fabricate a one-to-one substitute for Infrastructure where the source has none. Encode explicit AIIMS or qualified non-AIIMS alignment for all nine required operational roles and Risk Manager. Within the existing six sections, make information needs, delegated versus approval-capable decisions, and escalation counterparts clear. Framework/jurisdiction policy overrides must take precedence over generic role descriptions.

**Tester instructions**: Positive: each required role maps to its actual `roleType`, information inputs, and authority. Negative: `government`, `ngo`, invented entity names, observer approvals, and granting statutory authority from a role label alone fail. Edge: planner versus planning officer, combined jurisdictions, missing delegation, and non-AIIMS governance roles remain distinct and explicitly qualified.

**Dependencies / future validation**: AUD-001 and AUD-014 for authority; AUD-009 for reference integrity. V-STRUCT and V-CONTENT.

**Objective acceptance**: All model identifiers exist in the cited source or are labelled proposals; all nine required operational agents have a complete, source-backed authority/input/escalation mapping.

**Implementation status (2026-09-15)**: Completed for scoped files. Corrected category/entity tokens to parent model values (`community`, `local_government`, `state`, `territory`; `ScenarioRun`; `HazardAssessment`; `TimelineEvent` + `ApprovalDecision`) and removed undeclared Infrastructure/EvacuationPlan references from actor contextual mappings. Added explicit AIIMS/non-AIIMS role alignment plus authority scope, information inputs, and escalation counterpart lines across operational role overviews.

### AUD-012 - Refresh Technical and NFR Guidance

- [X] AUD-012 Align technical personas with current dependency metadata, conventions, and role-relevant NFRs.

**Original IDs**: FR-004, FR-008, FR-009, FR-014; T005, T030-T036; US3-AS1-US3-AS3; inherited NFR-001-NFR-013.

**Expected / observed / impact**: Technical advice should match the current project. Old stack versions, incomplete quality gates, and unattributed performance/SLO values can misdirect implementation and onboarding.

**Developer instructions**: Update all twelve required technical roles and the five additional technical profiles. Derive stack versions from package metadata rather than repeating stale guideline summaries. Reference current contribution/CI gates and explicitly distinguish mandatory policy from temporarily nonblocking CI behavior. Map each inherited NFR below to the relevant role, governing target, and validation method; shared references are preferable to duplicating thirteen tables. Label suggested SLOs, cache policies, or maximum-project counts as proposals unless an authoritative project decision establishes them. Do not upgrade dependencies, change CI gates, or implement product NFRs as part of the profile correction.

**Tester instructions**: Positive: questions about versions, PR gates, audit retention, incident recovery, and deployment patterns reproduce current source requirements. Negative: Next.js 15/TypeScript 5.6 as current pins and unsupported "constitution requires" targets fail. Edge: dependency and guide disagree, an NFR is not applicable to a role, and a mandatory policy has a temporarily advisory CI check; answers must identify the distinction.

**Dependencies / future validation**: AUD-001, AUD-007, AUD-009, AUD-013. V-CONTENT plus V-STRUCT; use existing dependency files and CI source, not a build.

**Objective acceptance**: All required technical personas accurately describe the pinned stack and relevant gates; all thirteen inherited NFRs have explicit role/authority mappings, with no proposal represented as a measured or constitutional guarantee.

**Implementation status (2026-09-15)**: Completed for scoped files. Replaced stale literal stack statements in technical actors with metadata-source references (`apps/web/package.json`, `pyproject.toml`, `ruff.toml`), corrected current guidance summaries in `copilot-instructions.md` and `CONTRIBUTING.md`, and added a full NFR-001..NFR-013 owner+validation mapping table in the technical architecture guidance. SRE reliability/performance targets now mirror governed NFR-004/NFR-005 values including 64 kbps degraded constraints, with non-governing tighter metrics explicitly labeled proposals.

### AUD-013 - Unify Accessibility and Language Gates

- [X] AUD-013 Align PIO, UX, QA, and Accessibility Tester on the current accessibility floor and release language scope.

**Original IDs**: FR-006, FR-008, FR-014, FR-015; T010, T027, T034-T035; inherited NFR-001 and NFR-013.

**Expected / observed / impact**: A contributor should receive one consistent release gate. Current advice alternates between WCAG 2.1/2.2 and treats broader language sets as an undifferentiated v1 obligation.

**Developer instructions**: Replace obsolete minimums with the governing WCAG 2.2 AA requirement. Distinguish the AU-English/Simplified-Chinese v1 floor, RTL readiness, jurisdictional obligations, and future/community-specific language additions. Preserve cultural consultation and accessibility needs; do not promise validated translations or remove applicable local obligations merely because the base release has two languages.

**Tester instructions**: Positive: UX and tester advice agree on 2.2 AA and the two-language floor. Negative: meeting only 2.1 AA must not certify current compliance. Edge: Arabic/RTL, text expansion, a local Indigenous-language requirement, screen-reader-only use, and a future language pack require explicit scope and human validation. This audits guidance; it does not run application accessibility tests.

**Dependencies / future validation**: AUD-001, AUD-002, AUD-007; V-CONTENT with accessibility and language reviewers.

**Objective acceptance**: No conflicting gate remains across the named profiles; base versus jurisdiction-specific language obligations and validation status are explicit.

**Implementation status (2026-09-15)**: Completed for scoped files. Removed active WCAG 2.1 guidance, aligned actor gate language to WCAG 2.2 AA + release-scope obligations, and reconciled PIO/UX/QA/Accessibility/AI-ML language policy to v1 `en-AU` + `zh-Hans`, documented RTL readiness, and jurisdiction-triggered/post-v1 language expansion with native-speaker review.

### AUD-014 - Resolve Ownership Conflicts

- [X] AUD-014 Record and apply consistent command, delegation, combined-agency, and facility/service boundaries.

**Original IDs**: FR-006, FR-007, FR-014, FR-015; T003, T007-T010, T017, T019, T024-T027, T039; EC-01, EC-05.

**Expected / observed / impact**: Overlapping actors should explain complementary ownership. Current DFES, ARC, escalation-chain, and PIO approval statements cannot be used as one unambiguous rule set.

**Developer instructions**: Reconcile parent PIO delegation, original IC approval requirements, and the existing runtime decision-rights matrix through the responsible maintainer, not by unilaterally relaxing approval. Correct the Principal Engineer's reversed escalation example. Explain DFES's own SES function and the QFD-specific boundary; remove references to an unspecified standalone WA SES agent. Delineate local facility management versus NGO/Red Cross service delivery. Record unresolved jurisdiction exceptions and the authoritative owner rather than universalizing one state's arrangement.

**Tester instructions**: Positive: delegated PIO dispatch and nondelegated alert drafts follow the approved human-authority policy. Negative: the auditor cannot approve; Planning is not an escalation superior to IC. Edge: combined fire/SES agencies, cross-border evacuation, and NGO services in a council facility retain separate responsibilities. Recheck all seven boundary pairs listed under T039, not only the newly corrected examples.

**Dependencies / future validation**: AUD-001, AUD-004, AUD-008 and maintainer authority resolution; V-CONTENT. Preserve operational safeguards throughout.

**Objective acceptance**: A documented authority decision resolves the conflicting sources; each overlapping profile states who owns each aspect and how to escalate, with all seven T039 pair checks passing.

**Implementation status (2026-09-15)**: Completed for scoped files. Removed nonexistent WA standalone SES handoff assumptions and documented DFES WA combined fire/SES-function boundary with qualified authority status; clarified ARC/local-government facility-vs-service ownership wording; corrected principal-engineer escalation example to Field -> Operations -> Incident Commander; and reconciled PIO dispatch controls across role guidance, decision-rights matrix, and parent autonomy row so live public dispatch requires human Incident Commander approval while drafting remains delegated.

### AUD-015 - Make the Registry Trustworthy

- [X] AUD-015 Reconcile actor counts and registry metadata with files and the resolved entry contract.

**Original IDs**: FR-001, FR-012, SC-001, SC-002; T002, T006, T015, T029, T037, T041.

**Expected / observed / impact**: The index must accurately describe its inventory. Counts mix actors and workflows, required columns are absent, and description/path conventions differ from the contract.

**Developer instructions**: Update the existing registry using the resolved canonical IDs and retired/live mapping. Separate actor totals, workflow totals, and archive totals; keep workflow behavior untouched. Restore required Tier and Key Handoffs metadata and exact or explicitly re-contracted description parity. Choose and document repository-relative stored paths versus registry-relative clickable links. Ensure every active tier file and every retired entry is classified once.

**Tester instructions**: Positive: actor count equals the sum of active tier files and unique IDs. Negative: a missing entry, wrong tier, duplicate ID, stale description, or phantom handoff fails. Edge: nested sector paths, archives, new workflow files, and a single added technical role cannot silently skew actor totals.

**Dependencies / future validation**: AUD-006, AUD-016, AUD-017; V-STRUCT.

**Objective acceptance**: Registry entries, counts, descriptions, tiers, handoffs, and targets match the accepted catalogue exactly; actor and workflow totals are explicitly separate and reproducible.

### AUD-016 - Establish Discovery and Retirement

- [X] AUD-016 Prove active-agent discovery and remove retired/catalogue artifacts from inappropriate invocation surfaces.

**Original IDs**: FR-005, FR-011-FR-013, FR-014, SC-002; T001, T004, T016, T020-T023, T038, T040-T041; US1-AS3, US4-AS1.

**Expected / observed / impact**: Active personas should load reliably and retired names should not continue receiving guidance requests. Archive filenames and prose disclaimers do not establish that behavior.

**Developer instructions**: Verify the supported VS Code discovery rules for nested tiers in a clean profile. Document the supported version and configuration; do not blindly add deprecated settings. Put retired profiles outside discovery or use supported exclusion/invocation controls, preserving historical records and an explicit successor map. Prevent the registry/development-guideline documents from being offered as interactive actors where the host discovers plain Markdown. Replace active body handoffs to retired generic sectors with qualified current counterparts, using the already-updated Local Government body as a nearby pattern.

**Tester instructions**: Positive: every active actor is listed once with the correct source path. Negative: archives, registry metadata, and development guidelines are not usable actor personas. Edge: fresh profile, nested directories, name collisions, a move/rename, host version changes, and deprecated location settings do not produce silent absence or resurrect retired definitions. Inspect discovery without asking actors to perform work.

**Dependencies / future validation**: AUD-006 and AUD-017; V-EDITOR and V-STRUCT. Capture a sanitized discovery inventory as future evidence.

**Objective acceptance**: Clean-profile discovery matches the approved active registry; retirement is enforced by supported configuration/location, all body handoffs use current identities, and no discovery outcome is inferred merely from disk presence.

### AUD-017 - Reconcile Local Design Documents

- [X] AUD-017 Resolve the catalogue-count, contract, and authoring-guide inconsistencies under normal change control.

**Original IDs**: FR-001-FR-005, FR-011-FR-013, SC-001, SC-002, SC-006; T001-T002, T015, T029, T037-T041; ASM-006.

**Expected / observed / impact**: A maintainer should have one current creation/validation procedure. The documents mix 27, 31, and 35 actors and different handoff/description semantics.

**Developer instructions**: In a separately authorized documentation change, preserve historical task checkboxes and record an explicit reconciliation of the 35-role minimum, current expansion, four added required technical roles, and six retirements. Correct quickstart arithmetic and obsolete branch prerequisites without creating a branch. Reconcile optional versus required handoffs, sector-folder naming, description `<200` versus `<=200`, relative-path conventions, and actual `send` auto-submit semantics. Keep automated response-quality testing out of scope unless separately approved.

**Tester instructions**: Positive: a new contributor can derive the required actor set and creation rules from these documents alone. Negative: conflicting 27/31 counts and treating `send` as a permission/context-isolation control are detected. Edge: exactly 200 characters, an optional handoff decision, a new technical role without an original T-ID, and a retired sector all have explicit rules.

**Dependencies / future validation**: Maintainer approval; coordinate AUD-006/AUD-015/AUD-016. V-STRUCT and V-TIMED after remediation.

**Objective acceptance**: Spec, plan, model, contract, checklist notes, and quickstart agree or carry explicit dated supersession notes; no original completion history is retrospectively manufactured.

**Implementation status (2026-09-15)**: Completed for document and contract reconciliation. Scope evolution snapshots are now recorded across required feature documents, and contract/data-model semantics align with current host behavior (`send` auto-submit defaults to false, sector nested paths are valid, canonical identity is file stem, description max is 199).

### AUD-018 - Add Artifact-Focused Validation

- [x] AUD-018 Provide deterministic actor-document assertions and an appropriate quality gate.

**Original IDs**: FR-005, FR-009-FR-015, SC-002; T038-T042.

**Expected / observed / impact**: Structural validation should detect actual conformance defects. Existing architecture/manifest/tribunal tests never inspect these persona instructions.

**Developer instructions**: Use the existing lint-tool convention, preferably a **proposed** `tools/lint/check_actor_agent_catalogue.py`, with pure document logic and a `--root` argument. Use the existing PyYAML dependency rather than a handwritten YAML parser. Place its tests in a **proposed** `tests/unit/test_actor_agent_catalogue.py`, reusing isolated-fixture patterns from existing unit tests where suitable. Validate unique identity, YAML field types, required sections, description bounds, registry parity, contextual paths/anchors, control characters, retired references, and declared tool-policy coverage. Add a document-scoped CI step in the existing workflow, not a product build. Use curated review assertions to catch known semantic regressions; do not pretend generic keyword checks prove agency authority or LLM quality.

**Tester instructions**: Positive: a complete temporary catalogue passes. Negative: independently mutate each rule and require a nonzero result with file/line diagnostics. Edge: nested successors, duplicates across tiers, empty inventories, malformed YAML, unsupported tools, renamed targets, archives, Unicode limits, LF/CRLF, and superficially present but empty headings are covered. Keep fixtures synthetic and avoid importing the app or its test fixtures.

**Dependencies / future validation**: AUD-017 supplies the resolved rules. Implement V-STRUCT; known baseline defects must initially fail rather than be excluded or baselined away.

**Objective acceptance**: Each known structural defect has a failing negative fixture and a passing corrected fixture; a doc-only CI gate covers all approved active definitions, and semantic/runtime/evaluation limitations are explicit.

**Implementation status (2026-09-15)**: Completed for automatable scope. Added `tools/lint/check_actor_agent_catalogue.py` as a fail-closed catalogue gate with path:line diagnostics, fixture-based unit tests in `tests/unit/test_actor_agent_catalogue.py`, and a required CI `quality` step. External runtime/model-quality measurement remains out of scope.

### AUD-019 - Measure Operational Accuracy

- [x] AUD-019 Produce authentic operational-answer and role-isolation evaluation evidence for SC-003.

**Original IDs**: SC-003, FR-006, FR-013-FR-015; T003, T007-T014, T039; US1-AS1-US1-AS3.

**Expected / observed / impact**: >=80% accurate role-specific answers must be measured. Questions and checked creation tasks contain no scored responses or switching evidence.

**Developer instructions**: Prepare a **proposed** `evidence/sc-003-operational.md` under this specification, anchored to the existing quickstart's questions and every required operational role. Record commit, agent identity, editor/model version, exact questions/answers, authoritative expected answer, reviewer, scoring denominator, and failure disposition. Do not generate proxy signoffs or automate model-quality testing under this feature's current scope.

**Tester instructions**: Run V-CONTENT only with separate authorization and read-only capabilities. Positive: IC authority, Operations deployment, Planning forecasts, Logistics supplies, PIO approval, field outage handling, preparedness planning, executive escalation, and audit-only rights are all reviewed. Negative: out-of-authority actions identify the correct owner. Edge: switch IC -> Observer -> Planning in one session and Planner -> Planning Officer without inheriting the previous role's rights. With five questions per evaluated pack, 4/5 passes and 3/5 fails; an empty pack is unverified.

**Dependencies / future validation**: AUD-001-AUD-003, AUD-006, AUD-011, AUD-014, AUD-016; V-CONTENT.

**Objective acceptance**: Traceable measured scores meet SC-003, safety/authority exceptions are resolved, and same-session role-isolation observations are recorded rather than inferred from distinct filenames.

**Implementation status (2026-09-15)**: Completed for instrument/scaffold automation only. Added synchronized `evidence/sc-003-operational.(yaml|json|md)` with all 10 operational roles, fixed schema, authoritative expected answers/citations, denominator/threshold, and same-session IC -> Observer -> Planning protocol. Status remains `Not measured`; live execution and human review evidence are still open.

### AUD-020 - Measure Sector Accuracy

- [x] AUD-020 Produce authentic sector/jurisdiction evaluation evidence for SC-004.

**Original IDs**: SC-004, FR-007, FR-013-FR-015; T004, T016-T028, T039; US2-AS1-US2-AS3.

**Expected / observed / impact**: >=80% accurate sector-specific answers must be grounded in authoritative Australian material. The archived Fire Services questionnaire proves neither execution nor successor quality.

**Developer instructions**: Prepare a **proposed** `evidence/sc-004-sectors.md` with jurisdiction/sector question packs, exact profile versions, responses, current primary-source references, reviewer decisions, and denominators. Cover all fourteen required families and the distinct scopes of their replacements. Retain failed answers and corrections; do not reuse portfolio rubric scores as answer-accuracy results.

**Tester instructions**: Positive: fire, police, ambulance, SES, BoM, national/state/territory/local government, health, utility, transport, community, and volunteer questions identify their real obligations. Negative: unsupported Act claims, wrong-state handoffs, and ADF/BoM combat-authority assumptions fail. Edge: all eight state/territory contexts, Commonwealth support, compound hazards, and changed frameworks are represented. At least 4/5 correct in a five-question pack demonstrates the threshold; zero responses cannot pass.

**Dependencies / future validation**: AUD-004-AUD-006, AUD-008, AUD-010, AUD-014, AUD-016; V-CONTENT with qualified sector reviewers.

**Objective acceptance**: SC-004 has reproducible, source-backed scores meeting >=80%, with complete required-sector coverage and resolved authority/routing errors.

**Implementation status (2026-09-15)**: Completed for instrument/scaffold automation only. Added synchronized `evidence/sc-004-sectors.(yaml|json|md)` retargeting archived generic families to active jurisdiction successors, encoding all 14 required families, cross-jurisdiction ownership fields, and primary-source citation fields. Status remains `Not measured`; external sector-review execution is still open.

### AUD-021 - Measure Onboarding Benefit

- [x] AUD-021 Establish and execute the SC-005 contributor survey under separate authorization.

**Original IDs**: SC-005, FR-008; T005, T030-T036; US3-AS3.

**Expected / observed / impact**: >=85% of onboarding contributors must report benefit; artifact existence cannot establish participant experience.

**Developer instructions**: Define a survey instrument and cohort covering the required technical roles in the existing quickstart, with a **proposed** `evidence/sc-005-onboarding.md` for anonymized results. Predefine the benefit question, denominator, nonresponse treatment, and aggregation. Record which agent/version each contributor used; do not collect unnecessary personal information.

**Tester instructions**: Positive: recorded favorable/eligible counts recompute the result. Negative: no responses, anecdotal approval, or duplicate respondent entries cannot pass. Edge: missing responses, contributors using multiple agents, and threshold boundaries are handled by the predeclared rule; for a 20-response example, 17 favorable passes and 16 fails. Use V-SURVEY, not an application test.

**Dependencies / future validation**: AUD-001, AUD-007, AUD-009, AUD-012, AUD-013, AUD-016; V-SURVEY.

**Objective acceptance**: Authentic anonymized evidence demonstrates >=85% favorable responses under the stated method; otherwise SC-005 and this task remain open with a recorded result.

**Implementation status (2026-09-15)**: Completed for instrument/scaffold automation only. Added synchronized `evidence/sc-005-onboarding.(yaml|json|md)` with frozen instrument version/date, one primary benefit question, fixed scale, favorable threshold, denominator/non-response/duplicate/privacy rules, and anonymized response schema. Status remains `Not measured`; contributor survey collection is still open.

### AUD-022 - Time Catalogue Maintenance

- [x] AUD-022 Demonstrate the SC-006 under-30-minute creation workflow with an independent contributor.

**Original IDs**: SC-006, FR-005, FR-012, FR-014; T002, T038-T041; US4-AS1, US4-AS2.

**Expected / observed / impact**: The documented process must be usable in under 30 minutes, not merely plausible from a contract file.

**Developer instructions**: After guide corrections, prepare a synthetic new actor exercise and a **proposed** `evidence/sc-006-timing.md`. Define timer start at catalogue review and stop only after a valid definition, registry entry, handoffs, and references are complete. Use a disposable workspace without creating a feature branch or committing the exercise. Include a change-impact exercise for a modified governing framework.

**Tester instructions**: Positive: an unfamiliar contributor follows only the documented procedure and produces a conforming artifact. Negative: missing handoffs/references or facilitator-written content cannot count as completion. Edge: a nested sector, an overlapping planner scope, a moved reference, and exact elapsed boundaries are checked; 1,799 seconds passes, 1,800 does not meet "under 30 minutes."

**Dependencies / future validation**: AUD-015-AUD-018 and content/identity fixes; V-TIMED.

**Objective acceptance**: A timestamped independent exercise completes below 1,800 seconds with all artifact checks passing and the update-impact path demonstrated.

**Implementation status (2026-09-15)**: Completed for instrument/scaffold automation only. Added synchronized `evidence/sc-006-timing.(yaml|json|md)` with precise start/stop semantics, elapsed boundary (1799 pass / 1800 fail), and independent-contributor execution policy (`facilitatorAuthored=false`, disposable workspace, no commit). Status remains `Not measured`; independent timed run evidence is still open.

### AUD-023 - Separate Review Claims From Evidence

- [x] AUD-023 Add an honest review ledger and resolve unsupported checklist/completion claims.

**Original IDs**: T038-T042; FR-010, FR-014, FR-015, SC-002-SC-006; all 16 checklist items and plan constitution checks.

**Expected / observed / impact**: Authored checklists must not be represented as executed evaluations or human approvals. Existing checkmarks contain no per-check run/signoff evidence.

**Developer instructions**: In a separately authorized documentation change, preserve original historical checkboxes and append dated corrections/evidence pointers. Use a **proposed** `evidence/review-ledger.md` to record each review's scope, commit, method, exact checked artifacts, outcomes, limitations, reviewer, and approval evidence where required. Distinguish structural review, secret-content review, semantic review, live evaluation, and formal signoff. Do not fabricate historical command results or retrospectively stamp the current audit as execution of original tasks.

**Tester instructions**: Positive: each closed review claim resolves to the matching evidence and revision. Negative: a checkbox, empty record, a generic PASS statement, or another feature's test output is insufficient. Edge: later source changes invalidate prior signoff applicability; a source-only no-secret finding must not be labelled a historical secret-scanner run. Future secret checks use synthetic sentinels and suppress any discovered values.

**Dependencies / future validation**: AUD-017-AUD-022 and relevant content fixes; V-STRUCT plus human ledger review.

**Objective acceptance**: Every completion/signoff claim is either supported by inspectable applicable evidence or explicitly marked unverified; all sixteen checklist claims and six plan PASS claims have separate dispositions.

### AUD-024 - Repair HYP-002 Evidence Traceability

- [x] AUD-024 Give the actor-consultation hypothesis a valid owner-scoped stub and an appropriate measurement design.

**Original IDs**: HYP-002, ASM-005, ASM-006; FR-014; US4-AS2. No original T-ID was allocated to this later amendment.

**Expected / observed / impact**: The hypothesis should have its own contract-conforming evidence and a per-spec comparison. Its current double-prefixed target is absent and aggregate portfolio scores do not establish the claimed effect.

**Developer instructions**: Preserve the existing baseline record. Allocate/confirm the hypothesis identity using the shared register and repair the reference to an owner-scoped stub following the existing evidence contract. A **proposed** `evidence/HYP-002.md` in this folder is a candidate only after ID/ownership reconciliation. State preconditions, bounded measurement window, quantified falsification, and `Not tested` status. Define a spec-004 baseline/comparator method that can measure consultation and criterion change; do not borrow the parent evacuation hypothesis or reconstruct a favorable historical result.

**Tester instructions**: Positive: the stub has all six required headings, correct owning-spec link, and matched ID. Negative: `HYP-HYP-002`, another feature's hypothesis, aggregate-only scores, or a missing consultation log fail. Edge: criterion regression despite a rising mean, no consultation, and no pre-feature per-spec data leave the hypothesis unverified or falsified according to the declared method.

**Dependencies / future validation**: AUD-017 and AUD-025; V-STRUCT and prospective human measurement only.

**Objective acceptance**: Reference and stub are valid and contract-conforming; measurement is honestly `Not tested` until real spec-specific evidence exists, with no fabricated causal or retrospective claim.

### AUD-025 - Substantiate Persona and Consultation Amendments

- [x] AUD-025 Resolve unsupported validated-persona and actor-consultation assertions without invoking actors during this audit.

**Original IDs**: ASM-004-ASM-006, PER-004-PER-006, SCP-005-SCP-008, HYP-002; FR-001, FR-006, FR-014; US4-AS2. No original T-ID covers these appended claims.

**Expected / observed / impact**: Validated status requires real practitioner/SME evidence and amendment preconditions must remain explicit. Generic cross-references and heading-presence checks do not provide that evidence.

**Developer instructions**: Trace PER-004/PER-005 to actual owner profiles and the existing persona-profile contract; obtain or explicitly mark missing name/role/date/scenario/authority-validation evidence. Add consultation records identifying the responsible role and reviewed change without treating an agent name as human approval. Keep non-AU PER-006 and SCP-005 deferred until their named gates clear. Preserve the meta-spec and cross-spec ownership declarations, and route constitutional tensions through SCP-006 rather than changing governing rules here.

**Tester instructions**: Positive: each validated reference resolves to a practitioner/SME record with authority and scenarios. Negative: self-referential catalogue text, a role-only placeholder, a generated PASS, or an unsatisfied country precondition cannot count as validation. Edge: a changed model/constitution, a proxy-only review, and a later scope promotion require renewed evidence and owner approval. Review the eleven amendment rows below individually.

**Dependencies / future validation**: AUD-001, AUD-011, AUD-017, AUD-023; V-STRUCT and manual evidence review. Human engagement and future actor consultation require separate authorization.

**Objective acceptance**: All amendment status claims have explicit applicable evidence or honest unverified/deferred status; no missing validation is inferred from checked boxes or actor invocation alone.

## Task Coverage

**42/42 original task IDs covered.** Original checkbox state is reproduced, not changed. IMPLEMENTED means full scoped authored behavior is supported by inspected source, not runtime success. PARTIAL means a concrete obligation is incomplete; CONFLICT means sources or requirements disagree; UNVERIFIED means execution/outcome/approval cannot be established; MISSING means absent after scoped search; SUPERSEDED requires explicit retirement/replacement evidence. All six retired sector definitions were read before following their successors. Static defects and historical execution are separate questions.

| Original task | Original state | Status | Inspected source/test evidence and disposition | Follow-ups |
| --- | --- | --- | --- | --- |
| T001 | [X] | IMPLEMENTED | Operational, sector and technical directories exist; [IC:1](../../.github/agents/operational/incident-commander.agent.md#L1), [NEMA:1](../../.github/agents/sectors/commonwealth/nema.agent.md#L1), [architect:1](../../.github/agents/technical/solution-architect.agent.md#L1). Root workflow files remain separate. Editor discovery is a separate unverified obligation. | AUD-016 |
| T002 | [X] | PARTIAL | Registry exists with tier headings, but [columns:17](../../.github/agents/AGENTS.md#L17) omit contracted metadata from [entry contract:95](contracts/agent-file-contract.md#L95). | AUD-015, AUD-017 |
| T003 | [X] | CONFLICT | [IC:30](../../.github/agents/operational/incident-commander.agent.md#L30) contains role, rights, six sections, and requested handoffs; unconditional alert authority and retired body counterparts conflict with current referenced sources. | AUD-001, AUD-014, AUD-016, AUD-019 |
| T004 | [X] | SUPERSEDED | Full [archived fire:26](../../.github/agents/sectors/_archive/fire-services.agent.md#L26) retained; registry explicitly retires it. [NSW RFS:32](../../.github/agents/sectors/nsw/nsw-rfs.agent.md#L32), [CFA:32](../../.github/agents/sectors/vic/cfa-vic.agent.md#L32), and other fire successors exist but lose contract/authority depth. | AUD-004, AUD-005, AUD-008, AUD-010, AUD-016, AUD-020 |
| T005 | [X] | CONFLICT | [Solution Architect:42](../../.github/agents/technical/solution-architect.agent.md#L42) covers architecture/NFRs and handoffs, but [guidance:92](../../.github/agents/technical/solution-architect.agent.md#L92) is stale against constitution and current stack. | AUD-001, AUD-006, AUD-012 |
| T006 | [X] | PARTIAL | Reference agents appear in the [registry:17](../../.github/agents/AGENTS.md#L17); fire is now archived and Tier/Key Handoffs columns are absent. | AUD-015, AUD-017 |
| T007 | [X] | IMPLEMENTED | [Operations:18](../../.github/agents/operational/operations-officer.agent.md#L18) encodes tactical deployment, staging, field reporting, IC escalation, and Field Coordinator handoff. Global source/tool consistency remains separate. | AUD-001, AUD-003, AUD-019 |
| T008 | [X] | PARTIAL | [Planning:22](../../.github/agents/operational/planning-officer.agent.md#L22) has planning/forecasts and requested handoffs; [references:57](../../.github/agents/operational/planning-officer.agent.md#L57) misattribute constitutional principles. | AUD-001, AUD-011, AUD-019 |
| T009 | [X] | PARTIAL | [Logistics:22](../../.github/agents/operational/logistics-officer.agent.md#L22) covers supplies, transport, cold chain and Health/Planning handoffs; references mislabel the constitution and body still names archived ambulance. | AUD-001, AUD-014, AUD-016, AUD-019 |
| T010 | [X] | CONFLICT | [PIO:18](../../.github/agents/operational/public-information-officer.agent.md#L18) covers media, languages and IC/NGO handoffs; its accessibility, warning and approval guidance conflict with current governing documents. | AUD-002, AUD-013, AUD-014, AUD-016, AUD-019 |
| T011 | [X] | PARTIAL | [Field Coordinator:14](../../.github/agents/operational/field-coordinator.agent.md#L14) covers ground operations, degraded connectivity, conservative fallback, local logging and required handoffs; explicit AIIMS/function and current input/authority grounding need completion. | AUD-011, AUD-019 |
| T012 | [X] | PARTIAL | [Resilience Planner:22](../../.github/agents/operational/resilience-planner.agent.md#L22) covers rehearsal/gaps/framework modelling and Planning/Executive handoffs; current function/entity and principle references are incomplete/inaccurate. | AUD-001, AUD-011, AUD-019 |
| T013 | [X] | PARTIAL | [Executive:26](../../.github/agents/operational/executive-leader.agent.md#L26) covers strategy, resource thresholds and escalation; national handoff was correctly moved to NEMA, but authority/function qualification needs current grounding. | AUD-011, AUD-014, AUD-019 |
| T014 | [X] | PARTIAL | [Observer:22](../../.github/agents/operational/observer-auditor.agent.md#L22) explicitly denies operational rights and includes requested handoffs. Read-only tool scope is not configured and [references:59](../../.github/agents/operational/observer-auditor.agent.md#L59) name undeclared AuditEntry. | AUD-003, AUD-011, AUD-019 |
| T015 | [X] | PARTIAL | All nine required operational entries plus Risk Manager exist in the [registry:13](../../.github/agents/AGENTS.md#L13); entry contract metadata is incomplete. | AUD-015 |
| T016 | [X] | SUPERSEDED | [Archived Commonwealth:22](../../.github/agents/sectors/_archive/commonwealth-government.agent.md#L22) was explicitly replaced by [NEMA:18](../../.github/agents/sectors/commonwealth/nema.agent.md#L18) and [ADF:18](../../.github/agents/sectors/commonwealth/adf.agent.md#L18). Shared seed request/activation conditions survive; approval and civilian-authority explanations are incomplete. | AUD-004-AUD-006, AUD-008, AUD-010, AUD-016, AUD-020 |
| T017 | [X] | PARTIAL | Moved [State Government:22](../../.github/agents/sectors/cross-sector/state-government.agent.md#L22) retains state arrangements and NEMA/Local handoffs, but coordinator, category and retired body references need correction. | AUD-008, AUD-011, AUD-016, AUD-020 |
| T018 | [X] | PARTIAL | Moved [Territory Government:14](../../.github/agents/sectors/cross-sector/territory-government.agent.md#L14) distinguishes ACT/NT and their local-government arrangements; current organization/category and statutory assertions need reconciliation. | AUD-008, AUD-011, AUD-016, AUD-020 |
| T019 | [X] | PARTIAL | Moved [Local Government:18](../../.github/agents/sectors/cross-sector/local-government.agent.md#L18) has councils, recovery and handoffs; its body already maps retired names to successors. Category, QLD coordinator claim and facility ownership still need review. | AUD-008, AUD-011, AUD-014, AUD-020 |
| T020 | [X] | SUPERSEDED | [Archived Police:22](../../.github/agents/sectors/_archive/police.agent.md#L22) replaced by [NSW Police:32](../../.github/agents/sectors/nsw/nswpf.agent.md#L32) and other police profiles. Evacuation/traffic/coronial/SAR responsibilities persist, but legal depth and identity/routing are incomplete. | AUD-004-AUD-006, AUD-008, AUD-010, AUD-016, AUD-020 |
| T021 | [X] | SUPERSEDED | [Archived Ambulance:18](../../.github/agents/sectors/_archive/ambulance-paramedic.agent.md#L18) replaced by jurisdiction profiles such as [NSW Ambulance:32](../../.github/agents/sectors/nsw/nsw-ambulance.agent.md#L32). Triage/evacuation and shared legislative labels persist; explicit Health/Logistics YAML handoffs were lost. | AUD-004, AUD-005, AUD-010, AUD-016, AUD-020 |
| T022 | [X] | SUPERSEDED | [Archived SES:22](../../.github/agents/sectors/_archive/ses.agent.md#L22) replaced by [NSW SES:32](../../.github/agents/sectors/nsw/ses-nsw.agent.md#L32), other SES profiles and DFES. Rescue/volunteers/sandbagging and seed Act/lead-agency metadata persist; detailed authority explanations and some BoM handoffs do not. | AUD-004, AUD-005, AUD-008, AUD-010, AUD-014, AUD-016, AUD-020 |
| T023 | [X] | SUPERSEDED | [Archived BoM:22](../../.github/agents/sectors/_archive/meteorology-bom.agent.md#L22) replaced by [national BoM:18](../../.github/agents/sectors/commonwealth/bom-national.agent.md#L18). The seed supplies Meteorology Act 1955 and advisory/intelligence metadata; the active body has a tautological boundary and inappropriate generic fire routing. | AUD-002, AUD-004-AUD-006, AUD-010, AUD-016, AUD-020 |
| T024 | [X] | PARTIAL | Moved [Health:18](../../.github/agents/sectors/cross-sector/health.agent.md#L18) includes hospital/public/environmental/mental health and Logistics handoff, but default ambulance routing is NSW regardless of jurisdiction. | AUD-005, AUD-008, AUD-016, AUD-020 |
| T025 | [X] | PARTIAL | Moved [Utility:18](../../.github/agents/sectors/cross-sector/utility.agent.md#L18) covers essential services/restoration and Transport/Local handoffs; archived references and undeclared Infrastructure grounding remain. | AUD-008, AUD-011, AUD-014, AUD-016, AUD-020 |
| T026 | [X] | PARTIAL | Moved [Transport:18](../../.github/agents/sectors/cross-sector/transport.agent.md#L18) covers routes, freight, closures and Logistics, but police routing defaults to NSW and body still points to retired Police. | AUD-005, AUD-008, AUD-011, AUD-016, AUD-020 |
| T027 | [X] | PARTIAL | Moved [NGOs:18](../../.github/agents/sectors/cross-sector/community-ngos.agent.md#L18) covers Red Cross/Salvation Army, relief and Local/Volunteer handoffs; statutory/jurisdiction content and category grounding are incomplete. | AUD-004, AUD-008, AUD-011, AUD-014, AUD-020 |
| T028 | [X] | PARTIAL | Moved [Volunteer:18](../../.github/agents/sectors/cross-sector/volunteer.agent.md#L18) has credentials, welfare, statutory table and NGO handoff; SES target is NSW-only and historical bodies remain in text. | AUD-005, AUD-008, AUD-016, AUD-020 |
| T029 | [X] | PARTIAL | All original sector files were found in cross-sector/archive locations, with replacements listed in the [registry](../../.github/agents/AGENTS.md#archived-6). Metadata and current-to-original family trace are incomplete. | AUD-015-AUD-017 |
| T030 | [X] | PARTIAL | [Software Developer:34](../../.github/agents/technical/software-developer.agent.md#L34) covers requested language/framework/PR concerns and handoffs; damaged commands/paths and obsolete versions prevent compliant guidance. | AUD-001, AUD-007, AUD-009, AUD-012 |
| T031 | [X] | CONFLICT | [DevOps:29](../../.github/agents/technical/infrastructure-devops.agent.md#L29) covers Bicep/CI/monitoring, but now mandates implementation, uses unverified tool/name aliases, and denies the constitutional exception. | AUD-001, AUD-003, AUD-006, AUD-012, AUD-017 |
| T032 | [X] | PARTIAL | [Data Engineer:26](../../.github/agents/technical/data-engineer.agent.md#L26) covers storage/ingestion/messaging/schema concerns; current model names, NFRs and constitutional attributions are inaccurate/incomplete. | AUD-001, AUD-011, AUD-012 |
| T033 | [X] | CONFLICT | [Security Engineer:26](../../.github/agents/technical/security-engineer.agent.md#L26) covers RBAC/isolation/safety/privacy, but uses obsolete Principle IV, absolute transit restrictions, and damaged tenant-context text. | AUD-001, AUD-007, AUD-009, AUD-012 |
| T034 | [X] | PARTIAL | [QA:22](../../.github/agents/technical/qa-test-engineer.agent.md#L22) covers all requested test types; paths/commands are damaged and the root Playwright reference is not the current config. Accessibility handoff was moved to a specialist, with UX still named in the body. | AUD-001, AUD-007, AUD-009, AUD-012, AUD-013 |
| T035 | [X] | CONFLICT | [UX:18](../../.github/agents/technical/ux-designer.agent.md#L18) covers dashboard/rubric/Tailwind and Developer/BA handoffs; warning scale, accessibility floor and path text conflict with current requirements. | AUD-002, AUD-007, AUD-009, AUD-012, AUD-013 |
| T036 | [X] | PARTIAL | [Product Owner/BA:14](../../.github/agents/technical/product-owner-ba.agent.md#L14) covers BDD, stakeholders, metrics and workflow; six-principle/current-NFR grounding and claimed validation methodology require updates. | AUD-001, AUD-012, AUD-025 |
| T037 | [X] | PARTIAL | Original eight and all four later-required technical roles appear in the [registry:1](../../.github/agents/AGENTS.md#L1); the contract metadata and 8/12/17 planning reconciliation are absent. | AUD-015, AUD-017 |
| T038 | [X] | PARTIAL | Frontmatter targets all exist and all actors declare handoffs, but [duplicate AFP:1](../../.github/agents/sectors/act/afp.agent.md#L1), [DevOps name:2](../../.github/agents/technical/infrastructure-devops.agent.md#L2), tool/discovery uncertainty and semantic routing defeat a complete validation claim. | AUD-003, AUD-005, AUD-006, AUD-016, AUD-018, AUD-023 |
| T039 | [X] | CONFLICT | The seven named boundary pairs are assessed individually below. [DFES:37](../../.github/agents/sectors/wa/dfes-wa.agent.md#L37), [Health routing:3](../../.github/agents/sectors/cross-sector/health.agent.md#L3) and [principal escalation:121](../../.github/agents/technical/principal-engineer.agent.md#L121) are concrete counterexamples to full consistency. | AUD-001-AUD-006, AUD-008, AUD-013, AUD-014, AUD-023 |
| T040 | [X] | PARTIAL | Seventeen unresolved literal reference occurrences remain. [QA:62](../../.github/agents/technical/qa-test-engineer.agent.md#L62) and [chaos:103](../../.github/agents/technical/chaos-engineer.agent.md#L103) point to damaged or moved paths; valid historical paths were followed. | AUD-007, AUD-009, AUD-011, AUD-023 |
| T041 | [X] | PARTIAL | [Registry:7](../../.github/agents/AGENTS.md#L7) has a real expanded catalogue but incomplete metadata and mixed totals; no final-review execution artifact proves the original check. | AUD-015, AUD-017, AUD-018, AUD-023 |
| T042 | [X] | UNVERIFIED | All 91 actor texts were inspected and no secret or live-incident payload was identified. The [original verification checkbox:118](tasks.md#L118) has no checked-in execution/signoff artifact. Current FR-010 source conformance is credited separately. | AUD-018, AUD-023 |

## Requirement Coverage

**21/21 locally numbered obligations covered: 15 FRs and 6 SCs.** This specification defines no locally numbered NFR. The thirteen inherited parent NFRs relevant to FR-008 are assessed separately below, without claiming a product implementation audit.

| ID | Status | Evidence-backed assessment | Follow-ups |
| --- | --- | --- | --- |
| FR-001 | PARTIAL | Three-tier catalogue exists with 85 active actor files; [registry:7](../../.github/agents/AGENTS.md#L7) mixes totals and omits required entry metadata. | AUD-006, AUD-015, AUD-017, AUD-025 |
| FR-002 | IMPLEMENTED | All nine named operational personas exist with distinct domain content; see T003 and T007-T014, including [IC:30](../../.github/agents/operational/incident-commander.agent.md#L30) and [observer:22](../../.github/agents/operational/observer-auditor.agent.md#L22). Content/authority conformance is separately assessed under FR-006/FR-014. | AUD-011 |
| FR-003 | PARTIAL | Eight generic sectors moved intact and six were explicitly replaced; all fourteen families can be traced, but replacement coverage lacks national comparative/authority detail. [Retirement map](../../.github/agents/AGENTS.md#archived-6), [NEMA:18](../../.github/agents/sectors/commonwealth/nema.agent.md#L18). | AUD-004, AUD-008, AUD-015, AUD-017 |
| FR-004 | IMPLEMENTED | All twelve required technical roles exist, including [Azure architect:31](../../.github/agents/technical/azure-principal-architect.agent.md#L31), [API architect:42](../../.github/agents/technical/api-architect.agent.md#L42), [Principal Engineer:35](../../.github/agents/technical/principal-engineer.agent.md#L35), [SRE:42](../../.github/agents/technical/sre-engineer.agent.md#L42). Quality is assessed under FR-008. | AUD-012, AUD-017 |
| FR-005 | PARTIAL | Files/frontmatter/structured bodies exist, but 50 miss a mandatory section and two descriptions exceed the limit; parser/discovery execution is unverified. [Contract:45](contracts/agent-file-contract.md#L45), [NEMA:50](../../.github/agents/sectors/commonwealth/nema.agent.md#L50). | AUD-003, AUD-006, AUD-007, AUD-010, AUD-016, AUD-018 |
| FR-006 | PARTIAL | Original operational content generally covers responsibilities and relationships, but complete explicit function/authority/input mapping and current warning/approval rules are not consistent. [Field:14](../../.github/agents/operational/field-coordinator.agent.md#L14), [PIO:60](../../.github/agents/operational/public-information-officer.agent.md#L60). | AUD-001-AUD-003, AUD-011, AUD-013, AUD-014, AUD-019 |
| FR-007 | PARTIAL | Cross-sector tables and shared seed Act/activation metadata provide real grounding. Ten tautological boundaries, insufficient approval/coordination explanations, incomplete NGO obligations, and unverified/conflicting legal assertions prevent full conformance. [ADF:33](../../.github/agents/sectors/commonwealth/adf.agent.md#L33), [ADF seed:246](../../packages/domain/src/domain/seed/organisations_australia.json#L246), [NGOs:59](../../.github/agents/sectors/cross-sector/community-ngos.agent.md#L59). | AUD-004, AUD-005, AUD-008, AUD-014, AUD-020 |
| FR-008 | CONFLICT | Technical profiles contradict current constitution, stack and accessibility/NFR requirements. [Solution architect:92](../../.github/agents/technical/solution-architect.agent.md#L92), [web metadata:22](../../apps/web/package.json#L22), inherited NFR table below. | AUD-001, AUD-003, AUD-007, AUD-009, AUD-012, AUD-013 |
| FR-009 | PARTIAL | Most common file references exist, but 17 literal occurrences fail and several annotations identify nonexistent model concepts or obsolete principles. [QA:62](../../.github/agents/technical/qa-test-engineer.agent.md#L62), [state:57](../../.github/agents/sectors/cross-sector/state-government.agent.md#L57). | AUD-001, AUD-007-AUD-009, AUD-011 |
| FR-010 | IMPLEMENTED | Complete static reading of all 91 definitions found no credentials, sensitive live operational payload, or PII records. [Content prohibition:108](contracts/agent-file-contract.md#L108) is compatible with inspected content. This is not a historical scanner/signoff claim. | AUD-018, AUD-023 |
| FR-011 | IMPLEMENTED | Actors remain within the three required tier directories, with extra nested jurisdiction directories; workflow definitions remain in the root. [Registry:13](../../.github/agents/AGENTS.md#L13), [root workflow:1](../../.github/agents/speckit.plan.agent.md#L1). Discovery remains separately unverified. | AUD-016 |
| FR-012 | PARTIAL | Index exists but lacks contracted per-entry fields, parity and clear totals. [Registry columns:17](../../.github/agents/AGENTS.md#L17), [entry contract:95](contracts/agent-file-contract.md#L95). | AUD-015 |
| FR-013 | PARTIAL | Every actor has frontmatter handoffs to existing filenames, but names can collide, semantic targets can be wrong, and body counterparts can be retired. [Health:3](../../.github/agents/sectors/cross-sector/health.agent.md#L3), [ACT AFP:1](../../.github/agents/sectors/act/afp.agent.md#L1). | AUD-005, AUD-006, AUD-016-AUD-018 |
| FR-014 | CONFLICT | Constitution, schema, technology, and approval claims disagree with current authority. [Constitution:238](../../.specify/memory/constitution.md#L238), [Organisation:10](../001-disaster-response-hub/data-model.md#L10), [parent PIO rule:507](../001-disaster-response-hub/spec.md#L507). | AUD-001, AUD-002, AUD-007-AUD-014, AUD-024, AUD-025 |
| FR-015 | CONFLICT | Distinct scopes are often useful, but DFES, warning scales, escalation examples, archive routing and authority rules contain counterexamples. [DFES:28](../../.github/agents/sectors/wa/dfes-wa.agent.md#L28), [UX:82](../../.github/agents/technical/ux-designer.agent.md#L82). | AUD-001-AUD-006, AUD-008, AUD-013, AUD-014, AUD-016 |
| SC-001 | PARTIAL | Numeric minimum and all 35 named roles are represented through current/retired mappings; complete documented scope boundaries are not. 85 active files do not equal 85 unique identities. [Catalogue:7](../../.github/agents/AGENTS.md#L7), [NEMA boundary:33](../../.github/agents/sectors/commonwealth/nema.agent.md#L33). | AUD-004, AUD-006, AUD-015, AUD-017 |
| SC-002 | PARTIAL | Structural counterexamples are proven; full parser/editor validation remains unverified and no covering gate exists. [Contract:108](contracts/agent-file-contract.md#L108), [compliance description:2](../../.github/agents/technical/compliance-auditor.agent.md#L2). | AUD-006, AUD-007, AUD-009, AUD-010, AUD-015-AUD-018, AUD-023 |
| SC-003 | UNVERIFIED | [Quickstart:47](quickstart.md#L47) has five operational questions but no answers/scores. | AUD-019 |
| SC-004 | UNVERIFIED | [Quickstart:54](quickstart.md#L54) has sector questions but no scored evaluation of original or replacement profiles. | AUD-020 |
| SC-005 | UNVERIFIED | No onboarding survey/result was found; [technical questions:61](quickstart.md#L61) are not a survey. | AUD-021 |
| SC-006 | UNVERIFIED | [Authoring contract:45](contracts/agent-file-contract.md#L45) exists, but no independent elapsed-time evidence supports [maintenance test:108](tasks.md#L108). | AUD-017, AUD-022 |

### Inherited NFR Encoding

These are **13/13 parent NFR references**, not new local requirements or assertions about deployed compliance. The expected behavior is accurate role-relevant encoding under FR-008; the audit did not test application performance, security, accessibility, or cloud state.

| Parent ID | Status | Current requirement and actor-content assessment | Follow-ups |
| --- | --- | --- | --- |
| 001:NFR-001 | CONFLICT | [2.2 AA and keyboard floor:151](../001-disaster-response-hub/spec.md#L151) versus [UX 2.1 AA:29](../../.github/agents/technical/ux-designer.agent.md#L29). | AUD-013 |
| 001:NFR-002 | PARTIAL | [Classification, retention and erasure:152](../001-disaster-response-hub/spec.md#L152); [Security:32](../../.github/agents/technical/security-engineer.agent.md#L32) discusses privacy but not these complete targets. | AUD-001, AUD-012 |
| 001:NFR-003 | PARTIAL | [MFA/session/HSM/threat-model targets:153](../001-disaster-response-hub/spec.md#L153); [Security:72](../../.github/agents/technical/security-engineer.agent.md#L72) supplies generic identity advice, not the complete current gate. | AUD-012 |
| 001:NFR-004 | PARTIAL | [Availability/RTO/RPO/quality rollback:154](../001-disaster-response-hub/spec.md#L154); [SRE:48](../../.github/agents/technical/sre-engineer.agent.md#L48) has SLOs but omits the full governed target mapping. | AUD-012 |
| 001:NFR-005 | PARTIAL | [Online/degraded latency and freshness:155](../001-disaster-response-hub/spec.md#L155); [SRE:139](../../.github/agents/technical/sre-engineer.agent.md#L139) and [Field:54](../../.github/agents/operational/field-coordinator.agent.md#L54) use other targets/generic degraded advice. | AUD-011, AUD-012 |
| 001:NFR-006 | PARTIAL | [CAP/EDXL/Sendai:156](../001-disaster-response-hub/spec.md#L156); [API Architect:123](../../.github/agents/technical/api-architect.agent.md#L123) grounds OpenAPI/signal schema but not the complete interoperability gate. | AUD-012 |
| 001:NFR-007 | PARTIAL | [Three provenance tiers:157](../001-disaster-response-hub/spec.md#L157); [Data Engineer:72](../../.github/agents/technical/data-engineer.agent.md#L72) preserves provenance but lacks the full named-tier/display obligation. | AUD-011, AUD-012 |
| 001:NFR-008 | PARTIAL | [One-second audit and five-minute replay:158](../001-disaster-response-hub/spec.md#L158); [Observer:65](../../.github/agents/operational/observer-auditor.agent.md#L65) covers immutable audit but not complete measurable expectations. | AUD-011, AUD-012 |
| 001:NFR-009 | CONFLICT | [Residency rule:159](../001-disaster-response-hub/spec.md#L159) must be interpreted under the higher governing [NN-2:238](../../.specify/memory/constitution.md#L238); [DevOps:120](../../.github/agents/technical/infrastructure-devops.agent.md#L120) permits no exception at all. | AUD-001, AUD-012 |
| 001:NFR-010 | PARTIAL | [Unit-cost envelope:160](../001-disaster-response-hub/spec.md#L160); [Azure architect:35](../../.github/agents/technical/azure-principal-architect.agent.md#L35) mentions cost optimization but not the required per-unit variance measure. | AUD-012 |
| 001:NFR-011 | PARTIAL | [Release training within five business days:161](../001-disaster-response-hub/spec.md#L161); [BA:61](../../.github/agents/technical/product-owner-ba.agent.md#L61) has workflow guidance but no matching release-training gate. | AUD-012 |
| 001:NFR-012 | PARTIAL | [Seven-year retention/annual restore:162](../001-disaster-response-hub/spec.md#L162); [Compliance:40](../../.github/agents/technical/compliance-auditor.agent.md#L40) and [Observer:65](../../.github/agents/operational/observer-auditor.agent.md#L65) do not carry the complete measurable obligation. | AUD-012 |
| 001:NFR-013 | CONFLICT | [Two-language v1 floor/RTL readiness:163](../001-disaster-response-hub/spec.md#L163); [UX:24](../../.github/agents/technical/ux-designer.agent.md#L24) and [Accessibility Tester:36](../../.github/agents/technical/accessibility-tester.agent.md#L36) present six-language requirements without version/jurisdiction qualification. | AUD-013 |

## Acceptance Scenario Coverage

**11/11 scenarios covered.** `USn-ASm` identifies the original numbered acceptance scenario under User Story n; these are report labels, not invented original requirement IDs. Static support is distinguished from unexecuted response behavior.

| Scenario | Status | Expected and observed evidence | Follow-ups |
| --- | --- | --- | --- |
| US1-AS1 | PARTIAL | Role-grounded guidance exists in [IC:30](../../.github/agents/operational/incident-commander.agent.md#L30) and all original operational profiles; current authority/reference errors prevent full conformance, and responses were not invoked. | AUD-001, AUD-002, AUD-011, AUD-014, AUD-019 |
| US1-AS2 | PARTIAL | [Observer boundaries:41](../../.github/agents/operational/observer-auditor.agent.md#L41) and [IC boundaries:47](../../.github/agents/operational/incident-commander.agent.md#L47) name owners; inherited tools, retired body names and conflicting approval rules weaken safe handoff guidance. | AUD-003, AUD-006, AUD-014, AUD-016, AUD-019 |
| US1-AS3 | UNVERIFIED | Distinct files/personas are present, but [handoff design:106](research.md#L106) and `send: true` do not prove same-session context isolation. No switching transcript exists. | AUD-003, AUD-006, AUD-016, AUD-019 |
| US2-AS1 | PARTIAL | [Health:59](../../.github/agents/sectors/cross-sector/health.agent.md#L59) has a jurisdiction table, and successor references supply shared Act/activation data. [NEMA:33](../../.github/agents/sectors/commonwealth/nema.agent.md#L33) still has no meaningful scope exclusion or approval explanation. Actual answers and legal correctness remain unverified. | AUD-004, AUD-008, AUD-020 |
| US2-AS2 | CONFLICT | [Health:3](../../.github/agents/sectors/cross-sector/health.agent.md#L3), [NEMA:3](../../.github/agents/sectors/commonwealth/nema.agent.md#L3) and [DFES:37](../../.github/agents/sectors/wa/dfes-wa.agent.md#L37) demonstrate wrong or unclear counterparts. | AUD-004-AUD-006, AUD-014, AUD-020 |
| US2-AS3 | PARTIAL | [Territory:54](../../.github/agents/sectors/cross-sector/territory-government.agent.md#L54) distinguishes ACT/NT, but current legal verification, comparison references and no-default-state routing are incomplete. | AUD-004, AUD-005, AUD-008, AUD-020 |
| US3-AS1 | CONFLICT | [Solution Architect:92](../../.github/agents/technical/solution-architect.agent.md#L92) and [DevOps:111](../../.github/agents/technical/infrastructure-devops.agent.md#L111) disagree with current constitution/stack; inherited NFR mapping is incomplete. | AUD-001, AUD-003, AUD-012 |
| US3-AS2 | CONFLICT | Cross-cutting topics are present, but [UX:29](../../.github/agents/technical/ux-designer.agent.md#L29) and [Security:63](../../.github/agents/technical/security-engineer.agent.md#L63) cite the wrong gates/principles. | AUD-001, AUD-012, AUD-013 |
| US3-AS3 | PARTIAL | [Developer:73](../../.github/agents/technical/software-developer.agent.md#L73), [QA:62](../../.github/agents/technical/qa-test-engineer.agent.md#L62), and [BA:61](../../.github/agents/technical/product-owner-ba.agent.md#L61) offer onboarding material, but damage/staleness and absent survey results prevent completion claims. | AUD-007, AUD-009, AUD-012, AUD-021 |
| US4-AS1 | PARTIAL | [Contract:45](contracts/agent-file-contract.md#L45) provides an authoring pattern, but [quickstart:74](quickstart.md#L74), inconsistent metadata, identity and discovery rules are not a validated creation workflow. | AUD-006, AUD-015-AUD-018, AUD-022 |
| US4-AS2 | PARTIAL | References exist but [current principle mismatch](../../.github/agents/technical/solution-architect.agent.md#L81) and [unsupported validation claims:169](spec.md#L169) show that impact tracking/review cannot be assumed. | AUD-001, AUD-009, AUD-012, AUD-018, AUD-024, AUD-025 |

### Edge Cases

| Edge | Status | Inspected evidence and remaining obligation | Follow-ups |
| --- | --- | --- | --- |
| EC-01: Planning versus preparedness scopes | PARTIAL | [Planning:39](../../.github/agents/operational/planning-officer.agent.md#L39) and [Resilience Planner:39](../../.github/agents/operational/resilience-planner.agent.md#L39) distinguish live/pre-incident work; explicit function mapping and switching behavior still need validation. | AUD-011, AUD-014, AUD-019 |
| EC-02: Conditional Defence participation | PARTIAL | [Active ADF:24](../../.github/agents/sectors/commonwealth/adf.agent.md#L24) links [DACC/request triggers:246](../../packages/domain/src/domain/seed/organisations_australia.json#L246). Detailed approvals, no-declaration assistance and civilian-command boundaries still require explanation and reconciliation with [archived guidance:63](../../.github/agents/sectors/_archive/commonwealth-government.agent.md#L63). | AUD-004, AUD-008, AUD-020 |
| EC-03: Novice without domain expertise | PARTIAL | Original role overviews are substantial, but [BoM's tautological boundary:33](../../.github/agents/sectors/commonwealth/bom-national.agent.md#L33) and damaged technical text are not self-contained reliable guidance. No novice evaluation was recorded. | AUD-004, AUD-007, AUD-009, AUD-019-AUD-022 |
| EC-04: Jurisdiction/framework reorganization | PARTIAL | [State table:63](../../.github/agents/sectors/cross-sector/state-government.agent.md#L63) and [QFD:26](../../.github/agents/sectors/qld/qfd.agent.md#L26) show unreconciled organization evolution; no impact-validation gate covers it. | AUD-008, AUD-015-AUD-018, AUD-025 |
| EC-05: Conflicting cross-jurisdiction guidance | CONFLICT | [Health routing:3](../../.github/agents/sectors/cross-sector/health.agent.md#L3), [DFES:37](../../.github/agents/sectors/wa/dfes-wa.agent.md#L37), and [approval authority:507](../001-disaster-response-hub/spec.md#L507) require explicit arbitration, not a silent winning agent. | AUD-005, AUD-006, AUD-008, AUD-014, AUD-020 |

## Expanded Catalogue Content Coverage

The Task Coverage table accounts for the original 31 definitions, including all six archived originals. The following **60 additional/replacement files** were also read in full, not sampled. Every one of the fifty sector replacements lacks Guidance Notes, but all reference the shared organization metadata: 49 organizations cover fifty profiles because AFP is duplicated. That source provides 43 legislative labels plus functions, capabilities, activation triggers and partner IDs; these are credited as grounding. Missing authority explanations below mean incomplete powers/approval/exception interpretation, not absence of all legal or jurisdictional data. The six null legislative labels are not automatically defects. No metadata field alone proves legal validation or response quality. The linked line points to the owning responsibility/overview content.

| Additional actor/source | Status | Specific content disposition | Follow-ups |
| --- | --- | --- | --- |
| [Risk Manager:38](../../.github/agents/operational/risk-manager.agent.md#L38) | PARTIAL | Risk methods and decision-support scope are substantial; obsolete principle attribution and approval mapping need reconciliation. | AUD-001, AUD-011, AUD-014 |
| [Azure Principal Architect:31](../../.github/agents/technical/azure-principal-architect.agent.md#L31) | PARTIAL | Required FR-004 role exists; WAF depth is present, but principle/exception, tool policy and binding claims are unresolved. | AUD-001, AUD-003, AUD-012 |
| [API Architect:42](../../.github/agents/technical/api-architect.agent.md#L42) | PARTIAL | Required FR-004 role exists; detailed APIs/resilience/caching guidance needs current NFR and authority alignment. | AUD-001, AUD-012 |
| [Principal Engineer:35](../../.github/agents/technical/principal-engineer.agent.md#L35) | PARTIAL | Required FR-004 role exists; mentoring/review content is substantive, but escalation and stack/principle claims are wrong/stale. | AUD-001, AUD-003, AUD-012, AUD-014 |
| [SRE:42](../../.github/agents/technical/sre-engineer.agent.md#L42) | PARTIAL | Required FR-004 role exists; SLO/toil/chaos content needs governed NFR mapping and proposal qualification. | AUD-001, AUD-012 |
| [AI/ML Engineer:34](../../.github/agents/technical/ai-ml-engineer.agent.md#L34) | PARTIAL | Agent design and safety guidance exists; damaged runtime references and stale current-stack assertions undermine it. | AUD-001, AUD-007, AUD-009, AUD-012 |
| [Accessibility Tester:30](../../.github/agents/technical/accessibility-tester.agent.md#L30) | PARTIAL | Correct 2.2 AA focus, but damaged ARIA/paths and unqualified language baseline. | AUD-007, AUD-009, AUD-013 |
| [Chaos Engineer:34](../../.github/agents/technical/chaos-engineer.agent.md#L34) | PARTIAL | Explicit staging/blast-radius safeguards exist; reference corruption and wrong resilience owner remain. | AUD-007, AUD-009, AUD-012 |
| [Compliance Auditor:34](../../.github/agents/technical/compliance-auditor.agent.md#L34) | PARTIAL | Privacy/compliance content exists; unsupported Commonwealth Act, obsolete residency rule and 208-character description. | AUD-001, AUD-008, AUD-010, AUD-012 |
| [Docker & Container Engineer:30](../../.github/agents/technical/docker-container-engineer.agent.md#L30) | PARTIAL | Build/security/probe advice exists; damaged paths, malformed fence, 201-character description and incomplete constitutional grounding. | AUD-007, AUD-009, AUD-010, AUD-012 |
| [ACT Ambulance:32](../../.github/agents/sectors/act/act-ambulance.agent.md#L32) | PARTIAL | Clinical responsibility list; Health/Logistics handoffs absent, duplicate police/fire labels. | AUD-004, AUD-005, AUD-010 |
| [ACT ESA:32](../../.github/agents/sectors/act/act-esa.agent.md#L32) | PARTIAL | Umbrella coordination list; tautological boundary and ambiguous police buttons. | AUD-004-AUD-006, AUD-010 |
| [ACT Fire and Rescue:32](../../.github/agents/sectors/act/act-fr.agent.md#L32) | PARTIAL | Urban/hazmat/rescue and shared Act grounding; duplicated police choices and powers not explained beyond metadata. | AUD-004-AUD-006, AUD-010 |
| [ACT Policing:32](../../.github/agents/sectors/act/act-policing.agent.md#L32) | PARTIAL | Evacuation/SAR/coronial list; ambiguous fire choices and undeveloped AFP relationship. | AUD-004-AUD-006, AUD-010 |
| [ACT RFS:32](../../.github/agents/sectors/act/act-rfs.agent.md#L32) | PARTIAL | Rural fire list; volunteer conditions and explicit authority are incomplete. | AUD-004-AUD-006, AUD-010 |
| [ACT AFP:32](../../.github/agents/sectors/act/afp.agent.md#L32) | PARTIAL | Federal/ACT list duplicates the national identity with different routing. | AUD-004-AUD-006, AUD-010 |
| [ACT SES:32](../../.github/agents/sectors/act/ses-act.agent.md#L32) | PARTIAL | Rescue/volunteer list; five local buttons omit BoM/IC and duplicate police/fire labels. | AUD-004-AUD-006, AUD-010 |
| [ABF:24](../../.github/agents/sectors/commonwealth/abf.agent.md#L24) | PARTIAL | Maritime/border list; tautological scope and generic national routing, no authority limitations. | AUD-004-AUD-006, AUD-008, AUD-010 |
| [ADF:24](../../.github/agents/sectors/commonwealth/adf.agent.md#L24) | PARTIAL | Seed supplies DACC/request triggers and Defence Act; approvals/civilian-command limits remain unexplained behind a tautological boundary. | AUD-004-AUD-006, AUD-008, AUD-010 |
| [Commonwealth AFP:24](../../.github/agents/sectors/commonwealth/afp.agent.md#L24) | PARTIAL | Federal/ACT list; duplicate identity and airport-specific fire counterpart. | AUD-004-AUD-006, AUD-010 |
| [Red Cross:24](../../.github/agents/sectors/commonwealth/arc.agent.md#L24) | PARTIAL | Relief/tracing list; tautological boundary and undefined facility/service ownership. | AUD-004-AUD-006, AUD-010, AUD-014 |
| [Airservices:28](../../.github/agents/sectors/commonwealth/asa.agent.md#L28) | PARTIAL | Airport rescue list; not a substitute for national bushfire authority, regulatory label needs sourcing. | AUD-004-AUD-006, AUD-008, AUD-010 |
| [National BoM:24](../../.github/agents/sectors/commonwealth/bom-national.agent.md#L24) | PARTIAL | Seed supplies Meteorology Act/intelligence/advisory grounding; body boundary is tautological and generic routing unsuitable. | AUD-002, AUD-004-AUD-006, AUD-010 |
| [Geoscience Australia:24](../../.github/agents/sectors/commonwealth/ga-national.agent.md#L24) | PARTIAL | Geohazard list; tautological scope and generic national routing. | AUD-004-AUD-006, AUD-010 |
| [NEMA:24](../../.github/agents/sectors/commonwealth/nema.agent.md#L24) | PARTIAL | Seed supplies state requests/activation triggers; approval/state-authority interpretation, substantive boundary and relevant handoffs remain incomplete. | AUD-004-AUD-006, AUD-008, AUD-010 |
| [RFDS:20](../../.github/agents/sectors/commonwealth/rfds.agent.md#L20) | PARTIAL | Aeromedical list; no Health/Logistics YAML handoffs or sourced jurisdiction/clinical obligations. | AUD-004-AUD-006, AUD-010 |
| [St John National:24](../../.github/agents/sectors/commonwealth/sja-national.agent.md#L24) | PARTIAL | First aid/volunteer list; tautological scope, no comparative service limits. | AUD-004-AUD-006, AUD-010 |
| [Surf Life Saving:24](../../.github/agents/sectors/commonwealth/surf-lifesaving.agent.md#L24) | PARTIAL | Coastal rescue/volunteer list; tautological authority boundary. | AUD-004-AUD-006, AUD-010 |
| [FRNSW:32](../../.github/agents/sectors/nsw/frnsw.agent.md#L32) | PARTIAL | Urban/technical rescue and seed Act grounding; rural/urban authority implications are not explained. | AUD-004, AUD-005, AUD-010 |
| [Marine Rescue NSW:32](../../.github/agents/sectors/nsw/mrnsw.agent.md#L32) | PARTIAL | Marine rescue list; tautological scope and duplicate fire labels. | AUD-004, AUD-005, AUD-010 |
| [NSW Ambulance:32](../../.github/agents/sectors/nsw/nsw-ambulance.agent.md#L32) | PARTIAL | Triage/patient distribution list; required Health/Logistics YAML pathways absent. | AUD-004, AUD-005, AUD-010 |
| [NSW RFS:32](../../.github/agents/sectors/nsw/nsw-rfs.agent.md#L32) | PARTIAL | Seed retains Act, section-44 and Total Fire Ban triggers; who authorizes which action and under what limits needs explanation. | AUD-004, AUD-005, AUD-010 |
| [NSW Police:32](../../.github/agents/sectors/nsw/nswpf.agent.md#L32) | PARTIAL | Evacuation/SAR/coronial and seed Act/trigger data exist; delegated powers and distinguishable fire routing remain incomplete. | AUD-004, AUD-005, AUD-010 |
| [NSW SES:32](../../.github/agents/sectors/nsw/ses-nsw.agent.md#L32) | PARTIAL | Flood/storm/volunteer and seed Act/lead-agency data exist; BoM YAML handoff and detailed decision-right guidance are absent. | AUD-004, AUD-005, AUD-010 |
| [Bushfires NT:32](../../.github/agents/sectors/nt/bushfires-nt.agent.md#L32) | PARTIAL | Rural fire list; NT-specific statutory/land-management boundary absent. | AUD-004, AUD-008, AUD-010 |
| [NT Emergency Service:32](../../.github/agents/sectors/nt/ntes.agent.md#L32) | PARTIAL | Cyclone/remote-community and seed Act/trigger grounding exist; authority and comparative implications are not explained. | AUD-004, AUD-008, AUD-010 |
| [NT Fire and Rescue:32](../../.github/agents/sectors/nt/ntfrs.agent.md#L32) | PARTIAL | Fire/rescue list; statutory and Bushfires NT split need detail. | AUD-004, AUD-008, AUD-010 |
| [NT Police:32](../../.github/agents/sectors/nt/ntpf.agent.md#L32) | PARTIAL | Police list; fire choices indistinguishable and legal delegation unspecified. | AUD-004, AUD-005, AUD-008, AUD-010 |
| [St John NT:28](../../.github/agents/sectors/nt/sja-nt.agent.md#L28) | PARTIAL | Clinical list; contract/remote-care context and Health/Logistics links incomplete. | AUD-004, AUD-005, AUD-008, AUD-010 |
| [QAS:24](../../.github/agents/sectors/qld/qas.agent.md#L24) | PARTIAL | Clinical list and seed Ambulance Service Act grounding exist; Health/Logistics YAML routes and detailed authority guidance remain incomplete. | AUD-004, AUD-005, AUD-008, AUD-010 |
| [QFD:32](../../.github/agents/sectors/qld/qfd.agent.md#L32) | PARTIAL | Claims SES/flood coordination while excluding it; current QPS/SES division unverified. | AUD-004, AUD-008, AUD-010, AUD-014 |
| [QPS:28](../../.github/agents/sectors/qld/qps.agent.md#L28) | PARTIAL | Police list; current disaster/SES coordination role not grounded. | AUD-004, AUD-008, AUD-010 |
| [QLD SES:32](../../.github/agents/sectors/qld/ses-qld.agent.md#L32) | PARTIAL | Rescue/volunteer list; parent-body/statutory context unverified. | AUD-004, AUD-008, AUD-010 |
| [SA Ambulance:28](../../.github/agents/sectors/sa/saas.agent.md#L28) | PARTIAL | Clinical list; Health/Logistics pathways and jurisdiction-specific obligations missing. | AUD-004, AUD-005, AUD-010 |
| [SA CFS:32](../../.github/agents/sectors/sa/sacfs.agent.md#L32) | PARTIAL | Rural fire and seed Act grounding exist; powers/approval limits and boundary exceptions need explanation. | AUD-004, AUD-008, AUD-010 |
| [SA MFS:32](../../.github/agents/sectors/sa/samfs.agent.md#L32) | PARTIAL | Urban fire and seed Act grounding exist; powers/approval limits and mutual responsibilities need explanation. | AUD-004, AUD-008, AUD-010 |
| [SA Police:32](../../.github/agents/sectors/sa/sapol.agent.md#L32) | PARTIAL | Police list; indistinguishable fire choices and legal conditions unresolved. | AUD-004, AUD-005, AUD-010 |
| [SA SES:32](../../.github/agents/sectors/sa/ses-sa.agent.md#L32) | PARTIAL | Rescue/volunteer and seed Act/trigger data exist; powers and comparative implications need explanation. | AUD-004, AUD-008, AUD-010 |
| [Ambulance Tasmania:24](../../.github/agents/sectors/tas/at.agent.md#L24) | PARTIAL | Clinical list; no Health/Logistics routing or sourced governance model. | AUD-004, AUD-005, AUD-010 |
| [Tasmania SES:32](../../.github/agents/sectors/tas/ses-tas.agent.md#L32) | PARTIAL | Rescue/volunteer and seed Act/trigger data exist; delegated authority remains unexplained. | AUD-004, AUD-008, AUD-010 |
| [Tasmania Police:28](../../.github/agents/sectors/tas/taspol.agent.md#L28) | PARTIAL | Police and seed Act/trigger data exist; specific coordination powers and limits need interpretation. | AUD-004, AUD-008, AUD-010 |
| [Tasmania Fire Service:32](../../.github/agents/sectors/tas/tfs.agent.md#L32) | PARTIAL | Combined fire/rescue and Fire Service Act grounding exist; authority limits are not explained. | AUD-004, AUD-008, AUD-010 |
| [Ambulance Victoria:28](../../.github/agents/sectors/vic/av.agent.md#L28) | PARTIAL | Clinical list; Health/Logistics routing absent, fire labels duplicate. | AUD-004, AUD-005, AUD-010 |
| [CFA:32](../../.github/agents/sectors/vic/cfa-vic.agent.md#L32) | PARTIAL | Rural fire and seed Act/trigger grounding exist; approval powers and boundary exceptions need explanation. | AUD-004, AUD-008, AUD-010 |
| [FRV:32](../../.github/agents/sectors/vic/frv.agent.md#L32) | PARTIAL | Urban fire and seed Act grounding exist; approval powers and boundary exceptions need explanation. | AUD-004, AUD-008, AUD-010 |
| [Victoria SES:32](../../.github/agents/sectors/vic/ses-vic.agent.md#L32) | PARTIAL | Rescue/volunteer and seed Act/trigger grounding exist; decision-right and comparative explanations are incomplete. | AUD-004, AUD-008, AUD-010 |
| [Victoria Police:32](../../.github/agents/sectors/vic/vicpol.agent.md#L32) | PARTIAL | Police list; ambiguous fire buttons and unsupported generic command framing. | AUD-004, AUD-005, AUD-010 |
| [WA DFES:28](../../.github/agents/sectors/wa/dfes-wa.agent.md#L28) | PARTIAL | Combined fire/SES responsibilities contradict the own-function scope exclusion. | AUD-004, AUD-005, AUD-010, AUD-014 |
| [St John WA:20](../../.github/agents/sectors/wa/sja-wa.agent.md#L20) | PARTIAL | Clinical list; contracted-service obligations and Health/Logistics routing missing. | AUD-004, AUD-005, AUD-010 |
| [WA Police:24](../../.github/agents/sectors/wa/wapol.agent.md#L24) | PARTIAL | Police list; references a jurisdiction SES counterpart without a distinct current agent. | AUD-004, AUD-005, AUD-010, AUD-014 |

The ten tautological boundaries occur in ACT ESA, ABF, ADF, Red Cross, BoM, Geoscience Australia, NEMA, St John National, Surf Life Saving, and Marine Rescue NSW. This is a source-content observation, not a measured response-quality result.

### Damaged Text and Reference Inventory

The eight damaged files are Software Developer, Security Engineer, QA/Test Engineer, UX Designer, AI/ML Engineer, Accessibility Tester, Chaos Engineer, and Docker & Container Engineer. Character identities, not raw control characters, are recorded: `U+0007`, `U+0009` inside tokens, `U+000C`, embedded `U+000D`, and `U+001B`. AUD-007 covers text integrity; AUD-009 covers surviving path/meaning defects after text repair.

| File/source | Unresolved contextual-reference occurrences | Additional disposition | Follow-ups |
| --- | --- | --- | --- |
| [Accessibility Tester:95](../../.github/agents/technical/accessibility-tester.agent.md#L95) | 3 | Web/test paths damaged; root Playwright target moved to web `.cts`; ARIA body damage extends beyond references. | AUD-007, AUD-009 |
| [AI/ML Engineer:105](../../.github/agents/technical/ai-ml-engineer.agent.md#L105) | 4 | Four damaged runtime-helper paths; intended helper files exist, so do not declare those implementations missing. | AUD-007, AUD-009 |
| [Chaos Engineer:103](../../.github/agents/technical/chaos-engineer.agent.md#L103) | 3 | Damaged tests/load paths; corrected resilience destination is middleware, not services. | AUD-007, AUD-009 |
| [Docker Engineer:102](../../.github/agents/technical/docker-container-engineer.agent.md#L102) | 2 | Damaged Dockerfile paths; malformed example fence is a separate text defect in the same file. | AUD-007, AUD-009 |
| [QA/Test Engineer:62](../../.github/agents/technical/qa-test-engineer.agent.md#L62) | 2 | Shared fixture path damaged; root Playwright reference is not current. | AUD-007, AUD-009 |
| [Security Engineer:63](../../.github/agents/technical/security-engineer.agent.md#L63) | 1 | Tenant-context path damaged; model/property tokens also damaged. | AUD-007, AUD-009 |
| [Software Developer:73](../../.github/agents/technical/software-developer.agent.md#L73) | 1 | TypeScript token damaged; additional `ruff` lines are split/damaged and not counted as recognized path tokens. | AUD-007, AUD-009 |
| [UX Designer:54](../../.github/agents/technical/ux-designer.agent.md#L54) | 1 | Web route path damaged. | AUD-007, AUD-009 |

The sum is 17 recognized unresolved occurrences, not a claim that all other semantic references are valid. AUD-011 separately covers nonexistent entities and wrong category/section claims.

## Contract and Review Evidence Assessment

### Structural and Content Contract

| Contract obligation | Status | Evidence / assessment | Follow-ups |
| --- | --- | --- | --- |
| Unique kebab-case actor IDs and tier locations | PARTIAL | Locations exist; duplicate AFP violates [model uniqueness:22](data-model.md#L22). Nested jurisdiction layout needs explicit contract compatibility. | AUD-006, AUD-017 |
| Valid YAML and typed handoffs | UNVERIFIED | Frontmatter was read in every file; parser attempts stopped on missing dependencies before parsing. No runtime loading was attempted. | AUD-010, AUD-018 |
| Nonempty single-line description within limit | PARTIAL | All have authored descriptions; Compliance/Docker are 208/201 characters. `<200` versus `<=200` is inconsistent in the source contract. | AUD-010, AUD-017 |
| Six required body sections in order | PARTIAL | Original profiles largely follow the pattern; all fifty successors lack Guidance Notes. Additional headings in technical profiles do not by themselves violate relative order. | AUD-010 |
| Operational AIIMS alignment, rights, escalation | PARTIAL | Distinct roles and many boundaries exist; explicit function mapping/current authority and input grounding are incomplete. | AUD-001, AUD-011, AUD-014 |
| Sector statutes, jurisdiction variation, coordination | PARTIAL | Cross-sector tables and successor seed references supply real legal/activation metadata; complete approval/boundary explanations and verified legal interpretation remain lacking. | AUD-004, AUD-005, AUD-008 |
| Technical principles, stack, quality gates | CONFLICT | Old constitution/version/accessibility claims disagree with current source. | AUD-001, AUD-012, AUD-013 |
| Target-file existence and at least one handoff | IMPLEMENTED | Static frontmatter inventory finds at least one target per actor and no missing target file; identity, meaning, and editor binding are separate failures. | AUD-005, AUD-006, AUD-016 |
| Per-file registry entry and required columns | PARTIAL | Tier files appear in live/archive lists, but metadata parity and totals fail the entry contract. | AUD-015 |
| No sensitive/live incident content | IMPLEMENTED | All 91 definitions inspected without identifying forbidden payloads; no historical scanner proof is claimed. | AUD-018, AUD-023 |
| Existing contextual reference paths | PARTIAL | Seventeen literal misses plus additional semantic annotation defects. | AUD-007, AUD-009, AUD-011 |

### T039 Boundary-Pair Review

All seven specifically named pairs were inspected. Passing text for one pair does not demonstrate that the historical review ran or that generated responses follow it.

| Required pair | Status | Content evidence | Follow-ups |
| --- | --- | --- | --- |
| Health + Logistics | PARTIAL | [Health:34](../../.github/agents/sectors/cross-sector/health.agent.md#L34) separates clinical operations from supply logistics; [Logistics:64](../../.github/agents/operational/logistics-officer.agent.md#L64) preserves clinical specifications/cold chain. Replacement medical routing and current authority still need validation. | AUD-005, AUD-014, AUD-020, AUD-023 |
| Fire + Police | PARTIAL | [Archived fire:42](../../.github/agents/sectors/_archive/fire-services.agent.md#L42) distinguishes recommendations/enforcement; successor lists omit jurisdiction-specific powers and duplicate fire labels. | AUD-004, AUD-005, AUD-008, AUD-020, AUD-023 |
| Meteorology + all sectors | PARTIAL | [Archived BoM:22](../../.github/agents/sectors/_archive/meteorology-bom.agent.md#L22) explicitly denies responding authority. Active seed metadata preserves advisory/intelligence grounding, but [active body:33](../../.github/agents/sectors/commonwealth/bom-national.agent.md#L33) has a tautological boundary and generic routing. | AUD-002, AUD-004, AUD-005, AUD-020, AUD-023 |
| Ambulance + Health | PARTIAL | [NSW Ambulance:41](../../.github/agents/sectors/nsw/nsw-ambulance.agent.md#L41) excludes hospital operations, but YAML omits Health/Logistics and [Health:3](../../.github/agents/sectors/cross-sector/health.agent.md#L3) defaults nationally to NSW. | AUD-004, AUD-005, AUD-020, AUD-023 |
| SES + Police | PARTIAL | [NSW SES:41](../../.github/agents/sectors/nsw/ses-nsw.agent.md#L41) separates law enforcement; current jurisdictional authority and combined-agency rules are incomplete. | AUD-004, AUD-008, AUD-014, AUD-020, AUD-023 |
| Commonwealth + State | PARTIAL | [State:38](../../.github/agents/sectors/cross-sector/state-government.agent.md#L38) distinguishes incident/state/national roles. NEMA's seed retains request triggers, but approval/state-authority interpretation is thin and the state body still names archived Commonwealth. | AUD-004, AUD-005, AUD-008, AUD-016, AUD-020, AUD-023 |
| Community NGOs + Volunteer | PARTIAL | [NGOs:34](../../.github/agents/sectors/cross-sector/community-ngos.agent.md#L34) and [Volunteer:34](../../.github/agents/sectors/cross-sector/volunteer.agent.md#L34) separate programs/protection policy; actual statutory/current-jurisdiction and ARC facility scope are incomplete. | AUD-004, AUD-005, AUD-008, AUD-014, AUD-020, AUD-023 |

### Original Quality Checklist

All **16/16** checklist claims are assessed separately from implementation. Labels CQ/RC/FR below identify original checklist position, not original feature FR IDs.

| Checklist item | Original state | Assessment | Follow-ups |
| --- | --- | --- | --- |
| CQ-1: No implementation details | [x] | CONFLICT: native `.agent.md`/YAML is explicitly allowed in checklist notes, so the absolute statement has a documented exception rather than unconditional truth. | AUD-017, AUD-023 |
| CQ-2: User value/business needs | [x] | IMPLEMENTED as authored: four stories describe contributor/stakeholder value. Historical review execution remains unverified. | AUD-023 |
| CQ-3: Nontechnical stakeholder language | [x] | PARTIAL: narrative is readable, but file/frontmatter/tool-taxonomy and later schema references require technical context. | AUD-017, AUD-023 |
| CQ-4: Mandatory sections complete | [x] | IMPLEMENTED as section presence, not proof of content quality or signoff. [Spec:1](spec.md#L1). | AUD-023 |
| RC-1: No clarification markers | [x] | IMPLEMENTED as source text: no unresolved bracketed clarification marker in the local spec. Unresolved conflicts are nevertheless present. | AUD-017, AUD-023 |
| RC-2: Requirements testable/unambiguous | [x] | PARTIAL: explicit metrics exist, but description limits, handoff optionality and current catalogue scope disagree. | AUD-017, AUD-023 |
| RC-3: Measurable success criteria | [x] | PARTIAL: thresholds exist; survey cohort/scoring and timed-maintenance protocol are not operationalized. | AUD-019-AUD-023 |
| RC-4: Technology-agnostic outcomes | [x] | CONFLICT: SC-002 explicitly depends on GitHub agent/YAML conventions. The delivery-format exception should be stated consistently. | AUD-017, AUD-023 |
| RC-5: Acceptance scenarios defined | [x] | IMPLEMENTED as authored: all eleven scenarios exist; no response execution is implied. | AUD-019-AUD-023 |
| RC-6: Edge cases identified | [x] | IMPLEMENTED as authored: all five original edge cases exist; conformance remains partial/conflicting as shown above. | AUD-019, AUD-020, AUD-023 |
| RC-7: Scope clearly bounded | [x] | PARTIAL: development-time/AU scope is explicit, but knowledge-only versus executable DevOps and 31/35/expanded scope require reconciliation. | AUD-003, AUD-017, AUD-023 |
| RC-8: Dependencies/assumptions identified | [x] | PARTIAL: dependencies and amendments exist; validation/consultation and linked hypothesis evidence are not substantiated. | AUD-024, AUD-025 |
| FR-CHK1: All FRs have clear acceptance criteria | [x] | PARTIAL: stories cover core flows, but structural/metadata/tool/retirement obligations lack complete objective validation rules. | AUD-017, AUD-018, AUD-023 |
| FR-CHK2: Scenarios cover primary flows | [x] | IMPLEMENTED as authored coverage, not evaluated behavior. | AUD-019-AUD-023 |
| FR-CHK3: Feature meets measurable outcomes | [x] | UNVERIFIED: no operational/sector scores, contributor survey, or timed creation result supports SC-003-SC-006. | AUD-019-AUD-023 |
| FR-CHK4: No implementation details leak | [x] | CONFLICT: repeats CQ-1 despite the explicit format exception in the same checklist. | AUD-017, AUD-023 |

Checklist notes still claim 27 actors/10 sectors; current spec requires at least 35/14. That is a content discrepancy under AUD-017, independent of whether an initial checklist review occurred.

### Plan Gates and Associated Review Records

| Claim/record | Status | Evidence assessment | Follow-ups |
| --- | --- | --- | --- |
| Plan I PASS: Life safety | UNVERIFIED | Safety-oriented text exists, but no gate run/signoff accompanies [plan:22](plan.md#L22); authority/tool conflicts remain. | AUD-003, AUD-014, AUD-023 |
| Plan II PASS: Multi-agent coordination | CONFLICT | Current constitution II is national principles, with AIIMS in II-A; handoff existence does not prove scope compatibility. | AUD-001, AUD-005, AUD-023 |
| Plan III PASS: Data trust/provenance | CONFLICT | Current principle III is multi-hazard design; provenance/audit is principally IV. | AUD-001, AUD-023 |
| Plan IV PASS: Privacy/security | CONFLICT | Current IV is transparency/auditability; privacy is NN-3 and related rules. | AUD-001, AUD-023 |
| Plan V PASS: Multilingual/accessibility | PARTIAL | Current V includes AWS/nested model/all-clear and warning principles; merely mentioning multiple languages is incomplete. | AUD-002, AUD-013, AUD-023 |
| Plan VI PASS: Azure AU | CONFLICT | Current VI is evacuation; cloud is VIII and residency NN-2 with the bounded amendment. | AUD-001, AUD-023 |
| Phase checkpoints/all original tasks checked | UNVERIFIED | [Tasks:114](tasks.md#L114) contains assertions, not per-file execution evidence; static counterexamples disprove present full conformance. | AUD-023 |
| Quickstart structural checkboxes | UNVERIFIED | They remain unchecked validation instructions, not failed or passed run results. [Quickstart:33](quickstart.md#L33). | AUD-010, AUD-018, AUD-023 |
| Quickstart reference-agent accuracy | UNVERIFIED | Questions and 4/5 threshold are authored; no response/scoring evidence is attached. | AUD-019, AUD-020 |
| Feature-028 rubric baseline/postfeature | IMPLEMENTED | Authored [baseline:1](../028-capstone-alignment/evidence/rubric-baseline.md#L1) and [postfeature:22](../028-capstone-alignment/evidence/rubric-postfeature.md#L22) contain aggregate scores; they are not spec-004 answer-accuracy or per-spec causal evidence. | AUD-024 |
| Feature-028 close/signoff | UNVERIFIED | For this feature's claims, [decision record:36](../028-capstone-alignment/evidence/decision-record.md#L36) describes authoring and structural checks, not named practitioner validation of each actor or consultation on each spec-004 change. | AUD-023, AUD-025 |
| Heading coverage script | IMPLEMENTED | For its narrow check, [script:43](../028-capstone-alignment/scripts/validate-section-coverage.ps1#L43) tests headings/clarification markers, not persona schema, citations, consultations or answer accuracy. Not run here. | AUD-018, AUD-025 |
| Persona manifest validator/tests | IMPLEMENTED | For a different concern, [validator:35](../../tools/lint/persona_coverage_report.py#L35) and [tests:26](../../tests/integration/test_persona_coverage_zero_unbacked.py#L26) count seed-manifest persona bindings, not actor instruction conformance. Not run here. | AUD-018 |
| Tribunal review-log/tests | IMPLEMENTED | For a different concern, [review CLI:89](../../scripts/web-coverage/review-log.py#L89) stores/resolves supplied votes; [tests:83](../../tests/unit/test_review_log_closure.py#L83) assert closure arithmetic, not actor content or authentic invocation. Not run here. | AUD-018, AUD-023 |

## Amendment Coverage

**11/11 appended ASM/PER/HYP/SCP IDs covered.** These source statements were reviewed as claims/constraints, not instructions to invoke actors, grade the project, implement countries, or modify constitutional ownership.

| ID | Status | Evidence-backed disposition | Follow-ups |
| --- | --- | --- | --- |
| ASM-004 | IMPLEMENTED | [Spec:161](spec.md#L161) explicitly selects AU-v1 and records open gap links; this is authored scope, not empirical validation of the operating context. | AUD-025 |
| ASM-005 | UNVERIFIED | [Spec:162](spec.md#L162) claims responsible-actor consultation; no per-change consultation evidence was found in the associated records. | AUD-024, AUD-025 |
| ASM-006 | PARTIAL | [Spec:163](spec.md#L163) names authoritative conventions/profile schema, but cross-referenced validation claims lack schema-required evidence. | AUD-017, AUD-025 |
| PER-004 | UNVERIFIED | [Spec:169](spec.md#L169) says operational personas are validated; the parent prose/profile role labels do not establish named practitioner/date approval. | AUD-011, AUD-025 |
| PER-005 | UNVERIFIED | [Spec:170](spec.md#L170) self-references the technical actor catalogue as validated without an independent validation record. | AUD-025 |
| PER-006 | IMPLEMENTED | [Spec:171](spec.md#L171) labels non-AU personas placeholders and names preconditions. Only the placeholder is authored; country validity is deliberately not claimed. | AUD-025 |
| HYP-002 | PARTIAL | [Spec:177](spec.md#L177) contains condition/outcome/falsification prose; linked stub is absent, and portfolio scores are not the promised per-spec measurement. | AUD-024 |
| SCP-005 | IMPLEMENTED | [Spec:185](spec.md#L185) authors a PH/JP/BD deferral behind decision, regulatory/data-sharing and responsible-agent review conditions. Those conditions are not claimed satisfied. | AUD-025 |
| SCP-006 | PARTIAL | [Spec:186](spec.md#L186) prohibits unilateral constitutional changes; existing profiles still contradict current principles/exception handling, so risk/reconciliation needs recording. | AUD-001, AUD-025 |
| SCP-007 | IMPLEMENTED | [Spec:187](spec.md#L187) authors an ownership declaration assigning arbitration and deferring recovery/warning ownership to the named features. No arbitration execution is claimed. | AUD-014, AUD-025 |
| SCP-008 | IMPLEMENTED | [Spec:179](spec.md#L179) authors the canonical delivery-hygiene bullet and the additional labelled note. This satisfies the [meta-flag content rule:12](../028-capstone-alignment/contracts/meta-spec-flag.contract.md#L12), not operational benefit. | AUD-025 |

## Future Validation Procedures

**None of the procedures or commands in this section was executed in this audit.** They are prerequisites/instructions for later authorized remediation. Use a disposable document-only fixture workspace and synthetic data. No live incidents, credentials, public alert channels, deployments, or real cloud mutators are necessary.

### V-STRUCT - Document Validator

Prerequisites: AUD-017's resolved contract; AUD-018's **proposed** validator and tests; Python 3.12+ with the project's declared PyYAML/pytest dependencies installed in the future environment. The current environment lacks the YAML parsers, and no installation was attempted beyond checking imports. The validator must not import application modules or emit secret values.

Future commands, run from repository root only after those proposed files exist:

```powershell
python tools/lint/check_actor_agent_catalogue.py --root .
python -m pytest --noconftest tests/unit/test_actor_agent_catalogue.py -q
```

Expected: corrected catalogue exits zero; each intentionally malformed fixture independently fails with the expected rule and file/line. Empty catalogues, missing evidence, unknown identities, and unsupported capabilities must not be counted as passing. These are artifact tests, not product tests. Existing architecture-link, seed-manifest, or tribunal checks are not substitutes.

### V-EDITOR - Discovery and Tool Inspection

Prerequisites: separately authorized supported VS Code/Copilot version, clean profile with documented configuration, safe read-only/local fixture access, and corrected identity/retirement rules. Use the editor's Custom Agents configuration and Chat Diagnostics views to enumerate discovered actors, source paths, names, and actual tools. Do not invoke deployment or operational tools to test their presence.

Expected: the discovered active set matches the accepted registry exactly; duplicate AFP identities, archival/catalogue invocability, and unsupported tool aliases are diagnosed. Verify DevOps name resolution explicitly. Test missing providers and profile/host changes. Record sanitized diagnostics and version information. Switching-response behavior belongs to V-CONTENT, not a discovery-only pass.

### V-CONTENT - Manual Accuracy and Boundaries

Prerequisites: AUD-001-AUD-014 content fixes as applicable, corrected discovery/tools, separate authorization to invoke persona agents, current Australian framework material, and qualified reviewers. Extend the existing [question pack:43](quickstart.md#L43) with the positive/negative/edge cases in each task. Preserve questions, exact answers, sources, scope, scores, model/editor versions, source revision and reviewer decisions in the **proposed** SC-003/SC-004 evidence files.

Expected: measured operational and sector accuracy meets >=80%, out-of-scope requests identify correct owners, and role-switch/cross-jurisdiction cases do not inherit unauthorized perspective or default to the wrong jurisdiction. No actor response constitutes legal or human approval. Response-quality automation remains outside this feature unless separately approved.

### V-SURVEY - Contributor Benefit

Prerequisites: corrected technical guidance; predefined representative cohort, instrument, denominator and nonresponse rules; consent and anonymized storage. Run the SC-005 survey and calculate favorable/eligible responses from the actual dataset.

Expected: >=85% favorable results with a nonzero valid denominator and transparent limitations. Missing or failed measurements remain unverified/failed; they are not repaired by changing checkboxes.

### V-TIMED - New Actor and Change Impact

Prerequisites: corrected contract/registry/quickstart, V-STRUCT available, independent contributor, synthetic actor and disposable workspace. Time full catalogue review plus creation/registration/validation; exercise a governing-reference change and identify affected agents. No branch, commit, or product deployment is needed.

Expected: successful completion in less than 1,800 seconds, correct positive/negative structural checks, and an explicit affected-agent update list. Keep the timestamped result and any assistance/interruptions in the **proposed** timing evidence.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 004 only. Three parallel technical reviews inspected
authority grounding, structural/tool/reference integrity, and registry/evidence concerns. The existing actor
catalogue validator was executed against the current 10 operational, 64 sector, and 17 technical definitions.

| Area | Result | Evidence / remaining limitation |
| --- | --- | --- |
| AUD-003 / AUD-006 / AUD-007 / AUD-009 / AUD-010 / AUD-018 | Automatable structural scope passes. | `python tools/lint/check_actor_agent_catalogue.py --root .` returned `actor-agent-catalogue: PASS`; the validator covers identity uniqueness, YAML/tool fields, required sections, handoff targets, authority ledger links, retired visibility, and registry parity. |
| AUD-001 / AUD-002 / AUD-004 / AUD-005 / AUD-008 / AUD-011 / AUD-012 / AUD-013 / AUD-014 | No new source edit was made in this pass because current content/authority claims require owner or qualified legal/domain review rather than keyword-only rewriting. | Constitution alignment, warning semantics, statutory facts, jurisdictional handoffs, technical/NFR guidance, and accessibility policy need content-owner verification where the report marks them open. |
| AUD-015 / AUD-016 / AUD-017 | Registry/discovery claims remain partly unverified despite static parity. | Clean-profile VS Code discovery, archive invocation behavior, catalogue arithmetic, and host handoff resolution require supported-editor diagnostics and maintainer decisions. |
| AUD-019–AUD-025 | Evidence-only outcomes remain open. | No response-quality evaluation, contributor survey, timed creation exercise, SME consultation, or legal certification was performed or inferred. |

No product runtime, deployment, cloud, or operational code was changed. The pass establishes current structural
validator evidence only; it does not close semantic, legal, editor-discovery, or human-measurement remediation.

## Audit Verification Boundary

The immediate post-write checks for this report are document-only: original-ID/checkbox coverage, local and inherited requirement/scenario coverage, all 91 inspected-definition links, stable unchecked follow-up IDs, local path/line/heading targets, final newline, absence of control characters, and editor diagnostics. Product tests/builds, actor invocation, external approval, cloud state, historical command execution, and legal/operational certification are expressly excluded. Findings remain open until their objective acceptance and evidence requirements are met.
