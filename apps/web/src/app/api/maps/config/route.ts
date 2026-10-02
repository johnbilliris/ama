export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export function GET() {
  const subscriptionKey = process.env.AZURE_MAPS_SUBSCRIPTION_KEY;

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
