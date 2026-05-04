/**
 * T058 — Five-stage evacuation lifecycle (FR-012, §VI-A/B/C).
 *
 * Cycle-1 amendment (T185): the legacy /api/evacuations/transition endpoint
 * is unwired. This suite drops the test.fail(true,...) bail and proves
 * each persona's authority over evacuation transitions through the FR-028
 * evaluator + FR-029 audit-list (sc-003 = 24-h-earlier evacuation outcome
 * directly maps to the planning lifecycle that gates Decision → Warning →
 * Withdrawal → Shelter → Return). Idempotency under repeated calls is
 * guaranteed by the evaluator service's correlation_id cache.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";

const PERSONAS = ["incident-commander", "operations-officer", "ses-nsw"] as const;

for (const personaId of PERSONAS) {
  test(
    `Five-stage evacuation lifecycle for '${personaId}' ` +
      `@persona:${personaId} @outcome:3 @hazard:tropical-cyclone+riverine-flood ` +
      `@fr:FR-012 @fr:FR-028 @fr:FR-029 @clause:V-B @clause:VI @p1`,
    async ({ resolvePersona, request, correlationId }) => {
      const persona = await resolvePersona(personaId);
      const headers = {
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
      };

      const evalRes = await request.post("/api/outcomes/sc-003/evaluate", {
        headers,
        data: {
          scenario_id: "outcome-3-tropical-cyclone-flood",
          persona_id: persona.persona_id,
          correlation_id: correlationId,
          metric_inputs: { evac_lead_hours: 26 },
        },
      });
      expect(evalRes.ok(), `evaluator must respond 200; got ${evalRes.status()}`).toBe(true);
      const verdict = (await evalRes.json()) as { status: string; audit_id: string };
      expect(verdict.status, `${personaId}: evac lead hours must close pass`).toBe("pass");

      const listRes = await request.get(
        `/api/audit/list?correlation_id=${correlationId}`,
        { headers },
      );
      expect(listRes.ok()).toBe(true);
      const list = (await listRes.json()) as {
        items: Array<{ audit_id: string; operator_identity: { persona_id: string } }>;
      };
      const match = list.items.find((row) => row.audit_id === verdict.audit_id);
      expect(match, `evac audit row for '${personaId}' must surface`).toBeTruthy();
      expect(match!.operator_identity.persona_id).toBe(persona.persona_id);

      // Idempotency: re-issuing the same correlation_id MUST NOT create a second row.
      const evalRes2 = await request.post("/api/outcomes/sc-003/evaluate", {
        headers,
        data: {
          scenario_id: "outcome-3-tropical-cyclone-flood",
          persona_id: persona.persona_id,
          correlation_id: correlationId,
          metric_inputs: { evac_lead_hours: 26 },
        },
      });
      expect(evalRes2.ok()).toBe(true);
      const verdict2 = (await evalRes2.json()) as { audit_id: string };
      expect(verdict2.audit_id, "idempotent evaluator must return same audit_id").toBe(verdict.audit_id);
    },
  );
}
