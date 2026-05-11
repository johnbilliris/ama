/** spec-038 T-AA108 — <picture> light/dark + numbered callouts list. */
import type { ReactNode } from "react";

export interface ScreenshotCallout {
  number: number;
  label: string;
  ariaDescribedBy?: string;
  keyboardSteps?: string;
}

export interface AnnotatedScreenshotProps {
  screenId: string;
  altText: string;
  lightSrc: string;
  darkSrc: string;
  callouts: ScreenshotCallout[];
  stale?: boolean;
  staleSince?: string;
  caption?: ReactNode;
}

export function AnnotatedScreenshot({
  screenId,
  altText,
  lightSrc,
  darkSrc,
  callouts,
  stale,
  staleSince,
  caption,
}: AnnotatedScreenshotProps) {
  return (
    <figure data-screen-id={screenId} className="my-4">
      {stale ? (
        <div role="status" className="rounded border border-amber-400 bg-amber-50 p-2 text-sm">
          Screenshot may be out of date{staleSince ? ` (flagged ${staleSince})` : ""}. Showing latest available version.
        </div>
      ) : null}
      <picture>
        <source srcSet={darkSrc} media="(prefers-color-scheme: dark)" />
        <img src={lightSrc} alt={altText} loading="lazy" />
      </picture>
      <figcaption>
        {caption}
        <ol aria-label={`Callouts for ${screenId}`}>
          {callouts
            .slice()
            .sort((a, b) => a.number - b.number)
            .map((c) => (
              <li key={c.number} id={c.ariaDescribedBy} aria-describedby={c.ariaDescribedBy}>
                <strong>{c.number}.</strong> {c.label}
                {c.keyboardSteps ? <em> ({c.keyboardSteps})</em> : null}
              </li>
            ))}
        </ol>
      </figcaption>
    </figure>
  );
}
