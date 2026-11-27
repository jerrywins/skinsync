import type { MetadataRoute } from "next";

const base = process.env.PUBLIC_BASE_URL ?? "http://localhost:3000";
const api = `${process.env.API_INTERNAL_URL ?? "http://localhost:8000"}/api/v1`;

// Rendered per request so PUBLIC_BASE_URL comes from the running container, not the image build.
export const dynamic = "force-dynamic";

// Only useful, sufficiently complete public pages are listed (thin and demo pages are excluded).
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const pages: MetadataRoute.Sitemap = ["", "/compare", "/alternatives", "/analyze", "/products", "/ingredients",
    "/how-it-works", "/methodology", "/safety", "/data-sources", "/about", "/privacy", "/terms"]
    .map((p) => ({ url: `${base}${p}`, changeFrequency: "weekly", priority: p === "" ? 1 : 0.6 }));
  try {
    for (let offset = 0; offset < 5000; offset += 50) {
      const r = await fetch(`${api}/products?limit=50&offset=${offset}`, { cache: "no-store" });
      if (!r.ok) break;
      const j = (await r.json()) as { items: { slug: string; is_demo: boolean; has_ingredients: boolean; completeness: number }[]; next_offset: number | null };
      for (const p of j.items) if (!p.is_demo && p.has_ingredients && p.completeness >= 0.6) pages.push({ url: `${base}/products/${p.slug}`, changeFrequency: "monthly", priority: 0.5 });
      if (j.next_offset == null) break;
    }
  } catch { /* API unavailable at build time: static pages only */ }
  return pages;
}
