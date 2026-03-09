"use client";

import { useDeferredValue, useState } from "react";

interface AlertLanguagePreviewProps {
  contentBlocks: Record<string, string>;
  languages: string[];
}

const PLACEHOLDER_TRANSLATIONS: Record<string, Record<string, string>> = {
  "en-AU": { headline: "Prepare to evacuate if directed.", body: "Follow emergency services instructions." },
  "zh-Hans": { headline: "如果指示，请准备撤离。", body: "请遵循紧急服务部门的指示。" },
  "ar": { headline: "استعد للإخلاء إذا طُلب منك ذلك.", body: "اتبع تعليمات خدمات الطوارئ." },
  "vi": { headline: "Chuẩn bị sơ tán nếu được chỉ đạo.", body: "Làm theo hướng dẫn của dịch vụ khẩn cấp." },
};

export function AlertLanguagePreview({ contentBlocks, languages }: AlertLanguagePreviewProps) {
  const availableLanguages = languages.length > 0 ? languages : ["en-AU"];
  const [selectedLanguage, setSelectedLanguage] = useState(availableLanguages[0]);
  const deferredLanguage = useDeferredValue(selectedLanguage);

  const translated = PLACEHOLDER_TRANSLATIONS[deferredLanguage] ?? contentBlocks;

  return (
    <section className="alert-language-preview" aria-label="Alert language preview">
      <header className="alert-language-preview-header">
        <h3 className="alert-language-preview-title">Multilingual alert preview</h3>
        <select
          className="alert-language-preview-select"
          value={selectedLanguage}
          onChange={(event: { target: { value: string } }) => setSelectedLanguage(event.target.value)}
          aria-label="Select preview language"
        >
          {availableLanguages.map((lang) => (
            <option key={lang} value={lang}>
              {lang}
            </option>
          ))}
        </select>
      </header>
      <div className="alert-language-preview-body" dir={deferredLanguage === "ar" ? "rtl" : "ltr"}>
        <p className="alert-language-preview-headline">
          <strong>{translated.headline ?? contentBlocks.headline ?? "—"}</strong>
        </p>
        <p className="alert-language-preview-text">{translated.body ?? contentBlocks.body ?? ""}</p>
      </div>
    </section>
  );
}
