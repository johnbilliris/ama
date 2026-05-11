/** spec-038 T-AA123 — help sitemap for pa11y-ci. */
import type { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  const base = process.env.NEXT_PUBLIC_BASE_URL ?? "http://localhost:3000";
  const paths = ["/help", "/help/search", "/help/chat"];
  return paths.map((p) => ({ url: `${base}${p}`, lastModified: new Date() }));
}
