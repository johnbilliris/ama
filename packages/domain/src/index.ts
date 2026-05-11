/**
 * @ama/domain — shared TypeScript domain types for spec-035.
 *
 * Authoritative source of the closed-set enums consumed by the Next.js web app
 * (apps/web) and any TypeScript test fixtures. The Python equivalents live at
 * apps/api/app/domain/ and MUST stay byte-identical in cardinality.
 *
 * Refs:
 *  - specs/035-webapp-capstone-closure/data-model.md § 4 AuditTimelineEntry
 *  - specs/035-webapp-capstone-closure/data-model.md § 6 EntraAppRoleBinding
 *  - specs/035-webapp-capstone-closure/data-model.md § 8 OfflineQueueEntry
 */

export * from "./audit-outcome.js";
export * from "./app-role.js";
export * from "./offline-queue-tier.js";
export * from "./persona-id.js";
export * from "./extension-envelope.js";

// spec-038 Help domain twins
export * as Help from "./help/index.js";
