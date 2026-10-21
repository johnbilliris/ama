import { afterEach, describe, expect, it, vi } from "vitest";
import { GET } from "@/app/api/[...path]/route";

const originalApiEndpoint = process.env.API_ENDPOINT;
const originalProxyUpstream = process.env.API_PROXY_UPSTREAM;

afterEach(() => {
  vi.unstubAllGlobals();
  if (originalApiEndpoint === undefined) delete process.env.API_ENDPOINT;
  else process.env.API_ENDPOINT = originalApiEndpoint;
  if (originalProxyUpstream === undefined) delete process.env.API_PROXY_UPSTREAM;
  else process.env.API_PROXY_UPSTREAM = originalProxyUpstream;
});

describe("API catch-all proxy", () => {
  it("routes API requests through the runtime endpoint and forwards identity headers", async () => {
    process.env.API_ENDPOINT = "https://api.example.test";
    delete process.env.API_PROXY_UPSTREAM;
    const upstreamFetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ items: [] }), {
        status: 200,
        headers: { "content-type": "application/json", "x-correlation-id": "corr-1" },
      }),
    );
    vi.stubGlobal("fetch", upstreamFetch);

    const request = new Request(
      "https://web.example.test/api/v1/governance/dashboard?scope=active",
      {
        headers: {
          authorization: "Bearer test-token",
          "x-tenant-id": "tenant-a",
        },
      },
    );
    const response = await GET(request, {
      params: Promise.resolve({ path: ["v1", "governance", "dashboard"] }),
    });

    expect(response.status).toBe(200);
    expect(response.headers.get("x-correlation-id")).toBe("corr-1");
    const [target, init] = upstreamFetch.mock.calls[0];
    expect(String(target)).toBe(
      "https://api.example.test/api/v1/governance/dashboard?scope=active",
    );
    const headers = new Headers(init.headers);
    expect(headers.get("authorization")).toBe("Bearer test-token");
    expect(headers.get("x-tenant-id")).toBe("tenant-a");
  });
});
