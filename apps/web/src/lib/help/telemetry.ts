/**
 * spec-038 T-AA093 — typed Application Insights telemetry wrappers for the
 * 10 events in contracts/help-ui.contract.ts.md §3.
 */

export type HelpTelemetryEvent =
  | { name: "help.affordance.opened"; surface: string }
  | { name: "help.article.viewed"; slug: string; persona: string }
  | { name: "help.search.executed"; query: string; resultCount: number }
  | { name: "help.chat.opened"; persona: string }
  | { name: "help.chat.message.sent"; sessionId: string; turnIndex: number }
  | { name: "help.chat.refused"; reason: string }
  | { name: "help.feedback.submitted"; targetKind: string; rating: string }
  | { name: "help.staleness.flag.raised"; screenId: string }
  | { name: "help.degraded.mode.activated"; trigger: string }
  | { name: "help.persona.switched"; from: string; to: string };

type AppInsights = {
  trackEvent?: (event: { name: string; properties?: Record<string, unknown> }) => void;
};

declare global {
   
  interface Window {
    appInsights?: AppInsights;
  }
}

export function trackHelpEvent(event: HelpTelemetryEvent): void {
  if (typeof window === "undefined") return;
  const ai = window.appInsights;
  if (!ai?.trackEvent) {
    // dev fallback — surface in console so a11y/e2e harness can assert
     
    console.debug("[help.telemetry]", event);
    return;
  }
  const { name, ...properties } = event;
  ai.trackEvent({ name, properties });
}
