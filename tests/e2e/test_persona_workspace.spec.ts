import { expect, test } from "@playwright/test";
import type { PersonaWorkspacePayload } from "../../apps/web/src/lib/api/personas";
import type { TaskStatus } from "../../apps/web/src/lib/api/tasks";

test("operator sees workspace tasks and updates status", async ({ page }) => {
  let taskStatus: TaskStatus = "queued";
  let taskVersion = 1;
  await page.route(
    (url) => url.pathname === "/api/personas/persona-ops-001/workspace",
    async (route) => {
      expect(route.request().method()).toBe("GET");
      expect(new URL(route.request().url()).searchParams.get("incidentId")).toBe("incident-001");
      await route.fulfill({
        json: {
          persona: {
            persona_id: "persona-ops-001",
            display_name: "Operations Officer",
            organisation_id: "ses-nsw",
            jurisdiction_id: "nsw",
            role: "operations_officer",
          },
          tasks: [
            {
              task_id: "task-001",
              title: "Open evacuation centre",
              status: taskStatus,
              priority: "critical",
              version: taskVersion,
            },
          ],
          dependencies: [],
        } satisfies PersonaWorkspacePayload,
      });
    },
  );

  await page.route("**/api/tasks/task-001", async (route) => {
    expect(route.request().method()).toBe("PATCH");
    expect(route.request().postDataJSON()).toEqual({
      personaId: "persona-ops-001",
      status: "in_progress",
      ifMatch: taskVersion,
    });
    taskStatus = "in_progress";
    taskVersion += 1;
    await route.fulfill({ json: { task_id: "task-001", status: taskStatus, version: taskVersion } });
  });

  await page.goto("/workspaces/persona-ops-001");

  await expect(page.getByRole("heading", { name: "Operations Officer" })).toBeVisible();
  await expect(page.getByLabel("Selected task").locator("option:checked")).toHaveText(
    "Open evacuation centre (queued)",
  );
  await page.getByRole("button", { name: "Start", exact: true }).click();
  await expect(page.getByLabel("Selected task").locator("option:checked")).toHaveText(
    "Open evacuation centre (in_progress)",
  );
  await expect(page.locator(".workspace-list-item").filter({ hasText: "Open evacuation centre" })).toContainText(
    "critical priority · in_progress",
  );
});
