import { afterEach, describe, expect, it, vi } from "vitest";

import { GET } from "@/app/api/maps/config/route";

describe("GET /api/maps/config", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("returns the current runtime Azure Maps key without caching", async () => {
    vi.stubEnv("AZURE_MAPS_SUBSCRIPTION_KEY", "runtime-key");

    const response = GET();

    expect(response.status).toBe(200);
    expect(response.headers.get("Cache-Control")).toBe("no-store");
    await expect(response.json()).resolves.toEqual({
      subscriptionKey: "runtime-key",
    });
  });

  it("returns 503 when Azure Maps is not configured", async () => {
    vi.stubEnv("AZURE_MAPS_SUBSCRIPTION_KEY", "");

    const response = GET();

    expect(response.status).toBe(503);
    expect(response.headers.get("Cache-Control")).toBe("no-store");
    await expect(response.json()).resolves.toEqual({
      error: "Azure Maps is not configured",
    });
  });
});
