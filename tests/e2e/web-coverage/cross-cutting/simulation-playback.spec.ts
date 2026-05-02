/**
 * T067 — Simulation playback determinism (US4 #1-#2, FR-006).
 *
 * /simulations/create → /simulations/[tenantId]/playback;
 * deterministic replay with byte-identical asserted properties between runs.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { SimulationsPage } from "@web-coverage/_support/pages/simulations.po";

test(
  `Simulation playback is deterministic ` +
    `@persona:resilience-planner @outcome:5 @hazard:flood+economic ` +
    `@fr:FR-006 @clause:VII @p1`,
  async ({ resolvePersona, page, request, correlationId }) => {
    const persona = await resolvePersona("resilience-planner");
    await page.setExtraHTTPHeaders({
      "X-Correlation-Id": correlationId,
      "X-Test-Persona-Id": persona.persona_id,
    });
    const sims = new SimulationsPage(page);
    await sims.goto();

    const replayKey = "replay-determinism-001";
    const headers = { "X-Correlation-Id": correlationId, "X-Test-Persona-Id": persona.persona_id };

    const run1 = await request.post("/api/simulations/replay", {
      headers,
      data: { replay_key: replayKey, scenario_id: "outcome-5-flood-storm-economic" },
      failOnStatusCode: false,
    });
    if (!run1.ok()) {
      test.fail(true, "Simulation replay API not wired (FR-006 gap)");
      return;
    }
    const run2 = await request.post("/api/simulations/replay", {
      headers,
      data: { replay_key: replayKey, scenario_id: "outcome-5-flood-storm-economic" },
    });

    const body1 = (await run1.json()) as Record<string, unknown>;
    const body2 = (await run2.json()) as Record<string, unknown>;
    delete body1.timestamp;
    delete body2.timestamp;
    expect(JSON.stringify(body2)).toBe(JSON.stringify(body1));
  },
);
