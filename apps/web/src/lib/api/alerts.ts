import { getApiBaseUrl } from "@/lib/api/base-url";
import { acquireBearer, isMsalConfigured } from "../auth/entra-msal";

const API_BASE_URL = getApiBaseUrl();
const COMMUNICATION_API_BASE_URL = process.env.NEXT_PUBLIC_COMMUNICATION_AGENT_URL?.replace(/\/$/, "");

export interface AlertDraftPayload {
  alert_id: string;
  incident_id: string;
  status: string;
  audience_segments: string[];
  languages: string[];
  channel_set: string[];
  content_blocks: Record<string, string>;
  content_safety_result?: string;
}

export interface AlertDraftUpdatePayload {
  contentBlocks?: Record<string, string>;
  audienceSegments?: string[];
  languages?: string[];
  channelSet?: string[];
}

export interface AlertDeliveryReceipt {
  alertId: string;
  contentVersion: string;
  channel: string;
  recipient: string;
  language?: string;
  status: "simulation" | "skipped" | "submitted" | "acknowledged" | "accepted" | "unconfigured" | "failed";
  providerReceipt: Record<string, unknown> | null;
}

async function authHeaders(): Promise<Record<string, string>> {
  if (typeof window === "undefined" || !isMsalConfigured()) return {};
  const { accessToken } = await acquireBearer();
  return { Authorization: `Bearer ${accessToken}` };
}

export function normalizeAlertDraft(raw: Record<string, unknown>): AlertDraftPayload {
  const sourceBlocks = (raw.content_blocks ?? {}) as Record<string, unknown>;
  const contentBlocks: Record<string, string> = {};
  for (const [key, value] of Object.entries(sourceBlocks)) {
    if (typeof value === "string") {
      contentBlocks[key] = value;
      continue;
    }
    if (value && typeof value === "object") {
      const block = value as Record<string, unknown>;
      contentBlocks[`headline__${key}`] = String(block.title ?? "");
      contentBlocks[`body__${key}`] = String(block.body ?? "");
      contentBlocks[`actionItems__${key}`] = String(block.action_items ?? "");
    }
  }
  contentBlocks.headline ??= contentBlocks["headline__en-AU"] ?? "";
  contentBlocks.body ??= contentBlocks["body__en-AU"] ?? "";
  contentBlocks.actionItems ??= contentBlocks["actionItems__en-AU"] ?? "";
  return {
    alert_id: String(raw.alert_id ?? ""),
    incident_id: String(raw.incident_id ?? ""),
    status: String(raw.status ?? "unknown"),
    audience_segments: Array.isArray(raw.audience_segments) ? raw.audience_segments.map(String) : [],
    languages: Array.isArray(raw.languages) ? raw.languages.map(String) : [],
    channel_set: Array.isArray(raw.channel_set) ? raw.channel_set.map(String) : [],
    content_blocks: contentBlocks,
    content_safety_result: raw.content_safety_result ? String(raw.content_safety_result) : undefined,
  };
}

export function usesCommunicationAgent(): boolean {
  return Boolean(COMMUNICATION_API_BASE_URL);
}

export async function publishAlert(alertId: string, publishedByPersonaId: string) {
  const response = await fetch(`${API_BASE_URL}/alerts/${alertId}/publish`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ publishedByPersonaId }),
  });

  if (!response.ok) {
    throw new Error("Failed to publish public alert");
  }

  return response.json();
}

export async function getAlertDraft(alertId: string): Promise<AlertDraftPayload> {
  const baseUrl = COMMUNICATION_API_BASE_URL ?? API_BASE_URL;
  const response = await fetch(`${baseUrl}/alerts/${alertId}`, {
    cache: "no-store",
    headers: await authHeaders(),
  });

  if (!response.ok) {
    throw new Error("Failed to load alert draft");
  }

  return normalizeAlertDraft((await response.json()) as Record<string, unknown>);
}

export async function updateAlertDraft(alertId: string, payload: AlertDraftUpdatePayload): Promise<AlertDraftPayload> {
  if (COMMUNICATION_API_BASE_URL) {
    const response = await fetch(`${COMMUNICATION_API_BASE_URL}/alerts/${alertId}/modify`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(await authHeaders()) },
      body: JSON.stringify({
        modifications: {
          audience_segments: payload.audienceSegments,
          content_overrides: {
            "en-AU": {
              title: payload.contentBlocks?.headline,
              body: payload.contentBlocks?.body,
              action_items: payload.contentBlocks?.actionItems,
            },
          },
        },
      }),
    });
    if (!response.ok) throw new Error("Failed to create revised public alert");
    const result = (await response.json()) as { alert_id: string };
    return getAlertDraft(result.alert_id);
  }
  const response = await fetch(`${API_BASE_URL}/alerts/${alertId}/draft`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Failed to update alert draft");
  }

  return normalizeAlertDraft((await response.json()) as Record<string, unknown>);
}

export async function approveAlertDraft(alertId: string, actorPersonaId: string, rationale: string) {
  const standalone = Boolean(COMMUNICATION_API_BASE_URL);
  const response = await fetch(
    standalone ? `${COMMUNICATION_API_BASE_URL}/alerts/${alertId}/approve` : `${API_BASE_URL}/alerts/${alertId}/approvals`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(await authHeaders()) },
      body: JSON.stringify(standalone ? { justification: rationale } : { approverPersonaId: actorPersonaId, rationale }),
    },
  );
  if (!response.ok) throw new Error("Failed to approve public alert");
  return response.json();
}

export async function deliverAlert(alertId: string): Promise<AlertDeliveryReceipt[]> {
  const baseUrl = COMMUNICATION_API_BASE_URL ?? API_BASE_URL;
  const response = await fetch(`${baseUrl}/alerts/${alertId}/deliver`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(await authHeaders()),
    },
  });

  if (!response.ok) {
    throw new Error("Failed to deliver public alert");
  }

  const receipts = (await response.json()) as Array<Record<string, unknown>>;
  return receipts.map((receipt) => ({
    alertId: String(receipt.alertId ?? receipt.alert_id ?? ""),
    contentVersion: String(receipt.contentVersion ?? receipt.alert_version ?? ""),
    channel: String(receipt.channel ?? ""),
    recipient: String(receipt.recipient ?? receipt.audience_segment_id ?? ""),
    language: receipt.language ? String(receipt.language) : receipt.language_used ? String(receipt.language_used) : undefined,
    status: String(receipt.status ?? receipt.delivery_status ?? "failed") as AlertDeliveryReceipt["status"],
    providerReceipt: (receipt.providerReceipt ?? receipt.provider_receipt_ids ?? null) as Record<string, unknown> | null,
  }));
}
