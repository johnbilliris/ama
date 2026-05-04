// Ambient module declarations for packages that resolve via apps/web/node_modules
// when the web-coverage tree is type-checked from apps/web/tsconfig.json.
//
// js-yaml: full types live in apps/web/node_modules/@types/js-yaml but TS's
// path-relative @types lookup can't reach them from outside apps/web. The
// runtime import works fine — Playwright transpiles via apps/web's resolver.
declare module "js-yaml" {
  export function load(input: string): unknown;
  export function loadAll(input: string): unknown[];
  export function dump(input: unknown, opts?: Record<string, unknown>): string;
}
