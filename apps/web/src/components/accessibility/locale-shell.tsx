"use client";

import type { PropsWithChildren } from "react";

import { LanguageSwitcher } from "./language-switcher";
import { I18nProvider, useI18n } from "../../lib/i18n/runtime";

function LocaleChrome({ children }: PropsWithChildren) {
  const { locale, setLocale, t } = useI18n();

  return (
    <>
      <div className="ama-locale-switcher-shell">
        <LanguageSwitcher
          defaultLanguage={locale}
          onLanguageChange={setLocale}
          ariaLabel={t("locale.switcherLabel")}
          selectAriaLabel={t("locale.selectLabel")}
        />
      </div>
      {children}
    </>
  );
}

export function LocaleShell({ children }: PropsWithChildren) {
  return (
    <I18nProvider>
      <LocaleChrome>{children}</LocaleChrome>
    </I18nProvider>
  );
}
