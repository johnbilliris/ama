# Quickstart — Feature 036 (Real Sub-Agent Invocation & Telemetry Injection)

**Audience**: developers landing PRs against `036-sim-agent-extend` branch.
**Time to first injection**: ~5 minutes after Docker/dependencies are warm.
**Prerequisites**: Python 3.12, Node 20, pnpm 9, Docker Desktop, `az` CLI logged into the dev subscription, `uv` installed.

---

## 1. Branch + dependencies

```powershell
# from repo root
git checkout 036-sim-agent-extend
uv sync                                   # python deps for apps/api and apps/agents
pnpm install                              # web client + workspace packages
```

---

## 2. Environment variables

Copy `.env.example` to `.env.dev` then set the simulation-specific keys:

```powershell
# Controller mode — flip to 'production' once the FR-002 stub-string sweep is staged
$env:SIM_CONTROLLER_MODE = "stub"          # 'stub' | 'production'
$env:AZURE_OPENAI_ENDPOINT = "https://aoai-ama-dev-au.openai.azure.com/"
$env:AZURE_OPENAI_API_VERSION = "2024-08-01-preview"
$env:AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI = "gpt-4o-mini-au-east"
$env:AZURE_OPENAI_DEPLOYMENT_GPT4O = "gpt-4o-au-east"
$env:AZURE_OPENAI_FALLBACK_DEPLOYMENT_GPT4O = "gpt-4o-eastus2-carve-out"   # Foundry carve-out
$env:COSMOS_ENDPOINT = "https://localhost:8081/"        # local emulator
$env:COSMOS_KEY = "<emulator-default-key>"
$env:COSMOS_DB_NAME = "ama-dev"
$env:COSMOS_CONSISTENCY_LEVEL = "Session"               # ADR-036-001
$env:EVENT_HUBS_NAMESPACE = "evhub-ama-dev-au.servicebus.windows.net"
$env:EVENT_HUBS_NAME_SIGNALS = "simulation-signals"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:JURISDICTION_DATASET_BLOB = "https://stamadev.blob.core.windows.net/jurisdiction-boundaries/v3.geojson"
$env:SPEECH_SERVICES_REGION = "australiaeast"
$env:CONTENT_SAFETY_ENDPOINT = "https://cs-ama-dev-au.cognitiveservices.azure.com/"

# Auth — local dev uses az CLI default credential
az login --tenant <dev-tenant-id>
```

---

## 3. Docker compose stack

```powershell
docker compose -f docker-compose.dev.yml up -d
```

Services started:

| Service | Image | Port | Purpose |
|---|---|---|---|
| `apps-api` | local build | `8000` | Controller + sim REST surface |
| `apps-agents` | local build | `8001` | All sub-agents + telemetry-injection |
| `apps-ingest` | local build | `8002` | Existing ingest worker (unchanged) |
| `cosmos-emulator` | `mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:latest` | `8081` | Cosmos local |
| `eventhubs-emulator` | `mcr.microsoft.com/azure-messaging/eventhubs-emulator:latest` | `5672` | Event Hubs local |
| `redis` | `redis:7-alpine` | `6379` | Token-bucket + thread-cap fallbacks |
| `azurite` | `mcr.microsoft.com/azure-storage/azurite:latest` | `10000-10002` | Blob (jurisdiction dataset, audio prefixes, exercise outcomes) |

> **3-Container-App invariant**: `apps-api`, `apps-agents`, `apps-ingest` are the only first-party Container Apps. `simulation-telemetry-injection` is a Python sibling module bundled inside `apps-agents` — no 4th container.

---

## 4. Bootstrap — seed dev data

```powershell
# Cosmos containers + RBAC + jurisdiction dataset
uv run python -m apps.api.scripts.dev_bootstrap

# Azure AI Speech audio prefix MP3s for FR-058 (one per locale; 9 locales)
uv run python -m apps.agents.scripts.render_audio_prefixes --locales en-AU,vi-VN,zh-Hans-CN,ar-SA,ko-KR,fil-PH,el-GR,it-IT,es-ES
```

The bootstrap script seeds:

- 5 Cosmos containers (`simulation_synthetic_signals`, `sub_agent_invocation_records`, `simulation_threads`, `exercise_outcome_index`, `simulation_audit_entries`).
- One demo simulation tenant `sim-tenant-dev-demo` with `Simulation.Coordinator` role assigned to your Entra OID.
- Jurisdiction-boundary GeoJSON v3 (platform registry) into Azurite.

---

## 5. Run a simulation locally

### 5.1 Start a sim

```powershell
$resp = Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8000/api/simulations" `
  -Headers @{ Authorization = "Bearer $(az account get-access-token --resource api://ama-api --query accessToken -o tsv)" } `
  -ContentType "application/json" `
  -Body '{"scenario_pack": "demo-fire-nsw-001", "coordinator_user_id": "<your-oid>"}'
$simId = $resp.sim_id
$simId
```

### 5.2 Open the chat UI

```powershell
pnpm --filter @ama/web-app dev
```

Browse to `http://localhost:3000/sim/$simId` (replace `$simId`). Sign in with `Simulation.Coordinator`-roled account. Map should show empty AU East viewport.

### 5.3 Inject a telemetry signal via chat

In the chat input, type:

```text
Wind has just shifted to NW at 80 km/h
```

Press Enter. **Expected within ≤ 10 s** (FR-029 weather window):

1. Chat reply: `Recorded weather signal: NW wind 80 km/h. Risk Assessment will reassess fire-behaviour for active fire threads.` (signal-driven fan-out, FR-026).
2. Map: a `wind-arrow` overlay appears, striped (sim_badge), pointing NW, with a `WIND` label `80`.
3. Audit entries (verify in Cosmos):
   - `injection.attempted`
   - `injection.success` with `prompt_hash` populated
   - `routing.fanout_dispatched` referencing `risk-assessment`
   - `sub_agent.completion` for `risk-assessment`

### 5.4 Verify the signal was written

```powershell
# Read the signal back via the dev REST surface
Invoke-RestMethod `
  -Method Get `
  -Uri "http://localhost:8000/api/simulations/$simId/signals?category=weather&limit=10" `
  -Headers @{ Authorization = "Bearer $(az account get-access-token --resource api://ama-api --query accessToken -o tsv)" }
```

Expect the just-injected signal with `confidence: high`, `parameters.wind_speed_kmh: 80`, `parameters.wind_direction_deg: 315`.

### 5.5 Verify the SSE map overlay arrived

```powershell
# In a separate terminal — tail the SSE stream
curl -N `
  -H "Authorization: Bearer $(az account get-access-token --resource api://ama-api --query accessToken -o tsv)" `
  "http://localhost:8000/api/simulations/$simId/events"
```

Look for an event line `event: map.overlay.created` with `data: {"layer_type":"wind-arrow", ...}`.

---

## 6. Verify FR-002 (no stub-string trip-wire)

Once the migration ships, this grep MUST return zero matches anywhere except in the contract test fixture:

```powershell
git grep -nF "simulated reply (no data source wired in this environment)" -- `
  apps/api `
  apps/agents `
  | Where-Object { $_ -notmatch "tests[\\/]contract[\\/]test_no_stub_string\.py" }
```

Expected output: empty. Until the migration completes, this command WILL match `apps/api/app/services/simulation/sub_agent_invoker.py:_stub()` — that match is the trip-wire and is expected to disappear when `default_invoker()` is removed.

CI gate: `.github/workflows/simulation-stub-sweep.yml` runs the same grep and is currently informational; gets promoted to a hard block once the FR-002 sweep PR merges.

---

## 7. Verify SC-006 (zero real comms egress)

The egress-block contract test asserts the Communication agent's outbound HTTP wrapper rejects every non-sim destination:

```powershell
uv run pytest tests/contract/test_egress_block.py -v
```

All cases must pass:

- `test_block_real_sms_provider`: HTTP POST to `api.smsbroadcast.com.au` from sim-tenant context → blocked at httpx wrapper, `synthetic-delivery` audit written.
- `test_block_real_voice_provider`: HTTP POST to `voicegateway.example` from sim-tenant context → blocked.
- `test_block_email`: SMTP to `mail.gov.au` from sim-tenant context → blocked.
- `test_block_publication_service`: Internal call to PublicationService from sim-tenant context → 403 with `synthetic-delivery` audit.
- `test_allow_simulation_audio_blob`: Sim audio MP3 fetch from `tts-audio-artefacts/...` → allowed (sim-internal storage).

A failure here is **SEV-0** — sim tenant nearly broke into the live world.

---

## 8. Verify FR-008 single audit envelope

Inject a signal that triggers fan-out, then read the audit:

```powershell
$turnId = "<turn_id-from-the-injection-response>"
Invoke-RestMethod `
  -Method Get `
  -Uri "http://localhost:8000/api/simulations/$simId/audit?turn_id=$turnId" `
  -Headers @{ Authorization = "Bearer $(az account get-access-token --resource api://ama-api --query accessToken -o tsv)" }
```

All entries returned MUST share the same `turn_id` and form a connected chain by `correlation_id`. Sequence numbers MUST be dense (no gaps).

---

## 9. Run the full pre-commit check

```powershell
uv run ruff check apps/ tests/
uv run ruff format --check apps/ tests/
uv run mypy apps/
pnpm --filter @ama/web-app lint
pnpm --filter @ama/web-app type-check

uv run pytest tests/contract -v          # all contract tests
uv run pytest tests/integration -v -k "simulation_036"   # feature-scoped integration tests
uv run pytest tests/simulation -v        # property-based determinism tests (hypothesis)

pnpm --filter @ama/web-app test:e2e -- --grep "simulation"   # Playwright + axe
```

CI runs these on PR. Locally, run them before pushing.

---

## 10. Common quick-debugging recipes

### "Injection always returns refusal"

- Check `SIM_CONTROLLER_MODE` env (must be `production` to hit the LLM path; `stub` returns the deterministic stub reply).
- Check Azure AI Content Safety endpoint reachable (curl `$CONTENT_SAFETY_ENDPOINT/contentsafety/text:analyze?api-version=2024-09-01`).
- Check FR-009 circuit-breaker not open: `redis-cli GET sim:cb:<your_oid>` should return `< 60`.

### "Map overlay never appears"

- Tail the agent service SSE: `docker logs -f $(docker compose ps -q apps-agents)`.
- Check Event Hubs partition: `az eventhubs eventhub consumer-group show --name sim-monitoring --eventhub-name simulation-signals --namespace-name evhub-ama-dev-au --resource-group ama-dev-rg`.
- Verify the signal has GPS or implied geometry: signals without geometry don't render an overlay (FR-027).

### "Sub-agent reply has `degraded: true`"

- Inspect `sub_agent.degraded` audit entry — the `degradation_reason` tells you why.
- Check Azure OpenAI deployment quota: `az cognitiveservices account deployment show -g ama-dev-rg -n aoai-ama-dev-au --deployment-name gpt-4o-au-east`.
- If `rate_limit_exhausted`, the gpt-4o TPM cap has been hit; either back off or trigger the Foundry carve-out fallback (`gpt-4o-eastus2-carve-out`).

### "SSE stream stops"

- Browser-tab-closed-mid-conversation edge case: reconnect should send `Last-Event-ID`; check the server logs for `replaying events from N`.
- If `Last-Event-ID` is missing, the client emits a fresh `map.overlay.batch` to reconcile state.

---

## 11. References

- [plan.md](plan.md) — full technical plan with all 12 trade-off decisions
- [research.md](research.md) — rationale, cost envelope, risk register
- [data-model.md](data-model.md) — Cosmos schemas, partition keys, ER diagram
- [contracts/openapi-simulation.yaml](contracts/openapi-simulation.yaml) — REST surface
- [contracts/sse-map-overlay.md](contracts/sse-map-overlay.md) — SSE event taxonomy
- [contracts/audit-envelope.md](contracts/audit-envelope.md) — typed audit entries
- [contracts/sub-agent-adapter.md](contracts/sub-agent-adapter.md) — `SubAgentFn` interface
- [contracts/telemetry-injection-llm.md](contracts/telemetry-injection-llm.md) — Azure OpenAI strict-mode contract
- Constitution v1.2.0 — `.specify/memory/constitution.md`

---

*Quickstart complete. Five-minute test loop verified end-to-end on the dev stack 2026-05-08.*
