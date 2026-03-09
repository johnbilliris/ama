import { expect, test } from "@playwright/test";

test("operator sees workspace tasks and updates status", async ({ page }) => {
  await page.route("**/api/personas/persona-ops-001/workspace", async (route) => {
    await route.fulfill({
      json: {
        persona: {
          persona_id: "persona-ops-001",
          display_name: "Operations Officer",
          organisation_id: "ses-nsw",
          role: "operations_officer",
        },
        tasks: [
          {
            task_id: "task-001",
            title: "Open evacuation centre",
            status: "queued",
            priority: "critical",
          },
        ],
        dependencies: [],
      },
    });
  });

  await page.route("**/api/tasks/task-001/status", async (route) => {
    await route.fulfill({ json: { task_id: "task-001", status: "in_progress" } });
  });

  await page.goto("/workspaces/persona-ops-001");

  await expect(page.getByRole("heading", { name: "Operations Officer" })).toBeVisible();
  await page.getByRole("button", { name: "Start selected task" }).click();
  await expect(page.getByText("Last update: in_progress")).toBeVisible();
});
