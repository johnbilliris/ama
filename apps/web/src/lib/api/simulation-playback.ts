const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

export interface PlaybackEvent {
  id: string;
  tenant_id: string;
  event_seq: number;
  event_type: string;
  sim_time_offset: number;
  wall_clock_time: string;
  payload: Record<string, unknown>;
}

export interface PlaybackEventsResponse {
  events: PlaybackEvent[];
  has_more: boolean;
  next_cursor: number | null;
  total_events: number;
  playback_status: "full" | "partial" | "none";
}

export interface PlaybackSnapshot {
  id: string;
  tenant_id: string;
  event_seq: number;
  sim_time_offset: number;
  state: Record<string, unknown>;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`API ${response.status}: ${body}`);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export async function getPlaybackEvents(
  tenantId: string,
  afterSeq: number = 0,
  limit: number = 200,
  includeAnnotations: boolean = true,
): Promise<PlaybackEventsResponse> {
  const params = new URLSearchParams({
    after_seq: String(afterSeq),
    limit: String(limit),
    include_annotations: String(includeAnnotations),
  });
  return apiFetch<PlaybackEventsResponse>(
    `/simulations/${encodeURIComponent(tenantId)}/playback/events?${params}`,
  );
}

export async function getAllPlaybackEvents(
  tenantId: string,
  includeAnnotations: boolean = true,
): Promise<{ events: PlaybackEvent[]; playback_status: "full" | "partial" | "none" }> {
  const all: PlaybackEvent[] = [];
  let cursor = 0;
  let status: "full" | "partial" | "none" = "full";
  // Paginate until has_more is false.
  for (let i = 0; i < 1000; i++) {
    const page = await getPlaybackEvents(tenantId, cursor, 200, includeAnnotations);
    all.push(...page.events);
    status = page.playback_status;
    if (!page.has_more || page.next_cursor === null) break;
    cursor = page.next_cursor;
  }
  return { events: all, playback_status: status };
}

export async function getPlaybackSnapshots(
  tenantId: string,
  beforeSimTime?: number,
): Promise<{ snapshots: PlaybackSnapshot[] }> {
  const params = beforeSimTime !== undefined
    ? `?before_sim_time=${beforeSimTime}`
    : "";
  return apiFetch(
    `/simulations/${encodeURIComponent(tenantId)}/playback/snapshots${params}`,
  );
}

export async function createAnnotation(
  tenantId: string,
  simTimeOffset: number,
  text: string,
): Promise<PlaybackEvent> {
  return apiFetch(
    `/simulations/${encodeURIComponent(tenantId)}/playback/annotations`,
    {
      method: "POST",
      body: JSON.stringify({ sim_time_offset: simTimeOffset, text }),
    },
  );
}

export async function updateAnnotation(
  tenantId: string,
  annotationId: string,
  text: string,
): Promise<PlaybackEvent> {
  return apiFetch(
    `/simulations/${encodeURIComponent(tenantId)}/playback/annotations/${encodeURIComponent(annotationId)}`,
    {
      method: "PUT",
      body: JSON.stringify({ text }),
    },
  );
}

export async function deleteAnnotation(
  tenantId: string,
  annotationId: string,
): Promise<void> {
  return apiFetch(
    `/simulations/${encodeURIComponent(tenantId)}/playback/annotations/${encodeURIComponent(annotationId)}`,
    { method: "DELETE" },
  );
}

/**
 * Persist a free-form Event Log line to the durable `sim-events` Cosmos
 * container. Fire-and-forget — failures are logged to the console rather
 * than thrown so a flaky API request never breaks the dashboard UI.
 */
export async function recordEventLogEntry(
  tenantId: string,
  text: string,
  category?: string,
): Promise<void> {
  try {
    await apiFetch(
      `/simulations/${encodeURIComponent(tenantId)}/playback/log-entries`,
      {
        method: "POST",
        body: JSON.stringify({ text, category }),
      },
    );
  } catch (err) {
    console.warn("recordEventLogEntry failed", err);
  }
}
