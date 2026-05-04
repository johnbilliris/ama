/**
 * T199 — utility: insurance recovery handoff (FR-013/FR-016 hazard pair #5).
 *
 * FR-030 net-new spec authored cycle-1 phase 14 (T199). FR-013 economic-
 * loss accounting + FR-016 hazard pair #5 (riverine-flood+severe-storm).
 * Utility (energy/water network operators) hands off restoration data
 * to insurance/recovery actors. Drives /api/outcomes/sc-005/evaluate
 * (economic_loss_aud baseline) + audit-list to confirm the
 * insurance-recovery handoff chain emits operator_identity matching
 * utility.
 *
 * Persona scope: utility  · Outcome: SC-005  · Hazard: riverine-flood+severe-storm  · P1
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { WorkspacesPage } from "@web-coverage/_support/pages/workspaces.po";

const PERSONA_ID = "utility";
const SC_ID = "sc-005";
const SCENARIO_ID = "outcome-5-flood-storm-economic";
const METRIC_INPUTS = { economic_loss_aud: 1_400_000_000 } as const;

test(
  `utility — insurance recovery handoff ` +
    `@persona:${PERSONA_ID} @outcome:5 @hazard:riverine-flood+severe-storm ` +
    `@fr:FR-030 @fr:FR-013 @fr:FR-016 @fr:FR-028 @fr:FR-029 ` +
    `@clause:VII @p1`,
  async ({ resolvePersona, page, request, correlationId }) => {
    const persona = await resolvePersona(PERSONA_ID);
    expect(persona.aiims_function).toBeTruthy();
    const headers = {
      "X-Correlation-Id": correlationId,
      "X-Test-Persona-Id": persona.persona_id,
    };
    await page.setExtraHTTPHeaders(headers);

    const ws = new WorkspacesPage(page);
    await ws.goto();
    await expect(ws.heading).toBeVisible();

    const evalRes = await request.post(`/api/outcomes/${SC_ID}/evaluate`, {
      headers: { ...headers, "Content-Type": "application/json" },
      data: {
        scenario_id: SCENARIO_ID,
        persona_id: persona.persona_id,
        correlation_id: correlationId,
        metric_inputs: METRIC_INPUTS,
      },
    });
    expect(evalRes.status(), `${SC_ID} evaluator must return 200`).toBe(200);
    const verdict = (await evalRes.json()) as { status: string; audit_id: string };
    expect(verdict.status).toBe("pass");

    const listRes = await request.get(
      `/api/audit/list?correlation_id=${correlationId}`,
      { headers },
    );
    expect(listRes.ok()).toBe(true);
    const list = (await listRes.json()) as {
      items: Array<{ audit_id: string; operator_identity: { persona_id: string } }>;
    };
    const match = list.items.find((row) => row.audit_id === verdict.audit_id);
    expect(match, "insurance-recovery handoff audit row must surface").toBeTruthy();
    expect(match!.operator_identity.persona_id).toBe(persona.persona_id);
  },
);
