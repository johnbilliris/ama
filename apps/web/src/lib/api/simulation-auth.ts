/**
 * AUD-016 — single authenticated transport for every simulation API client.
 *
 * Reuses the application's existing MSAL helper (`@/lib/auth/entra-msal`)
 * rather than introducing a second auth stack. When MSAL is not configured
 * (CI, local unauthenticated dev) no header is attached and the API's own
 * environment guard decides the outcome — the UI must not fabricate one.
 */
import { acquireBearer, isMsalConfigured } from "@/lib/auth/entra-msal";

export class SimulationAuthError extends Error {
  constructor(message: string, readonly cause?: unknown) {
    super(message);
    this.name = "SimulationAuthError";
  }
}

export async function simulationAuthHeaders(): Promise<Record<string, string>> {
  if (typeof window === "undefined") return {};
  if (!isMsalConfigured()) return {};
  try {
    const { accessToken } = await acquireBearer();
    return { Authorization: `Bearer ${accessToken}` };
  } catch (err) {
    throw new SimulationAuthError(
      "Sign-in required to reach the simulation API.",
      err,
    );
  }
}

/**
 * AUD-015 — the signed-in participant's Entra object ID, used to select their
 * own simulation assignment. Explicit dev mode uses a stable synthetic OID;
 * otherwise returns `null` when MSAL is unavailable.
 */
export async function simulationPrincipalOid(): Promise<string | null> {
  if (typeof window === "undefined") return null;
  if (!isMsalConfigured()) {
    return process.env.NEXT_PUBLIC_ALLOW_ANONYMOUS_DEV_ACCESS === "1" ? "dev-user" : null;
  }
  try {
    const { account } = await acquireBearer();
    return account?.localAccountId ?? null;
  } catch {
    return null;
  }
}
