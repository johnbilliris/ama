const DEFAULT_SERVER_API_BASE_URL = "http://localhost:8000/api";

export function getServerApiBaseUrl(): string {
  const configuredBaseUrl = [
    process.env.API_ENDPOINT,
    process.env.SERVICE_API_ENDPOINT_URL,
    process.env.API_PROXY_UPSTREAM,
  ].find((value) => value?.trim());
  if (!configuredBaseUrl) return DEFAULT_SERVER_API_BASE_URL;

  const baseUrl = new URL(configuredBaseUrl.trim());
  if (baseUrl.pathname === "/" || baseUrl.pathname === "") {
    baseUrl.pathname = "/api";
  }
  baseUrl.search = "";
  baseUrl.hash = "";
  return baseUrl.toString().replace(/\/+$/, "");
}

export function getApiBaseUrl(): string {
  if (typeof window === "undefined") return getServerApiBaseUrl();
  const configuredBaseUrl =
    process.env.NEXT_PUBLIC_API_BASE?.trim() ||
    process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  return configuredBaseUrl || "/api";
}
