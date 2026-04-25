<#
.SYNOPSIS
    Applies Phase 3 (US1) hardening across the AMA spec portfolio for feature 028-capstone-alignment.

.DESCRIPTION
    Idempotent. For each spec listed in the manifest, appends the four mandatory H2 sections
    (## Assumptions, ## Personas, ## Hypotheses, ## Out of Scope) if absent, plus per-spec FR/SC
    additions documented in tasks.md T008..T033. Adds the AU-only-residency [RISK] assumption (D-009)
    where the spec touches PII / persona / location / LLM data.

    ID allocation is global and monotonic across the portfolio.

.NOTES
    Run order: pwsh -File specs\028-capstone-alignment\scripts\apply-us1-hardening.ps1
    Then verify with:  pwsh -File specs\028-capstone-alignment\scripts\validate-section-coverage.ps1
#>
[CmdletBinding()]
param(
    [string] $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
)
$ErrorActionPreference = 'Stop'

$script:asmCounter = 0
$script:hypCounter = 0
$script:perCounter = 0
$script:scpCounter = 0
function Next-Id { param([string]$Family)
    switch ($Family) {
        'ASM' { $script:asmCounter++; return ('ASM-{0:D3}' -f $script:asmCounter) }
        'HYP' { $script:hypCounter++; return ('HYP-{0:D3}' -f $script:hypCounter) }
        'PER' { $script:perCounter++; return ('PER-{0:D3}' -f $script:perCounter) }
        'SCP' { $script:scpCounter++; return ('SCP-{0:D3}' -f $script:scpCounter) }
    }
}

$manifest = @(
    @{ slug='003-rubric-gap-closure'; domain='AMA rubric uplift programme'; agents='product-owner-ba, qa-test-engineer'; pii=$false; meta=$true },
    @{ slug='004-actor-github-agents'; domain='actor / GitHub agent catalogue and registry'; agents='product-owner-ba'; pii=$false; meta=$true },
    @{ slug='005-data-source-governance'; domain='per-country PII / data-source classification'; agents='compliance-auditor, security-engineer, product-owner-ba'; pii=$true; meta=$false },
    @{ slug='006-data-ingestion-storage'; domain='ingestion + storage of authoritative hazard feeds'; agents='data-engineer, bom-national, ga-national'; pii=$true; meta=$false },
    @{ slug='007-simulation-tenant-isolation'; domain='multi-tenant simulation isolation'; agents='security-engineer, product-owner-ba'; pii=$false; meta=$true },
    @{ slug='008-communication-agent'; domain='multilingual public alerting + misinformation defence'; agents='public-information-officer, accessibility-tester, ai-ml-engineer'; pii=$true; meta=$false },
    @{ slug='009-evacuation-agent'; domain='evacuation routing + lead-time recommendations'; agents='planning-officer, operations-officer, resilience-planner'; pii=$true; meta=$false },
    @{ slug='010-monitoring-agent'; domain='hazard-feed monitoring + signal triage'; agents='planning-officer, risk-manager, ai-ml-engineer'; pii=$true; meta=$false },
    @{ slug='011-resource-allocation-agent'; domain='resource allocation + recovery logistics'; agents='logistics-officer, operations-officer, resilience-planner'; pii=$false; meta=$false },
    @{ slug='012-risk-assessment-agent'; domain='hazard risk-index calibration'; agents='risk-manager, ga-national, ntes, bom-national'; pii=$false; meta=$false },
    @{ slug='013-root-readme'; domain='repo root README orchestration'; agents='product-owner-ba'; pii=$false; meta=$true },
    @{ slug='014-azure-openai-integration'; domain='LLM gateway + Azure OpenAI integration'; agents='ai-ml-engineer, azure-principal-architect, security-engineer'; pii=$true; meta=$false },
    @{ slug='015-performance-benchmarks'; domain='solution-wide performance benchmarks'; agents='qa-test-engineer, sre-engineer, product-owner-ba'; pii=$false; meta=$false },
    @{ slug='016-automated-demo-script'; domain='automated capstone demo scripting'; agents='product-owner-ba, qa-test-engineer'; pii=$false; meta=$true },
    @{ slug='017-cd-pipeline'; domain='continuous deployment pipeline'; agents='infrastructure-devops, azure-principal-architect, security-engineer'; pii=$true; meta=$true },
    @{ slug='018-aidr-guidance-integration'; domain='AIDR recovery + escalation authoritative source'; agents='incident-commander, resilience-planner, planning-officer'; pii=$false; meta=$false },
    @{ slug='019-aidr-additional-guidances'; domain='supplementary AIDR guidance ingestion'; agents='resilience-planner, product-owner-ba'; pii=$false; meta=$false },
    @{ slug='020-disaster-mapper-ui'; domain='situational-awareness map UI'; agents='ux-designer, accessibility-tester, operations-officer'; pii=$false; meta=$false },
    @{ slug='021-governance-dashboard'; domain='governance + audit dashboard'; agents='ux-designer, observer-auditor, compliance-auditor'; pii=$false; meta=$false },
    @{ slug='022-multi-jurisdiction-filter'; domain='jurisdiction filter UI + data scoping'; agents='ux-designer, solution-architect, state-government, local-government'; pii=$false; meta=$false },
    @{ slug='023-dashboard-real-data'; domain='dashboard real-data wiring (replaces seeded demo data)'; agents='data-engineer, ux-designer'; pii=$false; meta=$false },
    @{ slug='024-simulation-control-chat'; domain='conversational simulation control'; agents='ux-designer, product-owner-ba'; pii=$false; meta=$true },
    @{ slug='025-agent-spec-compliance'; domain='agent / spec cross-compliance verification'; agents='qa-test-engineer, product-owner-ba'; pii=$false; meta=$true },
    @{ slug='026-sim-warp-playback'; domain='simulation warp + playback'; agents='qa-test-engineer, ux-designer'; pii=$false; meta=$true }
)

function Build-Sections {
    param($Spec)
    $domain  = $Spec.domain
    $agents  = $Spec.agents
    $pii     = $Spec.pii
    $meta    = $Spec.meta

    $asm1 = Next-Id 'ASM'
    $asm2 = Next-Id 'ASM'
    $asm3 = Next-Id 'ASM'
    $asmRisk = if ($pii) { Next-Id 'ASM' } else { $null }

    $hyp1 = Next-Id 'HYP'

    $per1 = Next-Id 'PER'
    $per2 = Next-Id 'PER'
    $per3 = Next-Id 'PER'

    $scp1 = Next-Id 'SCP'
    $scp2 = Next-Id 'SCP'
    $scp3 = Next-Id 'SCP'

    $bt = [char]96  # backtick `
    $au = "${bt}australiaeast${bt} / ${bt}australiasoutheast${bt}"

    $assumptions = @"

## Assumptions

Scoped to this spec's domain ($domain). Tagging follows ${bt}specs/027-spec-hardening${bt} taxonomy: ${bt}[RISK]${bt} (open externally-driven risk), ${bt}[DECISION]${bt} (deliberate scoping decision), bare bullet (operating assumption).

- **$asm1**: The AU-v1 deployment context defined in ${bt}specs/001-disaster-response-hub/spec.md${bt} is the operational baseline for this spec; capstone-country variants (PH / JP / BD) are deferred. ${bt}linked_gaps:${bt} ${bt}specs/shared/gap-id-register.md${bt} A-GAP-001..003. ${bt}status:${bt} Open.
- **$asm2** [DECISION]: This spec's deliverables ($domain) integrate with the actor catalogue (${bt}specs/004-actor-github-agents/spec.md${bt}); responsible technical agents - $agents - are consulted via the ${bt}agent${bt} tool during authoring and review.
- **$asm3**: Speckit conventions (FR/SC numbering, ASM/HYP/PER/SCP families) and the persona-profile YAML schema (${bt}specs/027-spec-hardening/contracts/persona-profile.md${bt}) are authoritative; this spec defers to those rather than redefining them.
"@
    if ($asmRisk) {
        $assumptions += @"

- **$asmRisk** [RISK]: AU-only data residency (constitution NON-NEGOTIABLE #2; Azure $au only) is in tension with the capstone Asia framing (PH / JP / BD sovereign-data handling). Resolution requires a constitution-level amendment owned outside this feature (see ${bt}specs/028-capstone-alignment/research.md${bt} D-009). ${bt}linked_gaps:${bt} constitution NON-NEGOTIABLE #2. ${bt}status:${bt} Open.
"@
    }

    $personas = @"


## Personas

Authored against the ${bt}specs/027-spec-hardening/contracts/persona-profile.md${bt} schema. AU-v1 personas are validated; PH / JP / BD entries are explicit placeholders pending capstone-reinterpretation (D-009) and SME validation per FR-023.

- **$per1**: cross-ref to ${bt}specs/001-disaster-response-hub/spec.md${bt} AIIMS personas (Incident Commander / Planning Officer / Operations Officer / Logistics Officer / Public Information Officer) per ${bt}specs/027-spec-hardening/contracts/persona-profile.md${bt}. ${bt}status:${bt} validated. ${bt}preconditions:${bt} none.
- **$per2**: cross-ref to ${bt}specs/004-actor-github-agents/spec.md${bt} actor catalogue covering all ${bt}.github/agents/technical/*.agent.md${bt} actors. ${bt}status:${bt} validated. ${bt}preconditions:${bt} none.
- **$per3** [non-AU placeholder]: capstone-country operator personas for PH (NDRRMC), JP (Cabinet Office DRR / FDMA), BD (DDM / CPP volunteers). ${bt}status:${bt} placeholder. ${bt}preconditions:${bt} capstone-reinterpretation decision per D-009; SME validation via ${bt}ama-rubric-grader${bt}-vetted SME interviews.
"@

    $hypotheses = @"


## Hypotheses

Hypotheses use the FR-018 statement format (${bt}If <condition> then <observable>${bt}) and link to a structured evidence stub conforming to ${bt}specs/028-capstone-alignment/contracts/evidence-stub.contract.md${bt}. Capstone-country hypotheses for this spec's agent ownership (where applicable) are allocated in feature 028 / US2.

- **$hyp1**: If the actors named in ${bt}specs/004-actor-github-agents/spec.md${bt} consult on every change to this spec via the ${bt}agent${bt} tool, then the AMA rubric criterion mean (Assumptions / Requirements / Personas / Hypotheses / Scope) for this spec rises by at least +1 band relative to the baseline captured in ${bt}specs/028-capstone-alignment/evidence/rubric-baseline.md${bt}. **Falsification**: post-feature rubric snapshot shows a regression in any of those five criteria for this spec. **Evidence stub**: ${bt}specs/028-capstone-alignment/evidence/HYP-$hyp1.md${bt} (created in feature 028 polish).
"@

    $oos = @"


## Out of Scope

Items explicitly deferred from this spec; promotion to in-scope requires the named preconditions to clear. Cross-references to other specs use the canonical overlap phrasing (${bt}authoritative for: <capability>${bt} / ${bt}defers-to: <NNN> (<capability>)${bt}).

- **$scp1** [DEFERRED]: Capstone-country variants (PH typhoon, JP earthquake, BD flood) of this spec's capabilities are out of scope until: (i) capstone-reinterpretation decision per D-009; (ii) per-country regulatory + data-sharing preconditions documented in ${bt}specs/005-data-source-governance/spec.md${bt} clear; (iii) responsible technical agents ($agents) sign off on country-specific calibration.
- **$scp2**: Constitutional-level changes (NON-NEGOTIABLE #1..#5) are not modified by this spec; any tension is documented as ${bt}[RISK]${bt} in Assumptions, never resolved here.
- **$scp3**: Cross-spec authority disputes are arbitrated via ${bt}product-owner-ba${bt} and the speckit governance flow; this spec does not unilaterally claim ownership of capabilities owned elsewhere. ${bt}defers-to:${bt} 018 (recovery-phase indicators, triggers, phase-exit criteria); 008 (warning-tier authoring, multilingual delivery, misinformation defence) where applicable.
"@
    if ($meta) {
        $scp4 = Next-Id 'SCP'
        $oos += @"

- **$scp4** [META]: This spec is delivery-hygiene / enabling infrastructure; capstone-outcome-critical-path ownership lives in specs [list-pending - populated in feature 028 US4]. (See ${bt}specs/028-capstone-alignment/contracts/meta-spec-flag.contract.md${bt}; the verbatim canonical bullet is added in US4.)
"@
    }

    return @{ asm = $assumptions; per = $personas; hyp = $hypotheses; oos = $oos }
}

foreach ($s in $manifest) {
    $path = Join-Path $RepoRoot ('specs\' + $s.slug + '\spec.md')
    if (-not (Test-Path $path)) { Write-Warning "Missing $path"; continue }
    Write-Host "Processing $($s.slug)..." -ForegroundColor Cyan
    $sections = Build-Sections -Spec $s

    $content = Get-Content -Path $path -Raw
    $needAsm = -not [regex]::IsMatch($content, '(?m)^## Assumptions\s*$')
    $needPer = -not [regex]::IsMatch($content, '(?m)^## Personas\s*$')
    $needHyp = -not [regex]::IsMatch($content, '(?m)^## Hypotheses\s*$')
    $needOos = -not [regex]::IsMatch($content, '(?m)^## Out[ -]of[ -]Scope\s*$')

    $append = ''
    if ($needAsm) { $append += $sections.asm }
    if ($needPer) { $append += $sections.per }
    if ($needHyp) { $append += $sections.hyp }
    if ($needOos) { $append += $sections.oos }

    if ($append) {
        Add-Content -Path $path -Value $append -Encoding UTF8
        Write-Host "  Appended: ASM=$needAsm PER=$needPer HYP=$needHyp OOS=$needOos" -ForegroundColor Green
    } else {
        Write-Host "  Already complete" -ForegroundColor DarkGray
    }
}

# Per-spec custom additions
$customs = @{}
$bt = [char]96
$customs['005-data-source-governance'] = @"


## Capstone-Aligned Requirements (Feature 028 / FR-007)

The capabilities below are deferred-scope; AU-v1 today only. Promotion requires per-regime data-protection authority approval and constitution amendment per D-009.

- **FR-CAP-005-001** [DEFERRED]: Per-country PII classification covering: AU **Privacy Act 1988 (Cth) + Australian Privacy Principles (APPs)** (status: in-scope, AU-v1); JP **Act on the Protection of Personal Information (APPI) 2017 / 2020 amendments** (status: deferred); PH **RA 10173 Data Privacy Act 2012 + NPC Circulars** (status: deferred); BD **ICT Act 2006 + draft Data Protection Act 2023** (status: deferred). Each non-AU regime is gated by an MoU + DPIA + data-residency lawful basis precondition. ${bt}defers-to:${bt} future capstone-reinterpretation feature.
- **FR-CAP-005-002** [DEFERRED]: Cross-border data-transfer rules (where lawful) follow the strictest regime applicable to the data subject's locus and the data-storage region; default is to **forbid** transfer until the per-country regime is gated active. ${bt}defers-to:${bt} 028.
"@
$customs['006-data-ingestion-storage'] = @"


## Capstone-Aligned Requirements (Feature 028 / FR-009)

The candidate capstone-country hazard feeds below are deferred until the named preconditions clear. ${bt}defers-to:${bt} 005 for residency / lawful basis; ${bt}defers-to:${bt} 028 for capstone-reinterpretation.

- **FR-CAP-006-001** [DEFERRED]: Philippines feed candidate **PAGASA** (typhoon + flood). Preconditions: (i) data-sharing MoU with DOST-PAGASA; (ii) JSON / CAP schema validator; (iii) freshness SLO <= 15 min during typhoon season (Jun-Nov).
- **FR-CAP-006-002** [DEFERRED]: Japan feed candidate **JMA** (earthquake + tsunami; JAXA / QZSS for location-augmenting signals). Preconditions: (i) JMA data-licensing terms; (ii) sub-second seismic-event ingestion validator; (iii) 24x7 freshness SLO.
- **FR-CAP-006-003** [DEFERRED]: Bangladesh feed candidate **BWDB / FFWC** (riverine flood). Preconditions: (i) BWDB data-sharing arrangement; (ii) hydro-station schema validator; (iii) freshness SLO <= 30 min during monsoon (Apr-Sep).

> **Overlap note**: This spec carries an existing FR-024 that overlaps with ${bt}specs/008-communication-agent${bt}. ${bt}defers-to:${bt} 008 (warning-tier multilingual authoring + delivery); the canonical reciprocal ${bt}supersedes:${bt} rule is added in spec 008 by feature 028 / US3 / T044.
"@
$customs['008-communication-agent'] = @"


## Capstone-Aligned Requirements (Feature 028 / FR-006)

- **FR-CAP-008-001** [DEFERRED]: Multilingual language-pack plugin support with at least one non-English language pack per capstone country: **Philippines** (Filipino + regional languages), **Japan** (Japanese), **Bangladesh** (Bangla). Each language pack has the following preconditions: (i) content-safety classifier in target language; (ii) human back-translation audit on >=1 % of public-facing alerts; (iii) accessibility QA per ${bt}specs/020-disaster-mapper-ui${bt} and the accessibility-tester actor.
  - **BCP-47 identifier selection is deferred to research.md** per clarification Q2 / D-004; no concrete identifier (${bt}fil-PH${bt} / ${bt}ja-JP${bt} / ${bt}bn-BD${bt}) is hard-coded in this spec.
- **FR-CAP-008-002** [DEFERRED]: Multilingual misinformation-detection inherits the spec-010 fallback rule (when language-specific classifier confidence is below threshold, fall back to the conservative English-baseline classifier and flag for human review).
- **FR-CAP-008-003**: ${bt}defers-to:${bt} 018 (warning-tier approval timeout escalation; spec 018 is authoritative for portfolio-wide escalation timeout per FR-017 / T045).
- **FR-CAP-008-004**: ${bt}supersedes:${bt} ${bt}specs/006-data-ingestion-storage/spec.md${bt} FR-024 (warning-tier multilingual authoring + delivery - formally relocated here per FR-016 / T044).
"@
$customs['011-resource-allocation-agent'] = @"


## Capstone-Aligned Cross-References (Feature 028 / FR-018)

- **Recovery-phase scope**: ${bt}defers-to:${bt} 018 (recovery-phase indicators, triggers, and phase-exit criteria; spec 018 is authoritative across the portfolio per D-005).
"@
$customs['012-risk-assessment-agent'] = @"


## Capstone-Aligned Requirements (Feature 028 / P-004)

The hazard taxonomy owned here is *extended* - not replaced - to name capstone-country instances of the existing AU hazard classes.

| Hazard class (AU-v1) | Capstone country | Country-scoped instance | Status |
| --- | --- | --- | --- |
| Tropical cyclone (analog) | Philippines | Typhoon (Pacific basin) | Deferred - see ASM [RISK] AU-residency tension |
| Earthquake (existing) | Japan | Subduction-zone earthquake + tsunami | Deferred |
| Riverine flood (existing) | Bangladesh | Monsoon + cyclone-driven coastal flood | Deferred |

> No existing AU hazard row is modified.
"@
$customs['015-performance-benchmarks'] = @"


## Capstone-Aligned Success Criteria (Feature 028 / FR-012)

The five capstone success metrics MUST each map to at least one benchmark scenario in this spec; AU-v1 baselines are recorded today, capstone-country baselines are deferred. Cited by ${bt}specs/shared/capstone-metric-trace.md${bt} SC-Owner cells (see feature 028 / US2 / T039..T043).

- **SC-CAP-015-001** **${bt}LIVES_SAVED${bt}** - AU-v1 baseline scenario: lives at risk per major-flood exercise (BoM-driven); measurement method: pre/post intervention exercise outcomes; capstone target: >= 1,000 lives/yr saved at solution-of-whole level. Capstone-country baselines: deferred.
- **SC-CAP-015-002** **${bt}RESPONSE_SPEED${bt}** - AU-v1 baseline scenario: alert-to-acknowledgement median latency; measurement method: end-to-end timing in benchmark exercises; capstone target: 50 % faster than the unaided reference. Capstone-country baselines: deferred.
- **SC-CAP-015-003** **${bt}EVAC_LEAD_TIME${bt}** - AU-v1 baseline scenario: warning-issuance to recommended-evacuation-start delta; measurement method: timeline reconstruction in benchmark scenarios; capstone target: 24 h earlier evacuation than unaided reference. Capstone-country baselines: deferred.
- **SC-CAP-015-004** **${bt}LOGISTICS_EFFICIENCY${bt}** - AU-v1 baseline scenario: resource utilisation rate (allocated vs idle) during exercise; measurement method: telemetry from ${bt}specs/011-resource-allocation-agent${bt}; capstone target: 30 % efficiency uplift. Capstone-country baselines: deferred.
- **SC-CAP-015-005** **${bt}ECONOMIC_LOSS_REDUCTION${bt}** - AU-v1 baseline scenario: estimated avoided economic loss in exercise (Sendai indicator alignment); measurement method: scenario-modelled counterfactual; capstone target: 30 % loss-reduction. Capstone-country baselines: deferred.
"@
$customs['017-cd-pipeline'] = @"


## Capstone-Aligned Requirements (Feature 028 / FR-010)

- **FR-CAP-017-001** [DEFERRED]: The CD pipeline supports a region-per-country topology where each capstone country deploys to its own sovereign Azure region pair. Today the pipeline only deploys to ${bt}australiaeast${bt} / ${bt}australiasoutheast${bt} (constitution NON-NEGOTIABLE #2). Reversal of the AU-only default is explicitly a **capstone-reinterpretation decision** owned outside this feature; ${bt}defers-to:${bt} 028 for surfacing, constitution amendment for resolution. ${bt}linked_gaps:${bt} constitution NON-NEGOTIABLE #2.
"@
$customs['018-aidr-guidance-integration'] = @"


## Capstone-Aligned Cross-References (Feature 028 / FR-018, FR-017)

- **Recovery-phase authority**: ${bt}authoritative for:${bt} recovery-phase indicators, triggers, and phase-exit criteria across the AMA portfolio (per D-005 and ${bt}specs/028-capstone-alignment/spec.md${bt} FR-018). Other specs that touch recovery (specs 001 DEF-015, 011) carry the reciprocal ${bt}defers-to: 018 (recovery-phase indicators, triggers, phase-exit criteria)${bt} pointer.
- **Warning-tier escalation timeout authority**: ${bt}authoritative for:${bt} warning-tier approval-timeout escalation across the portfolio (per FR-017 and feature 028 / US3 / T045). Spec 008 carries the reciprocal ${bt}defers-to: 018 (warning-tier approval timeout)${bt} pointer.
"@
$customs['022-multi-jurisdiction-filter'] = @"


## Capstone-Aligned Requirements (Feature 028 / FR-008)

- **FR-CAP-022-001**: The jurisdiction filter supports a nested ${bt}country -> state/region${bt} hierarchy. The existing AU 9-jurisdiction set is preserved unchanged; capstone-country nodes are added as **placeholders** with explicit preconditions.

${bt}${bt}${bt}text
AU -> { NSW, VIC, QLD, SA, WA, TAS, ACT, NT, Commonwealth }   # status: validated (AU-v1)
PH -> { placeholder }                                          # status: placeholder; preconditions: D-009 + per-country regulatory clearance
JP -> { placeholder }                                          # status: placeholder; preconditions: D-009 + JMA / Cabinet Office DRR engagement
BD -> { placeholder }                                          # status: placeholder; preconditions: D-009 + DDM / BWDB engagement
${bt}${bt}${bt}

> No AU node is modified by this addition.
"@

foreach ($k in $customs.Keys) {
    $path = Join-Path $RepoRoot ('specs\' + $k + '\spec.md')
    if (-not (Test-Path $path)) { continue }
    $content = Get-Content -Path $path -Raw
    if ($content -match '## Capstone-Aligned') {
        Write-Host "  Custom block already in $k" -ForegroundColor DarkGray
    } else {
        Add-Content -Path $path -Value $customs[$k] -Encoding UTF8
        Write-Host "  Custom block appended to $k" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Done. ID counters: ASM=$asmCounter HYP=$hypCounter PER=$perCounter SCP=$scpCounter" -ForegroundColor Yellow
