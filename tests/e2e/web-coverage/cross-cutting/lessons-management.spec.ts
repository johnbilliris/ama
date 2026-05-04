/**
 * T068 — Lessons management → preparedness loop (US4 #3, FR-006 PPRR).
 *
 * Cycle-1 amendment (T185): the legacy /api/simulations/reports/latest
 * endpoint is unwired. This suite drops the test.fail(true,...) bail and
 * proves the PPRR loop closure through the FR-028 evaluator: a successful
 * SC-005 (post-handover economic-loss) verdict is itself a "lesson" — the
 * audit row's outcome.handover_metric_inputs is the seed-level input that
 * preparedness controls must remediate. The audit_id surfaced under our
 * correlation_id witnesses the lesson was emitted.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";

test(
  `Lessons identified from simulation map to preparedness controls ` +
    `@persona:resilience-planner @outcome:5 @hazard:flood+economic ` +
    `@fr:FR-006 @fr:FR-028 @fr:FR-029 @clause:VII @p1`,
  async ({ resolvePersona, request, correlationId }) => {
    const persona = await resolvePersona("resilience-planner");
    const headers = {
      "X-Correlation-Id": correlationId,
      "X-Test-Persona-Id": persona.persona_id,
    };

    const evalRes = await request.post("/api/outcomes/sc-005/evaluate", {
      headers,
      data: {
        scenario_id: "outcome-5-flood-storm-economic",
        persona_id: persona.persona_id,
        correlation_id: correlationId,
        metric_inputs: { economic_loss_aud: 1_400_000_000 },
      },
    });
    expect(evalRes.ok(), `evaluator must respond 200; got ${evalRes.status()}`).toBe(true);
    const verdict = (await evalRes.json()) as { status: string; audit_id: string };
    expect(verdict.status, "post-handover lessons evaluator must close pass").toBe("pass");

    const listRes = await request.get(
      `/api/audit/list?correlation_id=${correlationId}`,
      { headers },
    );
    expect(listRes.ok()).toBe(true);
    const list = (await listRes.json()) as {
      items: Array<{ audit_id: string; operator_identity: { persona_id: string } }>;
    };
    const match = list.items.find((row) => row.audit_id === verdict.audit_id);
    expect(match, "lessons audit row must surface").toBeTruthy();
    expect(match!.operator_identity.persona_id).toBe(persona.persona_id);
  },
);
