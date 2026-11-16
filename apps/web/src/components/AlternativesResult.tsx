"use client";

import Link from "next/link";
import { EXCLUDE_LABEL, inr, MODE_LABEL, pct } from "@/lib/format";
import { TEST_PRICE_SOURCE, type AlternativesEnvelope } from "@/lib/types";
import { track } from "@/lib/analytics";
import { ExplainPanel } from "./ExplainPanel";
import { TestPriceBadge } from "./ProductCard";
import { SaveShareBar } from "./SaveShareBar";
import { DemoBadge, Empty, Icon, Notice } from "./ui";

const DIM_LABEL: Record<string, string> = {
  ingredient_similarity: "Ingredient similarity", target_match: "Target ingredients", category_match: "Category",
  preference_match: "Your preferences", formulation_similarity: "Formulation",
};

export function AlternativesResult({ data, readOnly = false }: { data: AlternativesEnvelope; readOnly?: boolean }) {
  const excluded = Object.entries(data.excluded).filter(([, n]) => n > 0);
  return (
    <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_20rem]">
      <div className="min-w-0 space-y-6">
        <header>
          <p className="text-sm font-semibold text-ink-soft">{MODE_LABEL[data.mode] ?? data.mode} alternatives to</p>
          <h1 className="text-3xl font-extrabold sm:text-4xl">
            <Link href={`/products/${data.reference.slug}`} className="hover:underline">{data.reference.name}</Link>
          </h1>
          {data.reference.brand && <p className="text-ink-soft">{data.reference.brand}</p>}
          {data.reference.is_demo && <div className="mt-2"><DemoBadge /></div>}
        </header>
        {data.low_identification_confidence && (
          <Notice tone="caution">We are not certain this is the right product. Check the name before relying on these alternatives.</Notice>
        )}
        {data.notes.map((n) => <Notice key={n}>{n}</Notice>)}
        {!readOnly && <SaveShareBar kind="alternative_search" id={data.id} saved={data.saved} />}
        {data.results.length === 0 ? (
          <Empty title="No alternatives found"
                 action={<Link className="btn btn-quiet" href={`/alternatives?ref=${data.reference.id}&mode=similar`}>Try similar formulas</Link>}>
            {data.mode === "cheaper"
              ? "We only call something cheaper when both prices are recent observations in the same currency. Many products have no current price."
              : "Try another mode, or remove some preferences."}
          </Empty>
        ) : (
          <ol className="space-y-4" aria-label="Ranked alternatives">
            {data.results.map((a) => (
              <li key={a.product_id} className="rounded-2xl border border-line bg-sheet p-5">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div className="min-w-0">
                    <p className="text-sm text-ink-soft">Rank {a.rank}</p>
                    <Link href={`/products/${a.slug}`} className="text-lg font-bold hover:underline">{a.name}</Link>
                    <p className="text-sm text-ink-soft">{a.brand}</p>
                  </div>
                  <div className="text-right">
                    {a.price ? (
                      <>
                        {a.price.source === TEST_PRICE_SOURCE && <TestPriceBadge />}
                        <p className="font-bold">{inr(a.price.amount, a.price.currency)}</p>
                        <p className="text-xs text-ink-soft">
                          {a.price_state === "stale" ? "Older observation, " : "Observed "}{a.price.observed_at} at {a.price.seller}
                        </p>
                      </>
                    ) : <p className="text-sm text-unknown">Price unavailable</p>}
                  </div>
                </div>
                <div className="mt-3">
                  <p className="text-sm font-semibold">Why this alternative</p>
                  <ul className="mt-1 space-y-0.5 text-sm">
                    {a.reasons.map((r) => <li key={r} className="flex gap-2"><Icon name="check" className="mt-0.5 size-4 shrink-0 text-clear" />{r}</li>)}
                    {a.differences.map((d) => <li key={d} className="flex gap-2 text-ink-soft"><Icon name="gap" className="mt-0.5 size-4 shrink-0" />{d}</li>)}
                  </ul>
                </div>
                <details className="mt-3 text-sm">
                  <summary className="cursor-pointer font-semibold text-dropper">How it was ranked</summary>
                  <dl className="mt-2 grid gap-2 sm:grid-cols-2">
                    {a.dimensions.map((d) => (
                      <div key={d.name}>
                        <dt className="flex justify-between"><span>{DIM_LABEL[d.name] ?? d.name}</span><span className="font-semibold">{d.score == null ? "not used" : pct(d.score)}</span></dt>
                        <dd className="text-xs text-ink-soft">{d.detail}</dd>
                      </div>
                    ))}
                  </dl>
                  {a.missing_data.length > 0 && <p className="mt-2 text-xs text-ink-soft">Missing: {a.missing_data.join("; ")}.</p>}
                </details>
                {!readOnly && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    <Link className="btn btn-quiet min-h-10 text-sm" href={`/compare?a=${data.reference.id}&b=${a.product_id}`}
                          onClick={() => track("alternative_compared")}><Icon name="layers" className="size-4" />Compare with mine</Link>
                    <Link className="btn btn-quiet min-h-10 text-sm" href={`/products/${a.slug}`} onClick={() => track("alternative_clicked")}>View product</Link>
                  </div>
                )}
              </li>
            ))}
          </ol>
        )}
      </div>
      <ExplainPanel
        used={[
          { label: "Candidates considered", value: data.candidates_considered },
          { label: "Ranking weights", value: Object.keys(DIM_LABEL).filter((k) => k in data.weights).map((k) => `${DIM_LABEL[k]} ${Math.round(data.weights[k] * 100)}%`).join(", ") },
          { label: "Reference price", value: data.reference_price_state === "fresh" ? "recent observation" : data.reference_price_state },
        ]}
        missing={[
          ...excluded.map(([k, n]) => `Left out: ${EXCLUDE_LABEL[k] ?? k.replaceAll("_", " ")} (${n})`),
          ...(data.reference_price_state !== "fresh" ? ["No current price for your product, so cheaper or premium cannot be judged"] : []),
        ]}
        footnote="The weights are product-design choices, not science. Dimensions we can't compute are left out rather than counted as a match."
      />
    </div>
  );
}
