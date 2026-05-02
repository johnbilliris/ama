/**
 * Hazard scenario fixture (T024). Resolves outcomes 1-5 to deterministic
 * fixture data via the test-support endpoint plus the static JSON files
 * under ./data/.
 */
import { test as baseTest } from "@playwright/test";
import type { HazardScenarioFixture } from "../types/persona";

type ScenarioFixtures = {
  resolveScenario: (scenarioId: string) => Promise<HazardScenarioFixture>;
};

const cache = new Map<string, HazardScenarioFixture>();

export const scenarioResolver = baseTest.extend<ScenarioFixtures>({
  resolveScenario: async ({ request }, use) => {
    await use(async (scenarioId: string) => {
      const cached = cache.get(scenarioId);
      if (cached) {
        return cached;
      }
      const res = await request.post("/api/test-support/seed/scenario", {
        data: { scenario_id: scenarioId },
      });
      if (!res.ok()) {
        throw new Error(
          `hazardScenarioFixture: scenario '${scenarioId}' not found (${res.status()}). ` +
            `Confirm bootstrap_seed_data().hazard_scenarios is loaded.`,
        );
      }
      const body = (await res.json()) as { scenario: HazardScenarioFixture };
      cache.set(scenarioId, body.scenario);
      return body.scenario;
    });
  },
});

export type { HazardScenarioFixture };
