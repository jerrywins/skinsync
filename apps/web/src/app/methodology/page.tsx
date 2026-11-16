import type { Metadata } from "next";
import { StaticPage } from "@/components/StaticPage";

export const metadata: Metadata = { title: "Evidence and methodology", alternates: { canonical: "/methodology" } };

export default function Page() {
  return (
    <StaticPage title="Evidence and methodology" lead="How we grade evidence, measure confidence and handle missing data.">
      <h2>Two different measures</h2>
      <p><strong>Confidence</strong> is how sure we are about the data: that an ingredient was matched correctly, that a formulation is complete, or that a model saw a feature. <strong>Evidence strength</strong> is how well the science behind a finding is supported. A finding can have high confidence and limited evidence, so we always show both.</p>
      <h2>Evidence grades</h2>
      <ul>
        <li><strong>High</strong>: consistent support from strong sources.</li>
        <li><strong>Moderate</strong>: reasonable support with some gaps.</li>
        <li><strong>Limited</strong>: some support, not conclusive.</li>
        <li><strong>Insufficient</strong>: not enough to support a conclusion.</li>
        <li><strong>Unknown</strong>: not assessed.</li>
      </ul>
      <p>Rules backed only by insufficient or unknown evidence cannot be published.</p>
      <h2>Knowledge versions</h2>
      <p>Rules, evidence and concern mappings are written by people, reviewed, and published together as a numbered knowledge version. Published versions never change; corrections are made in a new version. Every result records the version it used.</p>
      <h2>Current state of the knowledge base</h2>
      <p>No reviewed interaction rules have been published yet. Until they are, comparisons of real products will say &ldquo;insufficient evidence&rdquo; or &ldquo;data incomplete&rdquo;. That is the honest answer, not a fault. A clearly labelled, fictional demo dataset shows how results look when rules exist.</p>
      <h2>Ranking alternatives</h2>
      <p>Default weights: ingredient similarity 35%, target ingredients 20%, category 15%, preferences 15%, formulation 15%. These are design choices, not science. Scores we can&apos;t compute are left out and the rest re-weighted, so missing data never counts as a match.</p>
    </StaticPage>
  );
}
