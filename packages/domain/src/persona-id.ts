/**
 * PersonaId placeholder type. The 68-persona registry resolution lives in the
 * existing repository layer (out-of-scope per OOS-001); this module only
 * supplies a typed brand for compile-time safety.
 */
export type PersonaId = string & { readonly __personaIdBrand: unique symbol };

export function asPersonaId(value: string): PersonaId {
  return value as PersonaId;
}

/**
 * The reserved system-administrator scope marker. Only the system-administrator
 * AppRole may carry "*" in personaId; every other audit row records the
 * resolved target persona.
 */
export const ADMIN_PERSONA_SCOPE = "*" as const;
export type AdminPersonaScope = typeof ADMIN_PERSONA_SCOPE;
