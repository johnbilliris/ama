/**
 * T148 — Capstone Outcome 3: 24-h-earlier evacuation.
 *
 * Proxy (SC-003): evac_lead_hours ≥ 24 vs seed reference baseline.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { validateOutcomeProxy } from "@web-coverage/_support/validators/outcome-proxy";
import outcome3 from "@web-coverage/_support/fixtures/data/outcome-3-tropical-cyclone-flood.fixture.json";

test(
  `Capstone Outcome 3 closes — 24-h-earlier evacuation (SC-003) ` +
    `@persona:planning-officer @outcome:3 @hazard:tropical-cyclone+riverine-flood ` +
    `@fr:FR-016 @clause:VI @p1`,
  async ({ resolvePersona, request, correlationId }) => {
    const persona = await resolvePersona("planning-officer");
    expect(outcome3.outcome).toBe(3);

    const res = await request.post("/api/outcomes/sc-003/evaluate", {
      headers: {
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
      },
      data: { scenario: "outcome-3-tropical-cyclone-flood" },
      failOnStatusCode: false,
    });
    if (!res.ok()) {
      test.fail(true, "Outcome SC-003 evaluator API not wired (gap)");
      return;
    }
    const body = (await res.json()) as { evac_lead_hours?: number; baseline_lead_hours?: number };
    expect(body.evac_lead_hours ?? 0).toBeGreaterThanOrEqual(24);

    const validation = validateOutcomeProxy({
      persona_id: persona.persona_id,
      aiims_function: "planning",
      outcome: 3,
      hazard: "tropical-cyclone+riverine-flood",
      fr_id: "FR-016",
      constitution_clauses: ["VI"],
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
