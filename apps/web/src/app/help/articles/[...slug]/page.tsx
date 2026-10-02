import { getServerApiBaseUrl } from "@/lib/api/base-url";
/**
 * spec-038 T-AA103 — help article page (server component).
 *
 * Catch-all route (`[...slug]`) so multi-segment slugs like
 * `screen-by-screen/disaster-mapper` and `playbooks/simulation` resolve
 * to the same article rows seeded by `scripts/seed_loader.py` (the slug
 * field in `help_articles` includes the `/` separator).
 */
import { notFound } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { FeedbackBar } from "@/components/help/FeedbackBar";

interface Article {
  id: string;
  slug: string;
  title: string;
  body_md?: string;
  body_url?: string;
  updated_at?: string;
}

// Server components run in Node, so `fetch` requires an absolute URL. Call
// the configured API endpoint directly and
// inject the same default tenant/persona headers the proxy injects so
// `help_deps.get_caller` doesn't 401 the request.
const UPSTREAM = getServerApiBaseUrl();

async function fetchArticle(slugSegments: string[]): Promise<Article | null> {
  const slugPath = slugSegments.map(encodeURIComponent).join("/");
  try {
    const r = await fetch(`${UPSTREAM}/help/articles/${slugPath}`, {
      cache: "no-store",
      headers: {
        "X-Tenant-Id": "live",
        "X-User-Id": "anonymous",
        "X-Persona-Id": "operational-default",
        "X-Persona-Source": "idp_default",
      },
    });
    if (!r.ok) return null;
    return (await r.json()) as Article;
  } catch {
    return null;
  }
}

export default async function ArticlePage({
  params,
}: {
  params: Promise<{ slug: string[] }>;
}) {
  const p = await params;
  const segments = Array.isArray(p.slug) ? p.slug : [p.slug];
  const article = await fetchArticle(segments);
  if (!article) notFound();
  // Seeded markdown bodies typically open with a `# Title` heading that
  // duplicates `article.title`. Strip a single leading h1 so the page header
  // is rendered exactly once.
  const body = article.body_md ? stripLeadingH1(article.body_md) : undefined;
  return (
    <article className="prose mx-auto max-w-3xl px-6 pb-6 pt-2">
      <h1 className="mt-0">{article.title}</h1>
      {body ? (
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{body}</ReactMarkdown>
      ) : null}
      <FeedbackBar targetKind="article" targetId={article.id} />
    </article>
  );
}

function stripLeadingH1(md: string): string {
  return md.replace(/^\s*#\s+[^\n]*\n+/, "");
}
