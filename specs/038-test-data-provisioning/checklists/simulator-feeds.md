# Simulator Feeds Checklist: Two-Path Rule, Deterministic Replay, Per-Jurisdiction Coverage

**Purpose**: Operational acceptance gate for Path-2 (live-stream / external-feed) data — covering Two-Path Rule isolation, byte-identical deterministic replay (CL-4 canonical NDJSON / SHA-256), and per-jurisdiction + per-domain feed shape coverage.
**Created**: 2026-05-11
**Feature**: [spec.md](../spec.md)
**Scope**: FR-020..FR-027, SC-005, SC-006, SC-007, A-1, A-14, A-16.

## Two-Path Rule: Isolation From Production Code

- [X] CHK001 Zero modules outside `apps/api/app/services/simulation/` and its declared sub-packages import any symbol from the simulator package (FR-024, SC-007, US2 acceptance scenario 4).
- [X] CHK002 A static dependency-graph CI check fails the build if any production module imports from the simulator package (SC-007).
- [X] CHK003 The simulator package exposes zero symbols to dependency-injection registries used by production agents (FR-024, US2 acceptance scenario 4).
- [X] CHK004 Mock resources are unreachable from production code paths and reachable only from test, evaluation, and local-dev configurations (FR-054).
- [X] CHK005 Selecting simulator-on vs simulator-off is a runtime configuration concern; no code-path branching is required to disable the simulator (FR-024, A-14).
- [X] CHK006 No new public HTTP endpoints are introduced by this feature solely for simulator delivery (FR-024, A-14).
- [X] CHK007 No new Azure resources are introduced by this feature solely for simulator delivery (FR-024, A-14, A-11).

## Two-Path Rule: No Real External Endpoints

- [X] CHK008 Zero outbound network calls are made by the simulator to `*.bom.gov.au` during any scenario run (FR-023, SC-006, US2 acceptance scenario 3).
- [X] CHK009 Zero outbound network calls are made by the simulator to `*.ga.gov.au` during any scenario run (FR-023, SC-006).
- [X] CHK010 Zero outbound network calls are made by the simulator to `*.abs.gov.au` during any scenario run (FR-023, SC-006).
- [X] CHK011 Zero outbound network calls are made by the simulator to `*.aurin.org.au` during any scenario run (FR-023, SC-006).
- [X] CHK012 Zero outbound network calls are made by the simulator to any EPA, OpenStreetMap, or jurisdictional production endpoint (FR-023, SC-006).
- [X] CHK013 A network-egress capture test runs in CI and asserts zero packets to any of the above hosts during simulator scenario execution (SC-006).
- [X] CHK014 All shape data used by the simulator is derived from cached, locally-stored, licence-attested public-dataset snapshots OR is fully synthetic (FR-023, FR-034).
- [X] CHK015 Every cached snapshot is enumerated in the manifest with `source_url`, `snapshot_date`, `dataset_version`, and SPDX licence (FR-031, FR-034, SC-009).

## Deterministic Byte-Identical Replay (CL-4)

- [X] CHK016 Given identical `(scenario_id, seed)` inputs, every feed emits records in the same total order across runs (FR-022(a), SC-005).
- [X] CHK017 Each emitted record is serialised as canonical JSON: UTF-8, RFC 8259, lexicographically sorted object keys, no insignificant whitespace, shortest round-trip numeric form (FR-022(b), A-16).
- [X] CHK018 NDJSON output uses `\n` (LF) as the line terminator (FR-022(b)(c), A-16).
- [X] CHK019 NDJSON output places exactly one record per line (FR-022(c)).
- [X] CHK020 All `timestamp` fields are populated from a deterministic simulated clock seeded by `(scenario_id, seed, ordinal)` and rendered as ISO-8601 UTC at microsecond precision (FR-022(d), A-16).
- [X] CHK021 Wall-clock timestamps are forbidden in any replay-comparable field of an emitted message (FR-022(d), A-16).
- [X] CHK022 Non-deterministic correlation IDs are derived from a seeded HMAC of `(scenario_id, seed, ordinal)` (FR-022(e), A-16).
- [X] CHK023 A SHA-256 digest of the concatenated canonical NDJSON stream per feed is computed and exposed to verification tooling (FR-022, SC-005).
- [X] CHK024 An automated test runs the same scenario+seed pair twice and asserts equal SHA-256 digests per feed (SC-005).
- [X] CHK025 An automated test runs the same scenario with a *different* seed and asserts the digest changes (SC-005, FR-022).
- [X] CHK026 Concurrent scenario runs use isolated simulated-clock namespaces so emitted timestamps cannot collide between scenarios (FR-026).

## Required Marker Fields on Every Emitted Message

- [X] CHK027 Every simulator-emitted message carries `simulated: true` at the document root (FR-021, US2 acceptance scenario 2).
- [X] CHK028 Every simulator-emitted message carries a `scenario_id` field (FR-021).
- [X] CHK029 Every simulator-emitted message carries the originating numeric `seed` field (FR-021).
- [X] CHK030 Every simulator-emitted message carries a `source_shape` identifier (e.g. `bom.severe_weather_warning.v1`) (FR-021).
- [X] CHK031 Every simulator-emitted message carries a simulated-clock `timestamp` (FR-021, FR-022(d)).
- [X] CHK032 Every simulator-emitted message carries a `feed_version` field (FR-021).
- [X] CHK033 Every message that imitates a real warning shape additionally carries the literal "TEST — DO NOT BROADCAST" in the message body (FR-046).

## Delivery Surface and Replay Mode (CL-2 / A-14)

- [X] CHK034 Simulator output is published only via the existing in-process Event Hub / Service Bus surface in `apps/api/app/services/simulation/event_hub_publisher.py` (FR-024, A-14).
- [X] CHK035 A deterministic file-based replay mode reads/writes NDJSON under `fixtures/sim_replays/<scenario>.ndjson` for offline/CI tests (FR-024, A-14).
- [X] CHK036 The file-based replay mode produces NDJSON that satisfies the canonical-encoding rules (CHK017–CHK022) (FR-022, FR-024).
- [X] CHK037 Production agents subscribe to the simulator-publish channel via the same subscription mechanism used for real-source ingestion (FR-024, A-14).

## Per-Domain Simulator Feed Coverage (FR-020)

- [X] CHK038 A BoM-shaped severe-weather-warning feed is implemented (FR-020).
- [X] CHK039 A BoM-shaped fire-weather / Fire Danger Index feed is implemented (FR-020).
- [X] CHK040 A BoM-shaped flood-gauge / flood-watch / flood-warning feed is implemented (FR-020).
- [X] CHK041 A BoM-shaped tropical-cyclone-track feed is implemented (FR-020).
- [X] CHK042 A GA-shaped earthquake-event feed is implemented (FR-020).
- [X] CHK043 A GA-shaped tsunami-threat-assessment feed is implemented (FR-020).
- [X] CHK044 An EPA-shaped PM2.5 / air-quality feed is implemented (FR-020).
- [X] CHK045 A traffic / road-closure status feed is implemented (FR-020).
- [X] CHK046 A utility outage feed (electricity, gas, water, telecoms) is implemented (FR-020).
- [X] CHK047 An ambulance computer-aided-dispatch (CAD) feed is implemented (FR-020).
- [X] CHK048 A social-media-chatter feed with misinformation markers is implemented (FR-020).
- [X] CHK049 A sensor-telemetry feed (water level, wind, temperature) is implemented (FR-020).

## Per-Jurisdiction Coverage and Fallback Shape

- [X] CHK050 At least one named scenario exists for each of the 9 jurisdictions plus commonwealth (FR-020, A-4).
- [X] CHK051 For any jurisdiction or hazard type with no available public-dataset shape, the simulator emits a `source_shape: synthetic.fallback.v1` message rather than fabricating a shape attributed to a real public dataset (FR-025, US2 acceptance scenario 5).
- [X] CHK052 A scenario targeting a remote NT regional zone successfully emits deterministic feed messages using the documented fallback shape (FR-025, US2 acceptance scenario 5).
- [X] CHK053 A scenario triggering a cross-state resource request produces coherent records on both sides (e.g. NSW request + VIC fulfilment) without requiring two separate seed loads (Edge Case "Cross-jurisdictional resource sharing").

## Feed Shape Versioning

- [X] CHK054 Every simulator feed shape carries an explicit version identifier in `source_shape` (FR-027, FR-021).
- [X] CHK055 A breaking change to a feed shape introduces a new `source_shape` version identifier (FR-027).
- [X] CHK056 A breaking change to a feed shape adds a new manifest entry for the new version without removing the prior version (FR-027, FR-031).

## How to Use

This checklist is an **operational gate**:
- **At end of `/speckit.plan`**: confirm CHK001–CHK007 (Two-Path isolation design), CHK016–CHK023 (canonical-encoding design), CHK034–CHK037 (delivery surface design) are addressed by the plan.
- **At end of `/speckit.implement`**: confirm CHK008–CHK015 (egress isolation), CHK024–CHK033 (marker enforcement), CHK038–CHK053 (per-domain / per-jurisdiction coverage), CHK054–CHK056 (versioning) all pass before merge.
- **Before every demo run**: re-run CHK024 (digest equality), CHK013 (egress capture). Any unchecked item blocks the demo.
- **CHK001–CHK013** are non-negotiable Two-Path Rule gates and have no waiver path.
