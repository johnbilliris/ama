"use client";

import * as React from "react";

import enAU from "./messages/en-AU.json";
import zhHans from "./messages/zh-Hans.json";
import { LANGUAGE_PACKS, type LanguagePackId } from "./language-packs";

type Messages = Record<string, string>;

type LocaleCode = "en-AU" | "zh-Hans";

const STORAGE_KEY = "ama.locale";
const COOKIE_KEY = "ama-locale";
const DEFAULT_LOCALE: LocaleCode = "en-AU";

const CATALOGUES: Record<LocaleCode, Messages> = {
  "en-AU": enAU,
  "zh-Hans": zhHans,
};

function normalizeLocale(input: string | null | undefined): string {
  return (input ?? "").trim();
}

function fallbackFor(locale: string): LocaleCode {
  if (locale === "zh-Hans") {
    return "zh-Hans";
  }
  const pack = LANGUAGE_PACKS[locale as LanguagePackId];
  if (!pack) {
    return DEFAULT_LOCALE;
  }
  for (const candidate of pack.fallback_chain) {
    if (candidate === "en" || candidate === "en-AU") {
      return "en-AU";
    }
    if (candidate === "zh-Hans") {
      return "zh-Hans";
    }
  }
  return DEFAULT_LOCALE;
}

function resolveLocale(input: string | null | undefined): LocaleCode {
  const locale = normalizeLocale(input);
  if (locale === "en-AU" || locale === "zh-Hans") {
    return locale;
  }
  return fallbackFor(locale);
}

function applyHtmlLanguage(locale: LocaleCode): void {
  if (typeof document === "undefined") {
    return;
  }
  document.documentElement.lang = locale;
  document.documentElement.dir = "ltr";
}

function readCookie(name: string): string | null {
  if (typeof document === "undefined") {
    return null;
  }
  const all = document.cookie.split(";").map((part) => part.trim());
  for (const chunk of all) {
    if (chunk.startsWith(`${name}=`)) {
      return decodeURIComponent(chunk.slice(name.length + 1));
    }
  }
  return null;
}

function writeCookie(name: string, value: string): void {
  if (typeof document === "undefined") {
    return;
  }
  document.cookie = `${name}=${encodeURIComponent(value)}; path=/; max-age=31536000; samesite=lax`;
}

function interpolate(template: string, values?: Record<string, string | number>): string {
  if (!values) {
    return template;
  }
  return template.replace(/\{(\w+)\}/g, (_, key: string) => String(values[key] ?? `{${key}}`));
}

interface I18nContextValue {
  locale: LocaleCode;
  setLocale: (locale: string) => void;
  t: (key: string, values?: Record<string, string | number>) => string;
  formatDateTime: (value: string | Date) => string;
  formatNumber: (value: number) => string;
}

const I18nContext = React.createContext<I18nContextValue | null>(null);

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = React.useState<LocaleCode>(DEFAULT_LOCALE);

  React.useEffect(() => {
    const fromCookie = readCookie(COOKIE_KEY);
    const fromStorage = typeof window !== "undefined" ? window.localStorage.getItem(STORAGE_KEY) : null;
    const fromNavigator = typeof navigator !== "undefined" ? navigator.language : null;
    const resolved = resolveLocale(fromCookie || fromStorage || fromNavigator);
    setLocaleState(resolved);
    applyHtmlLanguage(resolved);
  }, []);

  const setLocale = React.useCallback((nextLocale: string) => {
    const resolved = resolveLocale(nextLocale);
    setLocaleState(resolved);
    applyHtmlLanguage(resolved);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, resolved);
    }
    writeCookie(COOKIE_KEY, resolved);
  }, []);

  const t = React.useCallback(
    (key: string, values?: Record<string, string | number>) => {
      const active = CATALOGUES[locale][key];
      if (active) {
        return interpolate(active, values);
      }
      const fallback = CATALOGUES[DEFAULT_LOCALE][key];
      if (fallback) {
        return interpolate(fallback, values);
      }
      if (process.env.NODE_ENV !== "production") {
        return `[[missing:${key}]]`;
      }
      return key;
    },
    [locale],
  );

  const formatDateTime = React.useCallback(
    (value: string | Date) => {
      const date = value instanceof Date ? value : new Date(value);
      return new Intl.DateTimeFormat(locale, {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }).format(date);
    },
    [locale],
  );

  const formatNumber = React.useCallback(
    (value: number) => {
      return new Intl.NumberFormat(locale).format(value);
    },
    [locale],
  );

  return (
    <I18nContext.Provider value={{ locale, setLocale, t, formatDateTime, formatNumber }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n(): I18nContextValue {
  const context = React.useContext(I18nContext);
  if (!context) {
    throw new Error("useI18n must be used within I18nProvider");
  }
  return context;
}
