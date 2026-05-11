/** spec-038 T-AA115 — keyboard-equivalent step list paired with screenshot caption. */
export interface KeyboardStepsProps {
  labelledBy: string;
  steps: string[];
}

export function KeyboardSteps({ labelledBy, steps }: KeyboardStepsProps) {
  return (
    <ol aria-labelledby={labelledBy} className="ml-4 list-decimal text-sm">
      {steps.map((s, i) => (
        <li key={i}>{s}</li>
      ))}
    </ol>
  );
}
