/**
 * spec-038 T-AA095 — IndexedDB-backed offline cache for help articles + glossary + FAQ.
 *
 * Envelope-compatible with `apps/agents/common/offline_cache.py`. Cap 500 MB,
 * 14-day TTL. Emits "may be stale" once past TTL (FR-026a-AMEND).
 */

export interface CacheEnvelope<T = unknown> {
  key: string;
  value: T;
  storedAt: number; // epoch ms
  ttlMs: number;
  classification: "OFFICIAL";
}

const DB_NAME = "ama-help-offline";
const STORE = "envelopes";
const DEFAULT_TTL_MS = 14 * 24 * 60 * 60 * 1000;
const MAX_BYTES = 500 * 1024 * 1024;

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === "undefined") {
      reject(new Error("IndexedDB unavailable"));
      return;
    }
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => req.result.createObjectStore(STORE, { keyPath: "key" });
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

export async function putHelpCache<T>(key: string, value: T, ttlMs = DEFAULT_TTL_MS): Promise<void> {
  const db = await openDb();
  const tx = db.transaction(STORE, "readwrite");
  const envelope: CacheEnvelope<T> = {
    key,
    value,
    storedAt: Date.now(),
    ttlMs,
    classification: "OFFICIAL",
  };
  tx.objectStore(STORE).put(envelope);
  await new Promise<void>((res, rej) => {
    tx.oncomplete = () => res();
    tx.onerror = () => rej(tx.error);
  });
  db.close();
}

export async function getHelpCache<T>(key: string): Promise<{ value: T; stale: boolean } | null> {
  const db = await openDb();
  const tx = db.transaction(STORE, "readonly");
  const req = tx.objectStore(STORE).get(key);
  const envelope = await new Promise<CacheEnvelope<T> | undefined>((res, rej) => {
    req.onsuccess = () => res(req.result as CacheEnvelope<T> | undefined);
    req.onerror = () => rej(req.error);
  });
  db.close();
  if (!envelope) return null;
  return { value: envelope.value, stale: Date.now() - envelope.storedAt > envelope.ttlMs };
}

export { MAX_BYTES, DEFAULT_TTL_MS };
