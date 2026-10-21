export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export function GET() {
  // Keep the local fallback runtime-configurable instead of inlining it at build time.
  const subscriptionKey =
    process.env.AZURE_MAPS_SUBSCRIPTION_KEY ||
    process.env["NEXT_PUBLIC_AZURE_MAPS_KEY"];

  if (!subscriptionKey) {
    return Response.json(
      { error: "Azure Maps is not configured" },
      {
        status: 503,
        headers: { "Cache-Control": "no-store" },
      },
    );
  }

  return Response.json(
    { subscriptionKey },
    { headers: { "Cache-Control": "no-store" } },
  );
}
