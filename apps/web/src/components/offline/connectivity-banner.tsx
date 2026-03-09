"use client";

import { useDeferredValue, useState } from "react";

type ConnectivityState = "online" | "degraded" | "offline";

interface ConnectivityBannerProps {
  initialState?: ConnectivityState;
}

export function ConnectivityBanner({ initialState = "online" }: ConnectivityBannerProps) {
  const [connectivity, setConnectivity] = useState<ConnectivityState>(initialState);
  const deferredConnectivity = useDeferredValue(connectivity);

  if (typeof window !== "undefined") {
    window.addEventListener("online", () => setConnectivity("online"), { once: false });
    window.addEventListener("offline", () => setConnectivity("offline"), { once: false });
  }

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
