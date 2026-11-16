"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { RequireAuth } from "@/components/RequireAuth";
import { Empty, ErrorState, Loading, PageTitle } from "@/components/ui";
import { api } from "@/lib/api";
import { track } from "@/lib/analytics";

type R = { id: string; name: string; time_of_day: "morning" | "evening"; steps: { order: number; product: { name: string } }[] };

function Routines() {
  const router = useRouter();
  const q = useQuery({ queryKey: ["routines"], queryFn: () => api<{ items: R[] }>("/routines") });
  const [err, setErr] = useState<unknown>(null);
  const create = async (t: "morning" | "evening") => {
    try {
      const r = await api<R>("/routines", { body: { name: t === "morning" ? "Morning" : "Evening", time_of_day: t, steps: [] } });
      track("routine_created", { time: t });
      router.push(`/routines/${r.id}`);
    } catch (e) { setErr(e); }
  };
  return (
    <>
      <PageTitle title="Routines" lead="Put your products in order for morning and evening, then check every pair together." />
      <div className="mb-6 flex flex-wrap gap-2">
        <button className="btn btn-primary" onClick={() => create("morning")}>New morning routine</button>
        <button className="btn btn-quiet" onClick={() => create("evening")}>New evening routine</button>
      </div>
      {err != null && <ErrorState error={err} />}
      {q.isLoading ? <Loading /> : q.error ? <ErrorState error={q.error} retry={() => q.refetch()} /> : !q.data?.items.length ? (
        <Empty title="No routines yet">Start with a morning or evening routine. You can add products from your shelf or by searching.</Empty>
      ) : (
        <ul className="grid gap-4 md:grid-cols-2">
          {q.data.items.map((r) => (
            <li key={r.id} className="sheet p-5">
              <p className="text-sm text-ink-soft">{r.time_of_day === "morning" ? "Morning" : "Evening"}</p>
              <Link href={`/routines/${r.id}`} className="text-xl font-bold hover:underline">{r.name}</Link>
              <ol className="mt-2 list-decimal pl-5 text-sm">{r.steps.map((s) => <li key={s.order}>{s.product.name}</li>)}</ol>
              {r.steps.length === 0 && <p className="mt-2 text-sm text-ink-soft">No steps yet.</p>}
            </li>
          ))}
        </ul>
      )}
    </>
  );
}

export default function RoutinesPage() {
  return <RequireAuth>{() => <Routines />}</RequireAuth>;
}
