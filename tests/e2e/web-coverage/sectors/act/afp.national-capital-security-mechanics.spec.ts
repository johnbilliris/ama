/**
 * T193 — afp-act: national-capital security-mechanics escalation.
 *
 * FR-030 net-new spec authored cycle-1 phase 14 (T193). National-capital
 * security mechanics are AFP-ACT-owned (per generator T111 disambiguation
 * note), distinct from afp-commonwealth's national-evac-coordination
 * scope. Drives /api/outcomes/sc-002/evaluate (signal-to-action ms ≤
 * baseline) + audit-list to confirm the diplomatic-protection escalation
 * chain emits operator_identity matching afp-act.
 *
 * Persona scope: afp-act  · Outcome: SC-002  · Hazard: bushfire+severe-storm  · P1
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { WorkspacesPage } from "@web-coverage/_support/pages/workspaces.po";

const PERSONA_ID = "afp-act";
const SC_ID = "sc-002";
const SCENARIO_ID = "outcome-2-bushfire-severe-storm";
const METRIC_INPUTS = { signal_to_action_ms: 4500 } as const;

test(
  `afp-act — national-capital security-mechanics ` +
    `@persona:${PERSONA_ID} @outcome:2 @hazard:bushfire+severe-storm ` +
    `@fr:FR-030 @fr:FR-028 @fr:FR-029 @clause:II @p1`,
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
    expect(match, "diplomatic-protection escalation audit row must surface").toBeTruthy();
    expect(match!.operator_identity.persona_id).toBe(persona.persona_id);
  },
);
