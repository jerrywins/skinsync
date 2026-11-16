"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useEffect, useId, useState } from "react";
import { api } from "@/lib/api";
import { CATEGORY_LABEL, pct } from "@/lib/format";
import type { Page, ProductSummary } from "@/lib/types";
import { track } from "@/lib/analytics";
import { DemoBadge, Icon } from "./ui";

/** Accessible combobox for finding a product (search by name, brand or ingredient; typo tolerant).
 *  Ambiguity is never resolved silently: the person always picks. */
export function ProductPicker({ label, value, onChange, placeholder = "Product or brand" }: {
  label: string; value: ProductSummary | null; onChange: (p: ProductSummary | null) => void; placeholder?: string;
}) {
  const id = useId();
  const [q, setQ] = useState("");
  const [debounced, setDebounced] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  useEffect(() => { const t = setTimeout(() => setDebounced(q.trim()), 220); return () => clearTimeout(t); }, [q]);
  const search = useQuery({
    queryKey: ["products", debounced],
    queryFn: () => api<Page<ProductSummary>>(`/products?q=${encodeURIComponent(debounced)}&limit=8`),
    enabled: debounced.length >= 2,
  });
  useEffect(() => { if (debounced.length >= 2) track("product_search"); }, [debounced]);
  const items = search.data?.items ?? [];

  if (value) {
    return (
      <div>
        <p className="text-sm font-semibold text-ink-soft">{label}</p>
        <div className="mt-1 flex items-start justify-between gap-3 rounded-xl border-2 border-dropper bg-sheet px-4 py-3">
          <div>
            <p className="font-bold">{value.name}</p>
            <p className="text-sm text-ink-soft">
              {value.brand ?? "Unknown brand"}, {CATEGORY_LABEL[value.category] ?? value.category}
              {value.has_ingredients ? `, ${pct(value.completeness)} of ingredients recognised` : ", no ingredient list"}
            </p>
            {value.is_demo && <div className="mt-1"><DemoBadge /></div>}
          </div>
          <button type="button" className="btn btn-quiet min-h-9 px-3 text-sm" onClick={() => { onChange(null); setQ(""); }}
                  aria-label={`Change ${label}`}>Change</button>
        </div>
      </div>
    );
  }
  const select = (p: ProductSummary) => { onChange(p); setOpen(false); track("product_selected"); };
  return (
    <div className="relative">
      <label htmlFor={id} className="text-sm font-semibold text-ink-soft">{label}</label>
      <div className="relative mt-1">
        <Icon name="search" className="pointer-events-none absolute left-3 top-1/2 size-5 -translate-y-1/2 text-ink-soft" />
        <input id={id} className="field pl-10" role="combobox" aria-expanded={open && items.length > 0}
               aria-controls={`${id}-list`} aria-autocomplete="list" autoComplete="off" placeholder={placeholder}
               value={q}
               aria-activedescendant={open && items[active] ? `${id}-opt-${active}` : undefined}
               onChange={(e) => { setQ(e.target.value); setOpen(true); setActive(0); }}
               onFocus={() => setOpen(true)} onBlur={() => setTimeout(() => setOpen(false), 150)}
               onKeyDown={(e) => {
                 if (e.key === "ArrowDown") { e.preventDefault(); setActive((a) => Math.min(a + 1, items.length - 1)); }
                 if (e.key === "ArrowUp") { e.preventDefault(); setActive((a) => Math.max(a - 1, 0)); }
                 if (e.key === "Enter" && items[active]) { e.preventDefault(); select(items[active]); }
                 if (e.key === "Escape") setOpen(false);
               }} />
      </div>
      {open && debounced.length >= 2 && (
        <div className="absolute z-20 mt-1 w-full overflow-hidden rounded-xl border border-line bg-sheet shadow-[0_12px_32px_-12px_rgba(30,42,48,0.35)]">
          {search.isLoading && <p className="px-4 py-3 text-sm text-ink-soft" role="status">Searching…</p>}
          {search.isError && <p className="px-4 py-3 text-sm text-strong" role="alert">Search failed. Try again.</p>}
          {search.isSuccess && items.length === 0 && (
            <div className="px-4 py-3 text-sm">
              <p>No products match &ldquo;{debounced}&rdquo;.</p>
              <p className="mt-1 text-ink-soft">Try fewer words, <Link className="font-semibold text-dropper" href="/scan">scan the label</Link>, or type the ingredients instead.</p>
            </div>
          )}
          <ul id={`${id}-list`} role="listbox" aria-label={`${label} results`}>
            {items.map((p, i) => (
              <li key={p.id} id={`${id}-opt-${i}`} role="option" aria-selected={i === active}
                  className={`cursor-pointer px-4 py-2.5 ${i === active ? "bg-mist" : ""}`}
                  onMouseDown={(e) => { e.preventDefault(); select(p); }} onMouseEnter={() => setActive(i)}>
                <span className="block font-semibold">{p.name}</span>
                <span className="block text-sm text-ink-soft">
                  {p.brand ?? "Unknown brand"}, {CATEGORY_LABEL[p.category] ?? p.category}
                  {!p.has_ingredients && ", no ingredient list"}{p.is_demo && ", DEMO"}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
