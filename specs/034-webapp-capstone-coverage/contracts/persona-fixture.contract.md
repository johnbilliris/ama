# Persona Fixture Contract — spec 034

This is the human-readable contract for the `personaFixture` Playwright
fixture (lives at `tests/e2e/web-coverage/_support/fixtures/persona.fixture.ts`)
and its server counterpart, the test-support endpoint
`GET /api/test-support/personas/{id}`. Together they realise ASM-011
("personas are real seeded identities, not fixture-only synthetic
records").

## Contract intent

For each test in `tests/e2e/web-coverage/`:

1. The fixture MUST resolve the test's persona to a record in
   `bootstrap_seed_data().identities` — never a fabricated identity.
2. The fixture MUST set `X-Test-Persona-Id: {persona_id}` on every
   browser-context request so the FastAPI middleware honours the
   impersonation only in dev/test environments.
3. The server endpoint MUST refuse to start in any environment where
   `settings.environment == "production"` and the
   `AMA_TEST_SUPPORT` flag is not set to `1`.
4. Nothing in this fixture, its tests, or the endpoint is permitted to
   modify the seed data — reads only.

## Server-side contract

### Endpoint

```
GET /api/test-support/personas
GET /api/test-support/personas/{persona_id}
```

### Activation

- Activated only when **both** of the following hold at FastAPI startup:
  - `os.environ.get("AMA_TEST_SUPPORT") == "1"`.
  - `settings.environment in {"dev", "test"}`.
- When activation conditions fail, the router is **not registered**.
  Direct requests return `404 Not Found`. The startup log MUST emit
  `"test-support disabled: environment=... AMA_TEST_SUPPORT=..."`.

### Authentication

- The endpoint accepts the standard authentication chain (Entra ID in
  staging, none in dev). It is **read-only** and exposes only
  identities already in the seed registry, so the security boundary is
  the activation guard, not per-request auth.

### Response shape (single persona)

```json
{
  "persona_id": "ic-nsw-rfs",
  "display_name": "Fiona Reilly",
  "organisation_id": "org-nsw-rfs",
  "jurisdiction_id": "nsw",
  "role": "incident-controller",
  "permissions": ["incidents:read", "incidents:write", "warnings:issue", "..."],
  "aiims_function": "control",
  "direct_reports": ["op-nsw-rfs", "plan-nsw-rfs", "log-nsw-rfs", "pio-nsw-rfs"]
}
```

### Response shape (collection)

```json
{
  "count": 68,
  "items": [ /* PersonaFixture[] */ ]
}
```

### Error responses

- `404` when persona_id does not exist in the seed registry.
- `503 Service Unavailable` if `bootstrap_seed_data()` has not yet
  completed (the test runner MUST wait for ready signal in setup).

### Audit

Every request is logged via the standard
`apps/api/app/services/ingestion/audit_writer.py` pipeline with
`audit_type = "test-support.persona-resolved"` and the requester's
`X-Correlation-Id` header.

## Client-side fixture contract

### Type

```ts
export type PersonaFixture = {
  persona_id: string;
  display_name: string;
  organisation_id: string;
  jurisdiction_id:
    | "nsw" | "vic" | "qld" | "sa" | "wa" | "tas" | "act"
    | "nt" | "commonwealth" | "cross-sector";
  role:
    | "incident-controller"
    | "operations-officer"
    | "planning-officer"
    | "logistics-officer"
    | "public-information-officer";
  permissions: string[];
  aiims_function: "control" | "operations" | "planning" | "logistics" | "public-information";
  direct_reports: string[];
};
```

### Worker-scoped fixture

```ts
import { test as base } from "@playwright/test";
import type { PersonaFixture } from "../types/persona";

type Fixtures = {
  resolvePersona: (id: string) => Promise<PersonaFixture>;
};

export const test = base.extend<{}, Fixtures>({
  resolvePersona: [async ({ request }, use) => {
    const cache = new Map<string, PersonaFixture>();
    await use(async (id: string) => {
      if (cache.has(id)) return cache.get(id)!;
      const res = await request.get(`/api/test-support/personas/${encodeURIComponent(id)}`);
      if (!res.ok()) {
        throw new Error(
          `personaFixture: persona '${id}' not found in seed registry. ` +
          `Did you run scripts/seed-database.ps1? AMA_TEST_SUPPORT=${process.env.AMA_TEST_SUPPORT}`
        );
      }
      const persona = (await res.json()) as PersonaFixture;
      cache.set(id, persona);
      return persona;
    });
  }, { scope: "worker" }],
});
```

### Header propagation

All page-object navigations must use a context configured with:

```ts
const ctx = await browser.newContext({
  extraHTTPHeaders: {
    "X-Test-Persona-Id": persona.persona_id,
    "X-Correlation-Id": correlationId,
  },
});
```

The web app's auth middleware honours `X-Test-Persona-Id` only when
the same dual-guard activation conditions hold; otherwise it is
ignored and standard auth applies.

## Test obligations

Each test using this fixture MUST:

1. Declare its persona id at the top of the file (e.g.,
   `const PERSONA = "ic-nsw-rfs"`); persona ids appear once and only
   once per test file (no per-step changes).
2. Resolve the persona via `resolvePersona(PERSONA)` — never load
   identities from JSON fixtures or hard-code permissions arrays.
3. Assert the persona's `role` and `aiims_function` match the file's
   expected role before exercising any behaviour. This guards against
   silent seed-data drift.
4. Refuse to run if the fixture returns 404; tests do not "auto-create"
   identities.

## Acceptance criteria for this contract

- [x] No persona id appears in test code without a matching entry in
      `bootstrap_seed_data().identities`.
- [x] Test-support endpoint refuses to register in production
      regardless of `AMA_TEST_SUPPORT`.
- [x] CI grep gate forbids `permissions: [` literal arrays in test
      files (lint rule, fail on match).
- [x] Removing a persona from the seed registry causes affected tests
      to fail at fixture-resolution time with an actionable message
      naming the persona id and the seed script.
- [x] Activation guard is exercised by a dedicated test
      (`tests/e2e/web-coverage/cross-cutting/test-support-guard.spec.ts`)
      that asserts the endpoint returns 404 when
      `AMA_TEST_SUPPORT` is unset.

## References

- spec 034 ASM-011 (line ~415 of `spec.md`).
- `packages/domain/src/domain/seed/bootstrap.py` — seed loader.
- `packages/domain/src/domain/models/persona.py` — Persona model.
- `apps/api/app/middleware/` — auth middleware (must be extended with
  the dual-guard env check).
- `infra/parameters/foundry-carveout.yaml` — orthogonal but listed for
  context: only data layer, not identity layer.
- ADR-033 — classification filter; distinct from this fixture but the
  same env-guard pattern applies.
