import type { Metadata } from "next";
import { StaticPage } from "@/components/StaticPage";

export const metadata: Metadata = { title: "How SkinSync works", description: "How SkinSync compares products, finds alternatives and analyses photos.", alternates: { canonical: "/how-it-works" } };

export default function Page() {
  return (
    <StaticPage title="How it works" lead="Software reads labels and photos. Conclusions come from written, reviewed rules, so every result can be traced and repeated.">
      <h2>Comparing two products</h2>
      <ol className="list-decimal space-y-1 pl-5">
        <li>We find the current formulation of each product: its ingredient list on a known date, from a named source.</li>
        <li>Each ingredient is matched to a standard name. Anything we can&apos;t match is marked unknown, never assumed harmless.</li>
        <li>We check the pair against interaction rules in the published knowledge version. Every rule cites evidence.</li>
        <li>You get one of five results: no notable interaction found, caution, strong caution, insufficient evidence, or data incomplete.</li>
      </ol>
      <p>The same two formulations and the same knowledge version always give the same result. When a formulation or the knowledge base changes, saved results are marked out of date.</p>
      <h2>Finding alternatives</h2>
      <p>We look only at real products in our catalogue, in the same category. Each one is scored on ingredient similarity, shared key ingredients, category, formulation and your preferences, and you can see every score. Prices are shown only when we have a recent observation; we never estimate one.</p>
      <h2>Analysing a skin photo</h2>
      <p>A model looks for visible cosmetic features, such as shine or uneven tone, and reports how confident it is. Suggestions come from a reviewed table that links features to ingredient types, not from the model. The current model is a demonstration placeholder and is labelled as such.</p>
      <h2>What we don&apos;t do</h2>
      <ul>
        <li>Diagnose, name or treat any skin condition.</li>
        <li>Say a combination is safe for everyone.</li>
        <li>Let an AI model decide whether two products are compatible.</li>
        <li>Rank anything because of a commercial relationship.</li>
      </ul>
    </StaticPage>
  );
}
