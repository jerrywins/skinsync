"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { RequireAuth } from "@/components/RequireAuth";
import { DemoBadge, Empty, ErrorState, Loading, Notice, PageTitle } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { date, pct } from "@/lib/format";
import type { Page } from "@/lib/types";

type Flag = { id: number; target_type: string; target_ref: string; target_label?: string | null; target_slug?: string | null;
              reason: string; source: string; details: Record<string, unknown>; status: string; created_at: string };
type KV = { id: string; status: string; is_demo: boolean; notes: string | null; rules: number; evidence: number; mappings: number;
            created_at: string; published_at: string | null; blockers: string[] };
type DQ = { products: number; with_ingredient_list: number; fully_resolved: number; avg_completeness: number; ingredients_total: number;
            ingredients_reviewed: number; ingredients_with_function_class: number; price_observations: number;
            open_flags: Record<string, number>; published_knowledge: string | null; failed_jobs_24h: number };
type Audit = { id: number; actor_id: string | null; action: string; target: string | null; reason: string | null; occurred_at: string };
type Job = { id: string; type: string; status: string; error_code: string | null; retry_count: number; created_at: string };

const TABS = { quality: "Data quality", flags: "Review queue", knowledge: "Knowledge versions", audit: "Audit log", jobs: "Failed jobs" };

function Quality() {
  const q = useQuery({ queryKey: ["admin", "dq"], queryFn: () => api<DQ>("/admin/data-quality") });
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorState error={q.error} />;
  const d = q.data!;
  const rows: [string, string][] = [
    ["Products (real)", String(d.products)], ["With an ingredient list", `${d.with_ingredient_list} (${pct(d.with_ingredient_list / Math.max(d.products, 1))})`],
    ["Fully recognised formulations", String(d.fully_resolved)], ["Average recognition", pct(d.avg_completeness)],
    ["Ingredients", String(d.ingredients_total)], ["Reviewed ingredient names", String(d.ingredients_reviewed)],
    ["Ingredients with recorded functions", String(d.ingredients_with_function_class)], ["Price observations", String(d.price_observations)],
    ["Published knowledge version", d.published_knowledge ?? "none"], ["Failed jobs (24 h)", String(d.failed_jobs_24h)],
  ];
  return (
    <div className="grid gap-8 md:grid-cols-2">
      <dl className="divide-y divide-line rounded-2xl border border-line bg-sheet">
        {rows.map(([k, v]) => <div key={k} className="flex justify-between gap-4 px-4 py-2.5"><dt className="text-ink-soft">{k}</dt><dd className="font-semibold">{v}</dd></div>)}
      </dl>
      <div><h3 className="font-bold">Open review items</h3>
        <ul className="mt-2 space-y-1">{Object.entries(d.open_flags).map(([k, n]) => <li key={k} className="flex justify-between border-b border-line py-1"><span>{k.replaceAll("_", " ")}</span><span className="font-semibold">{n}</span></li>)}</ul></div>
    </div>
  );
}

function Flags() {
  const qc = useQueryClient();
  const [reason, setReason] = useState("");
  const q = useQuery({ queryKey: ["admin", "flags", reason], queryFn: () => api<Page<Flag>>(`/admin/flags?limit=50${reason ? `&reason=${reason}` : ""}`) });
  const act = async (f: Flag, status: "resolved" | "dismissed") => {
    const note = window.prompt(`Note for ${status === "resolved" ? "resolving" : "dismissing"} this item (required):`);
    if (!note || note.trim().length < 3) return;
    await api(`/admin/flags/${f.id}`, { method: "PATCH", body: { status, note } });
    qc.invalidateQueries({ queryKey: ["admin"] });
  };
  return (
    <div className="space-y-4">
      <label className="flex items-center gap-2 text-sm">Reason
        <select className="field w-auto min-h-9 py-1" value={reason} onChange={(e) => setReason(e.target.value)}>
          <option value="">All</option>{["unknown_ingredient", "missing_ingredient_list", "fuzzy_match", "low_ocr_confidence", "user_report", "conflicting_evidence"].map((r) => <option key={r} value={r}>{r.replaceAll("_", " ")}</option>)}
        </select></label>
      {q.isLoading ? <Loading /> : q.error ? <ErrorState error={q.error} /> : !q.data?.items.length ? <Empty title="Queue clear" /> : (
        <>
          <p className="text-sm text-ink-soft">{q.data.total} open items, newest first.</p>
          <ul className="space-y-2">
            {q.data.items.map((f) => (
              <li key={f.id} className="rounded-xl border border-line bg-sheet p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="font-semibold">{f.reason.replaceAll("_", " ")} <span className="font-normal text-ink-soft">from {f.source}, {date(f.created_at)}</span></p>
                    <p className="text-sm">{f.target_slug ? <Link className="text-dropper hover:underline" href={`/products/${f.target_slug}`}>{f.target_label}</Link> : `${f.target_type} ${f.target_ref}`}</p>
                    {Object.keys(f.details).length > 0 && <p className="label-voice mt-1 break-words text-sm text-ink-soft">{JSON.stringify(f.details)}</p>}
                  </div>
                  <div className="flex gap-2"><button className="btn btn-quiet min-h-9 text-sm" onClick={() => act(f, "resolved")}>Resolve</button>
                    <button className="btn btn-quiet min-h-9 text-sm" onClick={() => act(f, "dismissed")}>Dismiss</button></div>
                </div>
              </li>
            ))}
          </ul>
        </>
      )}
      <Notice>To correct an ingredient match, use <code>POST /api/v1/admin/ingredient-mappings</code> (see docs/ADMIN_GUIDE.md). It creates a new formulation version, so earlier results stay reproducible and are marked out of date.</Notice>
    </div>
  );
}

function Knowledge() {
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["admin", "kv"], queryFn: () => api<{ items: KV[] }>("/admin/knowledge-versions") });
  const [vid, setVid] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const run = async (fn: () => Promise<unknown>, ok: string) => {
    setMsg(null);
    try { await fn(); setMsg(ok); qc.invalidateQueries({ queryKey: ["admin"] }); }
    catch (e) { setMsg(e instanceof ApiError ? `${e.message}${Array.isArray(e.details.reasons) ? ` ${(e.details.reasons as string[]).join(" ")}` : ""}` : "Failed."); }
  };
  const move = (k: KV, to: string) => {
    const reason = window.prompt(`Reason for moving ${k.id} to ${to.replace("_", " ")} (required):`);
    if (reason && reason.trim().length >= 3) run(() => api(`/admin/knowledge-versions/${k.id}/transition`, { body: { to, reason } }), `${k.id} moved to ${to.replace("_", " ")}.`);
  };
  return (
    <div className="space-y-6">
      <form className="flex flex-wrap items-end gap-2" onSubmit={(e) => { e.preventDefault(); run(() => api("/admin/knowledge-versions", { body: { version_id: vid } }), `Draft ${vid} imported from knowledge/.`); }}>
        <div><label htmlFor="vid" className="text-sm font-semibold">New version id</label>
          <input id="vid" className="field mt-1" placeholder="kv-2026-11" pattern="[a-z0-9][a-z0-9.\-]+" required value={vid} onChange={(e) => setVid(e.target.value)} /></div>
        <button className="btn btn-primary">Import reviewed files as a draft</button>
      </form>
      {msg && <p role="status" className="text-sm">{msg}</p>}
      {q.isLoading ? <Loading /> : q.error ? <ErrorState error={q.error} /> : (
        <ul className="space-y-3">
          {q.data!.items.map((k) => (
            <li key={k.id} className="rounded-xl border border-line bg-sheet p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div><p className="font-bold">{k.id} {k.is_demo && <DemoBadge />}</p>
                  <p className="text-sm text-ink-soft">{k.status.replace("_", " ")}, {k.rules} rules, {k.evidence} evidence records, {k.mappings} concern mappings{k.published_at ? `, published ${date(k.published_at)}` : ""}</p>
                  {k.notes && <p className="text-sm">{k.notes}</p>}</div>
                <div className="flex flex-wrap gap-2">
                  {k.status === "draft" && <button className="btn btn-quiet min-h-9 text-sm" onClick={() => move(k, "in_review")}>Send to review</button>}
                  {k.status === "in_review" && <><button className="btn btn-primary min-h-9 text-sm" onClick={() => move(k, "published")}>Publish</button>
                    <button className="btn btn-quiet min-h-9 text-sm" onClick={() => move(k, "draft")}>Back to draft</button></>}
                  {k.status === "published" && <button className="btn btn-quiet min-h-9 text-sm" onClick={() => move(k, "retired")}>Retire</button>}
                  {k.status === "retired" && <button className="btn btn-quiet min-h-9 text-sm" onClick={() => move(k, "published")}>Roll back to this</button>}
                </div>
              </div>
              {k.blockers.length > 0 && <div className="mt-2 rounded-lg bg-caution-bg p-3 text-sm"><p className="font-semibold">Can&apos;t be published yet:</p><ul className="list-disc pl-5">{k.blockers.map((b) => <li key={b}>{b}</li>)}</ul></div>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function AuditLog() {
  const q = useQuery({ queryKey: ["admin", "audit"], queryFn: () => api<Page<Audit>>("/admin/audit?limit=100") });
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorState error={q.error} />;
  return (
    <table className="w-full text-left text-sm"><caption className="sr-only">Audit log</caption>
      <thead className="text-ink-soft"><tr><th className="py-2 pr-3">When</th><th className="pr-3">Action</th><th className="pr-3">Target</th><th>Reason</th></tr></thead>
      <tbody>{q.data!.items.map((a) => <tr key={a.id} className="border-t border-line align-top"><td className="py-2 pr-3 whitespace-nowrap">{new Date(a.occurred_at).toLocaleString("en-IN")}</td>
        <td className="pr-3">{a.action}</td><td className="pr-3 break-all">{a.target}</td><td>{a.reason}</td></tr>)}</tbody>
    </table>
  );
}

function Jobs() {
  const q = useQuery({ queryKey: ["admin", "jobs"], queryFn: () => api<{ items: Job[] }>("/admin/jobs?status=failed") });
  if (q.isLoading) return <Loading />;
  if (!q.data?.items.length) return <Empty title="No failed jobs" />;
  return <ul className="space-y-2">{q.data.items.map((j) => <li key={j.id} className="rounded-xl border border-line bg-sheet p-3 text-sm">{j.type}: {j.error_code} after {j.retry_count} retries, {date(j.created_at)}</li>)}</ul>;
}

function Admin() {
  const [tab, setTab] = useState<keyof typeof TABS>("quality");
  return (
    <>
      <PageTitle title="Data and knowledge" lead="Review data quality, correct records, and publish reviewed knowledge. Every action is recorded in the audit log." />
      <div role="tablist" aria-label="Admin sections" className="mb-6 flex flex-wrap gap-2">
        {(Object.keys(TABS) as (keyof typeof TABS)[]).map((t) => (
          <button key={t} role="tab" aria-selected={tab === t} onClick={() => setTab(t)}
                  className={`rounded-full px-4 py-2 text-sm font-medium ${tab === t ? "bg-ink text-paper" : "border border-line hover:bg-mist"}`}>{TABS[t]}</button>
        ))}
      </div>
      <div role="tabpanel" aria-label={TABS[tab]}>
        {tab === "quality" && <Quality />}{tab === "flags" && <Flags />}{tab === "knowledge" && <Knowledge />}
        {tab === "audit" && <AuditLog />}{tab === "jobs" && <Jobs />}
      </div>
    </>
  );
}

export default function AdminPage() {
  return <RequireAuth admin>{() => <Admin />}</RequireAuth>;
}
