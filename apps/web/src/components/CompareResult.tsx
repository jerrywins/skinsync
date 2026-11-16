"use client";

import Link from "next/link";
import { useState } from "react";
import type { Finding } from "@/lib/api";
import { STATUS, type StatusKey } from "@/lib/format";
import type { ComparisonEnvelope } from "@/lib/types";
import { ExplainPanel } from "./ExplainPanel";
import { LabelStrip } from "./LabelStrip";
import { SaveShareBar } from "./SaveShareBar";
import { ConfidenceBadge, DemoBadge, EvidenceBadge, Icon, Notice, severityTone, StatusPill } from "./ui";

const HEADLINE: Record<StatusKey, string> = {
  no_notable_interaction: "No notable interaction found",
  caution: "Use with some care",
  strong_caution: "Reconsider combining these",
  insufficient_evidence: "We can't say yet",
  data_incomplete: "Some of the data is missing",
};

const toneBorder: Record<string, string> = {
  strong: "border-l-strong", caution: "border-l-caution", unknown: "border-l-unknown", clear: "border-l-clear",
};

function FindingItem({ f }: { f: Finding }) {
  const [open, setOpen] = useState(false);
  const tone = f.type === "rule" ? severityTone(f.severity) : "unknown";
  return (
    <li className={`rounded-xl border border-line border-l-4 bg-sheet p-4 ${toneBorder[tone]}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="max-w-prose">
          <p className="font-bold">{f.title}</p>
          <p className="mt-1 text-ink-soft">{f.explanation}</p>
          {f.practical_guidance && <p className="mt-2"><span className="font-semibold">What you can do: </span>{f.practical_guidance}</p>}
        </div>
        {f.type === "rule" && (
          <div className="grid w-full gap-3 sm:w-auto sm:grid-cols-2">
            <ConfidenceBadge value={f.confidence} level={f.confidence_level} />
            <EvidenceBadge strength={f.evidence_strength} />
          </div>
        )}
      </div>
      <button className="mt-3 text-sm font-semibold text-dropper underline underline-offset-4" aria-expanded={open}
              onClick={() => setOpen((o) => !o)}>
        {open ? "Hide details" : "Why was this flagged?"}
      </button>
      {open && (
        <div className="mt-3 space-y-3 text-sm">
          <ol className="list-decimal space-y-1 pl-5">{f.why.map((w) => <li key={w}>{w}</li>)}</ol>
          {f.evidence.length > 0 && (
            <div>
              <p className="font-semibold">Evidence</p>
              <ul className="mt-1 space-y-2">
                {f.evidence.map((e) => (
                  <li key={e.id} className="rounded-lg bg-mist p-3">
                    <p>{e.claim}</p>
                    <p className="mt-1 text-ink-soft">{e.citation} ({e.source_type.replaceAll("_", " ")}, strength {e.strength})</p>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </li>
  );
}

export function CompareResult({ data, readOnly = false }: { data: ComparisonEnvelope; readOnly?: boolean }) {
  const r = data.result;
  const status = r.status as StatusKey;
  const shared = new Set(r.ingredients.shared);
  const ruleFindings = r.findings.filter((f) => f.type === "rule");
  const highlightA = new Set<string>(), highlightB = new Set<string>();
  const byName = (side: typeof data.product_a, names: string[]) =>
    side.ingredients.filter((i) => i.inci_name && names.includes(i.inci_name)).forEach((i) =>
      (side === data.product_a ? highlightA : highlightB).add(i.canonical_id!));
  ruleFindings.forEach((f) => { byName(data.product_a, f.a_ingredients); byName(data.product_b, f.b_ingredients); });
  const other = r.findings.filter((f) => f.type !== "rule");
  const missing = [
    ...(r.ingredients.unresolved_a.length ? [`${r.ingredients.unresolved_a.length} unrecognised in ${data.product_a.name}`] : []),
    ...(r.ingredients.unresolved_b.length ? [`${r.ingredients.unresolved_b.length} unrecognised in ${data.product_b.name}`] : []),
    ...r.findings.filter((f) => f.type === "incomplete_formulation").map((f) => f.title),
    ...(r.findings.some((f) => f.type === "insufficient_evidence") ? ["No reviewed interaction rules are published yet."] : []),
  ];
  return (
    <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_20rem]">
      <div className="min-w-0 space-y-8">
        <section aria-labelledby="verdict" className="space-y-3">
          {r.knowledge_is_demo && (
            <Notice tone="demo"><DemoBadge /> This result uses the fictional demo dataset to show how SkinSync works. It is not scientific advice.</Notice>
          )}
          {data.outdated.length > 0 && (
            <Notice tone="caution">
              <p className="font-semibold">This result may be out of date.</p>
              <ul className="mt-1 list-disc pl-5">{data.outdated.map((o) => <li key={o}>{o}</li>)}</ul>
              {data.product_a.product_id && data.product_b.product_id && (
                <Link className="mt-2 inline-block font-semibold text-dropper underline"
                      href={`/compare?a=${data.product_a.product_id}&b=${data.product_b.product_id}`}>Run it again with current data</Link>
              )}
            </Notice>
          )}
          <StatusPill status={status} />
          <h1 id="verdict" className="text-3xl font-extrabold sm:text-4xl">{HEADLINE[status]}</h1>
          {r.status_label !== STATUS[status].short && <p className="max-w-prose text-lg">{r.status_label}</p>}
          <p className="text-ink-soft">
            {data.product_a.name} and {data.product_b.name}
          </p>
        </section>

        {!readOnly && <SaveShareBar kind="comparison" id={data.id} saved={!!data.saved} saveable={data.saveable}
                                    claimToken={data.claim_token} />}

        <section aria-labelledby="findings-h">
          <h2 id="findings-h" className="text-xl font-bold">What we found</h2>
          {ruleFindings.length === 0 && (
            <p className="mt-2 max-w-prose text-ink-soft">
              No reviewed rule in our knowledge base applies to these two formulations.
              {status !== "no_notable_interaction" && " Read the notes below before relying on that."}
            </p>
          )}
          <ul className="mt-3 space-y-3">{ruleFindings.map((f) => <FindingItem key={`${f.rule_code}-${f.title}`} f={f} />)}</ul>
          {other.length > 0 && (
            <>
              <h3 className="mt-6 font-semibold">Notes about the data</h3>
              <ul className="mt-2 space-y-3">{other.map((f) => <FindingItem key={`${f.type}-${f.title}`} f={f} />)}</ul>
            </>
          )}
        </section>

        <section aria-labelledby="ingredients-h">
          <h2 id="ingredients-h" className="text-xl font-bold">Ingredients side by side</h2>
          <p className="mt-1 text-sm text-ink-soft">
            {r.ingredients.shared.length} shared, {r.ingredients.a_only.length} only in {data.product_a.name},{" "}
            {r.ingredients.b_only.length} only in {data.product_b.name}. Flagged ingredients are highlighted.
          </p>
          <div className="mt-3 grid gap-4 md:grid-cols-2">
            <LabelStrip title={data.product_a.name} subtitle={`Formulation ${data.product_a.version_label}`}
                        items={data.product_a.ingredients} shared={shared} highlight={highlightA} />
            <LabelStrip title={data.product_b.name} subtitle={`Formulation ${data.product_b.version_label}`}
                        items={data.product_b.ingredients} shared={shared} highlight={highlightB} />
          </div>
        </section>

        {!readOnly && data.product_a.product_id && data.product_b.product_id && (
          <section aria-labelledby="next-h">
            <h2 id="next-h" className="text-xl font-bold">Next</h2>
            <div className="mt-3 flex flex-wrap gap-2">
              <Link className="btn btn-quiet" href={`/alternatives?ref=${data.product_a.product_id}`}><Icon name="swap" className="size-4" />Alternatives to {data.product_a.name}</Link>
              <Link className="btn btn-quiet" href={`/alternatives?ref=${data.product_b.product_id}`}><Icon name="swap" className="size-4" />Alternatives to {data.product_b.name}</Link>
              <Link className="btn btn-quiet" href="/routines"><Icon name="layers" className="size-4" />Add to a routine</Link>
            </div>
          </section>
        )}
      </div>

      <ExplainPanel
        used={[
          { label: data.product_a.name, value: data.product_a.version_label },
          { label: data.product_b.name, value: data.product_b.version_label },
          { label: "Knowledge version", value: r.knowledge_version },
          { label: "Engine", value: r.engine_version },
          { label: "Completeness", value: `${Math.round(r.completeness * 100)}% of ingredients recognised (lower of the two)` },
        ]}
        confidence={r.confidence} confidenceLevel={r.confidence_level}
        evidence={ruleFindings.length ? r.evidence_strength : null}
        missing={missing}
        footnote={<>Results depend on the formulations and knowledge version listed. &ldquo;No notable interaction&rdquo; never means safe for everyone.</>}
      />
    </div>
  );
}
