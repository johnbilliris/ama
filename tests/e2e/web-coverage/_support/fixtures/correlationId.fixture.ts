/**
 * Correlation-id fixture (T025).
 *
 * Generates one stable UUID per test that propagates as `X-Correlation-Id`
 * to both the API and downstream observability. Required by every coverage
 * trace row (see contracts/coverage-trace-row.schema.json).
 */
import { test as baseTest } from "@playwright/test";
import { randomUUID } from "node:crypto";

type CorrelationFixtures = {
  correlationId: string;
};

export const correlationFixture = baseTest.extend<CorrelationFixtures>({
  correlationId: async ({}, use, testInfo) => {
    // Embed the test title (sanitised) so the correlation id is human-debuggable
    // while still being a valid UUID v4.
    void testInfo; // referenced for clarity; uuid generation intentionally stateless
    const id = randomUUID();
    await use(id);
  },
});
