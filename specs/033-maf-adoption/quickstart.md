# Quickstart — MAF Adoption (033)

**Audience**: Platform engineers and on-call operators.  
**Prerequisites**: Repo cloned to `C:\code\ama`; Python 3.12; `az login` against the AMA subscription; `kubectl` not required (Azure Container Apps).

---

## 1. Install the MAF Python SDK

```bash
cd apps/agents
pip install "agent-framework[azure-ai]"
pip install mcp                 # peer dep used by the routing-service MCP client wrapper
```

Verify:

```bash
python -c "from agent_framework import ChatAgent, WorkflowBuilder, AzureOpenAIChatClient; print('OK')"
```

The `agent-framework[azure-ai]` extra brings in the Azure-OpenAI-backed ChatClient and Azure Monitor OpenTelemetry exporter wiring used by `apps/agents/maf_runtime/observability.py`.

---

## 2. Run the Monitoring agent in isolation (US1 acceptance scenario)

The new agent surface lets each agent be invoked without the workflow runtime — useful for smoke tests and the equivalence harness.

```bash
cd apps/agents
python -m maf_runtime.agents.monitoring_agent --input examples/monitoring_signal.json
```

Expected: a triage decision (`escalate`, `suppress`, or `enrich`) plus an audit entry written to the `audit_entries` Cosmos container.

Verify the audit entry:

```bash
az cosmosdb sql query \
  --account-name ama-platform-dev \
  --database-name platform \
  --container-name audit_entries \
  --query-text "SELECT TOP 1 * FROM c WHERE c.agent_name = 'monitoring' ORDER BY c.started_at DESC"
```

---

## 3. Run a complete workflow against a fixture incident

```bash
cd apps/agents
python -m maf_runtime.workflow.builder --incident-fixture tests/fixtures/incidents/flood_level2.json
```

Expected output sequence:

1. `Running` (Monitoring step)
2. `Running` (Risk Assessment step)
3. `Running` (Evacuation + Resource Allocation steps, parallel)
4. `AwaitingApproval` — the workflow pauses; nothing is published.

In another shell, list active runs:

```bash
curl -s -H "Authorization: Bearer $(az account get-access-token --resource api://drh-api/.default --query accessToken -o tsv)" \
  https://api-drh-dev.<region>.azurecontainerapps.io/api/workflow_runs?status=AwaitingApproval | jq
```

---

## 4. Approve the paused workflow (HITL via spec 008)

The MAF `RequestInfoEvent` is wrapped into a spec 008 `ApprovalRequest` envelope and emitted onto Service Bus `commander-approval-queue`. Approve via the existing commander UI (or the dev script):

```bash
python scripts/approve_alert.py --request-id <REQUEST_ID_FROM_LIST> --decision approve
```

The workflow resumes; final status flips to `Completed`. The `approval_decisions` Cosmos container records approver identity per spec 008.

---

## 5. Crash-recovery smoke test (FR-007 / SC-002)

In one shell, start a long-running workflow:

```bash
python -m maf_runtime.workflow.builder --incident-fixture tests/fixtures/incidents/long_running.json &
```

In another shell, kill the process partway through (after the Risk Assessment step):

```bash
# find the runtime process
ps -ef | grep maf_runtime | grep -v grep
kill -9 <PID>
```

Restart the runtime (Container Apps auto-restarts in production; locally just re-launch):

```bash
python -m maf_runtime.workflow.builder --resume <RUN_ID>
```

Expected: the workflow resumes from the most recent checkpoint, does NOT re-execute the Risk Assessment step, and produces the same downstream outputs.

---

## 6. Register the routing service as an MCP tool (US4)

The routing service exposes an MCP server endpoint at `https://routing-mcp-drh-dev.<region>.azurecontainerapps.io/mcp`. Register it for the Evacuation agent:

```bash
python scripts/register_mcp_tool.py \
  --tool-name routing_service \
  --address https://routing-mcp-drh-dev.<region>.azurecontainerapps.io/mcp \
  --pinned-major-version 1 \
  --bind-agents evacuation
```

Verify the tool is callable:

```bash
python -m maf_runtime.agents.evacuation_agent --input examples/evacuation_with_routing.json
```

The agent's audit entry will include a `tool_invocations` array showing the routing-service call with its version.

---

## 7. Run the equivalence harness for one agent (FR-023)

Per-agent cutover gate.

```bash
cd apps/agents
python -m maf_runtime.equivalence.runner --agent monitoring --emit-report
```

Expected: a Markdown + JSON report at `apps/agents/maf_runtime/equivalence/reports/monitoring-<timestamp>.{md,json}` showing:

- ≥ 95% decision-equivalence on enumerated categorical fields (PASS or FAIL)
- 100% schema-equivalence on populated fields (PASS or FAIL)

If both PASS, the agent is eligible for cutover (flip `FEATURE_MAF_RUNTIME_MONITORING=maf` per environment via the spec 029 flag mechanism).

---

## 8. Promote one agent through the per-agent cutover

Per-environment, in order: `dev` → `staging` → `production`. For each environment:

1. **Shadow phase** (recommended — 24 hours minimum):
   ```bash
   az containerapp update --name ca-agents-drh-<env> --set-env-vars FEATURE_MAF_RUNTIME_MONITORING=shadow
   ```
   The MAF agent runs alongside the legacy pipeline; both outputs feed into the live equivalence monitor.
2. **Cutover**:
   ```bash
   az containerapp update --name ca-agents-drh-<env> --set-env-vars FEATURE_MAF_RUNTIME_MONITORING=maf
   ```
3. **Rollback (FR-026)** if needed:
   ```bash
   az containerapp update --name ca-agents-drh-<env> --set-env-vars FEATURE_MAF_RUNTIME_MONITORING=legacy
   ```

Repeat per agent. Production cutover requires the FR-012b load test to PASS in staging beforehand.

---

## 9. Inspect a workflow run from the operator dashboard

Browse to:

```
https://app-drh-<env>-<suffix>.azurewebsites.net/operations/workflows
```

The page lists runs grouped by the 7 canonical states (Running, AwaitingApproval, NeedsOperatorDecision, Completed, Failed, Cancelled, Superseded). Click any run to see step-by-step progress, checkpoint timeline, HITL pause indicator, and a link to the OTel trace in Application Insights.

---

## Useful Application Insights KQL

Active workflow runs by state:

```kusto
customMetrics
| where name == "workflow.run.state"
| summarize count() by tostring(customDimensions.status), bin(timestamp, 5m)
| render timechart
```

Approval-gate metrics (SC-008):

```kusto
customMetrics
| where name in ("workflow.approval.mtta_seconds", "workflow.approval.escalation", "workflow.approval.timeout")
| summarize avg(value), count() by name, bin(timestamp, 1h)
```

Per-agent audit/telemetry reconciliation (SC-004):

```kusto
let invocations = traces | where customDimensions.event == "agent.invocation" | summarize span_count = count() by tostring(customDimensions.agent_name);
let audits      = traces | where customDimensions.event == "audit.write"       | summarize audit_count = count() by tostring(customDimensions.agent_name);
invocations | join kind=fullouter audits on agent_name | project agent_name, span_count, audit_count, gap = abs(coalesce(span_count, 0) - coalesce(audit_count, 0))
```

---

## Where to look in code

| Concern | Path |
|---|---|
| ChatAgent definitions | `apps/agents/maf_runtime/agents/<agent>.py` |
| Workflow definition | `apps/agents/maf_runtime/workflow/builder.py` |
| Custom executors per step | `apps/agents/maf_runtime/workflow/executors/` |
| HITL `RequestPort` ↔ spec 008 wrapping | `apps/agents/maf_runtime/workflow/hitl_request_port.py` |
| 7-state enum + transitions | `apps/agents/maf_runtime/workflow/run_state.py` |
| 72h watchdog | `apps/agents/maf_runtime/workflow/duration_watchdog.py` |
| Cosmos checkpoint storage | `apps/agents/maf_runtime/checkpoint/cosmos_checkpoint_storage.py` |
| Content-safety / audit / OTel middleware | `apps/agents/maf_runtime/middleware/` |
| MCP routing tool wrapper | `apps/agents/maf_runtime/mcp/routing_tool.py` |
| Equivalence harness | `apps/agents/maf_runtime/equivalence/` |
| Operator REST API | `apps/api/app/api/routes/workflow_runs.py` |
| Operator dashboard | `apps/web/src/app/operations/workflows/page.tsx` |
| First MCP server | `tools/routing_mcp_server/server.py` |
| New Cosmos containers | `infra/bicep/modules/cosmos-workflow.bicep` |
