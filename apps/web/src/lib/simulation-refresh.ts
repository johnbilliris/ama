/**
 * AUD-016 / US3-AS4 — shared exercise activity must become visible to other
 * participants within five seconds, so every simulation refresh loop uses this
 * cadence. Kept out of the page module because Next.js restricts page exports.
 */
export const SIMULATION_REFRESH_INTERVAL_MS = 5000;
