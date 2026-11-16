"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ProductPicker } from "@/components/ProductPicker";
import { useMe } from "@/components/providers";
import { ErrorState } from "@/components/ui";
import { api } from "@/lib/api";
import { track } from "@/lib/analytics";
import { MODE_LABEL } from "@/lib/format";
import { toSummary } from "@/lib/summary";
import type { AlternativesEnvelope, ProductDetail, ProductSummary } from "@/lib/types";

const MODES = ["similar", "cheaper", "premium", "ingredient_focused", "routine_compatible"] as const;
const MODE_HINT: Record<string, string> = {
  similar: "Closest ingredient profile in the same category.",
  cheaper: "Lower recent price, still meaningfully similar.",
  premium: "Higher recent price with a similar profile.",
  ingredient_focused: "Contains the key ingredients of your product.",
  routine_compatible: "Nothing that conflicts with your saved routines.",
};

export function AltForm({ initialRef, initialMode }: { initialRef?: string; initialMode?: string }) {
  const router = useRouter();
  const me = useMe();
  const [ref, setRef] = useState<ProductSummary | null>(null);
  const [mode, setMode] = useState<string>(MODES.includes(initialMode as never) ? initialMode! : "similar");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<unknown>(null);
  const pre = useQuery({ queryKey: ["prefill", initialRef], enabled: !!initialRef,
                         queryFn: () => api<ProductDetail>(`/products/${encodeURIComponent(initialRef!)}`).then(toSummary) });
  useEffect(() => { if (pre.data) setRef(pre.data); }, [pre.data]);
  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ref) return;
    setBusy(true); setErr(null);
    track("alternative_search_started", { mode });
    try {
      const r = await api<AlternativesEnvelope>("/alternatives/search", { body: { product_id: ref.id, mode } });
      track("alternative_search_completed", { results: r.results.length });
      router.push(`/alternatives/${r.id}`);
    } catch (e2) {
      setErr(e2);
    } finally {
      setBusy(false);
    }
  };
  return (
    <form onSubmit={submit} className="sheet max-w-3xl space-y-6 p-5 sm:p-7">
      <ProductPicker label="Your product" value={ref} onChange={setRef} />
      <fieldset>
        <legend className="text-sm font-semibold text-ink-soft">What kind of alternative?</legend>
        <div className="mt-2 grid gap-2 sm:grid-cols-2">
          {MODES.map((m) => {
            const disabled = m === "routine_compatible" && !me.data;
            return (
              <label key={m} className={`flex cursor-pointer gap-3 rounded-xl border-2 p-3 ${mode === m ? "border-dropper bg-mist" : "border-line"} ${disabled ? "opacity-50" : ""}`}>
                <input type="radio" name="mode" value={m} checked={mode === m} disabled={disabled}
                       onChange={() => setMode(m)} className="mt-1 accent-[var(--color-dropper)]" />
                <span>
                  <span className="block font-semibold">{MODE_LABEL[m]}</span>
                  <span className="block text-sm text-ink-soft">{disabled ? "Sign in and build a routine to use this." : MODE_HINT[m]}</span>
                </span>
              </label>
            );
          })}
        </div>
      </fieldset>
      <button className="btn btn-primary" disabled={!ref || busy}>{busy ? "Searching…" : "Find alternatives"}</button>
      {err != null && <ErrorState error={err} />}
    </form>
  );
}
