# Phase 0 — Research Notes

Spec: [spec.md](./spec.md) · Plan: [plan.md](./plan.md)

This document resolves the technical-decision questions surfaced while
filling the plan's Technical Context. All questions tagged
`[NEEDS CLARIFICATION]` are resolved here; none remain open.

---

## Decision 1 — Canonical-JSON library (Python)

**Decision**: Use `rfc8785` (RFC 8785 JSON Canonicalisation Scheme, JCS).

**Context**: FR-022 / CL-4 require byte-identical NDJSON across runs. The
canonical encoder must produce: UTF-8, sorted keys, no insignificant
whitespace, shortest round-trip numeric form, deterministic Unicode escaping.

**Alternatives evaluated**:

| Library | Pros | Cons | Verdict |
|---|---|---|---|
| `rfc8785` (Filippo Valsorda; MIT) | Implements RFC 8785 exactly; ~200 LOC; pure-Python; deterministic float→string per IEEE-754 ryu; actively maintained. | New dependency. | **Selected.** |
| `canonicaljson` (Matrix.org; Apache-2) | Battle-tested in Synapse; pure-Python. | Does NOT implement RFC 8785 numeric form (rounds floats inconsistently for values requiring > 15-digit mantissa); no NaN handling guarantee. | Rejected. |
| Hand-rolled `json.dumps(sort_keys=True, separators=(",", ":"))` | Zero new deps. | Does not normalise numeric form (e.g. `1.0` vs `1`); does not normalise Unicode escapes; cross-Python-version drift possible. | Rejected. |
| `jcs` (PyPI) | Implements JCS. | Less actively maintained (last release > 2 years); duplicate functionality. | Rejected. |

**Rationale**: RFC 8785 is the IETF-standardised canonical JSON form,
explicitly named in the spec ("canonical JSON" in FR-022). Selecting a
library that implements the standard removes any encoder-version
sensitivity. `rfc8785`'s small surface area minimises supply-chain risk.

**Action**: add `rfc8785>=0.1.4` to `apps/api/pyproject.toml` and the
top-level `pyproject.toml` extras `[lint]` group.

---

## Decision 2 — NDJSON streaming approach

**Decision**: Generators yield records one at a time; the encoder pipeline
encodes + writes one line at a time; no in-memory list materialisation
above one record at a time.

**Context**: CL-3 requires that `xlarge` (10 000 records) and any larger
volumes be streamed without materialising the full set. This must hold for
both the seed/generator path and the simulator path.

**Implementation pattern**:

```python
# scripts/generators/_seed_contract.py
def write_canonical_ndjson(records: Iterator[dict], dest: Path) -> str:
    """Stream records → canonical NDJSON; return the SHA-256 hex of the bytes."""
    digest = hashlib.sha256()
    with dest.open("wb") as fh:
        for record in records:                       # generator, not list
            line = rfc8785.canonicalize(record) + b"\n"
            fh.write(line)
            digest.update(line)
    return digest.hexdigest()
```

**Verification**: a memory-bound test
(`tests/integration/test_xlarge_streaming_memory.py`, deferred to
/speckit.tasks) asserts that `tracemalloc.get_traced_memory()` peak stays
under 50 MB while streaming 10 000 records.

---

## Decision 3 — HMAC algorithm and ID derivation

**Decision**: HMAC-SHA-256, key = `f"ama.sim.{scenario_id}.{seed}".encode()`,
message = `f"{purpose}.{ordinal}".encode()`, output = first 32 hex chars
(128 bits) of `hmac.new(...).hexdigest()`.

**Context**: FR-022 / CL-4 require correlation IDs derived from
`(scenario_id, seed, ordinal)` so that replay produces identical IDs.

**Why HMAC-SHA-256**: stdlib (`hmac` + `hashlib.sha256`); FIPS-approved;
collision-resistant well above the cardinality required (max 10 000
records per feed × ~25 feeds × ~8 scenarios = 2 × 10⁶ IDs, well below
2⁶⁴ birthday bound at 128 bits).

**Why 128 bits**: matches the existing UUID4 string length used elsewhere
in the codebase; sufficient for collision-free IDs at our scale; halves
the bytes-per-record vs full SHA-256 hex.

**Why "purpose" prefix**: same `(scenario_id, seed, ordinal)` may need
multiple distinct IDs (e.g. one for the message envelope, one for an
embedded incident reference). The `purpose` string namespaces them.

---

## Decision 4 — Local-dev emulator choice (Azurite / Cosmos DB Emulator / in-memory)

**Decision**: **In-memory fakes are the default**; emulators are documented
opt-in. **No emulator is a required CI dependency.**

**Context**: A-11 / FR-024 / CL-2 forbid new Azure resources. The plan must
honour the existing pattern at `apps/api/app/services/simulation/event_hub_publisher.py`
where the absence of an `azure.eventhub` namespace falls back to an
in-process queue with a `captured_events_for(...)` accessor.

**Pattern by service**:

| Service | Default (CI / local quick) | Opt-in (end-to-end) | Rationale |
|---|---|---|---|
| Event Hub | Existing in-process queue (`event_hub_publisher`) | Real Azure Event Hubs namespace via `AZURE_EVENTHUB_NAMESPACE` env | Already implemented; zero infra. |
| Cosmos DB | In-process dict-backed `FakeCosmosClient` (already used by `apps/api/tests`) | **Cosmos DB Emulator** (Azure-native, docker image `mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:latest`) — opt-in via `AMA_USE_COSMOS_EMULATOR=1` | Honours Azure-native constraint; never required for the manifest CI lint or the deterministic-replay tests. |
| Blob Storage | In-process dict-backed fake | **Azurite** (Azure-native) — opt-in via `AMA_USE_AZURITE=1` | Same. |
| Service Bus | In-process queue | Real Azure Service Bus namespace (no Azure-native local emulator exists in May 2026 stable) | In-process is the only viable CI default; same as today. |
| Event Grid | In-process subscriber registry | Real Azure Event Grid topic | Same. |

**Rejected**: WireMock, MSW, MockServer, LocalStack — all third-party SaaS
or non-Azure clouds, violating the user's "Azure-only" constraint.

**Rejected**: requiring the Cosmos DB Emulator in CI — would slow CI by
~90 s per run and require Linux container privileges; not justified for a
test-data feature whose own tests use in-process fakes.

---

## Decision 5 — Manifest Markdown rendering

**Decision**: `tools/lint/check_test_data_manifest.py --render` writes
`docs/test-data/MANIFEST.md` from `manifest.json`. CI re-renders into a
temp file and diffs; any drift fails the build.

**Context**: FR-030 requires both the human-readable Markdown manifest and
the canonical JSON. To keep them consistent without manual maintenance, the
JSON is the source of truth and the Markdown is generated.

**Pattern**: same as `docs/corpus/INDEXING-LICENCE-INVENTORY.md`, which is
generated from per-source `source.json` sidecars by
`scripts/disaster_corpus/manifest.py` (verified to exist).

---

## Decision 6 — JSON Schema draft

**Decision**: JSON Schema **2020-12**.

**Context**: latest stable; supported by `jsonschema>=4.0` (already in the
Python dependency tree via FastAPI's transitive deps). Supports the
`if`/`then`/`else` keywords used for the conditional cross-checks (e.g.
`category=public ⇒ source_url` non-`n/a`).

**Validator**: `jsonschema.Draft202012Validator` invoked from the manifest
lint step (see `plan.md` § "CI Gate Wiring"). One-line invocation; no new
script needed beyond `check_test_data_manifest.py`.

---

## Decision 7 — Fictitious-marker location for code-generated artefacts

**Decision**: each generator module declares
`GENERATOR_FICTITIOUS = True` and `GENERATOR_VERSION = "<semver>"` as
module-level constants; the generator's primary callable validates these
exist before yielding any record.

**Context**: CL-5 requires "documented module-level constant or
file-prologue comment". The constant form is mechanically inspectable by
`check_test_data_manifest.py`, which AST-parses each
`scripts/generators/*.py` and fails the build if either constant is
missing.

---

## Decision 8 — Indigenous denylist sourcing and review cadence

**Decision**: the denylist file at `tools/lint/data/indigenous_denylist.txt`
is committed empty (with section headers + comments) at P2 ship-time;
denylist content is added in subsequent PRs that are co-authored by the
named cultural-authority custodians listed in the manifest's
`cultural_review_notes`. Review cadence: every 6 months and on demand.

**Context**: CL-6 mandates two-layer enforcement; the schema-cross-check
layer (`cultural_review_required: bool`) is the primary defence on day
one. The denylist is defence-in-depth and grows organically as
custodian-reviewed entries are added — committing a default-empty
denylist would be irresponsible and committing a guessed list would be
worse than nothing.

**Rejected**: pulling from any third-party Indigenous-language API (e.g.
First Languages Australia datasets) — these are not licensed for
denylist use and may themselves contain culturally sensitive material.

---

## Decision 9 — `import-linter` contract location

**Decision**: contracts live in `pyproject.toml` under
`[tool.importlinter]`, mirroring the existing pattern for any current
import-linter usage (`pip install … import-linter` is already in the
`quality` job at `.github/workflows/ci.yml` line 36).

**Contracts added**:

```toml
[tool.importlinter]
root_packages = ["apps", "scripts", "packages"]

[[tool.importlinter.contracts]]
name = "Production code MUST NOT import simulator"
type = "forbidden"
source_modules = [
  "apps.agents",
  "apps.api.app",
]
forbidden_modules = ["apps.api.app.services.simulation"]
ignore_imports = [
  # The simulation package itself is allowed to import its own submodules.
  "apps.api.app.services.simulation.* -> apps.api.app.services.simulation.*",
]

[[tool.importlinter.contracts]]
name = "Runtime code MUST NOT import generators"
type = "forbidden"
source_modules = [
  "apps.agents",
  "apps.api.app",
]
forbidden_modules = ["scripts.generators"]
```

The CI step `lint-imports --config pyproject.toml` already runs as part
of the `simulator-isolation-lint` step (see `plan.md`).

---

## Decision 10 — Persona ID source of truth

**Decision**: the 68 personas are enumerated in a single committed file
`docs/test-data/personas.json` (one entry per persona with `id`,
`name`, `domain_group`, `aiims_function`, `volume_guide`); the manifest
schema's `persona_bindings` array is `enum`-cross-checked against this file
by `check_test_data_manifest.py` (not by the JSON Schema itself, since
schema-side enums are static).

**Context**: A-4 names "the consolidated persona input report" as
authoritative but does not give a stable file path. We elevate the
canonical list into a committed JSON file so the manifest lint can verify
membership.

**Implementation note**: the initial `personas.json` is generated from the
existing persona input report during P2; a manifest-side `personas.source`
field cites the source-report commit SHA for audit traceability.

---

## Resolved [NEEDS CLARIFICATION] count

**Zero remaining.**

All open technical questions surfaced during plan authoring have been
resolved above and incorporated into `plan.md`, `data-model.md`, and the
`contracts/*.json` schemas.
