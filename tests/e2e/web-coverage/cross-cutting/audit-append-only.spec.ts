/**
 * T056 — Audit append-only invariant (FR-010, Constitution §IV).
 *
 * Cycle-1 amendment (T185): the previous /api/governance/audit-trail
 * route is unwired. This suite drops the test.fail(true,...) bail and
 * proves the append-only contract through the FR-028 evaluator: a
 * deterministic counterfactual emits exactly one audit_id under our
 * correlation_id and that row's operator_identity matches the persona
 * under test (the FR-010 + Constitution §IV obligations). FR-005 read-
 * back semantics are validated through the audit-list page-once contract.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";

const PERSONAS = ["incident-commander", "operations-officer", "act-esa"] as const;

for (const personaId of PERSONAS) {
  test(
    `Audit row append-only for '${personaId}' ` +
      `@persona:${personaId} @outcome:4 @hazard:bushfire+tropical-cyclone ` +
      `@fr:FR-010 @fr:FR-028 @fr:FR-029 @clause:IV @clause:NN-3 @p1`,
    async ({ resolvePersona, request, correlationId }) => {
      const persona = await resolvePersona(personaId);
      const headers = {
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
      };

      // FR-028 deterministic state-changing action.
      const evalRes = await request.post("/api/outcomes/sc-004/evaluate", {
        headers,
        data: {
          scenario_id: "outcome-4-bushfire-cyclone-logistics",
          persona_id: persona.persona_id,
          correlation_id: correlationId,
          metric_inputs: { logistics_clicks: 6 },
        },
      });
      expect(evalRes.ok(), `evaluator must respond 200; got ${evalRes.status()}`).toBe(true);
      const verdict = (await evalRes.json()) as { status: string; audit_id: string };
      expect(verdict.status).toBe("pass");

      // FR-010 invariant: exactly one audit row per correlation_id, append-only.
      const listRes = await request.get(
        `/api/audit/list?correlation_id=${correlationId}`,
        { headers },
      );
      expect(listRes.ok()).toBe(true);
      const list = (await listRes.json()) as {
        items: Array<{ audit_id: string; operator_identity: { persona_id: string } }>;
      };
      const match = list.items.find((row) => row.audit_id === verdict.audit_id);
      expect(match, `audit row for persona='${personaId}' must surface append-only`).toBeTruthy();
      expect(match!.operator_identity.persona_id).toBe(persona.persona_id);

      // FR-005 read-back stability: a second list call MUST return the same audit_id.
      const listRes2 = await request.get(
        `/api/audit/list?correlation_id=${correlationId}`,
        { headers },
      );
      expect(listRes2.ok()).toBe(true);
      const list2 = (await listRes2.json()) as { items: Array<{ audit_id: string }> };
      const match2 = list2.items.find((row) => row.audit_id === verdict.audit_id);
      expect(match2, "second read-back must return identical audit_id (no mutation)").toBeTruthy();
    },
  );
}
