/**
 * AUD-016 — the simulation API client must use the application's existing
 * MSAL helper and must not invent a second auth stack.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const acquireBearer = vi.fn();
const isMsalConfigured = vi.fn();

vi.mock("@/lib/auth/entra-msal", () => ({
  acquireBearer: (...args: unknown[]) => acquireBearer(...args),
  isMsalConfigured: () => isMsalConfigured(),
}));

import { listSimulations } from "@/lib/api/simulations";
import { SimulationAuthError, simulationAuthHeaders } from "@/lib/api/simulation-auth";

function okResponse(body: unknown) {
  return {
    ok: true,
    status: 200,
    json: async () => body,
    text: async () => JSON.stringify(body),
  } as unknown as Response;
}

describe("simulation API transport", () => {
  beforeEach(() => {
    acquireBearer.mockReset();
    isMsalConfigured.mockReset();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("attaches the MSAL bearer token when MSAL is configured", async () => {
    isMsalConfigured.mockReturnValue(true);
    acquireBearer.mockResolvedValue({ accessToken: "tok-123", expiresOn: null, account: {} });
    const fetchMock = vi.fn().mockResolvedValue(
      okResponse({ simulations: [], total: 0, limit: 20, offset: 0 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await listSimulations(undefined, 20, 0);

    const headers = fetchMock.mock.calls[0][1].headers as Record<string, string>;
    expect(headers.Authorization).toBe("Bearer tok-123");
    expect(acquireBearer).toHaveBeenCalledTimes(1);
  });

  it("sends no Authorization header when MSAL is not configured", async () => {
    isMsalConfigured.mockReturnValue(false);
    const fetchMock = vi.fn().mockResolvedValue(
      okResponse({ simulations: [], total: 0, limit: 20, offset: 0 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await listSimulations();

    const headers = fetchMock.mock.calls[0][1].headers as Record<string, string>;
    expect(headers.Authorization).toBeUndefined();
    expect(acquireBearer).not.toHaveBeenCalled();
  });

  it("surfaces a token-acquisition failure instead of calling the API anonymously", async () => {
    isMsalConfigured.mockReturnValue(true);
    acquireBearer.mockRejectedValue(new Error("interaction_required"));
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    await expect(simulationAuthHeaders()).rejects.toBeInstanceOf(SimulationAuthError);
    await expect(listSimulations()).rejects.toThrow(/Sign-in required/);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("propagates API failures with status and body", async () => {
    isMsalConfigured.mockReturnValue(false);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 403,
        text: async () => "forbidden",
      } as unknown as Response),
    );

    await expect(listSimulations()).rejects.toThrow(/API 403: forbidden/);
  });

  it("passes limit and offset through to the list query", async () => {
    isMsalConfigured.mockReturnValue(false);
    const fetchMock = vi.fn().mockResolvedValue(
      okResponse({ simulations: [], total: 0, limit: 20, offset: 40 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await listSimulations("Active", 20, 40);

    expect(String(fetchMock.mock.calls[0][0])).toContain("limit=20&offset=40");
  });
});
