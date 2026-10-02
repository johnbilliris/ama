"use client";

import { useDeferredValue, useEffect, useState } from "react";

type ConnectivityState = "online" | "degraded" | "offline";

interface ConnectivityBannerProps {
  initialState?: ConnectivityState;
}

export function ConnectivityBanner({ initialState = "online" }: ConnectivityBannerProps) {
  const [connectivity, setConnectivity] = useState<ConnectivityState>(initialState);
  const deferredConnectivity = useDeferredValue(connectivity);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    if (!navigator.onLine) setConnectivity("offline");
    const goOnline = () => setConnectivity("online");
    const goOffline = () => setConnectivity("offline");
    window.addEventListener("online", goOnline);
    window.addEventListener("offline", goOffline);
    return () => {
      window.removeEventListener("online", goOnline);
      window.removeEventListener("offline", goOffline);
    };
  }, []);

  if (deferredConnectivity === "online") {
    return null;
  }

  const isOffline = deferredConnectivity === "offline";

  return (
    <div
      className={`connectivity-banner ${isOffline ? "connectivity-banner--offline" : "connectivity-banner--degraded"}`}
      role="alert"
      aria-live="assertive"
    >
      <span className="connectivity-banner-icon" aria-hidden="true">
        {isOffline ? "⚡" : "⚠"}
      </span>
      <span className="connectivity-banner-text">
        {isOffline
          ? "You are offline. Cached data may be stale. Reconnect to resume live updates."
          : "Network connectivity is degraded. Some updates may be delayed."}
      </span>
    </div>
  );
}
