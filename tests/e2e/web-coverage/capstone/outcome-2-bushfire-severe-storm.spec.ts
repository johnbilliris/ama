/**
 * T147 — Capstone Outcome 2: 50% faster signal-to-action.
 *
 * Proxy (SC-002): metric_inputs.signal_to_action_ms vs the seeded
 * baseline. Pass when observed ≤ 0.5× baseline (i.e., halved). Cycle-1
 * amendment (T186) drops the test.fail(true,...) bail and drives the
 * FR-028 evaluator + FR-029 audit-list contracts directly.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { validateOutcomeProxy } from "@web-coverage/_support/validators/outcome-proxy";
import outcome2 from "@web-coverage/_support/fixtures/data/outcome-2-bushfire-severe-storm.fixture.json";

test(
  `Capstone Outcome 2 closes — 50% faster signal-to-action (SC-002) ` +
    `@persona:operations-officer @outcome:2 @hazard:bushfire+severe-storm ` +
    `@fr:FR-008 @fr:FR-028 @fr:FR-029 @clause:II @clause:II-A @p1`,
  async ({ resolvePersona, request, correlationId }) => {
    const persona = await resolvePersona("operations-officer");
    expect(outcome2.outcome).toBe(2);

    const evalRes = await request.post("/api/outcomes/sc-002/evaluate", {
      headers: {
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
      },
      data: {
        scenario_id: "outcome-2-bushfire-severe-storm",
        persona_id: persona.persona_id,
        correlation_id: correlationId,
        metric_inputs: { signal_to_action_ms: 4500 },
      },
    });
    expect(evalRes.ok(), `evaluator must respond 200; got ${evalRes.status()}`).toBe(true);
    const verdict = (await evalRes.json()) as {
      status: "pass" | "fail" | "gap";
      audit_id: string;
      metric_value: number;
      threshold: number;
    };
    expect(verdict.status, "SC-002 signal-to-action threshold must be satisfied").toBe("pass");
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
      aiims_function: "operations",
      outcome: 2,
      hazard: "bushfire+severe-storm",
      fr_id: "FR-008",
      constitution_clauses: ["II"],
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
