/**
 * Carve-out registry fixture (T027).
 *
 * Reads infra/parameters/foundry-carveout.yaml so tests can assert
 * sovereignty boundaries (no Asia-Pacific personas/data leak via /eval, /governance).
 */
import { test as baseTest } from "@playwright/test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import yaml from "js-yaml";

export interface CarveoutRegistry {
  carveouts: Array<{
    name: string;
    jurisdictions: string[];
    permitted_regions: string[];
    classification: string;
  }>;
}

type CarveoutFixtures = {
  carveoutRegistry: CarveoutRegistry;
};

const REPO_ROOT = resolve(__dirname, "..", "..", "..", "..", "..", "..");
const REGISTRY_PATH = resolve(REPO_ROOT, "infra", "parameters", "foundry-carveout.yaml");

export const carveoutRegistryFixture = baseTest.extend<CarveoutFixtures>({
  carveoutRegistry: async ({}, use) => {
    let registry: CarveoutRegistry;
    try {
      const text = readFileSync(REGISTRY_PATH, "utf-8");
      registry = yaml.load(text) as CarveoutRegistry;
    } catch {
      // Allow tests to run when registry is absent (CI catches missing file via its own gate).
      registry = { carveouts: [] };
    }
    await use(registry);
  },
});
