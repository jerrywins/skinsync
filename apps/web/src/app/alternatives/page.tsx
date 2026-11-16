import type { Metadata } from "next";
import { PageTitle } from "@/components/ui";
import { AltForm } from "./form";

export const metadata: Metadata = {
  title: "Find skincare alternatives",
  description: "Find cheaper, similar or premium skincare alternatives with matching ingredients, and see why each was chosen.",
  alternates: { canonical: "/alternatives" },
};

export default async function AlternativesPage({ searchParams }: { searchParams: Promise<{ ref?: string; mode?: string }> }) {
  const sp = await searchParams;
  return (
    <>
      <PageTitle title="What else could I use?" lead="Pick a product you know. We look for real products in the same category with closely matching ingredients, and show the reasons for every match." />
      <AltForm initialRef={sp.ref} initialMode={sp.mode} />
    </>
  );
}
