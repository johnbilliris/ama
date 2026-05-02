/**
 * T150 — Capstone Outcome 5: 30% economic-loss reduction.
 *
 * Proxy (SC-005, Q7):
 *   (baseline_loss − projected_loss) / baseline_loss ≥ 0.30
 *
 * Evaluated at response→recovery handover on the post-handover Economic
 * environment view (FR-013).
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { validateOutcomeProxy } from "@web-coverage/_support/validators/outcome-proxy";
import outcome5 from "@web-coverage/_support/fixtures/data/outcome-5-flood-storm-economic.fixture.json";

test(
  `Capstone Outcome 5 closes — 30% economic-loss reduction (SC-005) ` +
    `@persona:executive-leader @outcome:5 @hazard:riverine-flood+severe-storm ` +
    `@fr:FR-013 @clause:VII @p1`,
  async ({ resolvePersona, request, correlationId }) => {
    const persona = await resolvePersona("executive-leader");
    expect(outcome5.outcome).toBe(5);

    const res = await request.post("/api/outcomes/sc-005/evaluate", {
      headers: {
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
      },
      data: { scenario: "outcome-5-flood-storm-economic" },
      failOnStatusCode: false,
    });
    if (!res.ok()) {
      test.fail(true, "Outcome SC-005 evaluator API not wired (gap)");
      return;
    }
    const body = (await res.json()) as { baseline_loss?: number; projected_loss?: number };
    const baseline = body.baseline_loss ?? 0;
    const projected = body.projected_loss ?? baseline;
    const reduction = baseline > 0 ? (baseline - projected) / baseline : 0;
    expect(reduction).toBeGreaterThanOrEqual(0.3);

    const validation = validateOutcomeProxy({
      persona_id: persona.persona_id,
      aiims_function: "control",
      outcome: 5,
      hazard: "riverine-flood+severe-storm",
      fr_id: "FR-013",
      constitution_clauses: ["VII"],
      test_ids: [test.info().testId],
      route: "/governance/dashboard",
      audit_evidence_id: null,
      correlation_id: correlationId,
      status: "passed",
      duration_ms: 0,
      emitted_at: new Date().toISOString(),
    });
    expect(validation.reasons, validation.reasons.join("; ")).toEqual([]);
  },
);
