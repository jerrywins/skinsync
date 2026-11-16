import type { Metadata } from "next";
import Link from "next/link";
import { ProductRow } from "@/components/ProductCard";
import { Empty, PageTitle } from "@/components/ui";
import { serverApi } from "@/lib/api";
import { CATEGORY_LABEL } from "@/lib/format";
import type { Page, ProductSummary } from "@/lib/types";

type Sp = { q?: string; category?: string; brand?: string; ingredient?: string; page?: string };

export async function generateMetadata({ searchParams }: { searchParams: Promise<Sp> }): Promise<Metadata> {
  const sp = await searchParams;
  const filtered = !!(sp.q || sp.ingredient || sp.brand || (sp.page && sp.page !== "1"));
  const cat = sp.category ? CATEGORY_LABEL[sp.category] : null;
  return {
    title: cat ? `${cat} products` : "Skincare products",
    description: "Browse skincare products with their ingredient lists, data completeness and sources.",
    // Search results and deep pagination are not useful search-engine pages.
    robots: filtered ? { index: false, follow: true } : undefined,
    alternates: { canonical: sp.category ? `/products?category=${sp.category}` : "/products" },
  };
}

export default async function Products({ searchParams }: { searchParams: Promise<Sp> }) {
  const sp = await searchParams;
  const page = Math.max(1, Number(sp.page ?? 1) || 1);
  const qs = new URLSearchParams();
  for (const k of ["q", "category", "brand", "ingredient"] as const) if (sp[k]) qs.set(k, sp[k]!);
  qs.set("limit", "30");
  qs.set("offset", String((page - 1) * 30));
  const [data, cats] = await Promise.all([
    serverApi<Page<ProductSummary>>(`/products?${qs}`, 60),
    serverApi<{ id: string; label: string; count: number }[]>("/categories", 3600),
  ]);
  const link = (patch: Partial<Sp>) => {
    const n = new URLSearchParams(qs);
    n.delete("limit"); n.delete("offset");
    Object.entries(patch).forEach(([k, v]) => (v ? n.set(k, v) : n.delete(k)));
    return `/products?${n}`;
  };
  return (
    <>
      <PageTitle title="Products" lead="Every product shows where its data came from and how much of its ingredient list we recognise." />
      <form action="/products" className="mb-6 flex max-w-xl gap-2" role="search">
        <label htmlFor="pq" className="sr-only">Search products</label>
        <input id="pq" name="q" defaultValue={sp.q} className="field" placeholder="Product, brand or ingredient" />
        {sp.category && <input type="hidden" name="category" value={sp.category} />}
        <button className="btn btn-primary">Search</button>
      </form>
      <div className="grid gap-8 md:grid-cols-[13rem_1fr]">
        <nav aria-label="Categories">
          <ul className="flex flex-wrap gap-2 md:block md:space-y-1">
            <li><Link href={link({ category: undefined, page: undefined })} aria-current={!sp.category ? "page" : undefined}
                      className={`block rounded-lg px-3 py-1.5 text-sm ${!sp.category ? "bg-ink text-paper" : "hover:bg-mist"}`}>All</Link></li>
            {cats?.filter((c) => c.count > 0).map((c) => (
              <li key={c.id}>
                <Link href={link({ category: c.id, page: undefined })} aria-current={sp.category === c.id ? "page" : undefined}
                      className={`flex justify-between gap-3 rounded-lg px-3 py-1.5 text-sm ${sp.category === c.id ? "bg-ink text-paper" : "hover:bg-mist"}`}>
                  {c.label}<span className="opacity-70">{c.count}</span>
                </Link>
              </li>
            ))}
          </ul>
        </nav>
        <section aria-label="Results">
          <p className="text-sm text-ink-soft" role="status">{data?.total ?? 0} products</p>
          {!data || data.items.length === 0 ? (
            <div className="mt-4"><Empty title="No products found" action={<Link className="btn btn-quiet" href="/scan">Scan a label</Link>}>
              Try a shorter search, check the spelling, or remove a filter. If the product is missing you can scan its label or type its ingredients on the compare page.
            </Empty></div>
          ) : (
            <ul className="mt-2">{data.items.map((p) => <ProductRow key={p.id} p={p} />)}</ul>
          )}
          {data && data.total > 30 && (
            <nav aria-label="Pages" className="mt-6 flex items-center gap-3">
              {page > 1 && <Link className="btn btn-quiet" href={link({ page: String(page - 1) })}>Previous</Link>}
              <span className="text-sm text-ink-soft">Page {page} of {Math.ceil(data.total / 30)}</span>
              {data.next_offset != null && <Link className="btn btn-quiet" href={link({ page: String(page + 1) })}>Next</Link>}
            </nav>
          )}
        </section>
      </div>
    </>
  );
}
