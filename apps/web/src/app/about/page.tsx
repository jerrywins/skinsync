import type { Metadata } from "next";
import { StaticPage } from "@/components/StaticPage";

export const metadata: Metadata = { title: "About", alternates: { canonical: "/about" } };

export default function Page() {
  return (
    <StaticPage title="About SkinSync" lead="An evidence-aware skincare decision tool built as a software engineering project.">
      <p>SkinSync answers three everyday questions: what does my skin appear to need, can I use these products together, and what are my alternatives? It answers them from structured product data and reviewed rules, and shows its working.</p>
      <p>SkinSync has no commercial relationships with brands or sellers. If any are ever introduced, they will not affect compatibility results or evidence grades.</p>
    </StaticPage>
  );
}
