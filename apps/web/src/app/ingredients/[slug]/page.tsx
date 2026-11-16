import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ProductRow } from "@/components/ProductCard";
import { ReportData } from "@/components/ProductActions";
import { DemoBadge, EvidenceBadge, Notice } from "@/components/ui";
import { serverApi } from "@/lib/api";
import type { ProductSummary } from "@/lib/types";

type Detail = {
  id: string; inci_name: string; aliases: string[]; function_classes: string[]; considerations: string | null;
  is_demo: boolean; source: string; reviewed: boolean; data_status: string | null; product_count: number;
  products: ProductSummary[]; knowledge_version: string | null;
  evidence: { id: string; claim: string; citation: string; source_type: string; strength: string }[];
  related_rules: { code: string; interaction_type: string; severity: string; summary: string }[];
};

const load = (id: string) => serverApi<Detail>(`/ingredients/${encodeURIComponent(id)}`, 300);

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const i = await load((await params).slug);
  if (!i) return { title: "Ingredient not found", robots: { index: false } };
  return {
    title: `${i.inci_name} in skincare`,
    description: `What we know about ${i.inci_name}: names, recorded functions, evidence and ${i.product_count} products that contain it.`,
    alternates: { canonical: `/ingredients/${i.id}` },
    robots: i.is_demo || i.product_count < 3 ? { index: false, follow: true } : undefined,
  };
}

export default async function IngredientPage({ params }: { params: Promise<{ slug: string }> }) {
  const i = await load((await params).slug);
  if (!i) notFound();
  return (
    <article className="max-w-4xl space-y-8">
      <nav aria-label="Breadcrumb" className="text-sm text-ink-soft"><Link href="/ingredients" className="hover:underline">Ingredients</Link></nav>
      <header>
        <h1 className="label-voice text-4xl! font-semibold">{i.inci_name}</h1>
        {i.aliases.length > 1 && <p className="mt-2 text-ink-soft">Also written as: {i.aliases.filter((a) => a.toUpperCase() !== i.inci_name).join(", ")}</p>}
        {i.is_demo && <div className="mt-2"><DemoBadge /></div>}
      </header>
      {i.data_status && <Notice>{i.data_status}</Notice>}
      <section aria-labelledby="fn-h">
        <h2 id="fn-h" className="text-xl font-bold">What it does</h2>
        <p className="mt-2">{i.function_classes.length ? `Recorded functions: ${i.function_classes.join(", ")}.` : "Functions are not recorded for this ingredient yet."}</p>
        {i.considerations && <p className="mt-2">{i.considerations}</p>}
      </section>
      <section aria-labelledby="ev-h">
        <h2 id="ev-h" className="text-xl font-bold">Interactions and evidence</h2>
        {i.related_rules.length === 0 ? (
          <p className="mt-2 text-ink-soft">No reviewed interaction rule involves this ingredient in knowledge version {i.knowledge_version ?? "none"}. That is not the same as having no interactions.</p>
        ) : (
          <ul className="mt-3 space-y-3">
            {i.related_rules.map((r) => <li key={r.code} className="rounded-xl border border-line bg-sheet p-4"><p className="font-semibold">{r.summary}</p><p className="text-sm text-ink-soft">{r.interaction_type.replaceAll("_", " ")}, rule {r.code}</p></li>)}
          </ul>
        )}
        {i.evidence.length > 0 && (
          <ul className="mt-4 space-y-3">
            {i.evidence.map((e) => (
              <li key={e.id} className="grid gap-3 rounded-xl bg-mist p-4 sm:grid-cols-[1fr_10rem]">
                <div><p>{e.claim}</p><p className="mt-1 text-sm text-ink-soft">{e.citation}, {e.source_type.replaceAll("_", " ")}</p></div>
                <EvidenceBadge strength={e.strength} />
              </li>
            ))}
          </ul>
        )}
      </section>
      <section aria-labelledby="pr-h">
        <h2 id="pr-h" className="text-xl font-bold">Products that contain it</h2>
        <p className="text-sm text-ink-soft">{i.product_count} products in our catalogue{i.product_count > i.products.length ? `, showing ${i.products.length}` : ""}.</p>
        <ul className="mt-2">{i.products.map((p) => <ProductRow key={p.id} p={p} />)}</ul>
        {i.product_count > i.products.length && <Link className="mt-3 inline-block font-semibold text-dropper underline" href={`/products?ingredient=${i.id}`}>See all {i.product_count}</Link>}
      </section>
      <ReportData targetType="ingredient" targetRef={i.id} />
    </article>
  );
}
