/**
 * Vitest unit test for offline queue store (T034).
 *
 * Covers FR-006 + Q4/Q7 displacement & dedupe rules.
 */

import { describe, expect, it, beforeEach, afterEach, vi } from "vitest";

import {
  createOfflineQueueStore,
  type OfflineQueueStore,
  type QueueEntry,
} from "../../../src/lib/offline/queue-store";

function makeEntry(overrides: Partial<QueueEntry> = {}): QueueEntry {
  return {
    persona_id: "field-coordinator",
    client_correlation_id: `ccid-${Math.random().toString(36).slice(2, 10)}`,
    tier: "routine",
    route: "/api/outcomes/sc-1/evaluate",
    payload: { hello: "world" },
    captured_ts: new Date().toISOString(),
    ...overrides,
  };
}

let store: OfflineQueueStore;

async function freshStore() {
  if (store) {
    try {
      await store.clear();
    } catch {
      // ignore
    }
    store.close();
  }
  await new Promise<void>((resolve) => {
    const req = indexedDB.deleteDatabase("ama-offline-queue");
    req.onsuccess = () => resolve();
    req.onerror = () => resolve();
    req.onblocked = () => resolve();
  });
  store = await createOfflineQueueStore();
  return store;
}

describe("offline-queue-store (T034)", () => {
  beforeEach(() => {
    vi.unstubAllEnvs();
  });

  afterEach(() => {
    if (store) {
      store.close();
    }
  });

  it("dedupes by (persona_id, client_correlation_id)", async () => {
    const store = await freshStore();
    const entry = makeEntry();
    const a = await store.enqueue(entry);
    const b = await store.enqueue(entry);
    expect(a.status).toBe("queued");
    expect(b.status).toBe("deduped");
    expect(await store.size()).toBe(1);
  });

  it("respects NEXT_PUBLIC_OFFLINE_QUEUE_CAP=10 — overflow rejects routine", async () => {
    vi.stubEnv("NEXT_PUBLIC_OFFLINE_QUEUE_CAP", "10");
    const store = await freshStore();
    expect(store.cap()).toBe(10);
    for (let i = 0; i < 10; i++) {
      const r = await store.enqueue(
        makeEntry({
          client_correlation_id: `r-${i}`,
          captured_ts: new Date(2025, 0, 1, 0, 0, i).toISOString(),
        }),
      );
      expect(r.status).toBe("queued");
    }
    const overflow = await store.enqueue(
      makeEntry({ client_correlation_id: "r-overflow", tier: "routine" }),
    );
    expect(overflow.status).toBe("rejected");
  });

  it("life-safety insertion at-cap displaces oldest routine (Q7)", async () => {
    vi.stubEnv("NEXT_PUBLIC_OFFLINE_QUEUE_CAP", "3");
    const store = await freshStore();
    await store.enqueue(
      makeEntry({
        client_correlation_id: "r-old",
        tier: "routine",
        captured_ts: "2025-01-01T00:00:00.000Z",
      }),
    );
    await store.enqueue(
      makeEntry({
        client_correlation_id: "r-mid",
        tier: "routine",
        captured_ts: "2025-01-01T00:00:01.000Z",
      }),
    );
    await store.enqueue(
      makeEntry({
        client_correlation_id: "r-new",
        tier: "routine",
        captured_ts: "2025-01-01T00:00:02.000Z",
      }),
    );

    const result = await store.enqueue(
      makeEntry({
        client_correlation_id: "ls-1",
        tier: "life-safety",
        captured_ts: "2025-01-01T00:00:03.000Z",
      }),
    );
    expect(result.status).toBe("displaced");
    if (result.status === "displaced") {
      expect(result.displaced.client_correlation_id).toBe("r-old");
    }

    const remaining = (await store.list()).map((e) => e.client_correlation_id);
    expect(remaining).toEqual(["r-mid", "r-new", "ls-1"]);
  });

  it("drainBatch returns life-safety first then routine in captured_ts order", async () => {
    const store = await freshStore();
    await store.enqueue(
      makeEntry({
        client_correlation_id: "r-a",
        tier: "routine",
        captured_ts: "2025-01-01T00:00:00.000Z",
      }),
    );
    await store.enqueue(
      makeEntry({
        client_correlation_id: "ls-a",
        tier: "life-safety",
        captured_ts: "2025-01-01T00:00:05.000Z",
      }),
    );
    const batch = await store.drainBatch(10);
    expect(batch.map((e) => e.client_correlation_id)).toEqual([
      "ls-a",
      "r-a",
    ]);
    expect(await store.size()).toBe(0);
  });

  it("encrypts payload at rest (raw IDB row not human-readable)", async () => {
    const s = await freshStore();
    await s.enqueue(
      makeEntry({
        client_correlation_id: "secret-1",
        payload: { secret: "classified-payload" },
      }),
    );
    s.close();
    const open = indexedDB.open("ama-offline-queue");
    const db = await new Promise<IDBDatabase>((resolve, reject) => {
      open.onsuccess = () => resolve(open.result);
      open.onerror = () => reject(open.error);
    });
    const tx = db.transaction("queue", "readonly");
    const all = await new Promise<unknown[]>((resolve, reject) => {
      const req = tx.objectStore("queue").getAll();
      req.onsuccess = () => resolve(req.result as unknown[]);
      req.onerror = () => reject(req.error);
    });
    const serialised = JSON.stringify(all);
    expect(serialised).not.toContain("classified-payload");
    db.close();
  });
});
