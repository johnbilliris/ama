/**
 * Worker-scoped persona fixture (T023).
 *
 * Resolves a persona id to a real seed identity via the test-support
 * endpoint. ASM-011 forbids fabricating identities in test code.
 *
 * Each persona id appears once at the top of the test file:
 *
 *   const PERSONA = "ic-nsw-rfs";
 *   const test = personaTest(PERSONA);
 *
 * Usage:
 *   import { personaTest } from "@web-coverage/fixtures/persona.fixture";
 *   const PERSONA = "incident-commander";
 *   personaTest(PERSONA)("approves cross-agency action", async ({ persona, page }) => { ... });
 */
import { test as baseTest } from "@playwright/test";
import type { PersonaFixture } from "../types/persona";

type PersonaFixtures = {
  persona: PersonaFixture;
  resolvePersona: (id: string) => Promise<PersonaFixture>;
};

const cache = new Map<string, PersonaFixture>();

export const personaResolver = baseTest.extend<{ resolvePersona: (id: string) => Promise<PersonaFixture> }>({
  resolvePersona: async ({ request }, use) => {
    await use(async (id: string) => {
      const cached = cache.get(id);
      if (cached) {
        return cached;
      }
      const res = await request.get(`/api/test-support/personas/${encodeURIComponent(id)}`, {
        headers: { "X-Test-Persona-Id": id },
      });
      if (!res.ok()) {
        throw new Error(
          `personaFixture: persona '${id}' not found in seed registry (${res.status()}). ` +
            `Did you run scripts/seed-database.ps1? AMA_TEST_SUPPORT=${process.env.AMA_TEST_SUPPORT}`,
        );
      }
      const persona = (await res.json()) as PersonaFixture;
      cache.set(id, persona);
      return persona;
    });
  },
});

/**
 * Helper that returns a Playwright test factory pre-bound to the persona id.
 * Use the second-tier `test.use({ extraHTTPHeaders: { ... } })` for header propagation.
 */
export function personaTest(personaId: string) {
  return personaResolver.extend<{ persona: PersonaFixture }>({
    persona: async ({ resolvePersona }, use) => {
      const persona = await resolvePersona(personaId);
      if (persona.persona_id !== personaId) {
        throw new Error(
          `personaFixture drift: requested '${personaId}' but resolver returned '${persona.persona_id}'.`,
        );
      }
      await use(persona);
    },
  });
}

export type { PersonaFixture, PersonaFixtures };
