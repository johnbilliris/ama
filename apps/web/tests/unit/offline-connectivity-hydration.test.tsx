import { act, type ReactElement } from "react";
import { hydrateRoot } from "react-dom/client";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { ConnectivityBanner } from "@/components/offline/connectivity-banner";
import FieldCoordinatorOffline from "@/app/workspaces/[personaId]/_panels/field-coordinator-offline";

async function expectHydrationToMatch(element: ReactElement): Promise<void> {
  const container = document.createElement("div");
  container.innerHTML = renderToString(element);
  const recoverableErrors: Error[] = [];
  let root: ReturnType<typeof hydrateRoot> | undefined;

  await act(async () => {
    root = hydrateRoot(container, element, {
      onRecoverableError: (error) => recoverableErrors.push(error),
    });
  });

  expect(recoverableErrors).toEqual([]);
  await act(async () => root?.unmount());
}

describe("offline connectivity hydration", () => {
  it("keeps the server markup stable when the browser is offline", async () => {
    const onlineDescriptor = Object.getOwnPropertyDescriptor(navigator, "onLine");
    Object.defineProperty(navigator, "onLine", {
      configurable: true,
      value: false,
    });

    try {
      await expectHydrationToMatch(<ConnectivityBanner />);
      await expectHydrationToMatch(<FieldCoordinatorOffline />);
    } finally {
      if (onlineDescriptor) {
        Object.defineProperty(navigator, "onLine", onlineDescriptor);
      } else {
        Object.defineProperty(navigator, "onLine", {
          configurable: true,
          value: true,
        });
      }
    }
  });
});
