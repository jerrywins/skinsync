"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { PriceTag } from "@/components/ProductCard";
import { ProductPicker } from "@/components/ProductPicker";
import { RequireAuth } from "@/components/RequireAuth";
import { DemoBadge, Empty, ErrorState, Icon, Loading, PageTitle } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { CATEGORY_LABEL, pct } from "@/lib/format";
import type { ProductSummary } from "@/lib/types";

type Item = ProductSummary & { status: "owned" | "wishlist"; note: string | null; added_at: string; missing_data: boolean };

function Shelf() {
  const qc = useQueryClient();
  const [filter, setFilter] = useState("");
  const [pick, setPick] = useState<string[]>([]);
  const [msg, setMsg] = useState<string | null>(null);
  const q = useQuery({ queryKey: ["shelf"], queryFn: () => api<{ items: Item[] }>("/shelf") });
  const add = async (p: ProductSummary | null) => {
    if (!p) return;
    try { await api("/shelf", { body: { product_id: p.id } }); setMsg(`Added ${p.name}.`); qc.invalidateQueries({ queryKey: ["shelf"] }); }
    catch (e) { setMsg(e instanceof ApiError ? e.message : "Could not add it."); }
  };
  const remove = async (id: string, name: string) => {
    await api(`/shelf/${id}`, { method: "DELETE" }); setMsg(`Removed ${name}.`); setPick((p) => p.filter((x) => x !== id));
    qc.invalidateQueries({ queryKey: ["shelf"] });
  };
  const items = (q.data?.items ?? []).filter((i) => `${i.name} ${i.brand}`.toLowerCase().includes(filter.toLowerCase()));
  return (
    <>
      <PageTitle title="My Shelf" lead="The products you own or want. Pick any two to compare, or build a routine from them." />
      <div className="grid gap-6 md:grid-cols-[1fr_1fr]">
        <ProductPicker label="Add a product" value={null} onChange={add} />
        <div><label htmlFor="sf" className="text-sm font-semibold text-ink-soft">Search your shelf</label>
          <input id="sf" className="field mt-1" value={filter} onChange={(e) => setFilter(e.target.value)} /></div>
      </div>
      {msg && <p role="status" className="mt-3 text-sm text-ink-soft">{msg}</p>}
      {pick.length === 2 && (
        <div className="mt-4 flex flex-wrap items-center gap-3 rounded-xl bg-mist p-3">
          <span>Two products selected.</span>
          <Link className="btn btn-primary min-h-10" href={`/compare?a=${pick[0]}&b=${pick[1]}`}><Icon name="layers" className="size-4" />Compare them</Link>
        </div>
      )}
      <div className="mt-6">
        {q.isLoading ? <Loading /> : q.error ? <ErrorState error={q.error} retry={() => q.refetch()} /> : items.length === 0 ? (
          <Empty title={filter ? "Nothing on your shelf matches" : "Your shelf is empty"}
                 action={<Link className="btn btn-quiet" href="/scan"><Icon name="scan" className="size-4" />Scan a product</Link>}>
            Add products with the search box above or by scanning them.
          </Empty>
        ) : (
          <ul className="divide-y divide-line rounded-2xl border border-line bg-sheet">
            {items.map((i) => (
              <li key={i.id} className="flex flex-wrap items-start gap-4 p-4">
                <input type="checkbox" className="mt-1.5 size-5 accent-[var(--color-dropper)]" aria-label={`Select ${i.name} to compare`}
                       checked={pick.includes(i.id)} disabled={!pick.includes(i.id) && pick.length >= 2}
                       onChange={(e) => setPick((p) => e.target.checked ? [...p, i.id] : p.filter((x) => x !== i.id))} />
                <div className="min-w-0 flex-1">
                  <Link href={`/products/${i.slug}`} className="font-bold hover:underline">{i.name}</Link>
                  <p className="text-sm text-ink-soft">{i.brand}, {CATEGORY_LABEL[i.category] ?? i.category}{i.status === "wishlist" ? ", wishlist" : ""}</p>
                  <p className="text-sm">{i.missing_data ? <span className="text-unknown">No ingredient list: can&apos;t be checked</span> : `${pct(i.completeness)} of ingredients recognised`}</p>
                  {i.is_demo && <DemoBadge />}
                </div>
                <PriceTag price={i.price} />
                <div className="flex gap-2">
                  <Link className="btn btn-quiet min-h-9 text-sm" href={`/alternatives?ref=${i.id}`}>Alternatives</Link>
                  <button className="btn btn-quiet min-h-9 text-sm" onClick={() => remove(i.id, i.name)} aria-label={`Remove ${i.name}`}><Icon name="trash" className="size-4" /></button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  );
}

export default function ShelfPage() {
  return <RequireAuth>{() => <Shelf />}</RequireAuth>;
}
