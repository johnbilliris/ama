/**
 * Spec-035 production-auth extension envelope (Q10 / FR-009).
 *
 * Returned on every error response from the production-reachable endpoints.
 * The success body remains the spec-034 EvaluatorResponse shape unchanged
 * per OOS-006.
 *
 * Source: specs/035-webapp-capstone-closure/contracts/production-auth-extension.contract.md
 */
export const EXTENSION_ERROR_CODES = [
  "unauthorized",
  "forbidden",
  "sovereignty_denied",
  "rate_limited",
  "evaluator_not_routable",
  "schema_invalid",
  "seed_not_ready",
] as const;

export type ExtensionErrorCode = (typeof EXTENSION_ERROR_CODES)[number];

export interface ExtensionEnvelope {
  readonly error_code: ExtensionErrorCode;
  /** Non-null only for `rate_limited` and `seed_not_ready`. */
  readonly retry_after_seconds: number | null;
  readonly audit_id: string;
  readonly correlation_id: string;
}

export const ERROR_CODE_TO_HTTP_STATUS: Readonly<Record<ExtensionErrorCode, 400 | 401 | 403 | 422 | 429 | 503>> = {
  unauthorized: 401,
  forbidden: 403,
  sovereignty_denied: 403,
  rate_limited: 429,
  evaluator_not_routable: 400,
  schema_invalid: 422,
  seed_not_ready: 503,
};

/**
 * Error precedence ladder (highest → lowest), per
 * production-auth-extension.contract.md § "Error precedence ladder".
 * Index 0 wins.
 */
export const ERROR_PRECEDENCE: readonly ExtensionErrorCode[] = [
  "evaluator_not_routable",
  "sovereignty_denied",
  "unauthorized",
  "forbidden",
  "rate_limited",
  "schema_invalid",
  "seed_not_ready",
];

const EXTENSION_ERROR_CODE_SET: ReadonlySet<string> = new Set(EXTENSION_ERROR_CODES);

export function isExtensionErrorCode(value: unknown): value is ExtensionErrorCode {
  return typeof value === "string" && EXTENSION_ERROR_CODE_SET.has(value);
}
