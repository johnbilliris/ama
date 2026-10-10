import { expect, test } from "@playwright/test";

test("incident commander reviews the dashboard and publishes an alert", async ({ page }) => {
  await page.route("**/api/incidents/incident-001/dashboard", async (route) => {
    await route.fulfill({
      json: {
        incident: {
          incidentId: "incident-001",
          title: "NSW Flood Response",
          incidentType: "flood",
          status: "active",
          severity: "warning",
        },
        participatingOrganisations: [
          {
            organisationId: "ses-nsw",
            name: "NSW SES",
            category: "emergency_service",
            status: "active",
          },
        ],
        activeRecommendations: [
          {
            recommendation_id: "rec-001",
            type: "public_alert",
            summary: "Issue prepare-to-evacuate alert",
            status: "proposed",
          },
        ],
        activeTasks: [],
        signalSummary: {
          authoritativeCount: 2,
          communityCount: 1,
          contradictedCount: 0,
        },
      },
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
        ],
        total: 1,
      },
    });
  });

  await page.route("**/api/recommendations/rec-001/approvals", async (route) => {
    await route.fulfill({ json: { outcome: "approved" } });
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
      },
    });
  });

  await page.route("**/api/alerts/alert-rec-001/draft", async (route) => {
    await route.fulfill({
      json: {
        alert_id: "alert-rec-001",
        incident_id: "incident-001",
        status: "draft",
        audience_segments: ["community"],
        languages: ["en-AU"],
        channel_set: ["sms"],
        content_blocks: { headline: "Prepare to evacuate", body: "Follow SES directions" },
      },
    });
  });

  await page.route("**/api/alerts/alert-rec-001/publish", async (route) => {
    await route.fulfill({ json: { status: "published" } });
  });

  await page.route("**/api/alerts/alert-rec-001/deliver", async (route) => {
    await route.fulfill({
      json: [
        {
          alertId: "alert-rec-001",
          contentVersion: "v1",
          channel: "sms",
          recipient: "community",
          status: "acknowledged",
          providerReceipt: { acknowledged: true, id: "r-1" },
        },
      ],
    });
  });

  await page.goto("/incidents/incident-001");

  await expect(page.getByRole("heading", { name: "NSW Flood Response" })).toBeVisible();
  await expect(page.getByLabel("Headline")).toBeVisible();
  await page.getByRole("button", { name: "Approve and publish alert" }).click();
  await expect(page.getByText("Approved and delivered (1 acknowledged receipt(s))")).toBeVisible();
});
