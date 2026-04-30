/**
 * Liveness/readiness probe endpoint for Azure App Service.
 *
 * Wired up via `siteConfig.healthCheckPath: '/api/health'` in
 * `infra/main.bicep`, which is required by the PSRule rules
 * Azure.AppService.WebProbe + Azure.AppService.WebProbePath
 * (the latter rejects path lengths ≤ 1 character, so `/` is not enough).
 *
 * The route is intentionally minimal: it does not call downstream
 * dependencies. App Service treats any 2xx status code in under 1 minute
 * as healthy and restarts the instance after consecutive 5xx responses.
 */

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export function GET() {
  return Response.json({ status: "ok" });
}
