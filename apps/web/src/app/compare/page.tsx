import type { Metadata } from "next";
import { CompareForm } from "@/components/CompareForm";
import { PageTitle } from "@/components/ui";

export const metadata: Metadata = {
  title: "Compare two skincare products",
  description: "Check two skincare products for ingredient interactions, shared actives and missing data.",
  alternates: { canonical: "/compare" },
};

export default async function ComparePage({ searchParams }: { searchParams: Promise<{ a?: string; b?: string }> }) {
  const { a, b } = await searchParams;
  return (
    <>
      <PageTitle title="Can I use these together?"
                 lead="Choose two products, or paste an ingredient list. We compare the current formulations against our reviewed knowledge base." />
      <CompareForm initialA={a} initialB={b} />
    </>
  );
}
