/**
 * Audit observer fixture (T026).
 *
 * Wraps the FR-029 ``/api/audit/list`` query so every state-changing test
 * can assert that its action emitted an audit row within ≤ 2s (FR-018).
 * The observer returns the audit entry id which the reporter writes back
 * into the coverage trace row's `audit_evidence_id` field.
 *
 * spec 034 cycle-1: the legacy `/api/governance/audit-trail` endpoint
 * was never wired; the canonical contract is
 * ``GET /api/audit/list?correlation_id={uuid}`` returning
 * ``{items:[{audit_id, audit_type, correlation_id, ...}]}`` per
 * ``apps/api/app/api/routes/audit_list.py``. We filter client-side on
 * ``audit_type`` (defence-in-depth even though correlation_id is unique
 * per test).
 */
import { test as baseTest } from "@playwright/test";

type AuditObserverFixtures = {
  expectAudit: (params: {
    auditType: string;
    correlationId: string;
    timeoutMs?: number;
  }) => Promise<string | null>;
};

interface AuditListItem {
  audit_id: string;
  audit_type?: string;
}

interface AuditListResponse {
  items?: AuditListItem[];
}

export const auditObserver = baseTest.extend<AuditObserverFixtures>({
  expectAudit: async ({ request }, use) => {
    await use(async ({ auditType, correlationId, timeoutMs = 2000 }) => {
      const start = Date.now();
      const deadline = start + timeoutMs;
      while (Date.now() < deadline) {
        const res = await request.get(
          `/api/audit/list?correlation_id=${encodeURIComponent(correlationId)}`,
        );
        if (res.ok()) {
          const body = (await res.json()) as AuditListResponse;
          const items = body.items ?? [];
          const match = items.find((item) => item.audit_type === auditType);
          if (match) {
            return match.audit_id;
          }
        }
        await new Promise((r) => setTimeout(r, 100));
      }
      return null;
    });
  },
});
