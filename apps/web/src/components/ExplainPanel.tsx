import type { ReactNode } from "react";
import { ConfidenceBadge, EvidenceBadge } from "./ui";

/** The standard explainability panel (spec §9G, NFR-10), used on every result screen:
 *  What was used / How confident / Evidence strength / What's missing. */
export function ExplainPanel({ used, confidence, confidenceLevel, evidence, missing, footnote }: {
  used: { label: string; value: ReactNode }[];
  confidence?: number | null;
  confidenceLevel?: string;
  evidence?: string | null;
  missing: string[];
  footnote?: ReactNode;
}) {
  return (
    <aside aria-labelledby="explain-h" className="self-start rounded-2xl bg-mist p-5 lg:sticky lg:top-24">
      <h2 id="explain-h" className="text-lg font-bold">How this result was made</h2>
      <section className="mt-4">
        <h3 className="text-sm font-semibold text-ink-soft">What was used</h3>
        <dl className="mt-1 space-y-1 text-sm">
          {used.map((u) => (
            <div key={u.label} className="flex flex-wrap gap-x-2">
              <dt className="text-ink-soft">{u.label}:</dt><dd className="font-medium break-words [overflow-wrap:anywhere]">{u.value}</dd>
            </div>
          ))}
        </dl>
      </section>
      {(confidence != null || evidence) && (
        <section className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
          {confidence != null && (
            <div>
              <ConfidenceBadge value={confidence} level={confidenceLevel} label="How confident" />
              <p className="mt-1 text-xs text-ink-soft">How sure we are about the data and matching.</p>
            </div>
          )}
          {evidence && (
            <div>
              <EvidenceBadge strength={evidence} />
              <p className="mt-1 text-xs text-ink-soft">How well the science behind a finding is supported.</p>
            </div>
          )}
        </section>
      )}
      <section className="mt-5">
        <h3 className="text-sm font-semibold text-ink-soft">What&apos;s missing</h3>
        {missing.length ? (
          <ul className="mt-1 list-disc space-y-1 pl-5 text-sm">{missing.map((m) => <li key={m}>{m}</li>)}</ul>
        ) : (
          <p className="mt-1 text-sm">Nothing we know of.</p>
        )}
      </section>
      {footnote && <div className="mt-5 border-t border-mist-deep pt-3 text-xs text-ink-soft">{footnote}</div>}
    </aside>
  );
}
