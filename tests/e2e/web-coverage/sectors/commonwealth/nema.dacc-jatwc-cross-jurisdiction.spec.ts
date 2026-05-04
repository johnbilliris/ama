/**
 * T198 — nema: DACC/JATWC cross-jurisdiction handover.
 *
 * FR-030 net-new spec authored cycle-1 phase 14 (T198). NEMA orchestrates
 * the Domestic Aid and Crisis Coordination (DACC) handoff to the Joint
 * Australian Tsunami Warning Centre (JATWC) under the FR-015 cross-
 * jurisdiction handover clause. Drives /api/outcomes/sc-003/evaluate
 * (24-h-earlier evac lead) + audit-list to confirm the
 * cross-jurisdiction handover chain emits operator_identity matching
 * nema.
 *
 * Persona scope: nema  · Outcome: SC-003  · Hazard: bushfire+tropical-cyclone  · P1
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { WorkspacesPage } from "@web-coverage/_support/pages/workspaces.po";

const PERSONA_ID = "nema";
const SC_ID = "sc-003";
const SCENARIO_ID = "outcome-3-tropical-cyclone-flood";
const METRIC_INPUTS = { evac_lead_hours: 26 } as const;

test(
  `nema — DACC/JATWC cross-jurisdiction handover ` +
    `@persona:${PERSONA_ID} @outcome:3 @hazard:bushfire+tropical-cyclone ` +
    `@fr:FR-030 @fr:FR-015 @fr:FR-028 @fr:FR-029 @clause:VI @p1`,
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
    expect(match, "DACC/JATWC handover audit row must surface").toBeTruthy();
    expect(match!.operator_identity.persona_id).toBe(persona.persona_id);
  },
);
