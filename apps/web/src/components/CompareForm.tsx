"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { track } from "@/lib/analytics";
import { toSummary } from "@/lib/summary";
import type { ComparisonEnvelope, ProductDetail, ProductSummary } from "@/lib/types";
import { CompareResult } from "./CompareResult";
import { ProductPicker } from "./ProductPicker";
import { rememberClaim } from "./providers";
import { ErrorState, Icon } from "./ui";

type Side = { mode: "product"; product: ProductSummary | null } | { mode: "manual"; text: string };

function SideInput({ label, side, setSide }: { label: string; side: Side; setSide: (s: Side) => void }) {
  return (
    <div className="space-y-2">
      {side.mode === "product" ? (
        <ProductPicker label={label} value={side.product} onChange={(p) => setSide({ mode: "product", product: p })} />
      ) : (
        <div>
          <label className="text-sm font-semibold text-ink-soft" htmlFor={`${label}-manual`}>{label}: ingredient list</label>
          <textarea id={`${label}-manual`} className="field label-voice mt-1 min-h-28" value={side.text}
                    placeholder="Paste the ingredient list from the label, separated by commas"
                    onChange={(e) => setSide({ mode: "manual", text: e.target.value })} />
        </div>
      )}
      <button type="button" className="text-sm font-semibold text-dropper underline underline-offset-4"
              onClick={() => setSide(side.mode === "product" ? { mode: "manual", text: "" } : { mode: "product", product: null })}>
        {side.mode === "product" ? "Type the ingredients instead" : "Search for a product instead"}
      </button>
    </div>
  );
}

const spec = (s: Side) => s.mode === "product" ? (s.product ? { product_id: s.product.id } : null)
  : (s.text.trim() ? { manual_ingredients: s.text, label: "Your ingredient list" } : null);

export function CompareForm({ initialA, initialB, compact = false }: { initialA?: string; initialB?: string; compact?: boolean }) {
  const router = useRouter();
  const [a, setA] = useState<Side>({ mode: "product", product: null });
  const [b, setB] = useState<Side>({ mode: "product", product: null });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [manualResult, setManualResult] = useState<ComparisonEnvelope | null>(null);

  const pre = useQuery({
    queryKey: ["prefill", initialA, initialB],
    enabled: !!(initialA || initialB),
    queryFn: () => Promise.all([initialA, initialB].map((id) =>
      id ? api<ProductDetail>(`/products/${encodeURIComponent(id)}`).then(toSummary).catch(() => null) : null)),
  });
  useEffect(() => {
    if (!pre.data) return;
    const [pa, pb] = pre.data;
    if (pa) setA({ mode: "product", product: pa });
    if (pb) setB({ mode: "product", product: pb });
  }, [pre.data]);

  useEffect(() => {
    try {
      const t = sessionStorage.getItem("ss_manual_a");
      if (t) { setA({ mode: "manual", text: t }); sessionStorage.removeItem("ss_manual_a"); }
    } catch { /* unavailable */ }
  }, []);

  const ready = spec(a) && spec(b);
  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ready) return;
    setBusy(true); setError(null); setManualResult(null);
    track("comparison_started");
    try {
      const r = await api<ComparisonEnvelope>("/comparisons", { body: { a: spec(a), b: spec(b) } });
      track("comparison_completed", { status: r.result.status });
      rememberClaim(r.claim_token);
      if (r.id) router.push(`/compare/${r.id}`);
      else setManualResult(r);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="space-y-10">
      <form onSubmit={submit} aria-label="Compare two products"
            className={compact ? "space-y-4" : "sheet space-y-5 p-5 sm:p-7"}>
        <div className="grid items-start gap-5 md:grid-cols-[1fr_auto_1fr]">
          <SideInput label="First product" side={a} setSide={setA} />
          <span aria-hidden="true" className="mt-9 hidden size-9 place-items-center rounded-full bg-mist text-ink-soft md:grid">
            <Icon name="plus" className="size-4" />
          </span>
          <SideInput label="Second product" side={b} setSide={setB} />
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <button className="btn btn-primary" disabled={!ready || busy} aria-describedby="compare-hint">
            <Icon name="layers" className="size-4" />{busy ? "Checking…" : "Check this pair"}
          </button>
          <p id="compare-hint" className="text-sm text-ink-soft">
            {ready ? "We check the current formulations against our reviewed knowledge base." : "Choose both products to continue."}
          </p>
        </div>
        {error != null && (
          <ErrorState error={error instanceof ApiError && error.code === "DEMO_MIX"
            ? { message: "Demo products can only be compared with other demo products." } : error} />
        )}
      </form>
      {manualResult && <CompareResult data={manualResult} />}
    </div>
  );
}
