import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { ProductRow } from "@/components/ProductCard";
import { PageTitle } from "@/components/ui";
import { serverApi } from "@/lib/api";
import type { ProductSummary } from "@/lib/types";

type Brand = { name: string; slug: string; total: number; products: ProductSummary[] };
const load = (s: string) => serverApi<Brand>(`/brands/${encodeURIComponent(s)}`, 600);

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const b = await load((await params).slug);
  if (!b) return { title: "Brand not found", robots: { index: false } };
  return { title: `${b.name} skincare products`, description: `${b.total} ${b.name} products with ingredient lists and sources.`,
           alternates: { canonical: `/brands/${b.slug}` }, robots: b.total < 2 ? { index: false } : undefined };
}

export default async function BrandPage({ params }: { params: Promise<{ slug: string }> }) {
  const b = await load((await params).slug);
  if (!b) notFound();
  return (
    <>
      <PageTitle title={b.name} lead={`${b.total} product${b.total === 1 ? "" : "s"} in our catalogue.`} />
      <ul className="max-w-3xl">{b.products.map((p) => <ProductRow key={p.id} p={p} />)}</ul>
    </>
  );
}
