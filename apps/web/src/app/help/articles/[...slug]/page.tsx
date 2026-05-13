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

async function fetchArticle(slugSegments: string[]): Promise<Article | null> {
  const slugPath = slugSegments.map(encodeURIComponent).join("/");
  try {
    const r = await fetch(
      `${process.env.NEXT_PUBLIC_API_BASE ?? ""}/api/help/articles/${slugPath}`,
      { cache: "no-store" },
    );
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
  return (
    <article className="prose mx-auto max-w-3xl p-6">
      <h1>{article.title}</h1>
      {article.body_md ? (
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{article.body_md}</ReactMarkdown>
      ) : null}
      <FeedbackBar targetKind="article" targetId={article.id} />
    </article>
  );
}
