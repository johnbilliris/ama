# Test-Data Manifest (Spec 039)

> **Auto-generated** from `docs/test-data/manifest.json` by
> `tools/lint/render_test_data_manifest_md.py`.
> Do not edit by hand — re-run the renderer instead.

This document is the human-readable view of the canonical machine-readable
manifest enumerating every test-data artefact in the AMA repository.
Validation lives in `tools/lint/check_test_data_manifest.py` and is wired
into the `quality` job of `.github/workflows/ci.yml` (CL-7).

Cross-references:

- Corpus inventory: [`docs/corpus/MANIFEST.md`](../corpus/MANIFEST.md)
- Indexing licence inventory: [`docs/corpus/INDEXING-LICENCE-INVENTORY.md`](../corpus/INDEXING-LICENCE-INVENTORY.md)
- Schema: [`manifest.schema.json`](./manifest.schema.json)
- Indigenous placeholder denylist:
  [`tools/lint/data/indigenous_denylist.txt`](../../tools/lint/data/indigenous_denylist.txt)


## Summary

- Schema version: `1.0.0`
- Total entries: **136**
- `alert-template`: 8
- `generator`: 14
- `mock`: 42
- `simulator-feed-shape`: 13
- `synthetic`: 59

## Category: `alert-template`

| id | path / source_shape | domain_group | personas | pspf | licence | cultural_review |
|---|---|---|---|---|---|---|
| `packages-domain-src-domain-seed-alert-templates-ar-json` | `packages/domain/src/domain/seed/alert-templates/ar.json` | `cross-sector` | community-ngos, public-information-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-alert-templates-auslan-placeholder-json` | `packages/domain/src/domain/seed/alert-templates/auslan-placeholder.json` | `cross-sector` | community-ngos, public-information-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-alert-templates-el-json` | `packages/domain/src/domain/seed/alert-templates/el.json` | `cross-sector` | community-ngos, public-information-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-alert-templates-en-au-json` | `packages/domain/src/domain/seed/alert-templates/en-AU.json` | `cross-sector` | public-information-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-alert-templates-indigenous-placeholder-json` | `packages/domain/src/domain/seed/alert-templates/indigenous-placeholder.json` | `cross-sector` | community-ngos, public-information-officer | `OFFICIAL` | `CC-BY-4.0` | **YES** |
| `packages-domain-src-domain-seed-alert-templates-it-json` | `packages/domain/src/domain/seed/alert-templates/it.json` | `cross-sector` | community-ngos, public-information-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-alert-templates-vi-json` | `packages/domain/src/domain/seed/alert-templates/vi.json` | `cross-sector` | community-ngos, public-information-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-alert-templates-zh-hans-json` | `packages/domain/src/domain/seed/alert-templates/zh-Hans.json` | `cross-sector` | community-ngos, public-information-officer | `OFFICIAL` | `CC-BY-4.0` | no |

## Category: `generator`

| id | path / source_shape | domain_group | personas | pspf | licence | cultural_review |
|---|---|---|---|---|---|---|
| `scripts-generators-audit-entries-py` | `scripts/generators/audit_entries.py` | `operational` | incident-commander, planning-officer | `OFFICIAL` | `proprietary-fictitious-internal` | no |
| `scripts-generators-coordination-tasks-py` | `scripts/generators/coordination_tasks.py` | `operational` | incident-commander, planning-officer | `OFFICIAL` | `proprietary-fictitious-internal` | no |
| `scripts-generators-evacuee-registrations-py` | `scripts/generators/evacuee_registrations.py` | `operational` | incident-commander, planning-officer | `OFFICIAL` | `proprietary-fictitious-internal` | no |
| `scripts-generators-hospital-capacity-py` | `scripts/generators/hospital_capacity.py` | `operational` | incident-commander, planning-officer | `OFFICIAL` | `proprietary-fictitious-internal` | no |
| `scripts-generators-incidents-py` | `scripts/generators/incidents.py` | `operational` | incident-commander, planning-officer | `OFFICIAL` | `proprietary-fictitious-internal` | no |
| `scripts-generators-missing-persons-py` | `scripts/generators/missing_persons.py` | `operational` | incident-commander, planning-officer | `OFFICIAL` | `proprietary-fictitious-internal` | no |
| `scripts-generators-public-alerts-py` | `scripts/generators/public_alerts.py` | `operational` | incident-commander, planning-officer | `OFFICIAL` | `proprietary-fictitious-internal` | no |
| `scripts-generators-risk-register-py` | `scripts/generators/risk_register.py` | `operational` | incident-commander, planning-officer | `OFFICIAL` | `proprietary-fictitious-internal` | no |
| `scripts-generators-signals-py` | `scripts/generators/signals.py` | `operational` | incident-commander, planning-officer | `OFFICIAL` | `proprietary-fictitious-internal` | no |
| `scripts-generators-transport-assets-py` | `scripts/generators/transport_assets.py` | `operational` | incident-commander, planning-officer | `OFFICIAL` | `proprietary-fictitious-internal` | no |
| `scripts-generators-triage-records-py` | `scripts/generators/triage_records.py` | `operational` | incident-commander, planning-officer | `OFFICIAL` | `proprietary-fictitious-internal` | no |
| `scripts-generators-utility-outages-py` | `scripts/generators/utility_outages.py` | `operational` | incident-commander, planning-officer | `OFFICIAL` | `proprietary-fictitious-internal` | no |
| `scripts-generators-volunteer-registrations-py` | `scripts/generators/volunteer_registrations.py` | `operational` | incident-commander, planning-officer | `OFFICIAL` | `proprietary-fictitious-internal` | no |
| `scripts-generators-vulnerable-categories-py` | `scripts/generators/vulnerable_categories.py` | `operational` | incident-commander, planning-officer | `OFFICIAL` | `proprietary-fictitious-internal` | no |

## Category: `mock`

| id | path / source_shape | domain_group | personas | pspf | licence | cultural_review |
|---|---|---|---|---|---|---|
| `apps-api-app-services-simulation-data-jurisdiction-locale-priority-json` | `apps/api/app/services/simulation/data/jurisdiction_locale_priority.json` | `operational` | incident-commander, operations-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `apps-api-app-services-simulation-data-jurisdiction-routes-json` | `apps/api/app/services/simulation/data/jurisdiction_routes.json` | `operational` | incident-commander, operations-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `apps-api-app-services-simulation-data-sim-locale-table-json` | `apps/api/app/services/simulation/data/sim_locale_table.json` | `operational` | incident-commander, operations-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `apps-api-app-services-simulation-data-speech-prerender-catalog-json` | `apps/api/app/services/simulation/data/speech_prerender_catalog.json` | `operational` | incident-commander, operations-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `apps-api-app-services-simulation-feeds-simulator-feed-schema-json` | `apps/api/app/services/simulation/feeds/simulator_feed.schema.json` | `operational` | incident-commander, operations-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `apps-api-app-services-simulation-feeds-source-shapes-json` | `apps/api/app/services/simulation/feeds/source_shapes.json` | `operational` | incident-commander, operations-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `data-alert-templates-ar-json` | `data/alert-templates/ar.json` | `cross-sector` | community-ngos, public-information-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `data-alert-templates-el-json` | `data/alert-templates/el.json` | `cross-sector` | community-ngos, public-information-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `data-alert-templates-en-au-json` | `data/alert-templates/en-AU.json` | `cross-sector` | public-information-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `data-alert-templates-it-json` | `data/alert-templates/it.json` | `cross-sector` | community-ngos, public-information-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `data-alert-templates-vi-json` | `data/alert-templates/vi.json` | `cross-sector` | community-ngos, public-information-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `data-alert-templates-zh-hans-json` | `data/alert-templates/zh-Hans.json` | `cross-sector` | community-ngos, public-information-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `data-governance-foundry-carveout-registry-json` | `data/governance/foundry_carveout_registry.json` | `commonwealth` | executive-leader, nema | `OFFICIAL` | `CC-BY-4.0` | no |
| `data-population-sample-population-json` | `data/population/sample-population.json` | `cross-sector` | planning-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `data-resource-inventories-sample-inventory-json` | `data/resource-inventories/sample-inventory.json` | `operational` | logistics-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `data-road-networks-far-north-qld-sample-json` | `data/road-networks/far-north-qld-sample.json` | `police` | operations-officer, transport | `OFFICIAL` | `CC-BY-4.0` | no |
| `fixtures-sim-replays-ambulance-cad-vic-ndjson` | `fixtures/sim_replays/ambulance_cad_vic.ndjson` | `operational` | incident-commander | `OFFICIAL` | `CC-BY-4.0` | no |
| `fixtures-sim-replays-bom-cyclone-track-qld-ndjson` | `fixtures/sim_replays/bom_cyclone_track_qld.ndjson` | `operational` | incident-commander | `OFFICIAL` | `CC-BY-4.0` | no |
| `fixtures-sim-replays-bom-fire-weather-fdi-vic-ndjson` | `fixtures/sim_replays/bom_fire_weather_fdi_vic.ndjson` | `operational` | incident-commander | `OFFICIAL` | `CC-BY-4.0` | no |
| `fixtures-sim-replays-bom-flood-gauge-nsw-ndjson` | `fixtures/sim_replays/bom_flood_gauge_nsw.ndjson` | `operational` | incident-commander | `OFFICIAL` | `CC-BY-4.0` | no |
| `fixtures-sim-replays-bom-severe-weather-warning-nsw-ndjson` | `fixtures/sim_replays/bom_severe_weather_warning_nsw.ndjson` | `operational` | incident-commander | `OFFICIAL` | `CC-BY-4.0` | no |
| `fixtures-sim-replays-demo-ambulance-v1-ndjson` | `fixtures/sim_replays/demo_ambulance_v1.ndjson` | `ambulance` | av, incident-commander, nsw-ambulance, rfds, saas | `OFFICIAL` | `CC-BY-4.0` | no |
| `fixtures-sim-replays-demo-commonwealth-v1-ndjson` | `fixtures/sim_replays/demo_commonwealth_v1.ndjson` | `commonwealth` | adf, arc, bom-national, ga-national, nema | `OFFICIAL` | `CC-BY-4.0` | no |
| `fixtures-sim-replays-demo-cross-sector-v1-ndjson` | `fixtures/sim_replays/demo_cross_sector_v1.ndjson` | `cross-sector` | community-ngos, local-government, state-government, transport, utility | `OFFICIAL` | `CC-BY-4.0` | no |
| `fixtures-sim-replays-demo-fire-v1-ndjson` | `fixtures/sim_replays/demo_fire_v1.ndjson` | `fire` | cfa-vic, frnsw, incident-commander, nsw-rfs, operations-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `fixtures-sim-replays-demo-marine-aviation-v1-ndjson` | `fixtures/sim_replays/demo_marine_aviation_v1.ndjson` | `marine-aviation` | abf, asa, mrnsw, rfds, surf-lifesaving | `OFFICIAL` | `CC-BY-4.0` | no |
| `fixtures-sim-replays-demo-operational-v1-ndjson` | `fixtures/sim_replays/demo_operational_v1.ndjson` | `operational` | executive-leader, incident-commander, logistics-officer, operations-officer, planning-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `fixtures-sim-replays-demo-police-v1-ndjson` | `fixtures/sim_replays/demo_police_v1.ndjson` | `police` | afp-commonwealth, incident-commander, nswpf, operations-officer, vicpol | `OFFICIAL` | `CC-BY-4.0` | no |
| `fixtures-sim-replays-demo-ses-v1-ndjson` | `fixtures/sim_replays/demo_ses_v1.ndjson` | `ses` | logistics-officer, operations-officer, ses-nsw, ses-qld, ses-vic | `OFFICIAL` | `CC-BY-4.0` | no |
| `fixtures-sim-replays-epa-pm25-vic-ndjson` | `fixtures/sim_replays/epa_pm25_vic.ndjson` | `operational` | incident-commander | `OFFICIAL` | `CC-BY-4.0` | no |
| `fixtures-sim-replays-ga-earthquake-event-wa-ndjson` | `fixtures/sim_replays/ga_earthquake_event_wa.ndjson` | `operational` | incident-commander | `OFFICIAL` | `CC-BY-4.0` | no |
| `fixtures-sim-replays-ga-tsunami-threat-nsw-ndjson` | `fixtures/sim_replays/ga_tsunami_threat_nsw.ndjson` | `operational` | incident-commander | `OFFICIAL` | `CC-BY-4.0` | no |
| `fixtures-sim-replays-sensor-telemetry-nt-ndjson` | `fixtures/sim_replays/sensor_telemetry_nt.ndjson` | `operational` | incident-commander | `OFFICIAL` | `CC-BY-4.0` | no |
| `fixtures-sim-replays-social-chatter-au-ndjson` | `fixtures/sim_replays/social_chatter_au.ndjson` | `operational` | incident-commander | `OFFICIAL` | `CC-BY-4.0` | no |
| `fixtures-sim-replays-synthetic-fallback-au-ndjson` | `fixtures/sim_replays/synthetic_fallback_au.ndjson` | `operational` | incident-commander | `OFFICIAL` | `CC-BY-4.0` | no |
| `fixtures-sim-replays-traffic-road-closure-nsw-ndjson` | `fixtures/sim_replays/traffic_road_closure_nsw.ndjson` | `operational` | incident-commander | `OFFICIAL` | `CC-BY-4.0` | no |
| `fixtures-sim-replays-utility-outage-qld-ndjson` | `fixtures/sim_replays/utility_outage_qld.ndjson` | `operational` | incident-commander | `OFFICIAL` | `CC-BY-4.0` | no |
| `tests-fixtures-golden-set-v1-json` | `tests/fixtures/golden-set-v1.json` | `cross-sector` | observer-auditor | `OFFICIAL` | `CC-BY-4.0` | no |
| `tests-fixtures-jurisdiction-boundaries-au-minimal-wkt` | `tests/fixtures/jurisdiction_boundaries/au_minimal.wkt` | `cross-sector` | observer-auditor, planning-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `tests-fixtures-jurisdiction-boundaries-vic-minimal-geojson` | `tests/fixtures/jurisdiction_boundaries/vic_minimal.geojson` | `cross-sector` | observer-auditor, planning-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `tests-fixtures-llm-deployment-provenance-json` | `tests/fixtures/llm_deployment_provenance.json` | `cross-sector` | observer-auditor | `OFFICIAL` | `CC-BY-4.0` | no |
| `tools-lint-data-indigenous-denylist-txt` | `tools/lint/data/indigenous_denylist.txt` | `cross-sector` | observer-auditor, public-information-officer | `OFFICIAL` | `proprietary-fictitious-internal` | **YES** |

## Category: `simulator-feed-shape`

| id | path / source_shape | domain_group | personas | pspf | licence | cultural_review |
|---|---|---|---|---|---|---|
| `ambulance-cad-v1-shape` | `ambulance.cad.v1` | `ambulance` | incident-commander, operations-officer, nsw-ambulance, qas, av | `OFFICIAL` | `proprietary-fictitious-internal` | no |
| `bom-cyclone-track-v1-shape` | `bom.cyclone_track.v1` | `commonwealth` | incident-commander, operations-officer | `OFFICIAL` | `proprietary-fictitious-internal` | no |
| `bom-fire-weather-fdi-v1-shape` | `bom.fire_weather_fdi.v1` | `fire` | incident-commander, operations-officer, nsw-rfs, cfa-vic | `OFFICIAL` | `proprietary-fictitious-internal` | no |
| `bom-flood-gauge-v1-shape` | `bom.flood_gauge.v1` | `commonwealth` | incident-commander, operations-officer | `OFFICIAL` | `proprietary-fictitious-internal` | no |
| `bom-severe-weather-warning-v1-shape` | `bom.severe_weather_warning.v1` | `commonwealth` | incident-commander, operations-officer | `OFFICIAL` | `proprietary-fictitious-internal` | no |
| `epa-pm25-v1-shape` | `epa.pm25.v1` | `commonwealth` | incident-commander, operations-officer | `OFFICIAL` | `proprietary-fictitious-internal` | no |
| `ga-earthquake-event-v1-shape` | `ga.earthquake_event.v1` | `commonwealth` | incident-commander, operations-officer | `OFFICIAL` | `proprietary-fictitious-internal` | no |
| `ga-tsunami-threat-v1-shape` | `ga.tsunami_threat.v1` | `marine-aviation` | incident-commander, operations-officer, mrnsw, surf-lifesaving | `OFFICIAL` | `proprietary-fictitious-internal` | no |
| `sensor-telemetry-v1-shape` | `sensor.telemetry.v1` | `operational` | incident-commander, operations-officer | `OFFICIAL` | `proprietary-fictitious-internal` | no |
| `social-chatter-v1-shape` | `social.chatter.v1` | `cross-sector` | incident-commander, operations-officer | `OFFICIAL` | `proprietary-fictitious-internal` | no |
| `synthetic-fallback-v1-shape` | `synthetic.fallback.v1` | `operational` | incident-commander, operations-officer | `OFFICIAL` | `proprietary-fictitious-internal` | no |
| `traffic-road-closure-v1-shape` | `traffic.road_closure.v1` | `police` | incident-commander, operations-officer | `OFFICIAL` | `proprietary-fictitious-internal` | no |
| `utility-outage-v1-shape` | `utility.outage.v1` | `cross-sector` | incident-commander, operations-officer | `OFFICIAL` | `proprietary-fictitious-internal` | no |

## Category: `synthetic`

| id | path / source_shape | domain_group | personas | pspf | licence | cultural_review |
|---|---|---|---|---|---|---|
| `packages-domain-src-domain-seed-aiims-function-map-json` | `packages/domain/src/domain/seed/aiims_function_map.json` | `operational` | incident-commander, planning-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-coordination-tasks-australia-json` | `packages/domain/src/domain/seed/coordination_tasks_australia.json` | `operational` | incident-commander, planning-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-data-sources-australia-json` | `packages/domain/src/domain/seed/data_sources_australia.json` | `operational` | incident-commander, planning-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-disasters-australia-json` | `packages/domain/src/domain/seed/disasters_australia.json` | `operational` | incident-commander, planning-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-evacuation-routes-act-json` | `packages/domain/src/domain/seed/evacuation-routes/act.json` | `ses` | act-esa, act-policing, operations-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-evacuation-routes-nsw-json` | `packages/domain/src/domain/seed/evacuation-routes/nsw.json` | `ses` | nsw-rfs, nswpf, operations-officer, ses-nsw | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-evacuation-routes-nt-json` | `packages/domain/src/domain/seed/evacuation-routes/nt.json` | `ses` | ntes, ntpf, operations-officer | `OFFICIAL` | `CC-BY-4.0` | **YES** |
| `packages-domain-src-domain-seed-evacuation-routes-qld-json` | `packages/domain/src/domain/seed/evacuation-routes/qld.json` | `ses` | operations-officer, qfd, qps, ses-qld | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-evacuation-routes-sa-json` | `packages/domain/src/domain/seed/evacuation-routes/sa.json` | `ses` | operations-officer, sacfs, sapol, ses-sa | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-evacuation-routes-tas-json` | `packages/domain/src/domain/seed/evacuation-routes/tas.json` | `ses` | operations-officer, ses-tas, taspol, tfs | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-evacuation-routes-vic-json` | `packages/domain/src/domain/seed/evacuation-routes/vic.json` | `ses` | cfa-vic, operations-officer, ses-vic, vicpol | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-evacuation-routes-wa-json` | `packages/domain/src/domain/seed/evacuation-routes/wa.json` | `ses` | dfes-wa, operations-officer, wapol | `OFFICIAL` | `CC-BY-4.0` | **YES** |
| `packages-domain-src-domain-seed-framework-assignments-australia-json` | `packages/domain/src/domain/seed/framework_assignments_australia.json` | `operational` | incident-commander, planning-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-frameworks-australia-json` | `packages/domain/src/domain/seed/frameworks_australia.json` | `operational` | incident-commander, planning-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-hazard-scenarios-australia-json` | `packages/domain/src/domain/seed/hazard_scenarios_australia.json` | `operational` | incident-commander, planning-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-hospital-capability-act-json` | `packages/domain/src/domain/seed/hospital-capability/act.json` | `ambulance` | act-esa, act-policing, logistics-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-hospital-capability-nsw-json` | `packages/domain/src/domain/seed/hospital-capability/nsw.json` | `ambulance` | logistics-officer, nsw-rfs, nswpf, ses-nsw | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-hospital-capability-nt-json` | `packages/domain/src/domain/seed/hospital-capability/nt.json` | `ambulance` | logistics-officer, ntes, ntpf | `OFFICIAL` | `CC-BY-4.0` | **YES** |
| `packages-domain-src-domain-seed-hospital-capability-qld-json` | `packages/domain/src/domain/seed/hospital-capability/qld.json` | `ambulance` | logistics-officer, qfd, qps, ses-qld | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-hospital-capability-sa-json` | `packages/domain/src/domain/seed/hospital-capability/sa.json` | `ambulance` | logistics-officer, sacfs, sapol, ses-sa | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-hospital-capability-tas-json` | `packages/domain/src/domain/seed/hospital-capability/tas.json` | `ambulance` | logistics-officer, ses-tas, taspol, tfs | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-hospital-capability-vic-json` | `packages/domain/src/domain/seed/hospital-capability/vic.json` | `ambulance` | cfa-vic, logistics-officer, ses-vic, vicpol | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-hospital-capability-wa-json` | `packages/domain/src/domain/seed/hospital-capability/wa.json` | `ambulance` | dfes-wa, logistics-officer, wapol | `OFFICIAL` | `CC-BY-4.0` | **YES** |
| `packages-domain-src-domain-seed-identities-australia-json` | `packages/domain/src/domain/seed/identities_australia.json` | `operational` | incident-commander, planning-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-inter-government-agreements-agreements-australia-json` | `packages/domain/src/domain/seed/inter-government-agreements/agreements_australia.json` | `commonwealth` | executive-leader, nema | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-jurisdiction-policies-australia-json` | `packages/domain/src/domain/seed/jurisdiction_policies_australia.json` | `operational` | incident-commander, planning-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-jurisdictions-australia-json` | `packages/domain/src/domain/seed/jurisdictions_australia.json` | `operational` | incident-commander, planning-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-lemp-memp-templates-templates-australia-json` | `packages/domain/src/domain/seed/lemp-memp-templates/templates_australia.json` | `operational` | local-government, state-government | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-organisations-australia-json` | `packages/domain/src/domain/seed/organisations_australia.json` | `operational` | incident-commander, planning-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-persona-rosters-ambulance-json` | `packages/domain/src/domain/seed/persona-rosters/ambulance.json` | `ambulance` | act-ambulance, at, av, nsw-ambulance, qas, rfds, saas, sja-national, sja-nt, sja-wa | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-persona-rosters-commonwealth-json` | `packages/domain/src/domain/seed/persona-rosters/commonwealth.json` | `commonwealth` | adf, arc, bom-national, ga-national, nema | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-persona-rosters-cross-sector-json` | `packages/domain/src/domain/seed/persona-rosters/cross-sector.json` | `cross-sector` | community-ngos, health, local-government, state-government, territory-government, transport, utility, volunteer | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-persona-rosters-fire-json` | `packages/domain/src/domain/seed/persona-rosters/fire.json` | `fire` | act-fr, act-rfs, bushfires-nt, cfa-vic, dfes-wa, frnsw, frv, nsw-rfs, ntfrs, qfd, sacfs, samfs, tfs | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-persona-rosters-marine-aviation-json` | `packages/domain/src/domain/seed/persona-rosters/marine-aviation.json` | `marine-aviation` | abf, asa, mrnsw, surf-lifesaving | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-persona-rosters-operational-json` | `packages/domain/src/domain/seed/persona-rosters/operational.json` | `operational` | executive-leader, field-coordinator, incident-commander, logistics-officer, observer-auditor, operations-officer, planning-officer, public-information-officer, resilience-planner, risk-manager | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-persona-rosters-police-json` | `packages/domain/src/domain/seed/persona-rosters/police.json` | `police` | act-policing, afp-act, afp-commonwealth, nswpf, ntpf, qps, sapol, taspol, vicpol, wapol | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-persona-rosters-ses-json` | `packages/domain/src/domain/seed/persona-rosters/ses.json` | `ses` | act-esa, ntes, ses-act, ses-nsw, ses-qld, ses-sa, ses-tas, ses-vic | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-recovery-catalogue-built-json` | `packages/domain/src/domain/seed/recovery-catalogue/built.json` | `cross-sector` | executive-leader, resilience-planner | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-recovery-catalogue-economic-json` | `packages/domain/src/domain/seed/recovery-catalogue/economic.json` | `cross-sector` | executive-leader, resilience-planner | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-recovery-catalogue-evaluation-questions-json` | `packages/domain/src/domain/seed/recovery-catalogue/evaluation-questions.json` | `cross-sector` | executive-leader, resilience-planner | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-recovery-catalogue-natural-json` | `packages/domain/src/domain/seed/recovery-catalogue/natural.json` | `cross-sector` | executive-leader, resilience-planner | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-recovery-catalogue-overarching-json` | `packages/domain/src/domain/seed/recovery-catalogue/overarching.json` | `cross-sector` | executive-leader, resilience-planner | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-recovery-catalogue-social-json` | `packages/domain/src/domain/seed/recovery-catalogue/social.json` | `cross-sector` | executive-leader, resilience-planner | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-road-segments-act-json` | `packages/domain/src/domain/seed/road-segments/act.json` | `police` | act-esa, act-policing, operations-officer, transport | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-road-segments-nsw-json` | `packages/domain/src/domain/seed/road-segments/nsw.json` | `police` | nsw-rfs, nswpf, operations-officer, ses-nsw, transport | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-road-segments-nt-json` | `packages/domain/src/domain/seed/road-segments/nt.json` | `police` | ntes, ntpf, operations-officer, transport | `OFFICIAL` | `CC-BY-4.0` | **YES** |
| `packages-domain-src-domain-seed-road-segments-qld-json` | `packages/domain/src/domain/seed/road-segments/qld.json` | `police` | operations-officer, qfd, qps, ses-qld, transport | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-road-segments-sa-json` | `packages/domain/src/domain/seed/road-segments/sa.json` | `police` | operations-officer, sacfs, sapol, ses-sa, transport | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-road-segments-tas-json` | `packages/domain/src/domain/seed/road-segments/tas.json` | `police` | operations-officer, ses-tas, taspol, tfs, transport | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-road-segments-vic-json` | `packages/domain/src/domain/seed/road-segments/vic.json` | `police` | cfa-vic, operations-officer, ses-vic, transport, vicpol | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-road-segments-wa-json` | `packages/domain/src/domain/seed/road-segments/wa.json` | `police` | dfes-wa, operations-officer, transport, wapol | `OFFICIAL` | `CC-BY-4.0` | **YES** |
| `packages-domain-src-domain-seed-scenario-templates-australia-json` | `packages/domain/src/domain/seed/scenario_templates_australia.json` | `operational` | incident-commander, planning-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-seed-record-schema-json` | `packages/domain/src/domain/seed/seed_record.schema.json` | `operational` | incident-commander, planning-officer | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-utility-infrastructure-electricity-json` | `packages/domain/src/domain/seed/utility-infrastructure/electricity.json` | `cross-sector` | logistics-officer, utility | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-utility-infrastructure-gas-json` | `packages/domain/src/domain/seed/utility-infrastructure/gas.json` | `cross-sector` | logistics-officer, utility | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-utility-infrastructure-telecoms-json` | `packages/domain/src/domain/seed/utility-infrastructure/telecoms.json` | `cross-sector` | logistics-officer, utility | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-utility-infrastructure-water-json` | `packages/domain/src/domain/seed/utility-infrastructure/water.json` | `cross-sector` | logistics-officer, utility | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-volunteer-credentials-credentials-australia-json` | `packages/domain/src/domain/seed/volunteer-credentials/credentials_australia.json` | `cross-sector` | community-ngos, volunteer | `OFFICIAL` | `CC-BY-4.0` | no |
| `packages-domain-src-domain-seed-vulnerable-categories-categories-australia-json` | `packages/domain/src/domain/seed/vulnerable-categories/categories_australia.json` | `cross-sector` | resilience-planner | `OFFICIAL` | `CC-BY-4.0` | no |
