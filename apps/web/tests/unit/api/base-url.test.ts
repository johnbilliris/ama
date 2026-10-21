import { afterEach, describe, expect, it } from "vitest";
import { getApiBaseUrl, getServerApiBaseUrl } from "@/lib/api/base-url";

const environmentKeys = [
  "API_PROXY_UPSTREAM",
  "API_ENDPOINT",
  "SERVICE_API_ENDPOINT_URL",
  "NEXT_PUBLIC_API_BASE",
  "NEXT_PUBLIC_API_BASE_URL",
] as const;
const originalValues = new Map(
  environmentKeys.map((key) => [key, process.env[key]]),
);

afterEach(() => {
  for (const key of environmentKeys) {
    const value = originalValues.get(key);
    if (value === undefined) delete process.env[key];
    else process.env[key] = value;
  }
});

describe("getServerApiBaseUrl", () => {
  it("adds the API prefix to a configured origin", () => {
    delete process.env.API_PROXY_UPSTREAM;
    delete process.env.SERVICE_API_ENDPOINT_URL;
    process.env.API_ENDPOINT = "https://api.example.test";

    expect(getServerApiBaseUrl()).toBe("https://api.example.test/api");
  });

  it("preserves an API prefix already present in the upstream", () => {
    process.env.API_PROXY_UPSTREAM = "https://api.example.test/api/";

    expect(getServerApiBaseUrl()).toBe("https://api.example.test/api");
  });

  it("prefers the runtime API endpoint over a packaged proxy default", () => {
    process.env.API_PROXY_UPSTREAM = "https://stale-api.example.test/api";
    process.env.API_ENDPOINT = "https://api.example.test";

    expect(getServerApiBaseUrl()).toBe("https://api.example.test/api");
  });

  it("ignores blank runtime endpoints and uses the proxy upstream", () => {
    process.env.API_ENDPOINT = "  ";
    process.env.SERVICE_API_ENDPOINT_URL = "";
    process.env.API_PROXY_UPSTREAM = "https://api.example.test/api";

    expect(getServerApiBaseUrl()).toBe("https://api.example.test/api");
  });

  it("uses the local API default when no endpoint is configured", () => {
    for (const key of environmentKeys) delete process.env[key];

    expect(getServerApiBaseUrl()).toBe("http://localhost:8000/api");
  });
});

describe("getApiBaseUrl", () => {
  it("falls back to the same-origin proxy when the public endpoint is empty", () => {
    process.env.NEXT_PUBLIC_API_BASE = "";
    process.env.NEXT_PUBLIC_API_BASE_URL = "";

    expect(getApiBaseUrl()).toBe("/api");
  });

  it("uses the configured public endpoint when present", () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = " /custom-api ";

    expect(getApiBaseUrl()).toBe("/custom-api");
  });
});
