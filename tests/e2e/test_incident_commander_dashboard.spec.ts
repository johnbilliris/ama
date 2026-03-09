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
      json: [
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
    });
  });

  await page.route("**/api/recommendations/rec-001/approvals", async (route) => {
    await route.fulfill({ json: { outcome: "approved" } });
  });

  await page.route("**/api/alerts/alert-rec-001/publish", async (route) => {
    await route.fulfill({ json: { status: "published" } });
  });

  await page.goto("/incidents/incident-001");

  await expect(page.getByRole("heading", { name: "NSW Flood Response" })).toBeVisible();
  await page.getByRole("button", { name: "Approve and publish alert" }).click();
  await expect(page.getByText("Approved and published to outbound channels")).toBeVisible();
});
