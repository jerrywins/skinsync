import Link from "next/link";
import type { NormalizedIngredient } from "@/lib/api";

/** The signature element: an ingredient list set like the back of the bottle.
 *  Shared ingredients are underlined, unrecognised ones are struck through with a "?" and never hidden. */
export function LabelStrip({ title, subtitle, items, shared = new Set<string>(), highlight = new Set<string>() }: {
  title: string; subtitle?: string; items: Pick<NormalizedIngredient, "position" | "raw" | "canonical_id" | "inci_name" | "candidate" | "stated_role">[];
  shared?: Set<string>; highlight?: Set<string>;
}) {
  return (
    <figure className="rounded-2xl border border-line bg-sheet p-5">
      <figcaption>
        <p className="font-bold">{title}</p>
        {subtitle && <p className="text-sm text-ink-soft">{subtitle}</p>}
      </figcaption>
      {items.length === 0 ? (
        <p className="mt-3 text-sm text-unknown">No ingredient list on record.</p>
      ) : (
        <ol className="label-voice mt-3 flex flex-wrap gap-x-1 gap-y-0.5" aria-label={`Ingredients of ${title}`}>
          {items.map((i, idx) => {
            const known = i.canonical_id != null;
            const name = known ? i.inci_name ?? i.raw : i.raw;
            const isHi = known && highlight.has(i.canonical_id!);
            const isShared = known && shared.has(i.inci_name ?? "");
            const cls = [
              !known && "text-unknown line-through decoration-unknown/60",
              isShared && "underline decoration-dropper decoration-2 underline-offset-[3px]",
              isHi && "rounded bg-caution-bg px-0.5 font-semibold text-ink",
              i.stated_role === "may_contain" && "italic",
            ].filter(Boolean).join(" ");
            return (
              <li key={`${i.position}-${idx}`} className="after:content-[','] last:after:content-['']">
                {known ? (
                  <Link href={`/ingredients/${i.canonical_id}`} className={`hover:text-dropper ${cls}`}>{name}</Link>
                ) : (
                  <span className={cls} title={i.candidate ? `Not recognised. Possible match: ${i.candidate}` : "Not recognised"}>
                    {name}<span className="no-underline" aria-label=" (not recognised)">?</span>
                  </span>
                )}
              </li>
            );
          })}
        </ol>
      )}
      {items.length > 0 && (
        <p className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-soft">
          <span><span className="underline decoration-dropper decoration-2 underline-offset-[3px]">Underlined</span>: in both products</span>
          <span><span className="line-through">Struck through?</span>: not recognised, treated as unknown</span>
        </p>
      )}
    </figure>
  );
}
