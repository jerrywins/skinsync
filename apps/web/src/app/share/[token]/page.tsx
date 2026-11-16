import type { Metadata } from "next";
import Link from "next/link";
import { AlternativesResult } from "@/components/AlternativesResult";
import { CompareResult } from "@/components/CompareResult";
import { Empty } from "@/components/ui";
import { serverApi } from "@/lib/api";
import { date } from "@/lib/format";
import type { AlternativesEnvelope, ComparisonEnvelope } from "@/lib/types";

export const metadata: Metadata = { title: "Shared result", robots: { index: false, follow: false } };

type Shared = { type: string; created_at: string; read_only: true; data: unknown };

export default async function SharedPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  const s = await serverApi<Shared>(`/public/shares/${encodeURIComponent(token)}`, 0).catch(() => null);
  if (!s) return <Empty title="This link isn't available" action={<Link className="btn btn-primary" href="/">Go to SkinSync</Link>}>It may have been removed by the person who shared it.</Empty>;
  return (
    <div className="space-y-6">
      <p className="rounded-xl bg-mist px-4 py-2 text-sm">Shared result, read-only, created {date(s.created_at)}. It reflects the data and knowledge version at that time.</p>
      {s.type === "comparison" && <CompareResult data={s.data as ComparisonEnvelope} readOnly />}
      {s.type === "alternative_search" && <AlternativesResult data={s.data as AlternativesEnvelope} readOnly />}
      {s.type === "routine" && (() => {
        const r = s.data as { name: string; time_of_day: string; steps: { order: number; product: { name: string; slug: string } }[] };
        return <div><h1 className="text-3xl font-extrabold">{r.name}</h1><p className="text-ink-soft">{r.time_of_day} routine</p>
          <ol className="mt-4 list-decimal space-y-1 pl-5">{r.steps.map((x) => <li key={x.order}><Link className="hover:underline" href={`/products/${x.product.slug}`}>{x.product.name}</Link></li>)}</ol></div>;
      })()}
      {s.type === "product" && (() => { const p = s.data as { slug: string; name: string }; return <Link className="btn btn-primary" href={`/products/${p.slug}`}>Open {p.name}</Link>; })()}
    </div>
  );
}
