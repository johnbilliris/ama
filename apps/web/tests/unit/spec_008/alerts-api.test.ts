import { afterEach, describe, expect, it, vi } from "vitest";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.resetModules();
});

describe("communication alert API", () => {
  it("normalizes a persisted multilingual aggregate for the commander preview", async () => {
    const { normalizeAlertDraft } = await import("../../../src/lib/api/alerts");

    const draft = normalizeAlertDraft({
      alert_id: "ca-inc-1-v1",
      incident_id: "inc-1",
      status: "pending_review",
      audience_segments: ["zone-a-zh-Hans"],
      languages: ["en-AU", "zh-Hans"],
      channel_set: ["sms", "push"],
      content_safety_result: "passed",
      content_blocks: {
        "en-AU": { title: "Flood warning", body: "Water is rising", action_items: "Move now" },
        "zh-Hans": { title: "洪水警报", body: "水位上涨", action_items: "立即撤离" },
      },
    });

    expect(draft.content_blocks.headline).toBe("Flood warning");
    expect(draft.content_blocks["body__zh-Hans"]).toBe("水位上涨");
    expect(draft.audience_segments).toEqual(["zone-a-zh-Hans"]);
    expect(draft.content_safety_result).toBe("passed");
  });

  it("uses the standalone version-bound approval route without body identity", async () => {
    vi.stubEnv("NEXT_PUBLIC_COMMUNICATION_AGENT_URL", "http://communication:8084/");
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: "approved" }) });
    vi.stubGlobal("fetch", fetchMock);
    const { approveAlertDraft } = await import("../../../src/lib/api/alerts");

    await approveAlertDraft("ca-inc-1-v2", "persona-1", "Reviewed against current incident data");

    expect(fetchMock).toHaveBeenCalledWith(
      "http://communication:8084/alerts/ca-inc-1-v2/approve",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ justification: "Reviewed against current incident data" }),
      }),
    );
  });
});