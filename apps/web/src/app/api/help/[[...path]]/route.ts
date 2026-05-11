/**
 * spec-038 — Generic catch-all proxy for /api/help/*.
 *
 * Next.js `rewrites()` are unreliable for every help path under the App Service
 * standalone build (see prior spec-037 web fix for the same problem on
 * /api/incidents). This Route Handler streams every method (GET/POST/PUT/DELETE)
 * straight through to the upstream API, preserving headers, body, and SSE.
 *
 * Auth headers (X-Tenant-Id, X-User-Id, Authorization) are forwarded as-is so
 * tenant isolation (FR-019) and append-only audit (FR-020) operate end-to-end.
 */

import type { NextRequest } from "next/server";

const UPSTREAM =
  process.env.API_PROXY_UPSTREAM ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://localhost:8000/api";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

async function proxy(req: NextRequest, path: string[] | undefined) {
  const tail = (path ?? []).map(encodeURIComponent).join("/");
  const search = req.nextUrl.search ?? "";
  const url = `${UPSTREAM}/help${tail ? "/" + tail : ""}${search}`;

  const headers: Record<string, string> = {};
  for (const [k, v] of req.headers.entries()) {
    const lower = k.toLowerCase();
    if (
      lower === "host" ||
      lower === "connection" ||
      lower === "content-length" ||
      lower === "transfer-encoding" ||
      lower === "keep-alive" ||
      lower === "upgrade" ||
      lower === "proxy-authenticate" ||
      lower === "proxy-authorization"
    ) {
      continue;
    }
    headers[k] = v;
  }

  const init: RequestInit & { duplex?: "half" } = {
    method: req.method,
    headers,
    cache: "no-store",
  };

  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.text();
  }

  let upstream: Response;
  try {
    upstream = await fetch(url, init);
  } catch (err) {
    return new Response(
      JSON.stringify({
        error: "upstream_fetch_failed",
        detail: err instanceof Error ? err.message : String(err),
        upstream: url,
      }),
      { status: 502, headers: { "content-type": "application/json" } },
    );
  }

  const contentType = upstream.headers.get("content-type") ?? "";
  const isStream = contentType.startsWith("text/event-stream");

  const passHeaders: Record<string, string> = {};
  for (const [k, v] of upstream.headers.entries()) {
    const lower = k.toLowerCase();
    if (lower === "transfer-encoding" || lower === "connection") continue;
    passHeaders[k] = v;
  }
  if (isStream) {
    passHeaders["cache-control"] = "no-cache, no-transform";
    passHeaders["x-accel-buffering"] = "no";
  }

  return new Response(upstream.body, {
    status: upstream.status,
    headers: passHeaders,
  });
}

type Ctx = { params: Promise<{ path?: string[] }> };

export async function GET(req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(req, path);
}
export async function POST(req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(req, path);
}
export async function PUT(req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(req, path);
}
export async function PATCH(req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(req, path);
}
export async function DELETE(req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(req, path);
}
