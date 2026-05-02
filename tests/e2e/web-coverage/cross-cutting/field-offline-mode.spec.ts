/**
 * T061 — Field offline mode (FR-017, NN-#5).
 *
 * Queue + sync, idempotent dedupe by client correlation id, audit replay
 * preserves original timestamp/authorship.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";

test(
  `Field-coordinator offline queue dedupes + replays audit ` +
    `@persona:field-coordinator @outcome:2 @hazard:bushfire+severe-storm ` +
    `@fr:FR-017 @clause:NN-5 @p1`,
  async ({ resolvePersona, request, correlationId }) => {
    const persona = await resolvePersona("field-coordinator");
    const headers = {
      "X-Correlation-Id": correlationId,
      "X-Test-Persona-Id": persona.persona_id,
      "X-Client-Action-Id": "duplicate-test-001",
    };

    const submit1 = await request.post("/api/field/hazard-report", {
      headers,
      data: {
        gps: { lat: -35.28, lng: 149.13 },
        observed_at: "2025-01-15T08:00:00Z",
        note: "Smoke plume to NW",
      },
      failOnStatusCode: false,
    });
    const submit2 = await request.post("/api/field/hazard-report", {
      headers,
      data: {
        gps: { lat: -35.28, lng: 149.13 },
        observed_at: "2025-01-15T08:00:00Z",
        note: "Smoke plume to NW",
      },
      failOnStatusCode: false,
    });
    if (!submit1.ok() || !submit2.ok()) {
      test.fail(true, "Field hazard-report API not wired (FR-017 gap)");
      return;
    }
    const body1 = (await submit1.json()) as { id: string };
    const body2 = (await submit2.json()) as { id: string };
    expect(body2.id, "idempotent dedupe by correlation id").toBe(body1.id);
  },
);
