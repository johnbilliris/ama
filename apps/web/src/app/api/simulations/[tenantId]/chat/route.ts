import { getServerApiBaseUrl } from "@/lib/api/base-url";
/**
 * Streaming pass-through for the Simulation Controller SSE chat endpoint.
 *
 * Next.js `rewrites()` buffer streaming responses (notably SSE) in both
 * dev and production standalone builds, which makes the simulation chat
 * appear unresponsive in the UI. This Route Handler streams the upstream
 * API response straight back to the browser with the correct SSE
 * headers, bypassing the rewrite for this single path.
 */

import type { NextRequest } from "next/server";

const UPSTREAM = getServerApiBaseUrl();

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ tenantId: string }> },
) {
  const { tenantId } = await params;
  const url = `${UPSTREAM}/simulations/${encodeURIComponent(tenantId)}/chat`;

  // Body is a small JSON blob — reading it fully is fine and avoids the
  // Node.js fetch `duplex: 'half'` requirement for streaming request bodies.
  const body = await req.text();

  const upstream = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body,
    // Hint to Node fetch that we want the response body streamed.
    cache: "no-store",
  });

  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
