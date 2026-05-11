/** spec-038 T-AA103 — help article page (server component). */
import { notFound } from "next/navigation";
import { FeedbackBar } from "@/components/help/FeedbackBar";

interface Article {
  id: string;
  slug: string;
  title: string;
  body_md?: string;
  body_url?: string;
  updated_at?: string;
}

async function fetchArticle(slug: string): Promise<Article | null> {
  try {
    const r = await fetch(`${process.env.NEXT_PUBLIC_API_BASE ?? ""}/api/v1/help/articles/${encodeURIComponent(slug)}`, {
      cache: "no-store",
    });
    if (!r.ok) return null;
    return (await r.json()) as Article;
  } catch {
    return null;
  }
}

export default async function ArticlePage({ params }: { params: Promise<{ slug: string }> }) {
  const p = await params;
  const article = await fetchArticle(p.slug);
  if (!article) notFound();
  return (
    <article className="prose mx-auto max-w-3xl p-6">
      <h1>{article.title}</h1>
      {article.body_md ? <div dangerouslySetInnerHTML={{ __html: article.body_md }} /> : null}
      <FeedbackBar targetKind="article" targetId={article.id} />
    </article>
  );
}
