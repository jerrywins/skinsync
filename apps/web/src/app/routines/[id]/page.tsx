"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { use, useEffect, useState } from "react";
import { ExplainPanel } from "@/components/ExplainPanel";
import { ProductPicker } from "@/components/ProductPicker";
import { RequireAuth } from "@/components/RequireAuth";
import { DemoBadge, Empty, ErrorState, Icon, Loading, Notice, StatusPill } from "@/components/ui";
import { api, ApiError, type ComparisonResult } from "@/lib/api";
import { track } from "@/lib/analytics";
import type { StatusKey } from "@/lib/format";
import type { ProductSummary } from "@/lib/types";

const KINDS = ["cleanser", "toner", "treatment", "serum", "eye_care", "moisturizer", "sunscreen", "mask", "other"] as const;
type Step = { product: ProductSummary; step_kind: string | null; frequency: string | null; note: string | null };
type Routine = { id: string; name: string; time_of_day: "morning" | "evening"; steps: (Step & { order: number })[] };
type Analysis = {
  status: StatusKey; status_label: string; knowledge_version: string; knowledge_is_demo: boolean;
  pairs: { a: string; b: string; a_order: number; b_order: number; result: ComparisonResult }[];
  duplicated_key_actives: string[]; shared_ingredients: { ingredient: string; products: string[] }[];
  missing_data: string[]; sequencing: string;
};

function Builder({ id }: { id: string }) {
  const qc = useQueryClient();
  const router = useRouter();
  const q = useQuery({ queryKey: ["routine", id], queryFn: () => api<Routine>(`/routines/${id}`) });
  const [steps, setSteps] = useState<Step[]>([]);
  const [name, setName] = useState("");
  const [time, setTime] = useState<"morning" | "evening">("morning");
  const [dirty, setDirty] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [err, setErr] = useState<unknown>(null);
  useEffect(() => { if (q.data) { setSteps(q.data.steps); setName(q.data.name); setTime(q.data.time_of_day); } }, [q.data]);
  const change = (s: Step[]) => { setSteps(s); setDirty(true); setAnalysis(null); };
  const move = (i: number, d: -1 | 1) => {
    const n = [...steps]; [n[i], n[i + d]] = [n[i + d], n[i]]; change(n);
    setMsg(`${n[i + d].product.name} moved to step ${i + d + 1}.`);
  };
  const save = async () => {
    try {
      const r = await api<Routine & { warnings: string[] }>(`/routines/${id}`, { method: "PUT", body: {
        name, time_of_day: time, steps: steps.map((s) => ({ product_id: s.product.id, step_kind: s.step_kind, frequency: s.frequency || null, note: s.note || null })) } });
      setDirty(false); setMsg(r.warnings.length ? `Saved. ${r.warnings.join(" ")}` : "Routine saved.");
      qc.invalidateQueries({ queryKey: ["routines"] });
    } catch (e) { setErr(e); }
  };
  const analyze = async () => {
    setErr(null);
    try { if (dirty) await save(); setAnalysis(await api<Analysis>(`/routines/${id}/analyze`, { method: "POST" })); track("routine_analyzed"); }
    catch (e) { setErr(e); }
  };
  const remove = async () => { await api(`/routines/${id}`, { method: "DELETE" }); qc.invalidateQueries({ queryKey: ["routines"] }); router.push("/routines"); };
  if (q.isLoading) return <Loading />;
  if (q.error instanceof ApiError && q.error.status === 404) return <Empty title="Routine not found" action={<Link className="btn btn-primary" href="/routines">Your routines</Link>} />;
  if (q.error) return <ErrorState error={q.error} />;
  return (
    <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_20rem]">
      <div className="min-w-0 space-y-6">
        <div className="flex flex-wrap items-end gap-4">
          <div className="min-w-60 flex-1"><label htmlFor="rn" className="text-sm font-semibold text-ink-soft">Routine name</label>
            <input id="rn" className="field mt-1 text-xl font-bold" value={name} maxLength={120} onChange={(e) => { setName(e.target.value); setDirty(true); }} /></div>
          <fieldset className="flex gap-2"><legend className="sr-only">Time of day</legend>
            {(["morning", "evening"] as const).map((t) => (
              <label key={t} className={`cursor-pointer rounded-full border-2 px-4 py-2 text-sm font-medium ${time === t ? "border-dropper bg-mist" : "border-line"}`}>
                <input type="radio" className="sr-only" checked={time === t} onChange={() => { setTime(t); setDirty(true); }} />{t === "morning" ? "Morning" : "Evening"}
              </label>))}
          </fieldset>
        </div>
        <section aria-labelledby="steps-h">
          <h2 id="steps-h" className="text-xl font-bold">Steps</h2>
          {steps.length === 0 && <p className="mt-2 text-ink-soft">Add products below. A typical order is cleanser, treatment, serum, moisturizer{time === "morning" ? ", sunscreen" : ""}.</p>}
          <ol className="mt-3 space-y-2">
            {steps.map((s, i) => (
              <li key={`${s.product.id}-${i}`} className="flex flex-wrap items-center gap-3 rounded-xl border border-line bg-sheet p-3">
                <span className="grid size-8 shrink-0 place-items-center rounded-full bg-ink text-sm font-bold text-paper" aria-hidden="true">{i + 1}</span>
                <div className="min-w-0 flex-1"><p className="font-semibold">{s.product.name}</p>
                  {!s.product.has_ingredients && <p className="text-xs text-unknown">No ingredient list: this step can&apos;t be checked</p>}
                  {s.product.is_demo && <DemoBadge />}</div>
                <label className="sr-only" htmlFor={`k-${i}`}>Step type for {s.product.name}</label>
                <select id={`k-${i}`} className="field w-auto min-h-9 py-1 text-sm" value={s.step_kind ?? ""}
                        onChange={(e) => change(steps.map((x, j) => j === i ? { ...x, step_kind: e.target.value || null } : x))}>
                  <option value="">Step type</option>{KINDS.map((k) => <option key={k} value={k}>{k.replace("_", " ")}</option>)}
                </select>
                <div className="flex gap-1">
                  <button className="btn btn-quiet min-h-9 px-2" disabled={i === 0} onClick={() => move(i, -1)} aria-label={`Move ${s.product.name} up`}><Icon name="up" className="size-4" /></button>
                  <button className="btn btn-quiet min-h-9 px-2" disabled={i === steps.length - 1} onClick={() => move(i, 1)} aria-label={`Move ${s.product.name} down`}><Icon name="down" className="size-4" /></button>
                  <button className="btn btn-quiet min-h-9 px-2" onClick={() => change(steps.filter((_, j) => j !== i))} aria-label={`Remove ${s.product.name}`}><Icon name="trash" className="size-4" /></button>
                </div>
              </li>
            ))}
          </ol>
          <div className="mt-4 max-w-md"><ProductPicker label="Add a step" value={null}
              onChange={(p) => p && change([...steps, { product: p, step_kind: null, frequency: null, note: null }])} /></div>
        </section>
        <p role="status" aria-live="polite" className="text-sm text-ink-soft">{msg}</p>
        <div className="flex flex-wrap gap-2">
          <button className="btn btn-primary" onClick={analyze} disabled={steps.length < 2}><Icon name="layers" className="size-4" />Check this routine</button>
          <button className="btn btn-quiet" onClick={save} disabled={!dirty}>{dirty ? "Save changes" : "Saved"}</button>
          <button className="btn btn-quiet" onClick={remove}>Delete routine</button>
        </div>
        {err != null && <ErrorState error={err} />}
        {analysis && (
          <section aria-labelledby="an-h" className="space-y-4">
            {analysis.knowledge_is_demo && <Notice tone="demo"><DemoBadge /> Checked with the fictional demo knowledge base.</Notice>}
            <StatusPill status={analysis.status} />
            <h2 id="an-h" className="text-2xl font-extrabold">{analysis.status_label}</h2>
            <ul className="space-y-2">
              {analysis.pairs.map((p) => (
                <li key={`${p.a_order}-${p.b_order}`} className="rounded-xl border border-line bg-sheet p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p><span className="font-semibold">Step {p.a_order}</span> {p.a} with <span className="font-semibold">step {p.b_order}</span> {p.b}</p>
                    <StatusPill status={p.result.status as StatusKey} />
                  </div>
                  {p.result.findings.filter((f) => f.type === "rule").map((f) => <p key={f.rule_code} className="mt-1 text-sm">{f.explanation} <span className="text-ink-soft">{f.practical_guidance}</span></p>)}
                </li>
              ))}
            </ul>
            {analysis.duplicated_key_actives.length > 0 && <div><h3 className="font-bold">Same key active more than once</h3><ul className="list-disc pl-5 text-sm">{analysis.duplicated_key_actives.map((d) => <li key={d}>{d}</li>)}</ul></div>}
            {analysis.shared_ingredients.length > 0 && <details className="text-sm"><summary className="cursor-pointer font-semibold">Ingredients in more than one step ({analysis.shared_ingredients.length})</summary>
              <ul className="mt-2 space-y-1">{analysis.shared_ingredients.map((s) => <li key={s.ingredient}><span className="label-voice">{s.ingredient}</span>: {s.products.join(", ")}</li>)}</ul></details>}
            <p className="text-sm text-ink-soft">{analysis.sequencing}</p>
          </section>
        )}
      </div>
      <ExplainPanel used={[{ label: "Steps", value: steps.length }, { label: "Knowledge version", value: analysis?.knowledge_version ?? "run a check" }]}
                    missing={analysis ? analysis.missing_data : ["Run a check to see what's missing."]}
                    footnote="Every pair of steps is checked. Missing data is never treated as safe." />
    </div>
  );
}

export default function RoutinePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <RequireAuth>{() => <Builder id={id} />}</RequireAuth>;
}
