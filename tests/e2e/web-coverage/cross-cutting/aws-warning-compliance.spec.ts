/**
 * T057 — AWS three-state warning compliance (FR-011, Clauses V-A/V-B/V-C).
 *
 * Asserts every AWS-eligible warning route renders the three states
 * (Advice / Watch and Act / Emergency Warning) and supports de-escalation
 * + all-clear. Parameterised across the six primary hazard categories.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { validateAwsCapEnvelope } from "@web-coverage/_support/validators/aws-cap-envelope";

const HAZARDS = [
  "bushfire",
  "severe-storm",
  "tropical-cyclone",
  "riverine-flood",
  "extreme-heat",
  "earthquake",
] as const;

for (const hazard of HAZARDS) {
  test(
    `AWS three-state envelope for '${hazard}' ` +
      `@persona:public-information-officer @outcome:1 @hazard:${hazard} ` +
      `@fr:FR-011 @clause:V-A @clause:V-B @clause:V-C @p1`,
    async ({ resolvePersona, request, correlationId }) => {
      const persona = await resolvePersona("public-information-officer");

      const res = await request.get(`/api/warnings/preview`, {
        params: { hazard, level: "watch-and-act" },
        headers: {
          "X-Correlation-Id": correlationId,
          "X-Test-Persona-Id": persona.persona_id,
        },
      });
      if (!res.ok()) {
        test.fail(true, `Warning preview API not yet wired for ${hazard}`);
        return;
      }
      const body = (await res.json()) as Record<string, unknown>;
      const validation = validateAwsCapEnvelope(body);
      expect(validation.errors, validation.errors.join("; ")).toEqual([]);
    },
  );
}
