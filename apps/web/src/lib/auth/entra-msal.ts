/**
 * MSAL bearer acquisition + token refresh helper (T046, FR-010 / Q1).
 *
 * - Configured from the app registrations provisioned by azd/Bicep.
 * - Requests the API's explicit delegated `access_as_user` scope.
 * - Silent acquisition first, interactive popup fallback when silent fails.
 *
 * See [`auth-rbac.openapi.yaml`](../../../../specs/035-webapp-capstone-closure/contracts/auth-rbac.openapi.yaml).
 */

"use client";

import {
  PublicClientApplication,
  type Configuration,
  type AuthenticationResult,
  InteractionRequiredAuthError,
  type AccountInfo,
} from "@azure/msal-browser";

interface ResolvedConfig {
  clientId: string;
  authority: string;
  scopes: string[];
}

function resolveConfig(): ResolvedConfig | null {
  const clientId = process.env.NEXT_PUBLIC_AZURE_AD_CLIENT_ID;
  const tenantId = process.env.NEXT_PUBLIC_AZURE_AD_TENANT_ID;
  const apiAppId = process.env.NEXT_PUBLIC_AZURE_AD_API_APP_ID;
  const configuredAudience = process.env.NEXT_PUBLIC_AZURE_AD_API_AUDIENCE;
  const apiAudience = configuredAudience?.trim() || (apiAppId ? `api://${apiAppId}` : "");
  if (!clientId || !tenantId || !apiAudience) return null;
  return {
    clientId,
    authority: `https://login.microsoftonline.com/${tenantId}`,
    scopes: [`${apiAudience.replace(/\/+$/, "")}/access_as_user`],
  };
}

let _client: PublicClientApplication | null = null;
let _initPromise: Promise<PublicClientApplication> | null = null;

async function ensureClient(): Promise<PublicClientApplication | null> {
  const cfg = resolveConfig();
  if (!cfg) return null;
  if (_client) return _client;
  if (_initPromise) return _initPromise;
  const config: Configuration = {
    auth: {
      clientId: cfg.clientId,
      authority: cfg.authority,
      redirectUri:
        typeof window !== "undefined" ? window.location.origin : "/",
    },
    cache: { cacheLocation: "sessionStorage" },
  };
  _initPromise = (async () => {
    const c = new PublicClientApplication(config);
    await c.initialize();
    _client = c;
    return c;
  })();
  return _initPromise;
}

export interface BearerToken {
  accessToken: string;
  expiresOn: Date | null;
  account: AccountInfo;
}

/**
 * Acquire a bearer token. Throws when MSAL is not configured (CI/local
 * unauthenticated dev) — callers that gate UI on auth MUST surface the error.
 */
export async function acquireBearer(): Promise<BearerToken> {
  const client = await ensureClient();
  if (!client) {
    throw new Error(
      "msal-not-configured: NEXT_PUBLIC_AZURE_AD client, tenant, and API audience env not set",
    );
  }
  const cfg = resolveConfig()!;
  const accounts = client.getAllAccounts();
  const account =
    accounts[0] ??
    (
      (await client.loginPopup({
        scopes: cfg.scopes,
      })) as AuthenticationResult
    ).account;
  if (!account) throw new Error("msal-no-account");

  try {
    const result = await client.acquireTokenSilent({
      scopes: cfg.scopes,
      account,
    });
    return {
      accessToken: result.accessToken,
      expiresOn: result.expiresOn,
      account: result.account,
    };
  } catch (err) {
    if (err instanceof InteractionRequiredAuthError) {
      const result = await client.acquireTokenPopup({
        scopes: cfg.scopes,
        account,
      });
      return {
        accessToken: result.accessToken,
        expiresOn: result.expiresOn,
        account: result.account,
      };
    }
    throw err;
  }
}

export async function signOut(): Promise<void> {
  const client = await ensureClient();
  if (!client) return;
  await client.logoutPopup();
}

export function isMsalConfigured(): boolean {
  return resolveConfig() !== null;
}
