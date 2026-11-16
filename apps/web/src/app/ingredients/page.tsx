import type { Metadata } from "next";
import Link from "next/link";
import { Empty, PageTitle } from "@/components/ui";
import { serverApi } from "@/lib/api";
import type { Page } from "@/lib/types";

type Ing = { id: string; inci_name: string; function_classes: string[]; reviewed: boolean; product_count: number };

export async function generateMetadata({ searchParams }: { searchParams: Promise<{ q?: string; page?: string }> }): Promise<Metadata> {
  const sp = await searchParams;
  return {
    title: "Skincare ingredient explorer",
    description: "Look up skincare ingredients by INCI or common name and see which products contain them.",
    robots: sp.q || (sp.page && sp.page !== "1") ? { index: false, follow: true } : undefined,
    alternates: { canonical: "/ingredients" },
  };
}

export default async function Ingredients({ searchParams }: { searchParams: Promise<{ q?: string; page?: string }> }) {
  const sp = await searchParams;
  const page = Math.max(1, Number(sp.page ?? 1) || 1);
  const qs = new URLSearchParams({ limit: "60", offset: String((page - 1) * 60) });
  if (sp.q) qs.set("q", sp.q);
  const data = await serverApi<Page<Ing>>(`/ingredients?${qs}`, 300);
  const more = (n: number) => `/ingredients?${new URLSearchParams({ ...(sp.q ? { q: sp.q } : {}), page: String(n) })}`;
  return (
    <>
      <PageTitle title="Ingredients" lead="Search by INCI name or the name printed on the pack. Names marked unreviewed come from product data and have not been checked by our team yet." />
      <form action="/ingredients" role="search" className="mb-6 flex max-w-xl gap-2">
        <label htmlFor="iq" className="sr-only">Search ingredients</label>
        <input id="iq" name="q" defaultValue={sp.q} className="field" placeholder="For example glycerin or aqua" />
        <button className="btn btn-primary">Search</button>
      </form>
      <p className="text-sm text-ink-soft" role="status">{data?.total ?? 0} ingredients</p>
      {!data?.items.length ? (
        <div className="mt-4"><Empty title="No ingredients match">Check the spelling, or try the INCI name from the label.</Empty></div>
      ) : (
        <ul className="label-voice mt-3 grid gap-x-8 sm:grid-cols-2 lg:grid-cols-3">
          {data.items.map((i) => (
            <li key={i.id} className="flex items-baseline justify-between gap-3 border-b border-line py-2">
              <Link className="hover:text-dropper hover:underline" href={`/ingredients/${i.id}`}>{i.inci_name}</Link>
              <span className="shrink-0 font-sans text-xs text-ink-soft">{i.product_count} products{i.reviewed ? "" : ", unreviewed"}</span>
            </li>
          ))}
        </ul>
      )}
      {data && data.total > 60 && (
        <nav aria-label="Pages" className="mt-6 flex items-center gap-3">
          {page > 1 && <Link className="btn btn-quiet" href={more(page - 1)}>Previous</Link>}
          <span className="text-sm text-ink-soft">Page {page} of {Math.ceil(data.total / 60)}</span>
          {data.next_offset != null && <Link className="btn btn-quiet" href={more(page + 1)}>Next</Link>}
        </nav>
      )}
    </>
  );
}
