import { expect, test } from "@playwright/test";
import type { AlertDraftPayload } from "../../apps/web/src/lib/api/alerts";
import type { DashboardPayload } from "../../apps/web/src/lib/api/dashboard";

test("dashboard displays decision-support elements for incident commander", async ({ page }) => {
  await page.route("**/api/incidents/incident-001/dashboard", async (route) => {
    await route.fulfill({
      json: {
        incident: {
          incidentId: "incident-001",
          title: "NSW Flood Response",
          incidentType: "flood",
          status: "active",
          severity: "warning",
          actorPersonaId: "persona-ic-001",
        },
        participatingOrganisations: [
          {
            organisationId: "ses-nsw",
            name: "NSW SES",
            category: "emergency_service",
            status: "active",
          },
          {
            organisationId: "bom-national",
            name: "Bureau of Meteorology",
            category: "commonwealth",
            status: "active",
          },
        ],
        activeRecommendations: [
          {
            recommendation_id: "rec-001",
            type: "public_alert",
            summary: "Issue prepare-to-evacuate alert",
            status: "proposed",
            approvalAction: { allowed: true, requiresPersona: true },
          },
          {
            recommendation_id: "rec-002",
            type: "resource_allocation",
            summary: "Deploy additional sandbagging crews",
            status: "proposed",
          },
        ],
        activeTasks: [],
        signalSummary: {
          authoritativeCount: 3,
          communityCount: 2,
          contradictedCount: 1,
          degradedSources: [
            {
              sourceId: "community-001",
              status: "stale",
              reason: "stale_signal_window",
              since: "2026-03-09T00:00:00Z",
            },
          ],
        },
      } satisfies DashboardPayload,
    });
  });

  await page.route("**/api/signals?incidentId=incident-001", async (route) => {
    await route.fulfill({
      json: {
        items: [
          {
            signal_id: "sig-001",
            incident_id: "incident-001",
            data_source_id: "bom-001",
            category: "weather",
            validation_status: "validated",
            confidence_score: 0.95,
            freshness_score: 0.91,
            provenance: { sourceKind: "authoritative" },
          },
          {
            signal_id: "sig-002",
            incident_id: "incident-001",
            data_source_id: "community-001",
            category: "community_report",
            validation_status: "contradicted",
            confidence_score: 0.45,
            freshness_score: 0.6,
            provenance: { sourceKind: "community" },
          },
        ],
        total: 2,
      },
    });
  });

  await page.route("**/api/alerts/alert-rec-001", async (route) => {
    await route.fulfill({
      json: {
        alert_id: "alert-rec-001",
        incident_id: "incident-001",
        status: "draft",
        audience_segments: ["community"],
        languages: ["en-AU"],
        channel_set: ["sms"],
        content_blocks: { headline: "Prepare to evacuate", body: "Follow SES directions" },
      } satisfies AlertDraftPayload,
    });
  });

  await page.goto("/incidents/incident-001");

  // Decision-support element: incident title and status
  await expect(
    page.locator(".incident-hero").getByRole("heading", { name: "NSW Flood Response", exact: true }),
  ).toBeVisible();

  // Decision-support element: signal health panel with trust indicators
  await expect(page.locator(".source-health-label").filter({ hasText: "Authoritative" })).toBeVisible();
  await expect(page.locator(".source-health-label").filter({ hasText: "Community" })).toBeVisible();
  await expect(page.locator(".source-health-label").filter({ hasText: "Contradicted" })).toBeVisible();

  // Decision-support element: degraded-mode banner (1 contradicted signal)
  await expect(page.getByTestId("degraded-mode-banner")).toBeVisible();

  // Decision-support element: participating agencies
  await expect(page.getByText("NSW SES")).toBeVisible();
  await expect(page.getByText("Bureau of Meteorology")).toBeVisible();

  // Decision-support element: approval action available
  await expect(page.getByRole("button", { name: "Approve and publish alert" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Approve and publish alert" })).toBeEnabled();
});
