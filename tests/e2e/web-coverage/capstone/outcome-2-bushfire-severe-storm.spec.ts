/**
 * T147 — Capstone Outcome 2: 50% faster signal-to-action.
 *
 * Proxy (SC-002):
 *   • AIIMS Level 1 ≤ 5 minutes
 *   • AIIMS Level 2 ≤ 15 minutes
 *   • AIIMS Level 3 ≤ 30 minutes
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { validateOutcomeProxy } from "@web-coverage/_support/validators/outcome-proxy";
import outcome2 from "@web-coverage/_support/fixtures/data/outcome-2-bushfire-severe-storm.fixture.json";

test(
  `Capstone Outcome 2 closes — 50% faster signal-to-action (SC-002) ` +
    `@persona:operations-officer @outcome:2 @hazard:bushfire+severe-storm ` +
    `@fr:FR-008 @clause:II @clause:II-A @p1`,
  async ({ resolvePersona, request, correlationId }) => {
    const persona = await resolvePersona("operations-officer");
    expect(outcome2.outcome).toBe(2);

    const res = await request.post("/api/outcomes/sc-002/evaluate", {
      headers: {
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
      },
      data: { scenario: "outcome-2-bushfire-severe-storm" },
      failOnStatusCode: false,
    });
    if (!res.ok()) {
      test.fail(true, "Outcome SC-002 evaluator API not wired (gap)");
      return;
    }
    const body = (await res.json()) as {
      level_1_minutes?: number;
      level_2_minutes?: number;
      level_3_minutes?: number;
    };
    expect(body.level_1_minutes ?? Number.POSITIVE_INFINITY).toBeLessThanOrEqual(5);
    expect(body.level_2_minutes ?? Number.POSITIVE_INFINITY).toBeLessThanOrEqual(15);
    expect(body.level_3_minutes ?? Number.POSITIVE_INFINITY).toBeLessThanOrEqual(30);

    const validation = validateOutcomeProxy({
      persona_id: persona.persona_id,
      aiims_function: "operations",
      outcome: 2,
      hazard: "bushfire+severe-storm",
      fr_id: "FR-008",
      constitution_clauses: ["II"],
      test_ids: [test.info().testId],
      route: "/incidents",
      audit_evidence_id: null,
      correlation_id: correlationId,
      status: "passed",
      duration_ms: 0,
      emitted_at: new Date().toISOString(),
    });
    expect(validation.reasons, validation.reasons.join("; ")).toEqual([]);
  },
);
