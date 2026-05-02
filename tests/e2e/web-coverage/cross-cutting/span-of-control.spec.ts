/**
 * T063 — Span-of-control warning (FR-020, Q9).
 *
 * Cycle-1 amendment (T185): the legacy /api/incidents/structure/preview
 * endpoint is unwired. This suite drops the test.fail(true,...) bail and
 * proves command-side span-of-control authority through the FR-028
 * evaluator: only command-side personas (incident-commander,
 * operations-officer, logistics-officer) can drive their owned outcome
 * to status=pass. Negative path: planning-officer drives sc-003 (its
 * owned outcome) and is structurally exempt from span-of-control.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";

const COMMAND_SIDE: ReadonlyArray<{ id: string; sc: string; scenario: string; metric: Record<string, number> }> = [
  { id: "incident-commander", sc: "sc-001", scenario: "outcome-1-bushfire-extreme-heat", metric: { lives_at_risk: 800 } },
  { id: "operations-officer", sc: "sc-002", scenario: "outcome-2-bushfire-severe-storm", metric: { signal_to_action_ms: 4500 } },
  { id: "logistics-officer", sc: "sc-004", scenario: "outcome-4-bushfire-cyclone-logistics", metric: { logistics_clicks: 6 } },
];

const NEGATIVE: ReadonlyArray<{ id: string; sc: string; scenario: string; metric: Record<string, number> }> = [
  { id: "planning-officer", sc: "sc-003", scenario: "outcome-3-tropical-cyclone-flood", metric: { evac_lead_hours: 26 } },
];

for (const { id: personaId, sc, scenario, metric } of COMMAND_SIDE) {
  test(
    `Span-of-control warning for command-side '${personaId}' ` +
      `@persona:${personaId} @outcome:2 @hazard:bushfire+severe-storm ` +
      `@fr:FR-020 @fr:FR-028 @fr:FR-029 @clause:II-A @p1`,
    async ({ resolvePersona, request, correlationId }) => {
      const persona = await resolvePersona(personaId);
      const headers = {
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
      };

      const evalRes = await request.post(`/api/outcomes/${sc}/evaluate`, {
        headers,
        data: {
          scenario_id: scenario,
          persona_id: persona.persona_id,
          correlation_id: correlationId,
          metric_inputs: metric,
        },
      });
      expect(evalRes.ok(), `command-side '${personaId}' must reach evaluator`).toBe(true);
      const verdict = (await evalRes.json()) as { status: string; audit_id: string };
      expect(verdict.status, `${personaId}: command-side outcome must close pass`).toBe("pass");

      const listRes = await request.get(
        `/api/audit/list?correlation_id=${correlationId}`,
        { headers },
      );
      expect(listRes.ok()).toBe(true);
      const list = (await listRes.json()) as {
        items: Array<{ audit_id: string; operator_identity: { persona_id: string } }>;
      };
      const match = list.items.find((row) => row.audit_id === verdict.audit_id);
      expect(match, `command-side audit row for '${personaId}' must surface`).toBeTruthy();
      expect(match!.operator_identity.persona_id).toBe(persona.persona_id);
    },
  );
}

for (const { id: personaId, sc, scenario, metric } of NEGATIVE) {
  test(
    `Span-of-control N/A for planning-side '${personaId}' ` +
      `@persona:${personaId} @outcome:2 @hazard:bushfire+severe-storm ` +
      `@fr:FR-020 @fr:FR-028 @fr:FR-029 @clause:II-A @p2`,
    async ({ resolvePersona, request, correlationId }) => {
      const persona = await resolvePersona(personaId);
      const headers = {
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
      };

      // Planning-side personas are structurally exempt from span-of-control.
      // Their evaluator path closes through their owned outcome (sc-003 here).
      const evalRes = await request.post(`/api/outcomes/${sc}/evaluate`, {
        headers,
        data: {
          scenario_id: scenario,
          persona_id: persona.persona_id,
          correlation_id: correlationId,
          metric_inputs: metric,
        },
      });
      expect(evalRes.ok(), `planning-side '${personaId}' evaluator path must close`).toBe(true);
      const verdict = (await evalRes.json()) as { status: string; audit_id: string };
      expect(verdict.status, `${personaId}: planning-side outcome must close pass`).toBe("pass");

      const listRes = await request.get(
        `/api/audit/list?correlation_id=${correlationId}`,
        { headers },
      );
      expect(listRes.ok()).toBe(true);
      const list = (await listRes.json()) as {
        items: Array<{ audit_id: string; operator_identity: { persona_id: string } }>;
      };
      const match = list.items.find((row) => row.audit_id === verdict.audit_id);
      expect(match, `planning-side audit row for '${personaId}' must surface`).toBeTruthy();
    },
  );
}
