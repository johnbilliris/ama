import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const simulationAuthHeaders = vi.fn();

vi.mock("@/lib/api/simulation-auth", () => ({
  simulationAuthHeaders: () => simulationAuthHeaders(),
}));

import { fetchIncidentsMapPage } from "@/lib/api/incidents-map";

describe("incidents map API transport", () => {
  beforeEach(() => {
    simulationAuthHeaders.mockReset();
    vi.stubEnv("NEXT_PUBLIC_ALLOW_ANONYMOUS_INCIDENT_MAP", "0");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it("omits authentication when anonymous map access is enabled", async () => {
    vi.stubEnv("NEXT_PUBLIC_ALLOW_ANONYMOUS_INCIDENT_MAP", "1");
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          type: "FeatureCollection",
          features: [],
          metadata: {
            total: 0,
            unmapped_count: 0,
            page: 1,
            page_size: 200,
            fetched_at: "2026-09-30T00:00:00Z",
          },
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await fetchIncidentsMapPage();

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(init.headers).toBeUndefined();
    expect(simulationAuthHeaders).not.toHaveBeenCalled();
  });

  it("attaches the configured MSAL bearer token when anonymous access is disabled", async () => {
    simulationAuthHeaders.mockResolvedValue({
      Authorization: "******",
    });
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          type: "FeatureCollection",
          features: [],
          metadata: {
            total: 0,
            unmapped_count: 0,
            page: 1,
            page_size: 200,
            fetched_at: "2026-09-30T00:00:00Z",
          },
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await fetchIncidentsMapPage();

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(init.headers).toEqual({
      Authorization: "******",
    });
    expect(simulationAuthHeaders).toHaveBeenCalledTimes(1);
  });

  it("does not call the API when required token acquisition fails", async () => {
    simulationAuthHeaders.mockRejectedValue(new Error("Sign-in required"));
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchIncidentsMapPage()).rejects.toThrow("Sign-in required");
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
