/**
 * Composed Playwright test for the web-coverage suite.
 *
 * Merges the persona + scenario + correlation-id + audit-observer fixtures
 * so cross-cutting and persona specs only import this one symbol.
 *
 *   import { test, expect } from "@web-coverage/_support/webCoverageTest";
 *   test("...", async ({ resolvePersona, correlationId, expectAudit }) => {});
 */
import { expect, mergeTests } from "@playwright/test";
import { personaResolver } from "./fixtures/persona.fixture";
import { scenarioResolver } from "./fixtures/hazardScenario.fixture";
import { correlationFixture } from "./fixtures/correlationId.fixture";
import { auditObserver } from "./fixtures/auditObserver.fixture";

export const test = mergeTests(
  personaResolver,
  scenarioResolver,
  correlationFixture,
  auditObserver,
);

export { expect };
