/**
 * T149 — Capstone Outcome 4: 30% logistics-friction reduction.
 *
 * Proxy (SC-004):
 *   • routine logistics actions ≤ 7 clicks
 *   • mutual-aid request ≤ 12 clicks
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { validateOutcomeProxy } from "@web-coverage/_support/validators/outcome-proxy";
import outcome4 from "@web-coverage/_support/fixtures/data/outcome-4-bushfire-cyclone-logistics.fixture.json";

test(
  `Capstone Outcome 4 closes — 30% logistics friction reduction (SC-004) ` +
    `@persona:logistics-officer @outcome:4 @hazard:bushfire+tropical-cyclone ` +
    `@fr:FR-015 @clause:VIII @p1`,
  async ({ resolvePersona, request, correlationId }) => {
    const persona = await resolvePersona("logistics-officer");
    expect(outcome4.outcome).toBe(4);

    const res = await request.post("/api/outcomes/sc-004/evaluate", {
      headers: {
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
      },
      data: { scenario: "outcome-4-bushfire-cyclone-logistics" },
      failOnStatusCode: false,
    });
    if (!res.ok()) {
      test.fail(true, "Outcome SC-004 evaluator API not wired (gap)");
      return;
    }
    const body = (await res.json()) as { routine_clicks?: number; mutual_aid_clicks?: number };
    expect(body.routine_clicks ?? Number.POSITIVE_INFINITY).toBeLessThanOrEqual(7);
    expect(body.mutual_aid_clicks ?? Number.POSITIVE_INFINITY).toBeLessThanOrEqual(12);

    const validation = validateOutcomeProxy({
      persona_id: persona.persona_id,
      aiims_function: "logistics",
      outcome: 4,
      hazard: "bushfire+tropical-cyclone",
      fr_id: "FR-015",
      constitution_clauses: ["VIII"],
      test_ids: [test.info().testId],
      route: "/operations/workflows",
      audit_evidence_id: null,
      correlation_id: correlationId,
      status: "passed",
      duration_ms: 0,
      emitted_at: new Date().toISOString(),
    });
    expect(validation.reasons, validation.reasons.join("; ")).toEqual([]);
  },
);
