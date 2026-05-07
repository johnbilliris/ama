/**
 * Offline service worker registration helper (T040, FR-006).
 *
 * Registers the SW that intercepts state-changing routes when navigator
 * is offline and forwards them through the IndexedDB-backed queue.  The
 * actual SW lives at /public/offline-sw.js so it serves at root scope.
 */

export async function registerOfflineServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if (typeof navigator === "undefined" || !("serviceWorker" in navigator)) {
    return null;
  }
  try {
    return await navigator.serviceWorker.register("/offline-sw.js", {
      scope: "/",
    });
  } catch {
    return null;
  }
}

export async function unregisterOfflineServiceWorker(): Promise<void> {
  if (typeof navigator === "undefined" || !("serviceWorker" in navigator))
    return;
  const regs = await navigator.serviceWorker.getRegistrations();
  await Promise.all(regs.map((r) => r.unregister()));
}
