/* AMA offline service worker — minimal pass-through with retry suggestion. */
self.addEventListener("install", (event) => {
  self.skipWaiting();
});
self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});
self.addEventListener("fetch", (event) => {
  /* Currently a no-op; the queue-store is invoked from the app layer when
     a fetch call rejects with a network error.  This worker exists so the
     navigator.serviceWorker registration succeeds and the app can detect
     offline state via the controllerchange event. */
});
