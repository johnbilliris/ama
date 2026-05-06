/**
 * Closed-set Entra ID AppRole enum (spec-035 Clarifications Q1).
 *
 * Exactly 11 values: 10 AIIMS-function roles + system-administrator.
 * MUST stay aligned with apps/api/app/domain/app_role.py.
 */
export const APP_ROLES = [
  "incident-commander",
  "operations-officer",
  "logistics-officer",
  "planning-officer",
  "public-information-officer",
  "field-coordinator",
  "observer-auditor",
  "risk-manager",
  "resilience-planner",
  "executive-leader",
  "system-administrator",
] as const;

export type AppRole = (typeof APP_ROLES)[number];

export const AIIMS_FUNCTION_APP_ROLES: readonly AppRole[] = APP_ROLES.slice(0, 10) as readonly AppRole[];
export const ADMIN_APP_ROLE: AppRole = "system-administrator";

const APP_ROLE_SET: ReadonlySet<string> = new Set(APP_ROLES);

export function isAppRole(value: unknown): value is AppRole {
  return typeof value === "string" && APP_ROLE_SET.has(value);
}

export const APP_ROLE_COUNT: 11 = 11;
