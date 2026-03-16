"use client";

import { useState } from "react";

const SUPPORTED_LANGUAGES = [
  { code: "en-AU", label: "English (Australia)" },
  { code: "zh-Hans", label: "简体中文" },
  { code: "ar", label: "العربية", dir: "rtl" },
  { code: "vi", label: "Tiếng Việt" },
  { code: "el", label: "Ελληνικά" },
  { code: "it", label: "Italiano" },
] as const;

interface LanguageSwitcherProps {
  defaultLanguage?: string;
  onLanguageChange?: (code: string) => void;
}

export function LanguageSwitcher({
  defaultLanguage = "en-AU",
  onLanguageChange,
}: LanguageSwitcherProps) {
  const [activeLanguage, setActiveLanguage] = useState(defaultLanguage);

  function handleChange(event: { target: { value: string } }) {
    const code = event.target.value;
    setActiveLanguage(code);
    onLanguageChange?.(code);

    const entry = SUPPORTED_LANGUAGES.find((lang) => lang.code === code);
    if (entry && "dir" in entry) {
      document.documentElement.dir = entry.dir;
    } else {
      document.documentElement.dir = "ltr";
    }
    document.documentElement.lang = code;
  }

  return (
    <nav className="language-switcher" aria-label="Language selection">
      <label className="language-switcher-label">
        <span className="language-switcher-icon" aria-hidden="true">🌐</span>
        <select
          className="language-switcher-select"
          value={activeLanguage}
          onChange={handleChange}
          aria-label="Select language"
        >
          {SUPPORTED_LANGUAGES.map((lang) => (
            <option key={lang.code} value={lang.code}>
              {lang.label}
            </option>
          ))}
        </select>
      </label>
    </nav>
  );
}
