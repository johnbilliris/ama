import { afterEach, describe, expect, it, vi } from "vitest";

import { GET } from "@/app/api/maps/config/route";

describe("GET /api/maps/config", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("returns the current runtime Azure Maps key without caching", async () => {
    vi.stubEnv("AZURE_MAPS_SUBSCRIPTION_KEY", "runtime-key");
    vi.stubEnv("NEXT_PUBLIC_AZURE_MAPS_KEY", "local-key");

    const response = GET();

    expect(response.status).toBe(200);
    expect(response.headers.get("Cache-Control")).toBe("no-store");
    await expect(response.json()).resolves.toEqual({
      subscriptionKey: "runtime-key",
    });
  });

  it("uses the local public key when no server key is configured", async () => {
    vi.stubEnv("AZURE_MAPS_SUBSCRIPTION_KEY", "");
    vi.stubEnv("NEXT_PUBLIC_AZURE_MAPS_KEY", "local-key");

    const response = GET();

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({
      subscriptionKey: "local-key",
    });
  });

  it("returns 503 when Azure Maps is not configured", async () => {
    vi.stubEnv("AZURE_MAPS_SUBSCRIPTION_KEY", "");
    vi.stubEnv("NEXT_PUBLIC_AZURE_MAPS_KEY", "");

    const response = GET();

    expect(response.status).toBe(503);
    expect(response.headers.get("Cache-Control")).toBe("no-store");
    await expect(response.json()).resolves.toEqual({
      error: "Azure Maps is not configured",
    });
  });
});
