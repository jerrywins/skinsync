import type { Metadata } from "next";
import { headers } from "next/headers";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ExplainPanel } from "@/components/ExplainPanel";
import { LabelStrip } from "@/components/LabelStrip";
import { PriceTag } from "@/components/ProductCard";
import { ProductActions, ReportData } from "@/components/ProductActions";
import { DemoBadge, Notice } from "@/components/ui";
import { serverApi } from "@/lib/api";
import { CATEGORY_LABEL, date, pct } from "@/lib/format";
import type { ProductDetail } from "@/lib/types";

async function load(slug: string) {
  return serverApi<ProductDetail>(`/products/${encodeURIComponent(slug)}`, 300);
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const p = await load((await params).slug);
  if (!p) return { title: "Product not found", robots: { index: false } };
  const title = `${p.name}${p.brand ? ` by ${p.brand}` : ""}: ingredients`;
  return {
    title,
    description: `Ingredient list of ${p.name}, with ${pct(p.current_version?.completeness)} of ingredients recognised. Compare it or find alternatives.`,
    alternates: { canonical: `/products/${p.slug}` },
    robots: p.indexable ? undefined : { index: false, follow: true }, // thin or demo pages are not indexed
    openGraph: { title, type: "website", images: p.image_url ? [p.image_url] : undefined },
  };
}

export default async function ProductPage({ params }: { params: Promise<{ slug: string }> }) {
  const p = await load((await params).slug);
  if (!p) notFound();
  const nonce = (await headers()).get("x-nonce") ?? undefined;
  const v = p.current_version;
  const items = p.ingredients.map((i) => ({ position: i.position, raw: i.raw, canonical_id: i.ingredient_id,
                                           inci_name: i.inci_name, candidate: null, stated_role: i.stated_role }));
  const unreviewed = p.ingredients.filter((i) => i.ingredient_id && !i.name_reviewed).length;
  const jsonLd = {
    "@context": "https://schema.org", "@type": "Product", name: p.name,
    brand: p.brand ? { "@type": "Brand", name: p.brand } : undefined, category: CATEGORY_LABEL[p.category],
    image: p.image_url ?? undefined, gtin13: p.barcodes.find((b) => b.length === 13),
  };
  return (
    <article className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_20rem]">
      {p.indexable && <script type="application/ld+json" nonce={nonce} dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }} />}
      <div className="min-w-0 space-y-8">
        <nav aria-label="Breadcrumb" className="text-sm text-ink-soft">
          <Link href="/products" className="hover:underline">Products</Link> /{" "}
          <Link href={`/products?category=${p.category}`} className="hover:underline">{CATEGORY_LABEL[p.category] ?? p.category}</Link>
        </nav>
        <header className="flex flex-wrap items-start gap-6">
          {p.image_url && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={p.image_url} alt="" className="size-28 rounded-2xl border border-line bg-sheet object-contain" />
          )}
          <div className="min-w-0 flex-1">
            {p.brand && <Link href={`/brands/${p.brand_slug}`} className="font-semibold text-ink-soft hover:underline">{p.brand}</Link>}
            <h1 className="text-3xl font-extrabold sm:text-4xl">{p.name}</h1>
            <p className="mt-1 text-ink-soft">{CATEGORY_LABEL[p.category] ?? p.category}{p.market === "IN" ? ", sold in India" : ""}</p>
            {p.is_demo && <div className="mt-2"><DemoBadge>DEMO product: fictional, for demonstration only</DemoBadge></div>}
          </div>
        </header>
        <ProductActions id={p.id} name={p.name} />

        <section aria-labelledby="ing-h" className="space-y-3">
          <h2 id="ing-h" className="text-xl font-bold">Ingredients</h2>
          {!v?.has_ingredient_list ? (
            <Notice tone="caution">We have no ingredient list for this product, so it cannot be compared yet. You can type the list from the pack on the compare page.</Notice>
          ) : (
            <>
              <LabelStrip title={`Formulation ${v.label}`} subtitle={`Observed ${date(v.observed_at)}, source: ${v.source}`} items={items} />
              {p.unresolved_count > 0 && (
                <Notice>{p.unresolved_count} ingredient{p.unresolved_count > 1 ? "s are" : " is"} not recognised. They are treated as unknown, never as harmless.</Notice>
              )}
              <details className="text-sm">
                <summary className="cursor-pointer font-semibold">Ingredient details</summary>
                <table className="mt-2 w-full text-left">
                  <caption className="sr-only">Ingredients with recognition details</caption>
                  <thead className="text-ink-soft"><tr><th className="py-1 pr-3">#</th><th className="pr-3">As printed</th><th className="pr-3">Recognised as</th><th className="pr-3">Match</th><th>Functions</th></tr></thead>
                  <tbody>
                    {p.ingredients.map((i) => (
                      <tr key={i.position} className="border-t border-line align-top">
                        <td className="py-1.5 pr-3">{i.position}</td>
                        <td className="label-voice pr-3">{i.raw}</td>
                        <td className="pr-3">{i.ingredient_id ? <Link className="text-dropper hover:underline" href={`/ingredients/${i.ingredient_id}`}>{i.inci_name}</Link> : <span className="text-unknown">Not recognised</span>}</td>
                        <td className="pr-3">{i.ingredient_id ? `${i.method.replaceAll("_", " ")}, ${pct(i.confidence)}` : "–"}</td>
                        <td>{i.function_classes.length ? i.function_classes.join(", ") : <span className="text-unknown">not recorded</span>}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </details>
            </>
          )}
        </section>

        <section aria-labelledby="price-h">
          <h2 id="price-h" className="text-xl font-bold">Prices</h2>
          <ul className="mt-2 space-y-1">
            {p.prices.map((pr, i) => (
              <li key={i}><PriceTag price={pr} />{pr.seller && <span className="text-sm text-ink-soft">, {pr.seller}</span>}</li>
            ))}
          </ul>
          {!p.prices.some((pr) => pr.is_test) && <p className="mt-1 text-sm text-ink-soft">We only show prices we have actually observed, with the date. We never estimate one.</p>}
          {p.prices.some((pr) => pr.is_test) && <p className="mt-1 text-sm font-semibold text-caution">Prices marked TEST PRICE are random values loaded for testing this build. They are not real prices.</p>}
        </section>

        {p.versions.length > 1 && (
          <section aria-labelledby="ver-h">
            <h2 id="ver-h" className="text-xl font-bold">Formulation history</h2>
            <ul className="mt-2 space-y-1 text-sm">
              {p.versions.map((x) => <li key={x.id}>{x.label}{x.is_current ? " (current)" : ""}, {pct(x.completeness)} recognised</li>)}
            </ul>
          </section>
        )}
        <ReportData targetType="product" targetRef={p.id} />
      </div>
      <ExplainPanel
        used={[
          { label: "Source", value: p.provenance.source_url ? <a className="underline" href={p.provenance.source_url}>{p.provenance.source}</a> : p.provenance.source },
          { label: "Retrieved", value: date(p.provenance.retrieved_at) },
          ...(p.provenance.licence ? [{ label: "Licence", value: p.provenance.licence }] : []),
          ...(v ? [{ label: "Verification", value: v.verification }] : []),
        ]}
        confidence={v?.has_ingredient_list ? v.completeness : null}
        missing={[
          ...(!v?.has_ingredient_list ? ["Ingredient list"] : []),
          ...(p.unresolved_count ? [`${p.unresolved_count} unrecognised ingredient(s)`] : []),
          ...(unreviewed ? [`${unreviewed} ingredient name(s) taken from source data and not yet reviewed`] : []),
          ...(p.ingredients.some((i) => i.ingredient_id && i.function_classes.length === 0) ? ["Ingredient functions are not recorded for most ingredients yet"] : []),
          ...(p.prices[0]?.state === "unavailable" ? ["Current price"] : []),
        ]}
        footnote="Data completeness: the share of listed ingredients we recognise. It is not a quality score."
      />
    </article>
  );
}
