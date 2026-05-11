# Quickstart — Extending Test Data and Resources

Spec: [spec.md](./spec.md) · Plan: [plan.md](./plan.md)

Audience: a developer who wants to **add a new test-data artefact** —
seed catalogue entry, generator, simulator feed shape, demo scenario, or
mock resource — and have it pass CI on the first PR.

---

## Prerequisites

```powershell
# Windows + WSL (per repo convention)
pwsh
cd C:\code\ama  # or your worktree
pip install -e apps/api -e apps/agents -e packages/eval-core -e apps/eval-runner
pip install ruff mypy import-linter pytest pytest-asyncio pytest-benchmark hypothesis pyyaml jsonschema rfc8785
pnpm install --frozen-lockfile
```

> **Windows tests note**: pytest is invoked with
> `pytest --basetemp=C:\tmp\ama-tests` (per repo memory). Without this,
> long Cosmos paths overrun Windows MAX_PATH and tests fail mysteriously.

---

## Path 1 — Add a static seed catalogue entry

1. **Drop the JSON file** under the appropriate sub-folder of
   `packages/domain/src/domain/seed/`. Wrap with the `_fixture` marker
   per CL-5:

   ```json
   {
     "_fixture": {
       "fictitious": true,
       "residency": "AU",
       "licence": "proprietary-fictitious-internal",
       "schema_version": "1"
     },
     "records": [
       {
         "id": "nsw-rfs-org",
         "fictitious": true,
         "residency": "AU",
         "name": "[FICTITIOUS] NSW Rural Fire Service",
         "jurisdiction": "nsw",
         "aiims_function": "operations"
       }
     ]
   }
   ```

2. **Wire the file** into `scripts/seed_loader.py`'s `SEED_FILES` and
   `CONTAINER_MAP` / `PARTITION_KEY_MAP`.

3. **Add a manifest entry** to `docs/test-data/manifest.json`. Minimum
   shape:

   ```json
   {
     "id": "seed-organisations-nsw-rfs",
     "name": "Synthetic NSW RFS organisation seed",
     "category": "synthetic",
     "path": "packages/domain/src/domain/seed/organisations_australia.json",
     "version": "1.0.0",
     "content_hash": "<sha256>",
     "created_or_updated": "2026-05-11",
     "persona_bindings": ["nsw-rfs-incident-controller"],
     "domain_group": "fire",
     "fictitious": true,
     "pii": false,
     "pspf": "OFFICIAL",
     "residency": "AU",
     "licence": "proprietary-fictitious-internal",
     "source_url": "n/a",
     "snapshot_date": "n/a",
     "dataset_version": "n/a",
     "refresh_policy": "static",
     "volume_tier": "small",
     "record_count": 1,
     "cultural_review_required": false
   }
   ```

   Compute the content hash with:

   ```powershell
   python tools/lint/check_test_data_manifest.py --hash packages/domain/src/domain/seed/organisations_australia.json
   ```

4. **Run the lints locally**:

   ```powershell
   python tools/lint/check_test_data_manifest.py
   python tools/lint/check_indigenous_placeholders.py
   ```

5. **Run the loader idempotency test**:

   ```powershell
   pytest --basetemp=C:\tmp\ama-tests tests/integration/test_seed_loader_idempotent.py -q
   ```

---

## Path 2 — Add a simulator feed shape

1. **Create the feed module** at
   `apps/api/app/services/simulation/feeds/<your_feed>.py`:

   ```python
   from __future__ import annotations
   from collections.abc import Iterator
   from ._canonical import SimulatedClock, FeedParams, correlation_id
   from app.services.simulation.feeds._models import SimulatorRecord

   GENERATOR_FICTITIOUS = True
   GENERATOR_VERSION = "1.0.0"
   SOURCE_SHAPE = "myagency.my_feed.v1"
   FEED_VERSION = "v1"

   def emit(scenario_id: str, seed: int, clock: SimulatedClock,
            params: FeedParams) -> Iterator[SimulatorRecord]:
       for ordinal in range(10):
           yield SimulatorRecord(
               scenario_id=scenario_id,
               seed=seed,
               source_shape=SOURCE_SHAPE,
               timestamp=clock.tick(delta_us=ordinal * 1_000_000),
               feed_version=FEED_VERSION,
               correlation_id=correlation_id(scenario_id, seed, ordinal),
               body={"text": "TEST — DO NOT BROADCAST", "ordinal": ordinal},
           )
   ```

2. **Register the shape** in
   `apps/api/app/services/simulation/feeds/source_shapes.json`:

   ```json
   { "shape": "myagency.my_feed.v1", "kind": "synthetic-fallback", "version": "v1" }
   ```

3. **Add a manifest entry** with `category=simulator-feed-shape`:

   ```json
   {
     "id": "feed-myagency-my-feed-v1",
     "name": "MyAgency feed shape v1",
     "category": "simulator-feed-shape",
     "source_shape": "myagency.my_feed.v1",
     "feed_version": "v1",
     "version": "1.0.0",
     "content_hash": "0000000000000000000000000000000000000000000000000000000000000000",
     "created_or_updated": "2026-05-11",
     "persona_bindings": ["nsw-ses-comms-officer"],
     "domain_group": "ses",
     "fictitious": true,
     "pii": false,
     "pspf": "OFFICIAL",
     "residency": "AU",
     "licence": "proprietary-fictitious-internal",
     "source_url": "n/a",
     "snapshot_date": "n/a",
     "dataset_version": "n/a",
     "refresh_policy": "regenerate-each-run",
     "volume_tier": "n/a",
     "record_count": 0,
     "cultural_review_required": false
   }
   ```

4. **Trigger a deterministic replay locally**:

   ```powershell
   python -m apps.api.app.services.simulation.replay.ndjson_replay `
     --scenario nsw-ses-storm-2026 `
     --seed 42 `
     --feed myagency.my_feed.v1 `
     --out fixtures/sim_replays/nsw-ses-storm-2026.ndjson

   # Verify byte-equality across two runs:
   python -m apps.api.app.services.simulation.replay.ndjson_replay `
     --scenario nsw-ses-storm-2026 --seed 42 --feed myagency.my_feed.v1 --out /tmp/run-a.ndjson
   python -m apps.api.app.services.simulation.replay.ndjson_replay `
     --scenario nsw-ses-storm-2026 --seed 42 --feed myagency.my_feed.v1 --out /tmp/run-b.ndjson
   Get-FileHash /tmp/run-a.ndjson, /tmp/run-b.ndjson
   # Hashes MUST match.
   ```

5. **Run the simulator-isolation lint** to confirm no production
   module accidentally imports your new feed:

   ```powershell
   python tools/lint/check_simulator_isolation.py
   lint-imports --config pyproject.toml
   ```

---

## Add a generator

1. **Create** `scripts/generators/<your_generator>.py`. Use the seed
   contract:

   ```python
   from __future__ import annotations
   import argparse, random
   from collections.abc import Iterator
   from scripts.generators._seed_contract import resolve_seed

   GENERATOR_FICTITIOUS = True
   GENERATOR_VERSION = "1.0.0"

   def generate(*, seed: int | None = None, count: int = 100) -> Iterator[dict]:
       resolved = resolve_seed(fn_arg=seed, cli_arg=None)
       rng = random.Random(resolved)
       for i in range(count):
           yield {"id": f"vol-{i:05d}", "fictitious": True, "residency": "AU",
                  "skill_level": rng.choice(["basic", "advanced", "expert"])}

   def main() -> None:
       p = argparse.ArgumentParser()
       p.add_argument("--seed", type=int, default=None)
       p.add_argument("--count", type=int, default=100)
       args = p.parse_args()
       for r in generate(seed=args.seed, count=args.count):
           print(r)

   if __name__ == "__main__":
       main()
   ```

2. **Verify seed precedence**:

   ```powershell
   python scripts/generators/your_generator.py --seed 7 --count 3   # CLI wins
   $env:AMA_TEST_SEED="11"; python scripts/generators/your_generator.py --count 3  # env used
   python scripts/generators/your_generator.py --count 3            # default 0 + warning
   ```

3. **Add a manifest entry** with `category=generator` and
   `refresh_policy=regenerate-each-run`.

---

## Local CI dry-run

```powershell
ruff check apps tests packages
python tools/lint/check_licence_inventory.py
python tools/lint/check_test_data_manifest.py
python tools/lint/check_indigenous_placeholders.py
python tools/lint/check_simulator_isolation.py
lint-imports --config pyproject.toml
pytest --basetemp=C:\tmp\ama-tests tests/contract tests/unit -q
```

All five lints + ruff + the contract/unit tests must pass before
pushing.

---

## Common pitfalls

| Symptom | Likely cause | Fix |
|---|---|---|
| `manifest-lint`: "artefact <path> not enumerated" | New file added without manifest entry | Add the entry to `docs/test-data/manifest.json` |
| `manifest-lint`: "content_hash mismatch" | Edited the artefact without updating the hash | `python tools/lint/check_test_data_manifest.py --hash <path>` and copy the value |
| `simulator-isolation-lint`: "forbidden import" | Production module imports `apps.api.app.services.simulation.*` | Move the import behind a runtime DI lookup or relocate the code into the simulator package |
| Replay byte-equality fails | Generator uses wall-clock or unseeded RNG | Replace `time.time()`/`datetime.now()`/`random.random()` with `clock.tick(...)` and `random.Random(seed)` |
| `indigenous-placeholder-lint` fails | Region tag in `persona_bindings` matches a context zone but `cultural_review_required=false` | Set `cultural_review_required=true` and add a `cultural_review_notes` value |
| Loader rejects a record | Missing `_fixture` wrapper or missing record-level `fictitious=true` | Add the wrapper (CL-5) |

## Spec-038 — postprovision hook chain (T034)

The hook chain is:

```
azure.yaml: hooks.postprovision
  └── scripts/seed-database.ps1   (Windows / PowerShell)
  └── scripts/seed-database.sh    (Linux / bash)
        └── python scripts/seed_loader.py …
              ├── (existing) jurisdictions / frameworks / etc. catalogues
              ├── (existing) recovery-catalogue
              ├── (existing) coordination_tasks
              └── (spec-038, T032) seed_spec038_subdirectories(client, db)
                    ├── alert-templates / evacuation-routes / vulnerable-categories
                    ├── hospital-capability / road-segments / utility-infrastructure
                    └── volunteer-credentials / lemp-memp-templates / inter-government-agreements
```

The spec-038 subdirectory loader applies the four-scope fictitious marker
validator (packages/domain/src/domain/seed/_fixture_marker.py), the
PSPF cap of OFFICIAL: SENSITIVE, the PII detector
(scripts/_pii_detector.py, FR-045), and content-hash idempotency
(SC-004) before any upsert.
