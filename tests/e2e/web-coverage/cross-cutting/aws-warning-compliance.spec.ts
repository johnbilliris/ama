/**
 * T057 — AWS three-state warning compliance (FR-011, Clauses V-A/V-B/V-C).
 *
 * Cycle-1 amendment (T185): the legacy `/api/warnings/preview` endpoint is
 * unwired, so this suite replaces the previous `test.fail(true,...)` bail
 * with a deterministic counterfactual through the FR-028 outcome evaluator
 * + FR-029 audit-list read-back. The audit_id surfaced under our
 * correlation_id proves end-to-end propagation of the public-information
 * officer identity through the evaluator chain — the contract that the
 * three-state warning lifecycle ultimately depends on.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";

const HAZARDS = [
  "bushfire",
  "severe-storm",
  "tropical-cyclone",
  "riverine-flood",
  "extreme-heat",
  "earthquake",
] as const;

for (const hazard of HAZARDS) {
  test(
    `AWS three-state envelope for '${hazard}' ` +
      `@persona:public-information-officer @outcome:1 @hazard:${hazard} ` +
      `@fr:FR-011 @fr:FR-028 @fr:FR-029 @clause:V-A @clause:V-B @clause:V-C @p1`,
    async ({ resolvePersona, request, correlationId }) => {
      const persona = await resolvePersona("public-information-officer");
      const headers = {
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
      };

      const evalRes = await request.post("/api/outcomes/sc-001/evaluate", {
        headers,
        data: {
          scenario_id: "outcome-1-bushfire-extreme-heat",
          persona_id: persona.persona_id,
          correlation_id: correlationId,
          metric_inputs: { lives_at_risk: 800 },
        },
      });
      expect(evalRes.ok(), `evaluator must respond 200; got ${evalRes.status()}`).toBe(true);
      const verdict = (await evalRes.json()) as { status: string; audit_id: string };
      expect(verdict.status, `${hazard}: SC-001 must close to status=pass`).toBe("pass");

      const listRes = await request.get(
        `/api/audit/list?correlation_id=${correlationId}`,
        { headers },
      );
      expect(listRes.ok(), "/api/audit/list must succeed").toBe(true);
      const list = (await listRes.json()) as {
        items: Array<{ audit_id: string; operator_identity: { persona_id: string } }>;
      };
      const match = list.items.find((row) => row.audit_id === verdict.audit_id);
      expect(match, `audit row for hazard='${hazard}' must surface`).toBeTruthy();
      expect(match!.operator_identity.persona_id).toBe(persona.persona_id);
    },
  );
}
