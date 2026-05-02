/**
 * T150 — Capstone Outcome 5: 30% economic-loss reduction.
 *
 * Proxy (SC-005, Q7): metric_inputs.economic_loss_aud, evaluator pass
 * when (baseline − observed) / baseline ≥ 0.30. Cycle-1 amendment
 * (T186) drops the test.fail(true,...) bail and drives the FR-028
 * evaluator + FR-029 audit-list contracts directly. Evaluated at
 * response→recovery handover on the post-handover Economic environment
 * view (FR-013).
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { validateOutcomeProxy } from "@web-coverage/_support/validators/outcome-proxy";
import outcome5 from "@web-coverage/_support/fixtures/data/outcome-5-flood-storm-economic.fixture.json";

test(
  `Capstone Outcome 5 closes — 30% economic-loss reduction (SC-005) ` +
    `@persona:executive-leader @outcome:5 @hazard:riverine-flood+severe-storm ` +
    `@fr:FR-013 @fr:FR-028 @fr:FR-029 @clause:VII @p1`,
  async ({ resolvePersona, request, correlationId }) => {
    const persona = await resolvePersona("executive-leader");
    expect(outcome5.outcome).toBe(5);

    const evalRes = await request.post("/api/outcomes/sc-005/evaluate", {
      headers: {
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
      },
      data: {
        scenario_id: "outcome-5-flood-storm-economic",
        persona_id: persona.persona_id,
        correlation_id: correlationId,
        metric_inputs: { economic_loss_aud: 1_400_000_000 },
      },
    });
    expect(evalRes.ok(), `evaluator must respond 200; got ${evalRes.status()}`).toBe(true);
    const verdict = (await evalRes.json()) as {
      status: "pass" | "fail" | "gap";
      audit_id: string;
      metric_value: number;
      threshold: number;
    };
    expect(verdict.status, "SC-005 economic-loss threshold must be satisfied").toBe("pass");
    expect(verdict.metric_value).toBeLessThanOrEqual(verdict.threshold);

    const listRes = await request.get(
      `/api/audit/list?correlation_id=${correlationId}`,
      {
        headers: {
          "X-Correlation-Id": correlationId,
          "X-Test-Persona-Id": persona.persona_id,
        },
      },
    );
    expect(listRes.ok(), "/api/audit/list must succeed").toBe(true);
    const list = (await listRes.json()) as {
      items: Array<{
        audit_id: string;
        operator_identity: { persona_id: string };
      }>;
    };
    const match = list.items.find((row) => row.audit_id === verdict.audit_id);
    expect(match, "evaluator audit_id must appear in /api/audit/list").toBeTruthy();
    expect(match!.operator_identity.persona_id).toBe(persona.persona_id);

    const validation = validateOutcomeProxy({
      persona_id: persona.persona_id,
      aiims_function: "control",
      outcome: 5,
      hazard: "riverine-flood+severe-storm",
      fr_id: "FR-013",
      constitution_clauses: ["VII"],
      test_ids: [test.info().testId],
      route: "/governance/dashboard",
      audit_evidence_id: verdict.audit_id,
      correlation_id: correlationId,
      status: "passed",
      duration_ms: 0,
      emitted_at: new Date().toISOString(),
    });
    expect(validation.reasons, validation.reasons.join("; ")).toEqual([]);
  },
);
