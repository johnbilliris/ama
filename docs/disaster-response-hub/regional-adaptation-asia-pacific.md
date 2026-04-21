# Regional Adaptation: Asia-Pacific

## Decision Context

The capstone brief asks: *"How will the disaster response agent coordination hub adapt to Asia's diverse disaster types (typhoons in Philippines, earthquakes in Japan, floods in Bangladesh), multilingual emergency alerts across regional languages/dialects, varying government response protocols, and strict location data privacy laws?"*

This document maps every extensibility point in the current platform to the three target countries and explains the configuration changes required. No code changes are needed — the architecture was designed for multi-jurisdiction deployment from the outset.

## Architecture Extensibility Summary

| Extensibility Point | Current Configuration | Asia Adaptation Mechanism |
|---|---|---|
| Data sources | Australian agencies (BoM, GA, state SES) | Seed file per country (`data_sources_{country}.json`) |
| Operating frameworks | AIIMS (Australasian) | Framework records per country (`OperatingFramework` model) |
| Incident types | 19 types including bushfire, cyclone, earthquake, flood, tsunami | Already covers typhoon (mapped to `cyclone`), earthquake, flood — no schema change needed |
| Languages | en-AU, zh-Hans, ar, vi, el, it | `SUPPORTED_LANGUAGES` env var + alert template JSON per language |
| Jurisdiction policies | Australian state/territory scoping | `JurisdictionPolicy` records per country/region |
| Azure region | Australia East | Bicep `location` parameter — deploy to Southeast Asia or Japan East |
| Trust tiers | 7-tier model (authoritative govt → derived) | Same tier model applies universally; agencies slot into tiers |
| Agent handoff chains | Australian agency routing | `HandoffChainDefinition` records per country data sources |

---

## Country 1: Philippines — Typhoons

### Disaster Management Framework

The Philippines operates under **Republic Act 10121** (Philippine DRRM Act, 2010), which established the National Disaster Risk Reduction and Management Council (NDRRMC) as the apex coordinating body. The framework uses a four-pillar structure: Disaster Prevention and Mitigation, Disaster Preparedness, Disaster Response, and Disaster Rehabilitation and Recovery.

#### Operating Framework Mapping

| Hub Concept | Philippine Equivalent |
|---|---|
| `OperatingFramework.framework_type` | `"agency_specific"` (NDRRMC is not AIIMS-based) |
| PPRR phases | Maps directly to the four DRRM pillars |
| Incident levels | NDRRMC uses a 5-level alert system (Alert Level 1–5) mapped to `IncidentLevel` 1–3 with thresholds |
| Approval authority | Local → Provincial → Regional → National escalation chain |
| Legislative basis | RA 10121 (DRRM Act 2010), RA 10174 (Calamity Fund) |

#### Authoritative Data Sources

| Agency | Hub Data Source ID | Trust Tier | Signal Categories |
|---|---|---|---|
| PAGASA (Philippine Atmospheric, Geophysical and Astronomical Services Administration) | `pagasa-typhoon-warnings` | Tier 1 | weather, cyclone (typhoon) |
| PAGASA — Flood Forecasting | `pagasa-flood-forecasts` | Tier 1 | hydrology |
| PHIVOLCS (Philippine Institute of Volcanology and Seismology) | `phivolcs-earthquake-alerts` | Tier 1 | geohazard, earthquake |
| PHIVOLCS — Tsunami Warnings | `phivolcs-tsunami-warnings` | Tier 1 | tsunami |
| NDRRMC — Situation Reports | `ndrrmc-sitreps` | Tier 1 | multi-hazard |
| OCD (Office of Civil Defense) | `ocd-regional-reports` | Tier 2 | field_reports |
| DPWH (Dept. of Public Works and Highways) | `dpwh-infrastructure` | Tier 2 | infrastructure |
| DOH (Dept. of Health) | `doh-health-emergency` | Tier 2 | health |
| Philippine Red Cross | `prc-community-reports` | Tier 5 | community_report |
| Rappler / Twitter-PH | `social-ph` | Tier 6 | social_report |

Sample seed file: [`data_sources_philippines.json`](../../packages/domain/src/domain/seed/data_sources_philippines.json)

#### Typhoon-Specific Configuration

PAGASA uses a Public Storm Warning Signal (PSWS) system with 5 levels:
- **PSWS #1**: Winds 30–60 km/h within 36 hours
- **PSWS #2**: Winds 61–120 km/h within 24 hours
- **PSWS #3**: Winds 121–170 km/h within 18 hours
- **PSWS #4**: Winds 171–220 km/h within 12 hours
- **PSWS #5**: Winds >220 km/h within 12 hours

These map to the hub's `severity` levels: PSWS 1–2 → `watch`, PSWS 3 → `warning`, PSWS 4–5 → `emergency`.

### Languages

| Code | Language | Coverage |
|---|---|---|
| `fil` | Filipino (Tagalog-based) | National language, primary alert language |
| `en-PH` | English (Philippine) | Official language, government/institutional |
| `ceb` | Cebuano | Visayas and Mindanao regions |
| `ilo` | Ilocano | Northern Luzon |

Minimum viable deployment: `fil` and `en-PH`. Template file: [`data/alert-templates/fil.json`](../../data/alert-templates/fil.json).

### Privacy Framework

| Regulation | Hub Mapping |
|---|---|
| **Data Privacy Act of 2012 (RA 10173)** | `JurisdictionPolicy.data_residency_region` — no mandatory in-country hosting but National Privacy Commission (NPC) must approve cross-border transfers |
| Location precision | `allowed_location_precision_meters` = 500 (barangay-level, not household) |
| Consent | Emergency processing exemption under RA 10173 §13(e) — vital interests of data subject |
| Cross-agency sharing | Permitted under DRRM Act for emergency response; `cross_agency_sharing_rules` = `["ndrrmc_authorized", "ocd_regional"]` |

---

## Country 2: Japan — Earthquakes

### Disaster Management Framework

Japan operates under the **Basic Act on Disaster Management (1961, amended)**, with the Central Disaster Management Council chaired by the Prime Minister. The Fire and Disaster Management Agency (FDMA) under the Ministry of Internal Affairs and Communications coordinates operational response. Prefectural and municipal governments are the primary responders.

#### Operating Framework Mapping

| Hub Concept | Japanese Equivalent |
|---|---|
| `OperatingFramework.framework_type` | `"jurisdictional_policy"` (national law + prefectural plans) |
| PPRR phases | Maps to Japan's 3-phase model: Prevention (予防), Emergency Response (応急対策), Recovery/Reconstruction (復旧・復興) |
| Incident levels | Disaster Countermeasures HQ (local) → Prefectural HQ → Emergency Disaster Countermeasures HQ (national) |
| Approval authority | Municipal Mayor → Prefectural Governor → Prime Minister |
| Legislative basis | Basic Act on Disaster Management (災害対策基本法, 1961) |

#### Authoritative Data Sources

| Agency | Hub Data Source ID | Trust Tier | Signal Categories |
|---|---|---|---|
| JMA (Japan Meteorological Agency) — Earthquake Early Warning | `jma-eew` | Tier 1 | geohazard, earthquake |
| JMA — Tsunami Warnings | `jma-tsunami-warnings` | Tier 1 | tsunami |
| JMA — Weather Warnings | `jma-weather-warnings` | Tier 1 | weather |
| JMA — Volcanic Warnings | `jma-volcanic-warnings` | Tier 1 | geohazard |
| NIED (National Research Institute for Earth Science and Disaster Resilience) | `nied-seismic-data` | Tier 1 | geohazard |
| GSI (Geospatial Information Authority) | `gsi-crustal-deformation` | Tier 2 | geohazard |
| FDMA — Fire and Disaster Management Agency | `fdma-sitreps` | Tier 1 | multi-hazard |
| Prefectural Disaster Management HQs | `pref-{code}-dmhq` | Tier 2 | field_reports |
| J-ALERT (national alert system) | `j-alert-broadcasts` | Tier 1 | multi-hazard |
| NHK Emergency Broadcasts | `nhk-emergency` | Tier 2 | community_report |

Sample seed file: [`data_sources_japan.json`](../../packages/domain/src/domain/seed/data_sources_japan.json)

#### Earthquake-Specific Configuration

JMA uses the **Shindo scale** (震度, seismic intensity 0–7, with 5-lower/5-upper and 6-lower/6-upper subdivisions). The Earthquake Early Warning (EEW) system provides seconds of advance notice.

| Shindo Level | Hub Severity | Agent Behaviour |
|---|---|---|
| 0–3 | `advisory` | Monitoring agent logs; no escalation |
| 4 | `watch` | Risk assessment triggered |
| 5-lower / 5-upper | `warning` | Evacuation agent activated; resource allocation begins |
| 6-lower and above | `emergency` | Full multi-agent coordination; all agents activated |

EEW signals carry a `lead_time_seconds` field in the signal payload. The hub's ingestion pipeline normalises this into the `freshnessScore` calculation.

### Languages

| Code | Language | Coverage |
|---|---|---|
| `ja` | Japanese | National language, all official alerts |
| `en-JP` | English (Japan) | Foreign resident population (~3 million) |
| `zh-Hans` | Chinese Simplified | Largest foreign community |
| `ko` | Korean | Second-largest foreign community |
| `pt-BR` | Portuguese (Brazilian) | Third-largest foreign community (Nikkei) |

Minimum viable deployment: `ja` and `en-JP`. Template file: [`data/alert-templates/ja.json`](../../data/alert-templates/ja.json).

### Privacy Framework

| Regulation | Hub Mapping |
|---|---|
| **APPI (Act on Protection of Personal Information, amended 2022)** | `JurisdictionPolicy.data_residency_region` = `"japan-east"` — PPC (Personal Information Protection Commission) requires data to stay within Japan or be transferred to countries with equivalent protection |
| Location precision | `allowed_location_precision_meters` = 250 (city-block level; Japan has strict address privacy norms) |
| Consent | Emergency exception under APPI §27(1)(ii) — protection of life, body, or property |
| Cross-agency sharing | Coordinated through Central Disaster Management Council; `cross_agency_sharing_rules` = `["cdmc_authorized", "prefectural_dmhq"]` |

---

## Country 3: Bangladesh — Floods

### Disaster Management Framework

Bangladesh operates under the **Disaster Management Act 2012**, with the Ministry of Disaster Management and Relief (MoDMR) as the lead ministry. The Department of Disaster Management (DDM) serves as the operational arm. The Standing Orders on Disaster (SOD, 2019) define roles for 46 ministries/agencies.

#### Operating Framework Mapping

| Hub Concept | Bangladesh Equivalent |
|---|---|
| `OperatingFramework.framework_type` | `"agency_specific"` (SOD-defined coordination) |
| PPRR phases | Maps to Bangladesh's 5-phase model: Prevention, Mitigation, Preparedness, Response, Recovery |
| Incident levels | Union → Upazila → District → Division → National |
| Approval authority | Union Disaster Management Committee → Upazila → District → National DMC chaired by Prime Minister |
| Legislative basis | Disaster Management Act 2012, Standing Orders on Disaster (SOD, 2019) |

#### Authoritative Data Sources

| Agency | Hub Data Source ID | Trust Tier | Signal Categories |
|---|---|---|---|
| BMD (Bangladesh Meteorological Department) — Cyclone Warnings | `bmd-cyclone-warnings` | Tier 1 | weather |
| BMD — Weather Forecasts | `bmd-weather-forecasts` | Tier 1 | weather |
| FFWC (Flood Forecasting and Warning Centre) | `ffwc-flood-forecasts` | Tier 1 | hydrology |
| BWDB (Bangladesh Water Development Board) — River Gauges | `bwdb-river-gauges` | Tier 1 | hydrology |
| DDM (Department of Disaster Management) — Situation Reports | `ddm-sitreps` | Tier 1 | multi-hazard |
| SPARRSO (Space Research and Remote Sensing Organization) | `sparrso-satellite` | Tier 3 | infrastructure |
| CPP (Cyclone Preparedness Programme) — Community Volunteers | `cpp-field-reports` | Tier 4 | field_reports |
| BDRCS (Bangladesh Red Crescent Society) | `bdrcs-community` | Tier 5 | community_report |
| DAE (Department of Agricultural Extension) — Crop Damage | `dae-crop-damage` | Tier 2 | environment |
| Social media (Bangla) | `social-bd` | Tier 6 | social_report |

Sample seed file: [`data_sources_bangladesh.json`](../../packages/domain/src/domain/seed/data_sources_bangladesh.json)

#### Flood-Specific Configuration

FFWC issues flood forecasts using a **Danger Level** system for major rivers:
- **Normal**: Water level below danger level
- **Near Danger**: Within 0.5m of danger level
- **Above Danger**: Exceeds danger level
- **Severe**: Exceeds danger level by >1m (record-level flooding)

| FFWC Level | Hub Severity | Agent Behaviour |
|---|---|---|
| Normal | — | Monitoring agent logs only |
| Near Danger | `watch` | Risk assessment triggered; resource pre-positioning |
| Above Danger | `warning` | Evacuation agent activated; CPP volunteer mobilisation |
| Severe | `emergency` | Full coordination; national-level escalation |

Bangladesh's flood cycle is seasonal (June–October monsoon). The FFWC provides 1–5 day forecasts for 53 major river stations, enabling the hub's `spread_prediction` assessment type to generate meaningful 24-hour advance evacuation recommendations.

### Languages

| Code | Language | Coverage |
|---|---|---|
| `bn` | Bengali (Bangla) | National language, >98% population |
| `en-BD` | English (Bangladesh) | Government/institutional, NGO coordination |
| `ctg` | Chittagonian | Southeastern coastal population (cyclone-prone areas) |

Minimum viable deployment: `bn` and `en-BD`. Template file: [`data/alert-templates/bn.json`](../../data/alert-templates/bn.json).

### Privacy Framework

| Regulation | Hub Mapping |
|---|---|
| **Digital Security Act 2018** + **ICT Act 2006** | No comprehensive data protection law as of 2025; the Cyber Security Act 2023 governs digital systems. Hub enforces its own baseline. |
| Data residency | No mandatory local hosting requirement; `JurisdictionPolicy.data_residency_region` = `"southeast-asia"` (nearest Azure: Southeast Asia, Singapore) |
| Location precision | `allowed_location_precision_meters` = 200 (union-level, not household) |
| Consent | No formal consent framework for emergency data; hub applies the constitutional Life Safety First principle |
| Cross-agency sharing | Governed by SOD roles; `cross_agency_sharing_rules` = `["ddm_authorized", "district_dmc"]` |

---

## Infrastructure: Multi-Region Deployment

The Bicep templates in `infra/` parameterise `location` and `environmentName`. Deploying to Asia-Pacific requires only parameter overrides:

| Country | Primary Azure Region | DR Region | Rationale |
|---|---|---|---|
| Philippines | Southeast Asia (Singapore) | East Asia (Hong Kong) | Nearest region; Philippines has no Azure region; Singapore meets ASEAN data norms |
| Japan | Japan East (Tokyo) | Japan West (Osaka) | In-country pair; meets APPI data residency |
| Bangladesh | Central India (Pune) | South India (Chennai) | Nearest regions; no Southeast Asia data residency mandate |
| Australia (current) | Australia East (Sydney) | Australia Southeast (Melbourne) | Current deployment |

Azure OpenAI availability varies by region. Japan East supports GPT-4o. Southeast Asia may require traffic routing to a supported region with a Cosmos DB global distribution for state. The `LLMClient` in `apps/agents/common/llm_client.py` already supports configurable endpoints per deployment purpose.

### Sample Parameter Override (Japan)

```json
{
  "environmentName": { "value": "japan-prod" },
  "location": { "value": "japaneast" },
  "tags": {
    "value": {
      "project": "disaster-response-hub",
      "region": "japan",
      "data-residency": "japan-domestic"
    }
  }
}
```

---

## Operating Framework Seed Data

Each country requires `OperatingFramework` records that slot into the existing model without schema changes. Sample entries are provided in the seed files alongside data sources.

### Philippines — NDRRMC Framework

```json
{
  "framework_id": "ndrrmc-drrm-2010",
  "name": "National DRRM Framework",
  "abbreviation": "NDRRMC-DRRM",
  "framework_type": "agency_specific",
  "applicable_jurisdiction_ids": ["ph-national", "ph-ncr", "ph-region-3", "ph-region-4a"],
  "pprr_phases": ["prevention", "preparedness", "response", "recovery"],
  "hazard_types": ["cyclone", "flood", "earthquake", "tsunami", "landslide"],
  "principles": ["life_safety_first", "whole_of_nation", "community_based_drrm", "multi_hazard"],
  "control_model": "NDRRMC national coordination with LGU-first response",
  "legislative_basis": "Republic Act 10121 (DRRM Act 2010)",
  "status": "active"
}
```

### Japan — Basic Disaster Management Act

```json
{
  "framework_id": "jp-basic-disaster-act-1961",
  "name": "Basic Act on Disaster Management Framework",
  "abbreviation": "BADM",
  "framework_type": "jurisdictional_policy",
  "applicable_jurisdiction_ids": ["jp-national", "jp-tokyo", "jp-osaka", "jp-kanagawa"],
  "pprr_phases": ["prevention", "response", "recovery"],
  "hazard_types": ["earthquake", "tsunami", "cyclone", "flood", "storm"],
  "principles": ["life_safety_first", "prefectural_autonomy", "mutual_aid", "national_coordination"],
  "control_model": "Municipal-first with prefectural and national escalation",
  "legislative_basis": "Basic Act on Disaster Management (災害対策基本法, 1961)",
  "status": "active"
}
```

### Bangladesh — Standing Orders on Disaster

```json
{
  "framework_id": "bd-sod-2019",
  "name": "Standing Orders on Disaster",
  "abbreviation": "SOD",
  "framework_type": "agency_specific",
  "applicable_jurisdiction_ids": ["bd-national", "bd-dhaka", "bd-chittagong", "bd-sylhet"],
  "pprr_phases": ["prevention", "preparedness", "response", "recovery"],
  "hazard_types": ["flood", "cyclone", "earthquake", "landslide", "storm"],
  "principles": ["life_safety_first", "community_resilience", "multi_agency_coordination"],
  "control_model": "DDM national coordination with District DMC as primary responder",
  "legislative_basis": "Disaster Management Act 2012, Standing Orders on Disaster (SOD, 2019)",
  "status": "active"
}
```

---

## Jurisdiction Policy Examples

### Philippines

```json
{
  "policy_set_id": "ph-national-drrm",
  "data_residency_region": "southeastasia",
  "allowed_location_precision_meters": 500,
  "language_requirements": ["fil", "en-PH"],
  "cross_agency_sharing_rules": ["ndrrmc_authorized", "ocd_regional"]
}
```

### Japan

```json
{
  "policy_set_id": "jp-national-disaster",
  "data_residency_region": "japaneast",
  "allowed_location_precision_meters": 250,
  "language_requirements": ["ja", "en-JP"],
  "cross_agency_sharing_rules": ["cdmc_authorized", "prefectural_dmhq"]
}
```

### Bangladesh

```json
{
  "policy_set_id": "bd-national-disaster",
  "data_residency_region": "centralindia",
  "allowed_location_precision_meters": 200,
  "language_requirements": ["bn", "en-BD"],
  "cross_agency_sharing_rules": ["ddm_authorized", "district_dmc"]
}
```

---

## Adaptation Checklist

For each new country deployment, the following steps are required:

1. **Seed data**: Create `data_sources_{country}.json` with local authoritative agencies mapped to trust tiers
2. **Operating frameworks**: Add `OperatingFramework` records for the country's disaster management legislation
3. **Jurisdiction policies**: Configure data residency, location precision, language, and sharing rules
4. **Alert templates**: Create `data/alert-templates/{language_code}.json` with country-appropriate emergency contacts and action items
5. **Language config**: Add language codes to `SUPPORTED_LANGUAGES` environment variable
6. **Infrastructure**: Create `main.parameters.{country}.json` targeting the appropriate Azure region pair
7. **Handoff chains**: Define `HandoffChainDefinition` entries routing country-specific data sources to agents
8. **Validation**: Run the existing evaluation framework (baseline-metrics.md) with country-specific tabletop exercises

No changes to domain models, agent code, API routes, or schema definitions are required.
