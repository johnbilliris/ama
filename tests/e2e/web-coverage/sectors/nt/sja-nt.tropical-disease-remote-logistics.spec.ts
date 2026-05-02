/**
 * T196 — sja-nt: tropical-disease remote logistics allocation.
 *
 * FR-030 net-new spec authored cycle-1 phase 14 (T196). St John Ambulance
 * NT carries the unique tropical-disease (melioidosis, dengue) burden
 * during cyclone-flood compounding events. Drives /api/outcomes/sc-004/
 * evaluate (logistics_clicks ≤ baseline) + audit-list to confirm the
 * remote-clinic resupply chain emits operator_identity matching sja-nt.
 *
 * Persona scope: sja-nt  · Outcome: SC-004  · Hazard: bushfire+tropical-cyclone  · P1
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { WorkspacesPage } from "@web-coverage/_support/pages/workspaces.po";

const PERSONA_ID = "sja-nt";
const SC_ID = "sc-004";
const SCENARIO_ID = "outcome-4-bushfire-cyclone-logistics";
const METRIC_INPUTS = { logistics_clicks: 6 } as const;

test(
  `sja-nt — tropical-disease remote logistics ` +
    `@persona:${PERSONA_ID} @outcome:4 @hazard:bushfire+tropical-cyclone ` +
    `@fr:FR-030 @fr:FR-028 @fr:FR-029 @clause:VIII @p1`,
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
    expect(match, "remote-clinic resupply audit row must surface").toBeTruthy();
    expect(match!.operator_identity.persona_id).toBe(persona.persona_id);
  },
);
