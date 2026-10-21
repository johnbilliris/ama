import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { I18nProvider, useI18n } from "../../../src/lib/i18n/runtime";
import { AlertLanguagePreview } from "../../../src/components/alerts/alert-language-preview";

function RuntimeProbe() {
  const { locale, setLocale, t } = useI18n();
  return (
    <div>
      <button type="button" onClick={() => setLocale("zh-Hans")}>zh</button>
      <button type="button" onClick={() => setLocale("ar")}>ar</button>
      <span data-testid="locale">{locale}</span>
      <span data-testid="missing">{t("missing.key")}</span>
    </div>
  );
}

describe("i18n runtime and alert preview", () => {
  it("persists locale and uses fallback chain for unsupported locale", () => {
    render(
      <I18nProvider>
        <RuntimeProbe />
      </I18nProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "zh" }));
    expect(screen.getByTestId("locale").textContent).toBe("zh-Hans");
    expect(document.documentElement.lang).toBe("zh-Hans");
    expect(window.localStorage.getItem("ama.locale")).toBe("zh-Hans");

    fireEvent.click(screen.getByRole("button", { name: "ar" }));
    expect(screen.getByTestId("locale").textContent).toBe("en-AU");
    expect(document.documentElement.lang).toBe("en-AU");
  });

  it("shows missing-key marker in non-production mode", () => {
    render(
      <I18nProvider>
        <RuntimeProbe />
      </I18nProvider>,
    );

    expect(screen.getByTestId("missing").textContent).toBe("[[missing:missing.key]]");
  });

  it("preserves approved english content and surfaces fallback + version mismatch notice", () => {
    render(
      <I18nProvider>
        <AlertLanguagePreview
          languages={["en-AU", "zh-Hans"]}
          contentBlocks={{
            headline: "Approved English headline",
            body: "Approved English body",
            "headline__zh-Hans": "已审批中文标题",
            "contentVersion__zh-Hans": "v1",
            contentVersion: "v2",
          }}
        />
      </I18nProvider>,
    );

    expect(screen.getByText("Approved English headline")).toBeTruthy();

    fireEvent.change(screen.getByLabelText("Select preview language"), {
      target: { value: "zh-Hans" },
    });

    expect(screen.getByText(/Version mismatch/i)).toBeTruthy();

    fireEvent.change(screen.getByLabelText("Select preview language"), {
      target: { value: "en-AU" },
    });

    expect(screen.getByText("Approved English headline")).toBeTruthy();
  });
});
