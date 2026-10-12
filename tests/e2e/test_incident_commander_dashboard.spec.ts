import { expect, test } from "@playwright/test";
import type { AlertDraftPayload } from "../../apps/web/src/lib/api/alerts";
import type { DashboardPayload } from "../../apps/web/src/lib/api/dashboard";

test("incident commander reviews the dashboard and publishes an alert", async ({ page }) => {
  const workflowSteps: string[] = [];
  const alertDraft: AlertDraftPayload = {
    alert_id: "alert-rec-001",
    incident_id: "incident-001",
    status: "draft",
    audience_segments: ["community"],
    languages: ["en-AU"],
    channel_set: ["sms"],
    content_blocks: { headline: "Prepare to evacuate", body: "Follow SES directions" },
  };

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
        ],
        activeRecommendations: [
          {
            recommendation_id: "rec-001",
            type: "public_alert",
            summary: "Issue prepare-to-evacuate alert",
            status: "proposed",
            approvalAction: { allowed: true, requiresPersona: true },
          },
        ],
        activeTasks: [],
        signalSummary: {
          authoritativeCount: 2,
          communityCount: 1,
          contradictedCount: 0,
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
        ],
        total: 1,
      },
    });
  });

  await page.route("**/api/recommendations/rec-001/approvals", async (route) => {
    expect(route.request().method()).toBe("POST");
    expect(route.request().postDataJSON()).toMatchObject({
      approverPersonaId: "persona-ic-001",
      outcome: "approved",
    });
    workflowSteps.push("approve");
    await route.fulfill({ json: { outcome: "approved" } });
  });

  await page.route("**/api/alerts/alert-rec-001", async (route) => {
    expect(route.request().method()).toBe("GET");
    await route.fulfill({ json: alertDraft });
  });

  await page.route("**/api/alerts/alert-rec-001/draft", async (route) => {
    expect(route.request().method()).toBe("PUT");
    expect(route.request().postDataJSON()).toMatchObject({
      contentBlocks: alertDraft.content_blocks,
      audienceSegments: alertDraft.audience_segments,
      languages: alertDraft.languages,
      channelSet: alertDraft.channel_set,
    });
    workflowSteps.push("draft");
    await route.fulfill({ json: alertDraft });
  });

  await page.route("**/api/alerts/alert-rec-001/publish", async (route) => {
    expect(route.request().method()).toBe("POST");
    expect(route.request().postDataJSON()).toEqual({ publishedByPersonaId: "persona-ic-001" });
    workflowSteps.push("publish");
    await route.fulfill({ json: { status: "published" } });
  });

  await page.route("**/api/alerts/alert-rec-001/deliver", async (route) => {
    expect(route.request().method()).toBe("POST");
    workflowSteps.push("deliver");
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

  await expect(
    page.locator(".incident-hero").getByRole("heading", { name: "NSW Flood Response", exact: true }),
  ).toBeVisible();
  await expect(page.getByLabel("Headline")).toBeVisible();
  await expect(page.getByLabel("Headline")).toHaveValue(alertDraft.content_blocks.headline);
  await expect(page.getByRole("button", { name: "Approve and publish alert" })).toBeEnabled();
  await page.getByRole("button", { name: "Approve and publish alert" }).click();
  await expect(page.getByText("Approved and delivered (1 acknowledged receipt(s))")).toBeVisible();
  expect(workflowSteps).toEqual(["draft", "approve", "publish", "deliver"]);
});
