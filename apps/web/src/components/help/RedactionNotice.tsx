/** spec-038 T-AA117 — redaction notice. */
export function RedactionNotice() {
  return (
    <p role="status" className="text-xs text-amber-800">
      Personally identifying details were redacted by our model gateway before this question was answered.
    </p>
  );
}
