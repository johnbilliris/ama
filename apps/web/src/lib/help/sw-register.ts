/** spec-038 T-AA124 — service worker registration. */
export function registerHelpServiceWorker(): void {
  if (typeof navigator === "undefined" || !("serviceWorker" in navigator)) return;
  navigator.serviceWorker.register("/help-sw.js").catch(() => undefined);
}
