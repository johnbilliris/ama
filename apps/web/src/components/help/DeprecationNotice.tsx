/** spec-038 T-AA111 — deprecation notice surfaces replacement or support handoff. */
export interface DeprecationNoticeProps {
  oldSlug: string;
  replacement?: { slug: string; title: string };
  supportHandoff?: { label: string; href?: string };
}

export function DeprecationNotice({ oldSlug, replacement, supportHandoff }: DeprecationNoticeProps) {
  return (
    <aside role="note" className="rounded border border-amber-400 bg-amber-50 p-3 text-sm">
      {replacement ? (
        <p>
          The page <code>{oldSlug}</code> has been superseded by{" "}
          <a className="underline" href={`/help/articles/${replacement.slug}`}>
            {replacement.title}
          </a>
          . The content below comes from the current version.
        </p>
      ) : (
        <p>
          The page <code>{oldSlug}</code> has been withdrawn with no replacement.{" "}
          {supportHandoff ? (
            supportHandoff.href ? (
              <a className="underline" href={supportHandoff.href}>Contact {supportHandoff.label}</a>
            ) : (
              <>Contact {supportHandoff.label}.</>
            )
          ) : (
            <>Contact your tenant support handoff.</>
          )}
        </p>
      )}
    </aside>
  );
}
