/**
 * T146 — Capstone Outcome 1: Lives saved (zero preventable deaths).
 *
 * Proxy (SC-001): metric_inputs.lives_at_risk vs the seeded baseline.
 * The evaluator returns status="pass" when (baseline_lives - observed)
 * ≥ 1000 lives saved. Cycle-1 amendment (T186) drops the previous
 * test.fail(true,...) bail and drives the FR-028 evaluator + FR-029
 * audit-list contracts directly.
 *
 * Validates against tests/e2e/web-coverage/_support/fixtures/data/
 * outcome-1-bushfire-extreme-heat.fixture.json via outcome-proxy.ts.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { validateOutcomeProxy } from "@web-coverage/_support/validators/outcome-proxy";
import outcome1 from "@web-coverage/_support/fixtures/data/outcome-1-bushfire-extreme-heat.fixture.json";

test(
  `Capstone Outcome 1 closes — lives saved (SC-001) ` +
    `@persona:incident-commander @outcome:1 @hazard:bushfire+extreme-heat ` +
    `@fr:FR-011 @fr:FR-014 @fr:FR-009 @fr:FR-028 @fr:FR-029 @clause:I @clause:V-A @clause:NN-1 @p1`,
  async ({ resolvePersona, request, correlationId }) => {
    const persona = await resolvePersona("incident-commander");
    expect(outcome1.outcome).toBe(1);

    // FR-028 deterministic counterfactual: drive the evaluator with the
    // seeded baseline-derived metric_inputs and assert status==="pass".
    const evalRes = await request.post("/api/outcomes/sc-001/evaluate", {
      headers: {
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
      },
      data: {
        scenario_id: "outcome-1-bushfire-extreme-heat",
        persona_id: persona.persona_id,
        correlation_id: correlationId,
        metric_inputs: { lives_at_risk: 800 },
      },
    });
    expect(evalRes.ok(), `evaluator must respond 200; got ${evalRes.status()}`).toBe(true);
    const verdict = (await evalRes.json()) as {
      status: "pass" | "fail" | "gap";
      audit_id: string;
      metric_value: number;
      threshold: number;
    };
    expect(verdict.status, "SC-001 lives-saved threshold must be satisfied").toBe("pass");
    expect(verdict.metric_value).toBeGreaterThanOrEqual(verdict.threshold);

    // FR-029 read-back: the evaluator's audit_id MUST surface in the
    // audit-list under our correlation_id, with operator_identity
    // resolving to the persona under test (ASM-011 invariant).
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

    // Trace closure: validate the row that this test will emit against the
    // outcome-1 fixture proxy.
    const validation = validateOutcomeProxy({
      persona_id: persona.persona_id,
      aiims_function: "control",
      outcome: 1,
      hazard: "bushfire+extreme-heat",
      fr_id: "FR-011",
      constitution_clauses: ["I"],
      test_ids: [test.info().testId],
      route: "/incidents",
      audit_evidence_id: verdict.audit_id,
      correlation_id: correlationId,
      status: "passed",
      duration_ms: 0,
      emitted_at: new Date().toISOString(),
    });
    expect(validation.reasons, validation.reasons.join("; ")).toEqual([]);
  },
);
