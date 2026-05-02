/**
 * T063 — Span-of-control warning (FR-020, Q9).
 *
 * Command-side persona with > 7 direct reports surfaces a warning before
 * save. Negative test: planning-side persona is exempt.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";

const COMMAND_SIDE = ["incident-commander", "operations-officer", "logistics-officer"] as const;
const NEGATIVE = ["planning-officer"] as const;

for (const personaId of COMMAND_SIDE) {
  test(
    `Span-of-control warning for command-side '${personaId}' ` +
      `@persona:${personaId} @outcome:2 @hazard:bushfire+severe-storm ` +
      `@fr:FR-020 @clause:II-A @p1`,
    async ({ resolvePersona, request, correlationId }) => {
      const persona = await resolvePersona(personaId);
      const res = await request.post("/api/incidents/structure/preview", {
        headers: {
          "X-Correlation-Id": correlationId,
          "X-Test-Persona-Id": persona.persona_id,
        },
        data: { direct_reports: Array.from({ length: 9 }, (_, i) => `report-${i}`) },
        failOnStatusCode: false,
      });
      if (!res.ok()) {
        test.fail(true, "Incident structure API not wired (FR-020 gap)");
        return;
      }
      const body = (await res.json()) as { warnings?: string[] };
      expect(
        (body.warnings ?? []).some((w) => /span.of.control/i.test(w)),
        "span-of-control warning expected when direct_reports > 7",
      ).toBe(true);
    },
  );
}

for (const personaId of NEGATIVE) {
  test(
    `Span-of-control N/A for planning-side '${personaId}' ` +
      `@persona:${personaId} @outcome:2 @hazard:bushfire+severe-storm ` +
      `@fr:FR-020 @clause:II-A @p2`,
    async ({ resolvePersona, request, correlationId }) => {
      const persona = await resolvePersona(personaId);
      const res = await request.post("/api/incidents/structure/preview", {
        headers: {
          "X-Correlation-Id": correlationId,
          "X-Test-Persona-Id": persona.persona_id,
        },
        data: { direct_reports: Array.from({ length: 9 }, (_, i) => `report-${i}`) },
        failOnStatusCode: false,
      });
      if (!res.ok()) {
        test.fail(true, "Incident structure API not wired (FR-020 gap)");
        return;
      }
      const body = (await res.json()) as { warnings?: string[] };
      expect((body.warnings ?? []).filter((w) => /span.of.control/i.test(w))).toHaveLength(0);
    },
  );
}
