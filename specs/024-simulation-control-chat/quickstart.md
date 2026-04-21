# Quickstart: Simulation Control & Chat Orchestration

## Prerequisites

- Azure OpenAI deployment (`gpt-4o-mini` or newer) in Australia East.
- Azure Maps account + Entra ID role `Azure Maps Data Reader` for the API's managed identity.
- Cosmos DB `disaster-hub` with the three new containers (`sim_chat_turns`, `sim_tool_invocations`, `sim_synthetic_deliveries`), all with `/tenant_id` partition key.
- Redis (already provisioned) for the rate limiter.

## Local run

```powershell
# from repo root
pnpm install
uv sync
$env:AZURE_OPENAI_ENDPOINT = "https://aoai-ama-ae.openai.azure.com/"
$env:AZURE_OPENAI_DEPLOYMENT = "gpt-4o-mini"
$env:AZURE_MAPS_CLIENT_ID = "<maps-client-id>"
pnpm --filter @ama/api dev   # FastAPI
pnpm --filter @ama/web dev   # Next.js
```

Navigate to `http://localhost:3000/simulations`, pick a simulation, use the chat to start a
scenario. Default seeded user is `sim-coordinator@local` with the `SimulationCoordinator`
role.

## Run the jailbreak suite

```powershell
pytest tests/security/jailbreak -q
```

Must return ≥ 99% refusal / safe rate on the 200-prompt set.

## Run the egress-block fuzz

```powershell
pytest tests/security/egress_block -q -m fuzz  # 10 000 messages
```

Must produce **zero** real deliveries (mock transports assert on every call).
