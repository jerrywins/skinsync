import type { Metadata } from "next";
import { CompareView } from "./view";

export const metadata: Metadata = { title: "Comparison result", robots: { index: false } };

export default async function ComparisonPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <CompareView id={id} />;
}
