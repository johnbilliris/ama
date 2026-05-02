/**
 * PSPF-aware redaction helper (T036).
 *
 * Strips PII / PSPF-classified payloads from anything written to disk by the
 * reporter. Belt-and-braces: the test-support endpoint is read-only so seed
 * data should never appear here, but we redact defensively anyway.
 */

const REDACTED = "[redacted]";

const PII_KEYS = new Set([
  "email",
  "phone",
  "phone_number",
  "ssn",
  "tax_file_number",
  "medicare_number",
  "address",
  "dob",
  "date_of_birth",
  "drivers_licence",
  "passport_number",
]);

export function redact<T>(input: T): T {
  if (input === null || input === undefined) return input;
  if (Array.isArray(input)) return input.map((v) => redact(v)) as unknown as T;
  if (typeof input === "object") {
    const out: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(input as Record<string, unknown>)) {
      if (PII_KEYS.has(key.toLowerCase())) {
        out[key] = REDACTED;
        continue;
      }
      if (typeof value === "string" && /(?:protected|secret|official:sensitive)/i.test(value)) {
        out[key] = REDACTED;
        continue;
      }
      out[key] = redact(value);
    }
    return out as T;
  }
  return input;
}
