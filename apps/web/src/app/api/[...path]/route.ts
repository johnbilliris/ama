import { getServerApiBaseUrl } from "@/lib/api/base-url";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

const HOP_BY_HOP_HEADERS = [
  "connection",
  "content-length",
  "host",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
];

function removeHeaders(headers: Headers, names: string[]): void {
  for (const name of names) headers.delete(name);
}

async function proxy(request: Request, context: RouteContext): Promise<Response> {
  const { path } = await context.params;
  const incomingUrl = new URL(request.url);
  const upstreamUrl = new URL(
    `${path.map((segment) => encodeURIComponent(segment)).join("/")}${incomingUrl.search}`,
    `${getServerApiBaseUrl()}/`,
  );
  const requestHeaders = new Headers(request.headers);
  removeHeaders(requestHeaders, HOP_BY_HOP_HEADERS);

  const init: RequestInit & { duplex?: "half" } = {
    method: request.method,
    headers: requestHeaders,
    cache: "no-store",
    redirect: "manual",
    signal: request.signal,
  };
  if (request.method !== "GET" && request.method !== "HEAD" && request.body) {
    init.body = request.body;
    init.duplex = "half";
  }

  const upstreamResponse = await fetch(upstreamUrl, init);
  const responseHeaders = new Headers(upstreamResponse.headers);
  removeHeaders(responseHeaders, [...HOP_BY_HOP_HEADERS, "content-encoding"]);
  return new Response(upstreamResponse.body, {
    status: upstreamResponse.status,
    statusText: upstreamResponse.statusText,
    headers: responseHeaders,
  });
}

export const GET = proxy;
export const HEAD = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
export const OPTIONS = proxy;
