/**
 * Audit observer fixture (T026).
 *
 * Wraps the `/api/governance/audit-trail` query so every state-changing test
 * can assert that its action emitted an audit row within ≤ 2s (FR-018).
 * The observer returns the audit entry id which the reporter writes back
 * into the coverage trace row's `audit_evidence_id` field.
 */
import { test as baseTest } from "@playwright/test";

type AuditObserverFixtures = {
  expectAudit: (params: {
    auditType: string;
    correlationId: string;
    timeoutMs?: number;
  }) => Promise<string | null>;
};

export const auditObserver = baseTest.extend<AuditObserverFixtures>({
  expectAudit: async ({ request }, use) => {
    await use(async ({ auditType, correlationId, timeoutMs = 2000 }) => {
      const start = Date.now();
      const deadline = start + timeoutMs;
      while (Date.now() < deadline) {
        const res = await request.get("/api/governance/audit-trail", {
          params: { audit_type: auditType, correlation_id: correlationId },
        });
        if (res.ok()) {
          const body = (await res.json()) as { entries?: Array<{ id: string }> };
          if (body.entries && body.entries.length > 0) {
            return body.entries[0].id;
          }
        }
        await new Promise((r) => setTimeout(r, 100));
      }
      return null;
    });
  },
});
