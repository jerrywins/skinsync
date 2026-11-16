"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { RequireAuth } from "@/components/RequireAuth";
import { ErrorState, Notice, PageTitle } from "@/components/ui";
import { api } from "@/lib/api";
import { SKIN_TYPES } from "@/lib/format";
import type { Me } from "@/lib/types";

const list = (s: string) => s.split(",").map((x) => x.trim()).filter(Boolean);

function Profile({ me }: { me: Me }) {
  const qc = useQueryClient();
  const p = me.profile.preferences as { budget_max_inr?: number; preferred_brands?: string[]; avoided_brands?: string[];
                                        avoided_ingredients?: string[]; fragrance_free?: boolean };
  const [skin, setSkin] = useState(me.profile.skin_type ?? "unsure");
  const [budget, setBudget] = useState(p.budget_max_inr?.toString() ?? "");
  const [pref, setPref] = useState((p.preferred_brands ?? []).join(", "));
  const [avoidB, setAvoidB] = useState((p.avoided_brands ?? []).join(", "));
  const [avoidI, setAvoidI] = useState((p.avoided_ingredients ?? []).join(", "));
  const [ff, setFf] = useState(!!p.fragrance_free);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<unknown>(null);
  const save = async (e: React.FormEvent) => {
    e.preventDefault(); setErr(null);
    try {
      await api("/me/profile", { method: "PUT", body: { skin_type: skin, preferences: {
        budget_max_inr: budget ? Number(budget) : null, preferred_brands: list(pref), avoided_brands: list(avoidB),
        avoided_ingredients: list(avoidI), fragrance_free: ff } } });
      setMsg("Profile saved."); qc.invalidateQueries({ queryKey: ["me"] });
    } catch (e2) { setErr(e2); }
  };
  return (
    <form onSubmit={save} className="max-w-2xl space-y-6">
      <PageTitle title="Profile" lead="These preferences change how alternatives and suggestions are ranked and filtered. They never change a compatibility result." />
      <fieldset><legend className="font-semibold">Skin type</legend>
        <div className="mt-2 flex flex-wrap gap-2">{SKIN_TYPES.map((t) => (
          <label key={t.id} className={`cursor-pointer rounded-full border-2 px-4 py-2 text-sm ${skin === t.id ? "border-dropper bg-mist" : "border-line"}`}>
            <input type="radio" className="sr-only" checked={skin === t.id} onChange={() => setSkin(t.id)} />{t.label}</label>))}</div>
      </fieldset>
      <div><label htmlFor="bud" className="font-semibold">Budget per product (INR)</label>
        <input id="bud" type="number" min={0} className="field mt-1 max-w-48" value={budget} onChange={(e) => setBudget(e.target.value)} /></div>
      <div><label htmlFor="pb" className="font-semibold">Preferred brands</label>
        <input id="pb" className="field mt-1" value={pref} onChange={(e) => setPref(e.target.value)} placeholder="Separate with commas" /></div>
      <div><label htmlFor="ab" className="font-semibold">Brands to avoid</label>
        <input id="ab" className="field mt-1" value={avoidB} onChange={(e) => setAvoidB(e.target.value)} placeholder="Separate with commas" /></div>
      <div><label htmlFor="ai" className="font-semibold">Ingredients to avoid</label>
        <input id="ai" className="field label-voice mt-1" value={avoidI} onChange={(e) => setAvoidI(e.target.value)} placeholder="INCI names, separated with commas" />
        <p className="mt-1 text-sm text-ink-soft">Only names we recognise can be filtered. We&apos;ll tell you if one isn&apos;t recognised.</p></div>
      <label className="flex gap-3"><input type="checkbox" className="mt-0.5 size-5 accent-[var(--color-dropper)]" checked={ff} onChange={(e) => setFf(e.target.checked)} />Prefer fragrance-free</label>
      <Notice>Fragrance status isn&apos;t recorded for ingredients yet, so this preference is saved but can&apos;t filter results today.</Notice>
      {err != null && <ErrorState error={err} />}
      <button className="btn btn-primary">Save profile</button>
      {msg && <p role="status" className="text-sm text-ink-soft">{msg}</p>}
    </form>
  );
}

export default function ProfilePage() {
  return <RequireAuth>{(me) => <Profile me={me} />}</RequireAuth>;
}
