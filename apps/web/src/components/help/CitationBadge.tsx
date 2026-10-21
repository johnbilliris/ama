/** spec-038 T-AA109 — inline citation badge. */
export interface CitationBadgeProps {
  index: number;
  citation: { source_id: string; source_title: string; anchor: string; snippet?: string };
}

function citationHref(citation: CitationBadgeProps["citation"]): string {
  const slug = citation.source_id
    .split("/")
    .map((segment) => encodeURIComponent(segment))
    .join("/");
  const anchor = citation.anchor ? `#${encodeURIComponent(citation.anchor)}` : "";
  return `/help/articles/${slug}${anchor}`;
}

export function CitationBadge({ index, citation }: CitationBadgeProps) {
  return (
    <a
      href={citationHref(citation)}
      aria-label={`Citation ${index}: ${citation.source_title}`}
      title={citation.snippet ?? citation.source_title}
      className="ml-1 inline-flex items-center rounded bg-blue-50 px-1 text-xs text-blue-700 underline"
    >
      [{index}]
    </a>
  );
}
