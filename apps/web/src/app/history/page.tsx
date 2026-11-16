"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { RequireAuth } from "@/components/RequireAuth";
import { Empty, ErrorState, Icon, Loading, PageTitle, StatusPill } from "@/components/ui";
import { api } from "@/lib/api";
import { date, MODE_LABEL, type StatusKey } from "@/lib/format";

type H = { type: "comparison" | "skin_analysis" | "alternative_search"; id: string; title: string; status: string;
           created_at: string; outdated: string[]; is_demo_model?: boolean };
type Share = { share_id: string; target_type: string; target_id: string; created_at: string; revoked_at: string | null };

const HREF = { comparison: "/compare/", skin_analysis: "/analyze/", alternative_search: "/alternatives/" };
const KIND = { all: "Everything", comparison: "Comparisons", skin_analysis: "Skin analyses", alternative_search: "Alternatives" };

function History() {
  const qc = useQueryClient();
  const [kind, setKind] = useState<keyof typeof KIND>("all");
  const q = useQuery({ queryKey: ["history", kind], queryFn: () => api<{ items: H[] }>(`/history?kind=${kind}`) });
  const shares = useQuery({ queryKey: ["shares"], queryFn: () => api<{ items: Share[] }>("/shares") });
  const del = async (h: H) => {
    if (h.type === "skin_analysis") await api(`/skin-analyses/${h.id}`, { method: "DELETE" });
    else await api(`/history/${h.type}/${h.id}`, { method: "DELETE" });
    qc.invalidateQueries({ queryKey: ["history"] }); qc.invalidateQueries({ queryKey: ["shares"] });
  };
  const revoke = async (s: Share) => { await api(`/shares/${s.share_id}`, { method: "DELETE" }); qc.invalidateQueries({ queryKey: ["shares"] }); };
  return (
    <>
      <PageTitle title="History" lead="Saved results with the product and knowledge versions they used. We tell you when one goes out of date." />
      <div role="tablist" aria-label="Filter" className="mb-6 flex flex-wrap gap-2">
        {(Object.keys(KIND) as (keyof typeof KIND)[]).map((k) => (
          <button key={k} role="tab" aria-selected={kind === k} onClick={() => setKind(k)}
                  className={`rounded-full px-4 py-2 text-sm font-medium ${kind === k ? "bg-ink text-paper" : "border border-line hover:bg-mist"}`}>{KIND[k]}</button>
        ))}
      </div>
      {q.isLoading ? <Loading /> : q.error ? <ErrorState error={q.error} retry={() => q.refetch()} /> : !q.data?.items.length ? (
        <Empty title="Nothing saved yet" action={<Link className="btn btn-primary" href="/compare">Compare two products</Link>}>Results you save appear here.</Empty>
      ) : (
        <ul className="divide-y divide-line rounded-2xl border border-line bg-sheet">
          {q.data.items.map((h) => (
            <li key={h.id} className="flex flex-wrap items-start gap-4 p-4">
              <div className="min-w-0 flex-1">
                <p className="text-sm text-ink-soft">{KIND[h.type]}, {date(h.created_at)}</p>
                <Link href={`${HREF[h.type]}${h.id}`} className="font-bold hover:underline">{h.title}</Link>
                <div className="mt-1">
                  {h.type === "comparison" ? <StatusPill status={h.status as StatusKey} /> :
                   h.type === "alternative_search" ? <span className="text-sm">{MODE_LABEL[h.status] ?? h.status}</span> :
                   <span className="text-sm">{h.status}{h.is_demo_model ? ", demo model" : ""}</span>}
                </div>
                {h.outdated.length > 0 && <p className="mt-1 text-sm text-caution">Out of date: {h.outdated.join(" ")}</p>}
              </div>
              <button className="btn btn-quiet min-h-9 text-sm" onClick={() => del(h)} aria-label={`Delete ${h.title}`}><Icon name="trash" className="size-4" />Delete</button>
            </li>
          ))}
        </ul>
      )}
      <section aria-labelledby="sh-h" className="mt-12">
        <h2 id="sh-h" className="text-xl font-bold">Share links</h2>
        {!shares.data?.items.length ? <p className="mt-2 text-ink-soft">You haven&apos;t shared anything.</p> : (
          <ul className="mt-3 space-y-2">
            {shares.data.items.map((s) => (
              <li key={s.share_id} className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-line bg-sheet p-3 text-sm">
                <span>{s.target_type.replace("_", " ")} shared {date(s.created_at)}{s.revoked_at ? `, revoked ${date(s.revoked_at)}` : ""}</span>
                {!s.revoked_at && <button className="btn btn-quiet min-h-9 text-sm" onClick={() => revoke(s)}>Revoke link</button>}
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  );
}

export default function HistoryPage() {
  return <RequireAuth>{() => <History />}</RequireAuth>;
}
