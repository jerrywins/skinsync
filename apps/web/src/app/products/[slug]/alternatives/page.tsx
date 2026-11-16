import { redirect } from "next/navigation";

// SEO-friendly route from the spec; the search itself runs on /alternatives.
export default async function ProductAlternatives({ params }: { params: Promise<{ slug: string }> }) {
  redirect(`/alternatives?ref=${encodeURIComponent((await params).slug)}`);
}
