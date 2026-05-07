/**
 * Offline queue priority tier (spec-035 Clarifications Q7).
 *
 * Life-safety entries displace routine entries when the per-persona 500-entry cap
 * is reached. Mirrors apps/api/app/domain/offline_queue_tier.py.
 */
export const OFFLINE_QUEUE_TIERS = ["life_safety", "routine"] as const;

export type OfflineQueueTier = (typeof OFFLINE_QUEUE_TIERS)[number];

const OFFLINE_QUEUE_TIER_SET: ReadonlySet<string> = new Set(OFFLINE_QUEUE_TIERS);

export function isOfflineQueueTier(value: unknown): value is OfflineQueueTier {
  return typeof value === "string" && OFFLINE_QUEUE_TIER_SET.has(value);
}

export const OFFLINE_QUEUE_CAP_PER_PERSONA = 500 as const;
export const OFFLINE_QUEUE_LIFE_SAFETY_BATCH_SIZE = 50 as const;
