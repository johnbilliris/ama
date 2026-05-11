// Vitest setup file (spec-032 T904).
// Imports global matchers from testing-library so tests can assert on DOM.

import "@testing-library/jest-dom/vitest";
import "fake-indexeddb/auto";
import { Crypto } from "@peculiar/webcrypto";

// JSDOM does not implement SubtleCrypto in older versions; polyfill if missing.
if (typeof globalThis.crypto === "undefined" || !globalThis.crypto.subtle) {
  // Cast — node Crypto has the same surface we touch in tests.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (globalThis as any).crypto = new Crypto();
}
