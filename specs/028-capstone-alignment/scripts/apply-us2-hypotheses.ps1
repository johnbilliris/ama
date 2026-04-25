<#
.SYNOPSIS
    Phase 4 (US2) bulk script: appends 3 capstone-country (PH/JP/BD) hypotheses to each of the
    5 agent specs (008..012) and creates 15 evidence/HYP-NNN.md stubs conforming to
    contracts/evidence-stub.contract.md. Then populates capstone-metric-trace.md (T039..T043)
    by replacing TBD owner cells and marking AU-v1 rows Validated, capstone-country rows Deferred.

.NOTES
    Idempotent: skips append if marker block already present, re-creates stub files only if missing.
    HYP IDs continue from the US1 watermark (post-US1: hypCounter=24+1=25 onward; after spec 027
    HYP-025 was added, US2 starts at HYP-027).
#>
[CmdletBinding()]
param(
    [string] $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
)
$ErrorActionPreference = 'Stop'

# Continuation watermark: US1 used HYP-001..HYP-024 (in 24 specs), spec-027 HYP-025, spec-028 HYP-026.
# US2 starts at HYP-027.
$script:hypCounter = 26
function Next-Hyp { $script:hypCounter++; return ('HYP-{0:D3}' -f $script:hypCounter) }

$cohorts = @(
    @{ code='PH'; name='Philippines'; window='PH typhoon season Jun-Nov'; hazard='typhoon' },
    @{ code='JP'; name='Japan';        window='JP continuous; quarterly review'; hazard='subduction-zone earthquake / tsunami' },
    @{ code='BD'; name='Bangladesh';   window='BD monsoon Apr-Sep'; hazard='monsoon flood' }
)

$agents = @(
    @{
        slug = '008-communication-agent'
        capability = 'multilingual public alerting + misinformation detection'
        capByCohort = @{
            PH = 'a Filipino + regional-language pack with content-safety classifier and human back-translation audit'
            JP = 'a Japanese language pack with JMA-aligned warning-tier templates and content-safety classifier'
            BD = 'a Bangla language pack with BMD / FFWC-aligned templates and content-safety classifier'
        }
        outcomeByCohort = @{
            PH = 'true-positive misinformation detection >= 85% on known PH samples and alert delivery confirmation latency p95 <= 60s'
            JP = 'true-positive misinformation detection >= 85% on known JP samples and earthquake-alert delivery latency p95 <= 5s'
            BD = 'true-positive misinformation detection >= 80% on known BD samples and flood-alert delivery latency p95 <= 60s'
        }
        falsByCohort = @{
            PH = 'true-positive rate < 70% on the labelled fil-PH validation corpus during PH typhoon season Jun-Nov'
            JP = 'true-positive rate < 70% on the labelled ja-JP validation corpus or earthquake-alert latency p95 > 10s during quarterly review'
            BD = 'true-positive rate < 65% on the labelled bn-BD validation corpus during BD monsoon Apr-Sep'
        }
        precondByCohort = @{
            PH = @('PH NDRRMC data-sharing MoU signed.','fil-PH training corpus reviewed by >=1 native-speaker content-safety reviewer.','D-009 capstone-reinterpretation decision cleared.')
            JP = @('JMA / Cabinet Office DRR data-licensing agreement signed.','ja-JP training corpus reviewed by >=1 native-speaker content-safety reviewer.','D-009 capstone-reinterpretation decision cleared.')
            BD = @('BD DDM / BMD data-sharing MoU signed.','bn-BD training corpus reviewed by >=1 native-speaker content-safety reviewer.','D-009 capstone-reinterpretation decision cleared.')
        }
    },
    @{
        slug = '009-evacuation-agent'
        capability = 'evacuation routing + lead-time recommendations'
        capByCohort = @{
            PH = 'pre-warned typhoon evacuation routing across archipelagic terrain'
            JP = 'immediate-onset earthquake / tsunami evacuation routing in dense urban topology'
            BD = 'pre-warned monsoon flood evacuation routing across deltaic / cyclone-shelter network (CPP)'
        }
        outcomeByCohort = @{
            PH = 'recommended evacuation start >= 24h earlier than the unaided NDRRMC reference timeline'
            JP = 'first safe-route recommendation issued within 60s of JMA seismic warning, prioritising vertical evacuation where applicable'
            BD = 'recommended evacuation start >= 24h earlier than the unaided BD reference timeline using CPP shelter capacity awareness'
        }
        falsByCohort = @{
            PH = 'mean lead-time uplift < 12h across exercise scenarios during PH typhoon season Jun-Nov'
            JP = 'first-recommendation latency p95 > 120s during quarterly tabletop exercises'
            BD = 'mean lead-time uplift < 12h across exercise scenarios during BD monsoon Apr-Sep'
        }
        precondByCohort = @{
            PH = @('PH road / port topology dataset licensed.','NDRRMC tabletop scenario pack available.','D-009 cleared.')
            JP = @('JP urban-routing topology dataset (with vertical-evacuation index) licensed.','Cabinet Office tabletop scenario pack available.','D-009 cleared.')
            BD = @('BD CPP shelter inventory + deltaic routing dataset licensed.','DDM tabletop scenario pack available.','D-009 cleared.')
        }
    },
    @{
        slug = '010-monitoring-agent'
        capability = 'hazard-feed monitoring + signal triage'
        capByCohort = @{
            PH = 'PAGASA typhoon + flood feed ingestion with CAP / JSON validation and freshness SLO <= 15 min'
            JP = 'JMA seismic + tsunami feed ingestion with sub-second event detection latency SLO'
            BD = 'BWDB / FFWC hydro-station feed ingestion with freshness SLO <= 30 min during monsoon'
        }
        outcomeByCohort = @{
            PH = '>= 99% feed availability during typhoon-season exercise windows; signal-to-alert end-to-end p95 <= 5 min'
            JP = '>= 99.9% feed availability continuous; seismic-event-to-alert p95 <= 30s'
            BD = '>= 99% feed availability during monsoon exercise windows; signal-to-alert p95 <= 10 min'
        }
        falsByCohort = @{
            PH = 'feed availability < 95% or signal-to-alert p95 > 10 min during PH typhoon season Jun-Nov'
            JP = 'seismic-event-to-alert p95 > 60s during quarterly review'
            BD = 'feed availability < 95% during BD monsoon Apr-Sep'
        }
        precondByCohort = @{
            PH = @('PAGASA data-licensing terms accepted.','PH CAP schema validator deployed.','D-009 cleared.')
            JP = @('JMA data-licensing terms accepted.','JP seismic schema validator deployed.','D-009 cleared.')
            BD = @('BWDB / FFWC data-sharing arrangement signed.','BD hydro schema validator deployed.','D-009 cleared.')
        }
    },
    @{
        slug = '011-resource-allocation-agent'
        capability = 'resource allocation + logistics efficiency'
        capByCohort = @{
            PH = 'archipelagic logistics planning with sea-lift / air-lift / road segment awareness'
            JP = 'urban-dense logistics planning with rail + road segment awareness and earthquake-degraded-network re-planning'
            BD = 'deltaic logistics planning with riverine + road segment awareness during flood-degraded routes'
        }
        outcomeByCohort = @{
            PH = '>= 30% logistics efficiency uplift (time-to-assignment, utilisation, unfilled-priority count) vs unaided reference during PH typhoon-season exercises'
            JP = '>= 30% logistics efficiency uplift vs unaided reference during JP earthquake / tsunami quarterly exercises'
            BD = '>= 30% logistics efficiency uplift vs unaided reference during BD monsoon-season exercises'
        }
        falsByCohort = @{
            PH = 'efficiency uplift < 15% during PH typhoon season Jun-Nov'
            JP = 'efficiency uplift < 15% during quarterly JP earthquake exercises'
            BD = 'efficiency uplift < 15% during BD monsoon Apr-Sep'
        }
        precondByCohort = @{
            PH = @('PH sea-lift / air-lift carrier directory licensed.','PH typhoon-season exercise pack available.','D-009 cleared.')
            JP = @('JP rail + road network dataset licensed.','JP earthquake exercise pack available.','D-009 cleared.')
            BD = @('BD riverine + road network dataset licensed.','BD monsoon exercise pack available.','D-009 cleared.')
        }
    },
    @{
        slug = '012-risk-assessment-agent'
        capability = 'hazard risk-index calibration'
        capByCohort = @{
            PH = 'typhoon (Pacific basin) risk-index calibration using PAGASA + historical track data'
            JP = 'subduction-zone earthquake + tsunami risk-index calibration using JMA + JSHIS data'
            BD = 'monsoon flood + cyclonic-flood risk-index calibration using BWDB + BMD data'
        }
        outcomeByCohort = @{
            PH = 'risk-index calibration error <= 15% on out-of-sample historical typhoon events'
            JP = 'risk-index calibration error <= 10% on out-of-sample historical earthquake events'
            BD = 'risk-index calibration error <= 20% on out-of-sample historical flood events'
        }
        falsByCohort = @{
            PH = 'calibration error > 25% on out-of-sample PH events during PH typhoon season Jun-Nov'
            JP = 'calibration error > 20% on out-of-sample JP events during quarterly review'
            BD = 'calibration error > 30% on out-of-sample BD events during BD monsoon Apr-Sep'
        }
        precondByCohort = @{
            PH = @('Out-of-sample PH typhoon corpus prepared (>=10 historical events).','PH hazard-class taxonomy ratified by `risk-manager` actor.','D-009 cleared.')
            JP = @('Out-of-sample JP earthquake corpus prepared (>=10 historical events).','JP hazard-class taxonomy ratified.','D-009 cleared.')
            BD = @('Out-of-sample BD flood corpus prepared (>=10 historical events).','BD hazard-class taxonomy ratified.','D-009 cleared.')
        }
    }
)

$bt = [char]96

foreach ($a in $agents) {
    $specPath = Join-Path $RepoRoot ('specs\' + $a.slug + '\spec.md')
    $evDir = Join-Path $RepoRoot ('specs\' + $a.slug + '\evidence')
    if (-not (Test-Path $evDir)) { New-Item -ItemType Directory -Path $evDir -Force | Out-Null }

    $content = Get-Content -Path $specPath -Raw
    if ($content -match 'Capstone-Country Hypotheses \(Feature 028 / US2\)') {
        Write-Host "  US2 block already present in $($a.slug); skipping" -ForegroundColor DarkGray
        continue
    }

    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine()
    [void]$sb.AppendLine()
    [void]$sb.AppendLine('## Capstone-Country Hypotheses (Feature 028 / US2)')
    [void]$sb.AppendLine()
    [void]$sb.AppendLine("> Three deferred capstone-country hypotheses for $($a.capability). Each cites an evidence stub at ``specs/$($a.slug)/evidence/HYP-<id>.md`` conforming to ``specs/028-capstone-alignment/contracts/evidence-stub.contract.md``. ``Status = Not tested`` until D-009 capstone-reinterpretation clears and per-cohort preconditions are met.")
    [void]$sb.AppendLine()

    foreach ($c in $cohorts) {
        $hypId = Next-Hyp
        $cap = $a.capByCohort[$c.code]
        $out = $a.outcomeByCohort[$c.code]
        $fal = $a.falsByCohort[$c.code]
        $prec = $a.precondByCohort[$c.code]

        $statement = "We believe $cap will produce $out for the $($c.name) operator persona; we will know we are wrong if $fal is observed in the measurement window ($($c.window))."
        [void]$sb.AppendLine("- **$hypId** [$($c.code) deferred]: $statement")
        [void]$sb.AppendLine("  - **Falsification**: $fal.")
        [void]$sb.AppendLine("  - **Evidence stub**: ``specs/$($a.slug)/evidence/$hypId.md`` (created by feature 028 / US2 / T034..T038).")

        $stubPath = Join-Path $evDir ($hypId + '.md')
        if (-not (Test-Path $stubPath)) {
            $stub = @"
# $hypId - $($c.code) capstone $($c.hazard) hypothesis for $($a.slug)

## Hypothesis
We believe $cap will produce $out for the $($c.name) operator persona; we will know we are wrong if $fal is observed in the measurement window ($($c.window)).

## Preconditions
- $($prec[0])
- $($prec[1])
- $($prec[2])

## Measurement Window
$($c.window).

## Falsification Criterion
- $fal.

## Status
Not tested

## Linked
- Spec: ``specs/$($a.slug)/spec.md``
- ASM: ``specs/005-data-source-governance/spec.md`` (per-country PII / data-source regime preconditions; FR-CAP-005-001)
- Other HYP: feature 028 ``specs/028-capstone-alignment/spec.md`` HYP-026
"@
            Set-Content -Path $stubPath -Value $stub -Encoding UTF8
            Write-Host "    Created $stubPath" -ForegroundColor Green
        }
    }

    Add-Content -Path $specPath -Value $sb.ToString() -Encoding UTF8
    Write-Host "  US2 hypotheses block appended to $($a.slug)" -ForegroundColor Green
}

# Populate capstone-metric-trace.md
$tracePath = Join-Path $RepoRoot 'specs\shared\capstone-metric-trace.md'
$trace = Get-Content -Path $tracePath -Raw

# Replace AU-v1 owners with concrete IDs and Validated; PH/JP/BD with Deferred + preconditions.
$replacements = @(
    # LIVES_SAVED
    @{ pat = '\| LIVES_SAVED \| AU-v1 \|.*?\| Unresolved \|';
       rep = '| LIVES_SAVED | AU-v1 | `specs/001-disaster-response-hub/spec.md` SC-002 + SC-004 (response coordination uplift driving lives-saved) and `specs/015-performance-benchmarks/spec.md` SC-CAP-015-001 | `specs/001-disaster-response-hub/spec.md` HYP-001..HYP-006 (operational uplift hypotheses) | Validated |' },
    @{ pat = '\| LIVES_SAVED \| PH \|.*?\| Unresolved \|';
       rep = '| LIVES_SAVED | PH | `specs/015-performance-benchmarks/spec.md` SC-CAP-015-001 (PH baseline deferred) | HYP-027 (PH typhoon multilingual alerting; `specs/008-communication-agent/evidence/HYP-027.md`) | Deferred — preconditions: D-009 capstone-reinterpretation; PH NDRRMC + PAGASA data-sharing MoU; PH baseline exercise pack available. |' },
    @{ pat = '\| LIVES_SAVED \| JP \|.*?\| Unresolved \|';
       rep = '| LIVES_SAVED | JP | `specs/015-performance-benchmarks/spec.md` SC-CAP-015-001 (JP baseline deferred) | HYP-028 (JP earthquake multilingual alerting; `specs/008-communication-agent/evidence/HYP-028.md`) | Deferred — preconditions: D-009; JMA / Cabinet Office DRR data-licensing; JP baseline exercise pack available. |' },
    @{ pat = '\| LIVES_SAVED \| BD \|.*?\| Unresolved \|';
       rep = '| LIVES_SAVED | BD | `specs/015-performance-benchmarks/spec.md` SC-CAP-015-001 (BD baseline deferred) | HYP-029 (BD monsoon multilingual alerting; `specs/008-communication-agent/evidence/HYP-029.md`) | Deferred — preconditions: D-009; BD DDM / BMD MoU; BD baseline exercise pack available. |' },
    # RESPONSE_SPEED
    @{ pat = '\| RESPONSE_SPEED \| AU-v1 \|.*?\| Unresolved \|';
       rep = '| RESPONSE_SPEED | AU-v1 | `specs/001-disaster-response-hub/spec.md` SC-004 (50% response-time uplift) and `specs/015-performance-benchmarks/spec.md` SC-CAP-015-002 | `specs/001-disaster-response-hub/spec.md` HYP-001 (coordination uplift) | Validated |' },
    @{ pat = '\| RESPONSE_SPEED \| PH \|.*?\| Unresolved \|';
       rep = '| RESPONSE_SPEED | PH | `specs/015-performance-benchmarks/spec.md` SC-CAP-015-002 (deferred) | HYP-033 (PH PAGASA monitoring latency; `specs/010-monitoring-agent/evidence/HYP-033.md`) | Deferred — preconditions: D-009; PAGASA feed accepted. |' },
    @{ pat = '\| RESPONSE_SPEED \| JP \|.*?\| Unresolved \|';
       rep = '| RESPONSE_SPEED | JP | `specs/015-performance-benchmarks/spec.md` SC-CAP-015-002 (deferred) | HYP-034 (JP JMA seismic latency; `specs/010-monitoring-agent/evidence/HYP-034.md`) | Deferred — preconditions: D-009; JMA feed accepted. |' },
    @{ pat = '\| RESPONSE_SPEED \| BD \|.*?\| Unresolved \|';
       rep = '| RESPONSE_SPEED | BD | `specs/015-performance-benchmarks/spec.md` SC-CAP-015-002 (deferred) | HYP-035 (BD BWDB hydro latency; `specs/010-monitoring-agent/evidence/HYP-035.md`) | Deferred — preconditions: D-009; BWDB / FFWC arrangement signed. |' },
    # EVAC_LEAD_TIME
    @{ pat = '\| EVAC_LEAD_TIME \| AU-v1 \|.*?\| Unresolved \|';
       rep = '| EVAC_LEAD_TIME | AU-v1 | `specs/001-disaster-response-hub/spec.md` SC-005 (24h earlier evacuation) and `specs/015-performance-benchmarks/spec.md` SC-CAP-015-003 | `specs/001-disaster-response-hub/spec.md` HYP-002 (evacuation lead-time) | Validated |' },
    @{ pat = '\| EVAC_LEAD_TIME \| PH \|.*?\| Unresolved \|';
       rep = '| EVAC_LEAD_TIME | PH | `specs/015-performance-benchmarks/spec.md` SC-CAP-015-003 (deferred) | HYP-030 (PH typhoon pre-warned evac; `specs/009-evacuation-agent/evidence/HYP-030.md`) | Deferred — preconditions: D-009; PH topology + NDRRMC tabletop pack. |' },
    @{ pat = '\| EVAC_LEAD_TIME \| JP \|.*?\| Unresolved \|';
       rep = '| EVAC_LEAD_TIME | JP | `specs/015-performance-benchmarks/spec.md` SC-CAP-015-003 (deferred) | HYP-031 (JP immediate-onset evac; `specs/009-evacuation-agent/evidence/HYP-031.md`) | Deferred — preconditions: D-009; JP urban-routing topology dataset. |' },
    @{ pat = '\| EVAC_LEAD_TIME \| BD \|.*?\| Unresolved \|';
       rep = '| EVAC_LEAD_TIME | BD | `specs/015-performance-benchmarks/spec.md` SC-CAP-015-003 (deferred) | HYP-032 (BD monsoon pre-warned evac; `specs/009-evacuation-agent/evidence/HYP-032.md`) | Deferred — preconditions: D-009; BD CPP shelter inventory. |' },
    # LOGISTICS_EFFICIENCY
    @{ pat = '\| LOGISTICS_EFFICIENCY \| AU-v1 \|.*?\| Unresolved \|';
       rep = '| LOGISTICS_EFFICIENCY | AU-v1 | `specs/001-disaster-response-hub/spec.md` SC-006 (30% efficiency) and `specs/015-performance-benchmarks/spec.md` SC-CAP-015-004 | `specs/001-disaster-response-hub/spec.md` HYP-003 (logistics efficiency) | Validated |' },
    @{ pat = '\| LOGISTICS_EFFICIENCY \| PH \|.*?\| Unresolved \|';
       rep = '| LOGISTICS_EFFICIENCY | PH | `specs/015-performance-benchmarks/spec.md` SC-CAP-015-004 (deferred) | HYP-036 (PH archipelagic logistics; `specs/011-resource-allocation-agent/evidence/HYP-036.md`) | Deferred — preconditions: D-009; PH carrier directory licensed. |' },
    @{ pat = '\| LOGISTICS_EFFICIENCY \| JP \|.*?\| Unresolved \|';
       rep = '| LOGISTICS_EFFICIENCY | JP | `specs/015-performance-benchmarks/spec.md` SC-CAP-015-004 (deferred) | HYP-037 (JP urban-dense logistics; `specs/011-resource-allocation-agent/evidence/HYP-037.md`) | Deferred — preconditions: D-009; JP rail+road network dataset. |' },
    @{ pat = '\| LOGISTICS_EFFICIENCY \| BD \|.*?\| Unresolved \|';
       rep = '| LOGISTICS_EFFICIENCY | BD | `specs/015-performance-benchmarks/spec.md` SC-CAP-015-004 (deferred) | HYP-038 (BD deltaic logistics; `specs/011-resource-allocation-agent/evidence/HYP-038.md`) | Deferred — preconditions: D-009; BD riverine+road dataset. |' },
    # ECONOMIC_LOSS_REDUCTION
    @{ pat = '\| ECONOMIC_LOSS_REDUCTION \| AU-v1 \|.*?\| Unresolved \|';
       rep = '| ECONOMIC_LOSS_REDUCTION | AU-v1 | `specs/015-performance-benchmarks/spec.md` SC-CAP-015-005 (Sendai-aligned scenario-modelled counterfactual) | `specs/012-risk-assessment-agent/spec.md` HYP-NNN (AU-v1 risk-index calibration; AU baseline validated) | Validated |' },
    @{ pat = '\| ECONOMIC_LOSS_REDUCTION \| PH \|.*?\| Unresolved \|';
       rep = '| ECONOMIC_LOSS_REDUCTION | PH | `specs/015-performance-benchmarks/spec.md` SC-CAP-015-005 (deferred) | HYP-039 (PH typhoon risk-index calibration; `specs/012-risk-assessment-agent/evidence/HYP-039.md`) | Deferred — preconditions: D-009; PH out-of-sample typhoon corpus. |' },
    @{ pat = '\| ECONOMIC_LOSS_REDUCTION \| JP \|.*?\| Unresolved \|';
       rep = '| ECONOMIC_LOSS_REDUCTION | JP | `specs/015-performance-benchmarks/spec.md` SC-CAP-015-005 (deferred) | HYP-040 (JP earthquake risk-index calibration; `specs/012-risk-assessment-agent/evidence/HYP-040.md`) | Deferred — preconditions: D-009; JP out-of-sample earthquake corpus. |' },
    @{ pat = '\| ECONOMIC_LOSS_REDUCTION \| BD \|.*?\| Unresolved \|';
       rep = '| ECONOMIC_LOSS_REDUCTION | BD | `specs/015-performance-benchmarks/spec.md` SC-CAP-015-005 (deferred) | HYP-041 (BD flood risk-index calibration; `specs/012-risk-assessment-agent/evidence/HYP-041.md`) | Deferred — preconditions: D-009; BD out-of-sample flood corpus. |' }
)
foreach ($r in $replacements) {
    $trace = [regex]::Replace($trace, $r.pat, $r.rep)
}
Set-Content -Path $tracePath -Value $trace -Encoding UTF8

Write-Host ""
Write-Host "Done US2. HYP IDs allocated: HYP-027..HYP-$('{0:D3}' -f $hypCounter)" -ForegroundColor Yellow
$unresolved = (Get-Content $tracePath | Select-String 'Unresolved').Count
Write-Host "Unresolved rows remaining: $unresolved" -ForegroundColor Yellow
