import Link from "next/link";
import { CATEGORY_LABEL, inr, pct } from "@/lib/format";
import { TEST_PRICE_SOURCE, type ProductSummary } from "@/lib/types";
import { DemoBadge } from "./ui";

export function PriceTag({ price }: { price: ProductSummary["price"] }) {
  if (price.state === "unavailable") return <span className="text-sm text-unknown">Price unavailable</span>;
  return (
    <span className="text-sm">
      {price.source === TEST_PRICE_SOURCE && <TestPriceBadge />}
      <span className="font-semibold">{inr(price.amount, price.currency)}</span>
      <span className="text-ink-soft"> {price.state === "stale" ? "(older observation)" : `seen ${price.observed_at}`}</span>
    </span>
  );
}

export function TestPriceBadge() {
  return <span className="mr-1 rounded border border-caution px-1 text-xs font-bold text-caution" title="Random value for testing. Not a real price.">TEST PRICE — not real</span>;
}

export function ProductRow({ p }: { p: ProductSummary }) {
  return (
    <li className="flex items-start justify-between gap-4 border-b border-line py-4 last:border-b-0">
      <div className="min-w-0">
        <Link href={`/products/${p.slug}`} className="font-bold hover:text-dropper hover:underline">{p.name}</Link>
        <p className="text-sm text-ink-soft">
          {p.brand ?? "Unknown brand"}, {CATEGORY_LABEL[p.category] ?? p.category}
        </p>
        <p className="mt-1 text-sm">
          {p.has_ingredients ? `${pct(p.completeness)} of ingredients recognised` : <span className="text-unknown">No ingredient list</span>}
        </p>
        {p.is_demo && <div className="mt-1"><DemoBadge /></div>}
      </div>
      <div className="shrink-0 text-right"><PriceTag price={p.price} /></div>
    </li>
  );
}
