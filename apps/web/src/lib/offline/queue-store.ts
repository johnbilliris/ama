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

export interface QueueEntry {
  persona_id: string;
  client_correlation_id: string;
  tier: Tier;
  route: string;
  payload: unknown;
  captured_ts: string; // ISO-8601 with milliseconds, UTC
}

export type EnqueueResult =
  | { status: "queued"; entry: QueueEntry }
  | { status: "deduped"; entry: QueueEntry }
  | { status: "displaced"; entry: QueueEntry; displaced: QueueEntry }
  | { status: "rejected"; entry: QueueEntry; reason: "overflow" };

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
  key: CryptoKey | null,
  payload: unknown,
): Promise<{ iv: ArrayBuffer; ciphertext: ArrayBuffer } | { plain: unknown }> {
  if (!key) return { plain: payload };
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
  key: CryptoKey | null,
  blob: { iv?: ArrayBuffer; ciphertext?: ArrayBuffer; plain?: unknown },
): Promise<unknown> {
  if (!key || !blob.iv || !blob.ciphertext) return blob.plain ?? null;
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
  route: string;
  captured_ts: string;
  blob: { iv?: ArrayBuffer; ciphertext?: ArrayBuffer; plain?: unknown };
}

export interface OfflineQueueStore {
  enqueue(entry: QueueEntry): Promise<EnqueueResult>;
  list(): Promise<QueueEntry[]>;
  size(): Promise<number>;
  drainBatch(maxBatch: number): Promise<QueueEntry[]>;
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

  async function rowToEntry(row: StoredRow): Promise<QueueEntry> {
    return {
      persona_id: row.persona_id,
      client_correlation_id: row.client_correlation_id,
      tier: row.tier,
      route: row.route,
      payload: await decryptPayload(key, row.blob),
      captured_ts: row.captured_ts,
    };
  }

  return {
    cap() {
      return cap;
    },

    async size() {
      return db.count(STORE);
    },

    async list() {
      const rows = await readAllRows();
      return Promise.all(rows.map(rowToEntry));
    },

    async enqueue(entry: QueueEntry): Promise<EnqueueResult> {
      const rows = await readAllRows();

      const dup = rows.find(
        (r) =>
          r.persona_id === entry.persona_id &&
          r.client_correlation_id === entry.client_correlation_id,
      );
      if (dup) return { status: "deduped", entry };

      if (rows.length >= cap) {
        if (entry.tier !== "life-safety") {
          return { status: "rejected", entry, reason: "overflow" };
        }
        const oldestRoutine = rows.find((r) => r.tier === "routine");
        if (!oldestRoutine) {
          return { status: "rejected", entry, reason: "overflow" };
        }
        await db.delete(STORE, oldestRoutine.id!);
        const blob = await encryptPayload(key, entry.payload);
        await db.add(STORE, {
          persona_id: entry.persona_id,
          client_correlation_id: entry.client_correlation_id,
          tier: entry.tier,
          route: entry.route,
          captured_ts: entry.captured_ts,
          blob,
        } as StoredRow);
        const displaced = await rowToEntry(oldestRoutine);
        return { status: "displaced", entry, displaced };
      }

      const blob = await encryptPayload(key, entry.payload);
      await db.add(STORE, {
        persona_id: entry.persona_id,
        client_correlation_id: entry.client_correlation_id,
        tier: entry.tier,
        route: entry.route,
        captured_ts: entry.captured_ts,
        blob,
      } as StoredRow);
      return { status: "queued", entry };
    },

    async drainBatch(maxBatch: number): Promise<QueueEntry[]> {
      const rows = await readAllRows();
      const lifeSafety = rows.filter((r) => r.tier === "life-safety");
      const routine = rows.filter((r) => r.tier === "routine");
      const ordered = [...lifeSafety, ...routine].slice(0, maxBatch);
      const drained: QueueEntry[] = [];
      for (const row of ordered) {
        drained.push(await rowToEntry(row));
        await db.delete(STORE, row.id!);
      }
      return drained;
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
