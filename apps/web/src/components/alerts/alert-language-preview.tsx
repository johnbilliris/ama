"use client";

import { useDeferredValue, useState } from "react";
import { useI18n } from "../../lib/i18n/runtime";

interface AlertLanguagePreviewProps {
  contentBlocks: Record<string, string>;
  languages: string[];
}

export function AlertLanguagePreview({ contentBlocks, languages }: AlertLanguagePreviewProps) {
  const { t } = useI18n();
  const availableLanguages = languages.length > 0 ? languages : ["en-AU"];
  const [selectedLanguage, setSelectedLanguage] = useState(availableLanguages[0]);
  const deferredLanguage = useDeferredValue(selectedLanguage);

  const fallbackLocale = availableLanguages.includes("en-AU") ? "en-AU" : availableLanguages[0];
  const fallbackHeadline = contentBlocks[`headline__${fallbackLocale}`] ?? contentBlocks.headline ?? "—";
  const fallbackBody = contentBlocks[`body__${fallbackLocale}`] ?? contentBlocks.body ?? "";
  const requestedHeadline = contentBlocks[`headline__${deferredLanguage}`];
  const requestedBody = contentBlocks[`body__${deferredLanguage}`];
  const requestedVersion = contentBlocks[`contentVersion__${deferredLanguage}`];
  const canonicalVersion = contentBlocks.contentVersion;
  const hasVariant = typeof requestedHeadline === "string" || typeof requestedBody === "string";

  const headline = hasVariant ? requestedHeadline ?? fallbackHeadline : fallbackHeadline;
  const body = hasVariant ? requestedBody ?? fallbackBody : fallbackBody;
  const direction = deferredLanguage === "ar" || deferredLanguage === "he" ? "rtl" : "ltr";

  return (
    <section className="alert-language-preview" aria-label="Alert language preview">
      <header className="alert-language-preview-header">
        <h3 className="alert-language-preview-title">{t("alerts.previewTitle")}</h3>
        <select
          className="alert-language-preview-select"
          value={selectedLanguage}
          onChange={(event: { target: { value: string } }) => setSelectedLanguage(event.target.value)}
          aria-label={t("alerts.previewSelect")}
        >
          {availableLanguages.map((lang) => (
            <option key={lang} value={lang}>
              {lang}
            </option>
          ))}
        </select>
      </header>
      <div className="alert-language-preview-body" dir={direction}>
        {!hasVariant ? (
          <p className="alert-composer-status" role="status">
            {t("alerts.translationMissing", { locale: deferredLanguage, fallbackLocale })}
          </p>
        ) : null}
        {requestedVersion && canonicalVersion && requestedVersion !== canonicalVersion ? (
          <p className="alert-composer-status" role="alert">
            {t("alerts.translationVersionMismatch", {
              requestedVersion,
              actualVersion: canonicalVersion,
            })}
          </p>
        ) : null}
        <p className="alert-language-preview-headline">
          <strong>{headline}</strong>
        </p>
        <p className="alert-language-preview-text">{body}</p>
      </div>
    </section>
  );
}
