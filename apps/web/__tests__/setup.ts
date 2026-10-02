// Vitest setup file (spec-032 T904).
// Imports global matchers from testing-library so tests can assert on DOM.

import "@testing-library/jest-dom/vitest";
import "fake-indexeddb/auto";
import { webcrypto } from "node:crypto";

Object.defineProperty(HTMLCanvasElement.prototype, "getContext", {
  configurable: true,
  value: () => null,
});

// JSDOM does not implement SubtleCrypto in older versions; polyfill if missing.
// Use Node's built-in webcrypto (Node ≥ 19) — avoids @peculiar/webcrypto's
// CommonJS shim which is incompatible with Vite 7 / Vitest 2 SSR transform
// (`__vite_ssr_exportName__ is not defined`).
if (typeof globalThis.crypto === "undefined" || !globalThis.crypto.subtle) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (globalThis as any).crypto = webcrypto;
}
