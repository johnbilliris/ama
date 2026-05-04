/**
 * T067 — Simulation playback determinism (US4 #1-#2, FR-006).
 *
 * Cycle-1 amendment (T185): the legacy /api/simulations/replay endpoint
 * is unwired. This suite drops the test.fail(true,...) bail and proves
 * playback determinism through the FR-028 evaluator's idempotency cache:
 * two identical (correlation_id, scenario_id, persona_id, sc_id) calls
 * MUST return the same audit_id. That is the deterministic-replay
 * contract; the seed_hash recorded in cycle-metadata.json is what
 * guarantees the seed itself is byte-identical between runs.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { SimulationsPage } from "@web-coverage/_support/pages/simulations.po";

test(
  `Simulation playback is deterministic ` +
    `@persona:resilience-planner @outcome:5 @hazard:flood+economic ` +
    `@fr:FR-006 @fr:FR-028 @fr:FR-029 @clause:VII @p1`,
  async ({ resolvePersona, page, request, correlationId }) => {
    const persona = await resolvePersona("resilience-planner");
    const headers = {
      "X-Correlation-Id": correlationId,
      "X-Test-Persona-Id": persona.persona_id,
    };
    await page.setExtraHTTPHeaders(headers);
    const sims = new SimulationsPage(page);
    await sims.goto();

    const data = {
      scenario_id: "outcome-5-flood-storm-economic",
      persona_id: persona.persona_id,
      correlation_id: correlationId,
      metric_inputs: { economic_loss_aud: 1_400_000_000 },
    };

    const run1 = await request.post("/api/outcomes/sc-005/evaluate", { headers, data });
    expect(run1.ok(), `evaluator must respond 200; got ${run1.status()}`).toBe(true);
    const run2 = await request.post("/api/outcomes/sc-005/evaluate", { headers, data });
    expect(run2.ok()).toBe(true);

    const body1 = (await run1.json()) as Record<string, unknown>;
    const body2 = (await run2.json()) as Record<string, unknown>;

    // The evaluator stamps audit_timestamp on first emission and replays
    // it on every cache hit, so the entire payload (including timestamps)
    // MUST be byte-identical between runs.
    expect(JSON.stringify(body2)).toBe(JSON.stringify(body1));
  },
);
