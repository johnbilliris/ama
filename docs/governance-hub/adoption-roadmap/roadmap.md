# Adoption Roadmap (spec-037 artefact 2)

- Publication: `9fc39c52-0f94-5036-8759-8662c8ef64cb`
- Published: 2026-05-11T17:30:00Z
- Manual-row ratio: 1.00
- Auditor sign-off: Capstone Evidence Pack v1 Author

## Waves

### WAVE-01 — state-lead

**Jurisdictions**: NSW, VIC, QLD

**Lead agency map**:
- `NSW` — NSW SES + NSW RFS (lead) with NSWPF + NSW Ambulance
- `VIC` — VIC SES + CFA-VIC (lead) with VICPOL + AV
- `QLD` — QLD QFD + SES-QLD (lead) with QPS + QAS

**Readiness gates**:
- Spec-001/007/024 deployed; AIIMS Unified Command rehearsed; jurisdiction lead-agency MoU signed

**Training/exercise cadence**: quarterly, citing specs 007/024/026.

**Change-management artefacts**:
- Communications plan; AIIMS-aligned training pack; tabletop exercise pack; SLO baseline

**Decommission/rollback criteria** (preserves life-safety defaults per Constitution § Primacy of Life):
- Preserve life-safety defaults per Constitution § Primacy of Life; degrade to manual ops without data loss; Field Coordinator conservative defaults preserved
- Rollback to spec-001 baseline if WAVE-01 SLO breached for 7 consecutive days

### WAVE-02 — state-lead

**Jurisdictions**: SA, WA, TAS

**Lead agency map**:
- `SA` — SA SES + SA MFS (lead) with SAPOL + SA Ambulance
- `WA` — WA DFES (lead) with WAPOL + St John WA
- `TAS` — TAS SES (lead) with TASPOL + Ambulance Tasmania

**Readiness gates**:
- WAVE-01 SLOs green for 30 days; WAVE-02-specific scenario pack rehearsed

**Training/exercise cadence**: quarterly, citing specs 007/024/026.

**Change-management artefacts**:
- WAVE-02 onboarding playbook; cross-state mutual-aid table; per-state communications cadence

**Decommission/rollback criteria** (preserves life-safety defaults per Constitution § Primacy of Life):
- Same as WAVE-01; conservative life-safety defaults non-negotiable

### WAVE-03 — state-lead

**Jurisdictions**: ACT, NT, Commonwealth

**Lead agency map**:
- `ACT` — ACT ESA (lead)
- `NT` — NTFRS + NT Police, Fire & Emergency Services (lead)
- `Commonwealth` — NEMA (lead) with BoM National + Geoscience Australia + ADF + ABF

**Readiness gates**:
- WAVE-02 SLOs green for 30 days; COMDISPLAN coordination pattern rehearsed; NEMA mutual-aid agreement

**Training/exercise cadence**: quarterly, citing specs 007/024/026.

**Change-management artefacts**:
- Federal-state escalation playbook; COMDISPLAN integration guide

**Decommission/rollback criteria** (preserves life-safety defaults per Constitution § Primacy of Life):
- Same as WAVE-01; Commonwealth fallback to existing NEMA processes preserved

### WAVE-04 — local-government

**Jurisdictions**: NSW, VIC, QLD, WA, SA, TAS, ACT, NT

**Lead agency map**:
- `NSW` — State LGA peak body (NSW)
- `VIC` — State LGA peak body (VIC)
- `QLD` — State LGA peak body (QLD)
- `WA` — State LGA peak body (WA)
- `SA` — State LGA peak body (SA)
- `TAS` — State LGA peak body (TAS)
- `ACT` — State LGA peak body (ACT)
- `NT` — State LGA peak body (NT)

**Readiness gates**:
- WAVE-01..03 SLOs green; LGA-level data-sharing MoU; community evacuation centre integration

**Training/exercise cadence**: biannual, citing specs 007/024/026.

**Change-management artefacts**:
- LGA onboarding pack; community-of-practice quarterly forum; LGA-tier dashboard subset

**Decommission/rollback criteria** (preserves life-safety defaults per Constitution § Primacy of Life):
- Same as WAVE-01; LGA-tier rollback to spec-021 dashboard with manual coordination

### WAVE-05 — volunteer-ngo

**Jurisdictions**: NSW, VIC, QLD, WA, SA, TAS, ACT, NT, Commonwealth

**Lead agency map**:
- `NSW` — State volunteer peak (Surf Life Saving / SES Volunteers / SJA / RFDS)
- `VIC` — State volunteer peak (Surf Life Saving / SES Volunteers / SJA / RFDS)
- `QLD` — State volunteer peak (Surf Life Saving / SES Volunteers / SJA / RFDS)
- `WA` — State volunteer peak (Surf Life Saving / SES Volunteers / SJA / RFDS)
- `SA` — State volunteer peak (Surf Life Saving / SES Volunteers / SJA / RFDS)
- `TAS` — State volunteer peak (Surf Life Saving / SES Volunteers / SJA / RFDS)
- `ACT` — State volunteer peak (Surf Life Saving / SES Volunteers / SJA / RFDS)
- `NT` — State volunteer peak (Surf Life Saving / SES Volunteers / SJA / RFDS)
- `Commonwealth` — Australian Red Cross + St John Ambulance Australia

**Readiness gates**:
- Volunteer credentialing readiness; community comms pack signed off; WAVE-04 LGA forums established

**Training/exercise cadence**: biannual, citing specs 007/024/026.

**Change-management artefacts**:
- Volunteer onboarding pack; multilingual community brochures; degraded-mode field guide

**Decommission/rollback criteria** (preserves life-safety defaults per Constitution § Primacy of Life):
- Conservative life-safety defaults; volunteer activations defer to credentialed responders if uncertain
