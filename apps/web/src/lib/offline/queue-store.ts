/**
 * Offline queue store (T040, FR-006, Q4 + Q7).
 *
 * - IndexedDB via `idb`, encrypted at rest with subtle-crypto AES-GCM.
 * - Hard cap sourced from `process.env.NEXT_PUBLIC_OFFLINE_QUEUE_CAP`
 *   (falls back to `500` ONLY when unset).  No other hardcoded business
 *   constant for the cap appears in this file.
 * - Tiered displacement: a `life-safety` insertion at-cap displaces the
 *   oldest `routine` entry (returned to the caller as `displaced`).  At-cap
 *   `routine` insertions are rejected (`overflow`).
 * - Dedupe by `(persona_id, client_correlation_id)`.
 *
 * See [`spec.md` § Q4/Q7](../../../specs/035-webapp-capstone-closure/spec.md#clarifications).
 */

import { openDB, type IDBPDatabase } from "idb";

export type Tier = "life-safety" | "routine";

export type QueueMode = "live" | "rehearsal";

export interface QueueEntry {
  persona_id: string;
  client_correlation_id: string;
  tier: Tier;
  method: "POST" | "PATCH" | "PUT";
  route: string;
  actor_id: string;
  tenant_id: string;
  incident_id: string;
  mode: QueueMode;
  expires_ts: string;
  payload: unknown;
  captured_ts: string; // ISO-8601 with milliseconds, UTC
  attempts: number;
  lease_until_ts?: string | null;
}

const DEFAULT_REPLAY_EXPIRY_MS = 24 * 60 * 60 * 1000;

export type EnqueueResult =
  | { status: "queued"; entry: QueueEntry }
  | { status: "deduped"; entry: QueueEntry }
  | { status: "displaced"; entry: QueueEntry; displaced: QueueEntry }
  | { status: "rejected"; entry: QueueEntry; reason: "overflow" | "crypto_unavailable" };

const DB_NAME = "ama-offline-queue";
const DB_VERSION = 1;
const STORE = "queue";
const KEY_STORE = "keys";
const KEY_ID = "data-key";

const DEFAULT_CAP_FALLBACK = 500;

function resolveCap(): number {
  const raw =
    typeof process !== "undefined" && process.env
      ? process.env.NEXT_PUBLIC_OFFLINE_QUEUE_CAP
      : undefined;
  if (!raw) return DEFAULT_CAP_FALLBACK;
  const n = Number.parseInt(raw, 10);
  if (Number.isFinite(n) && n > 0) return n;
  return DEFAULT_CAP_FALLBACK;
}

async function openQueueDb(): Promise<IDBPDatabase> {
  return openDB(DB_NAME, DB_VERSION, {
    upgrade(db) {
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE, { keyPath: "id", autoIncrement: true });
      }
      if (!db.objectStoreNames.contains(KEY_STORE)) {
        db.createObjectStore(KEY_STORE);
      }
    },
  });
}

async function loadOrCreateKey(db: IDBPDatabase): Promise<CryptoKey | null> {
  if (typeof crypto === "undefined" || !crypto.subtle) return null;
  const existing = (await db.get(KEY_STORE, KEY_ID)) as
    | JsonWebKey
    | undefined;
  if (existing) {
    return crypto.subtle.importKey("jwk", existing, "AES-GCM", false, [
      "encrypt",
      "decrypt",
    ]);
  }
  const key = await crypto.subtle.generateKey(
    { name: "AES-GCM", length: 256 },
    true,
    ["encrypt", "decrypt"],
  );
  const jwk = await crypto.subtle.exportKey("jwk", key);
  await db.put(KEY_STORE, jwk, KEY_ID);
  return key;
}

async function encryptPayload(
  key: CryptoKey,
  payload: unknown,
): Promise<{ iv: ArrayBuffer; ciphertext: ArrayBuffer }> {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const enc = new TextEncoder().encode(JSON.stringify(payload ?? null));
  const ciphertext = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv },
    key,
    enc,
  );
  return { iv: iv.buffer, ciphertext };
}

async function decryptPayload(
  key: CryptoKey,
  blob: { iv?: ArrayBuffer; ciphertext?: ArrayBuffer },
): Promise<unknown> {
  if (!blob.iv || !blob.ciphertext) return null;
  const dec = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv: new Uint8Array(blob.iv) },
    key,
    blob.ciphertext,
  );
  return JSON.parse(new TextDecoder().decode(dec));
}

interface StoredRow {
  id?: number;
  persona_id: string;
  client_correlation_id: string;
  tier: Tier;
  method: "POST" | "PATCH" | "PUT";
  route: string;
  actor_id: string;
  tenant_id: string;
  incident_id: string;
  mode: QueueMode;
  expires_ts: string;
  attempts: number;
  lease_until_ts?: string | null;
  retry_after_ts?: string | null;
  last_error?: string | null;
  captured_ts: string;
  blob: { iv?: ArrayBuffer; ciphertext?: ArrayBuffer };
}

export interface OfflineQueueStore {
  enqueue(entry: QueueEntry): Promise<EnqueueResult>;
  list(): Promise<QueueEntry[]>;
  size(): Promise<number>;
  leaseBatch(maxBatch: number, leaseMs: number): Promise<QueueEntry[]>;
  ack(actor_id: string, client_correlation_id: string): Promise<void>;
  nack(actor_id: string, client_correlation_id: string, reason: string, backoffMs?: number): Promise<void>;
  remove(persona_id: string, client_correlation_id: string): Promise<void>;
  clear(): Promise<void>;
  close(): void;
  cap(): number;
}

export async function createOfflineQueueStore(): Promise<OfflineQueueStore> {
  const cap = resolveCap();
  const db = await openQueueDb();
  const key = await loadOrCreateKey(db);

  async function readAllRows(): Promise<StoredRow[]> {
    const all = (await db.getAll(STORE)) as StoredRow[];
    return all.sort((a, b) => a.captured_ts.localeCompare(b.captured_ts));
  }

  function nowIso(): string {
    return new Date().toISOString();
  }

  function isExpired(row: StoredRow, now: string): boolean {
    return row.expires_ts <= now;
  }

  function isLeased(row: StoredRow, now: string): boolean {
    return typeof row.lease_until_ts === "string" && row.lease_until_ts > now;
  }

  function isBackoffPending(row: StoredRow, now: string): boolean {
    return typeof row.retry_after_ts === "string" && row.retry_after_ts > now;
  }

  async function pruneExpired(): Promise<void> {
    const now = nowIso();
    const rows = await readAllRows();
    for (const row of rows) {
      if (isExpired(row, now)) {
        await db.delete(STORE, row.id!);
      }
    }
  }

  async function rowToEntry(row: StoredRow): Promise<QueueEntry> {
    if (key === null) {
      throw new Error("offline_queue_crypto_required");
    }
    return {
      persona_id: row.persona_id,
      client_correlation_id: row.client_correlation_id,
      tier: row.tier,
      method: row.method,
      route: row.route,
      actor_id: row.actor_id,
      tenant_id: row.tenant_id,
      incident_id: row.incident_id,
      mode: row.mode,
      expires_ts: row.expires_ts,
      payload: await decryptPayload(key, row.blob),
      captured_ts: row.captured_ts,
      attempts: row.attempts,
      lease_until_ts: row.lease_until_ts ?? null,
    };
  }

  return {
    cap() {
      return cap;
    },

    async size() {
      await pruneExpired();
      return db.count(STORE);
    },

    async list() {
      await pruneExpired();
      const rows = await readAllRows();
      return Promise.all(rows.map(rowToEntry));
    },

    async enqueue(entry: QueueEntry): Promise<EnqueueResult> {
      const normalizedEntry: QueueEntry = {
        ...entry,
        expires_ts: entry.expires_ts || new Date(Date.now() + DEFAULT_REPLAY_EXPIRY_MS).toISOString(),
        attempts: Number.isFinite(entry.attempts) ? Math.max(0, entry.attempts) : 0,
      };

      if (key === null) {
        return { status: "rejected", entry: normalizedEntry, reason: "crypto_unavailable" };
      }

      await pruneExpired();
      const rows = await readAllRows();

      const dup = rows.find(
        (r) =>
          r.persona_id === entry.persona_id &&
          r.client_correlation_id === normalizedEntry.client_correlation_id,
      );
      if (dup) return { status: "deduped", entry: normalizedEntry };

      if (rows.length >= cap) {
        if (normalizedEntry.tier !== "life-safety") {
          return { status: "rejected", entry: normalizedEntry, reason: "overflow" };
        }
        const oldestRoutine = rows.find((r) => r.tier === "routine");
        if (!oldestRoutine) {
          return { status: "rejected", entry: normalizedEntry, reason: "overflow" };
        }
        await db.delete(STORE, oldestRoutine.id!);
        const blob = await encryptPayload(key, normalizedEntry.payload);
        await db.add(STORE, {
          persona_id: normalizedEntry.persona_id,
          client_correlation_id: normalizedEntry.client_correlation_id,
          tier: normalizedEntry.tier,
          method: normalizedEntry.method,
          route: normalizedEntry.route,
          actor_id: normalizedEntry.actor_id,
          tenant_id: normalizedEntry.tenant_id,
          incident_id: normalizedEntry.incident_id,
          mode: normalizedEntry.mode,
          expires_ts: normalizedEntry.expires_ts,
          attempts: normalizedEntry.attempts,
          captured_ts: normalizedEntry.captured_ts,
          blob,
        } as StoredRow);
        const displaced = await rowToEntry(oldestRoutine);
        return { status: "displaced", entry: normalizedEntry, displaced };
      }

      const blob = await encryptPayload(key, normalizedEntry.payload);
      await db.add(STORE, {
        persona_id: normalizedEntry.persona_id,
        client_correlation_id: normalizedEntry.client_correlation_id,
        tier: normalizedEntry.tier,
        method: normalizedEntry.method,
        route: normalizedEntry.route,
        actor_id: normalizedEntry.actor_id,
        tenant_id: normalizedEntry.tenant_id,
        incident_id: normalizedEntry.incident_id,
        mode: normalizedEntry.mode,
        expires_ts: normalizedEntry.expires_ts,
        attempts: normalizedEntry.attempts,
        captured_ts: normalizedEntry.captured_ts,
        blob,
      } as StoredRow);
      return { status: "queued", entry: normalizedEntry };
    },

    async leaseBatch(maxBatch: number, leaseMs: number): Promise<QueueEntry[]> {
      await pruneExpired();
      const rows = await readAllRows();
      const now = nowIso();
      const leaseUntil = new Date(Date.now() + Math.max(1000, leaseMs)).toISOString();
      const leaseable = rows.filter((r) => !isLeased(r, now) && !isBackoffPending(r, now));
      const lifeSafety = leaseable.filter((r) => r.tier === "life-safety");
      const routine = leaseable.filter((r) => r.tier === "routine");
      const ordered = [...lifeSafety, ...routine].slice(0, maxBatch);
      const leased: QueueEntry[] = [];
      for (const row of ordered) {
        row.lease_until_ts = leaseUntil;
        row.retry_after_ts = null;
        await db.put(STORE, row);
        leased.push(await rowToEntry(row));
      }
      return leased;
    },

    async ack(actor_id, client_correlation_id) {
      const rows = await readAllRows();
      for (const row of rows) {
        if (row.actor_id === actor_id && row.client_correlation_id === client_correlation_id) {
          await db.delete(STORE, row.id!);
        }
      }
    },

    async nack(actor_id, client_correlation_id, reason, backoffMs = 0) {
      const rows = await readAllRows();
      for (const row of rows) {
        if (row.actor_id === actor_id && row.client_correlation_id === client_correlation_id) {
          row.attempts += 1;
          row.lease_until_ts = null;
          row.last_error = reason;
          row.retry_after_ts = backoffMs > 0 ? new Date(Date.now() + backoffMs).toISOString() : null;
          await db.put(STORE, row);
        }
      }
    },

    async remove(persona_id, client_correlation_id) {
      const rows = await readAllRows();
      for (const row of rows) {
        if (
          row.persona_id === persona_id &&
          row.client_correlation_id === client_correlation_id
        ) {
          await db.delete(STORE, row.id!);
        }
      }
    },

    async clear() {
      const tx = db.transaction(STORE, "readwrite");
      await tx.store.clear();
      await tx.done;
    },

    close() {
      db.close();
    },
  };
}
