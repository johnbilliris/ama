/**
 * T187 — sapol: state-control-centre RBAC + multi-LGA delegated authority.
 *
 * FR-030 net-new spec authored cycle-1 phase 14 (T187). Per Q23 owning-
 * persona placement, this spec sits under sectors/sa/ because sapol is
 * the SA-jurisdiction-owned persona for cross-LGA control-centre
 * delegation. Drives /api/outcomes/sc-001/evaluate (lives saved as the
 * operative outcome of multi-LGA evac) + /api/audit/list to confirm
 * operator_identity propagates the delegated authority.
 *
 * Persona scope: sapol  · Outcome: SC-001  · Hazard: bushfire  · P2
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { WorkspacesPage } from "@web-coverage/_support/pages/workspaces.po";

const PERSONA_ID = "sapol";
const SC_ID = "sc-001";
const SCENARIO_ID = "outcome-1-bushfire-extreme-heat";
const METRIC_INPUTS = { lives_at_risk: 800 } as const;

test(
  `sapol — state control centre multi-LGA RBAC ` +
    `@persona:${PERSONA_ID} @outcome:1 @hazard:bushfire ` +
    `@fr:FR-030 @fr:FR-028 @fr:FR-029 @clause:I @p2`,
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
    expect(match, "delegated-authority audit row must surface").toBeTruthy();
    expect(match!.operator_identity.persona_id).toBe(persona.persona_id);
  },
);
