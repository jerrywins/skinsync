"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { use, useEffect, useState } from "react";
import { ExplainPanel } from "@/components/ExplainPanel";
import { ConfidenceBadge, DemoBadge, Empty, ErrorState, EvidenceBadge, Icon, Loading, Notice } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { track } from "@/lib/analytics";
import { SKIN_TYPES } from "@/lib/format";
import { forgetPollToken, pollHeaders } from "@/lib/poll";
import type { SkinAnalysis } from "@/lib/types";

const SEVERITY: Record<string, string> = { mild: "Mild", moderate: "Moderate", pronounced: "Pronounced" };

export default function SkinResultPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const [deleted, setDeleted] = useState(false);
  const q = useQuery({
    queryKey: ["skin", id],
    queryFn: () => api<SkinAnalysis>(`/skin-analyses/${id}`, { headers: pollHeaders(id) }),
    refetchInterval: (query) => (["queued", "analyzing", "created", "validating"].includes(query.state.data?.status ?? "") ? 1500 : false),
  });
  useEffect(() => { if (q.data?.status === "completed") track("skin_analysis_completed"); }, [q.data?.status]);
  const del = async (what: "all" | "image") => {
    await api(`/skin-analyses/${id}${what === "image" ? "/image" : ""}`, { method: "DELETE", headers: pollHeaders(id) });
    if (what === "all") { forgetPollToken(id); setDeleted(true); } else q.refetch();
  };
  if (deleted) return <Empty title="Analysis deleted" action={<button className="btn btn-primary" onClick={() => router.push("/analyze")}>Start a new analysis</button>}>The result, observations and photo have been removed.</Empty>;
  if (q.isLoading) return <Loading label="Loading analysis" />;
  if (q.error instanceof ApiError && q.error.status === 404)
    return <Empty title="This analysis isn't available" action={<Link className="btn btn-primary" href="/analyze">Start a new analysis</Link>}>Analyses are private. A guest result can only be opened in the browser tab that created it.</Empty>;
  if (q.error) return <ErrorState error={q.error} retry={() => q.refetch()} />;
  const a = q.data!;
  if (a.status !== "completed") {
    if (a.status === "failed" || a.status === "rejected")
      return <div className="max-w-2xl space-y-4"><ErrorState error={{ message: a.message ?? "The analysis could not be completed." }} />
        <Link className="btn btn-primary" href="/analyze">Try again</Link></div>;
    return (
      <div className="max-w-xl" role="status" aria-live="polite">
        <h1 className="text-3xl font-extrabold">Analyzing your photo</h1>
        <p className="mt-2 text-ink-soft">This usually takes a few seconds. You can keep this tab open.</p>
        <progress className="mt-6 h-2 w-full" max={100} value={a.progress || undefined} aria-label="Analysis progress" />
      </div>
    );
  }
  const r = a.result!;
  const skin = SKIN_TYPES.find((s) => s.id === a.skin_type)?.label ?? a.skin_type;
  const byObs = new Map<string, typeof r.recommendations>();
  r.recommendations.forEach((x) => byObs.set(x.observation, [...(byObs.get(x.observation) ?? []), x]));
  return (
    <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_20rem]">
      <div className="min-w-0 space-y-8">
        <header className="space-y-3">
          {a.is_demo_model && <Notice tone="demo"><DemoBadge>{a.demo_label ?? "Demo model"}</DemoBadge> These observations come from a placeholder model that does not look at skin. They only show how the flow works.</Notice>}
          {!a.is_demo_model && a.model_version?.startsWith("heuristic") && <Notice tone="demo"><DemoBadge>{a.demo_label ?? "Experimental — not validated"}</DemoBadge> These are simple colour and texture measurements, not a trained or tested skin model. Lighting, camera and skin tone change them a lot. Treat them as rough hints only.</Notice>}
          <h1 className="text-3xl font-extrabold sm:text-4xl">Visible features in your photo</h1>
          <p className="text-ink-soft">Skin type you chose: {skin}</p>
          <Notice>{a.medical_boundary}</Notice>
        </header>
        <section aria-labelledby="obs-h">
          <h2 id="obs-h" className="text-xl font-bold">What we observed</h2>
          {r.observations.length === 0 ? <p className="mt-2 text-ink-soft">No supported features were observed with enough confidence.</p> : (
            <ul className="mt-3 grid gap-3 sm:grid-cols-2">
              {r.observations.map((o) => (
                <li key={o.characteristic} className={`rounded-xl border bg-sheet p-4 ${o.low_confidence ? "border-dashed border-unknown" : "border-line"}`}
                    onFocus={() => track("skin_observation_viewed")}>
                  <p className="font-bold">{o.label}</p>
                  <p className="text-sm text-ink-soft">Estimated level: {SEVERITY[o.severity]}</p>
                  <div className="mt-3"><ConfidenceBadge value={o.confidence} level={o.confidence_level} /></div>
                  {o.low_confidence && <p className="mt-2 text-xs text-unknown">Low confidence: shown for completeness, not used for suggestions.</p>}
                </li>
              ))}
            </ul>
          )}
        </section>
        <section aria-labelledby="rec-h">
          <h2 id="rec-h" className="text-xl font-bold">What you could explore</h2>
          {r.recommendations.length === 0 ? (
            <p className="mt-2 max-w-prose text-ink-soft">We don&apos;t have reviewed guidance linking these features to ingredient types yet, so we make no suggestions rather than guess.</p>
          ) : (
            <ul className="mt-3 space-y-4">
              {[...byObs.entries()].map(([obs, recs]) => (
                <li key={obs} className="rounded-2xl border border-line bg-sheet p-5">
                  {recs.map((rec) => (
                    <div key={rec.concern_category} className="space-y-3">
                      <div className="flex flex-wrap items-start justify-between gap-4">
                        <div><p className="font-bold">{rec.concern_category}</p><p className="text-sm text-ink-soft">{rec.intended_role}</p>
                          <p className="mt-1 text-sm">Ingredient types: {rec.ingredient_classes.join(", ")}</p></div>
                        <div className="grid gap-3 sm:grid-cols-2"><ConfidenceBadge value={rec.observation_confidence} label="Observation" /><EvidenceBadge strength={rec.evidence_strength} /></div>
                      </div>
                      <ul className="space-y-2">
                        {r.products.filter((p) => p.observation === obs && p.concern_category === rec.concern_category).map((p) => (
                          <li key={p.product_id} className="flex flex-wrap items-center justify-between gap-2 border-t border-line pt-2">
                            <div><Link href={`/products/${p.slug}`} className="font-semibold hover:underline" onClick={() => track("skin_recommendation_clicked")}>{p.name}</Link>
                              <p className="text-xs text-ink-soft">{p.rationale}</p></div>
                            <Link className="btn btn-quiet min-h-9 text-sm" href={`/alternatives?ref=${p.product_id}`}><Icon name="swap" className="size-4" />Alternatives</Link>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </li>
              ))}
            </ul>
          )}
          {r.unmapped_observations.length > 0 && <p className="mt-3 text-sm text-ink-soft">No reviewed guidance yet for: {r.unmapped_observations.map((x) => x.replaceAll("_", " ")).join(", ")}.</p>}
        </section>
        <section aria-labelledby="priv-h" className="rounded-2xl border border-line p-5">
          <h2 id="priv-h" className="font-bold">Your photo and this result</h2>
          <p className="mt-1 text-sm text-ink-soft">{a.image_stored ? "Your photo is stored encrypted until you delete it or it expires." : "Your photo has already been deleted."} This result is private and cannot be shared.</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {a.image_stored && <button className="btn btn-quiet" onClick={() => del("image")}><Icon name="trash" className="size-4" />Delete photo now</button>}
            <button className="btn btn-quiet" onClick={() => del("all")}><Icon name="trash" className="size-4" />Delete this analysis</button>
            <Link className="btn btn-quiet" href="/routines">Build a routine</Link>
          </div>
        </section>
      </div>
      <ExplainPanel
        used={[{ label: "Model", value: `${a.model_version}${a.is_demo_model ? " (demo, not real)" : a.model_version?.startsWith("heuristic") ? " (experimental, not validated)" : ""}` },
               { label: "Knowledge version", value: r.knowledge_version }, { label: "Skin type", value: skin }]}
        missing={[
          ...(a.is_demo_model ? ["A validated skin model. These observations are placeholders."] : []),
          ...(a.model_version?.startsWith("heuristic") ? ["A validated skin model. These are uncalibrated image measurements."] : []),
          ...(r.unmapped_observations.length ? ["Reviewed guidance for some observations"] : []),
          "Anything a single photo can't show: how your skin feels, changes over time, or reactions",
        ]}
        footnote="Observation confidence is how sure the model is. Evidence strength is how well the ingredient guidance is supported. They are separate."
      />
    </div>
  );
}
