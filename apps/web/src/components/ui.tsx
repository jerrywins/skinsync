import Link from "next/link";
import type { ReactNode } from "react";
import { CONFIDENCE_LABEL, STATUS, STRENGTH_LABEL, type StatusKey } from "@/lib/format";

/* ---------- icons (inline SVG, aria-hidden; meaning always carried by text) ---------- */
export function Icon({ name, className = "size-5" }: { name: string; className?: string }) {
  const p: Record<string, ReactNode> = {
    check: <path d="M5 12.5l4.5 4.5L19 7.5" />,
    alert: <><path d="M12 4l9 16H3z" /><path d="M12 10v4.5M12 17.5v.01" /></>,
    stop: <><path d="M8 3h8l5 5v8l-5 5H8l-5-5V8z" /><path d="M9 9l6 6M15 9l-6 6" /></>,
    question: <><circle cx="12" cy="12" r="9" /><path d="M9.5 9.5a2.5 2.5 0 114 2c-1 .6-1.5 1.2-1.5 2.5M12 17v.01" /></>,
    gap: <><circle cx="12" cy="12" r="9" strokeDasharray="3 3" /><path d="M8 12h8" /></>,
    search: <><circle cx="11" cy="11" r="6.5" /><path d="M16 16l4.5 4.5" /></>,
    scan: <><path d="M4 8V5a1 1 0 011-1h3M16 4h3a1 1 0 011 1v3M20 16v3a1 1 0 01-1 1h-3M8 20H5a1 1 0 01-1-1v-3" /><path d="M7 12h10" /></>,
    camera: <><path d="M4 8h3l2-3h6l2 3h3v11H4z" /><circle cx="12" cy="13" r="3.5" /></>,
    swap: <><path d="M7 7h12l-3-3M17 17H5l3 3" /></>,
    layers: <><path d="M12 3l9 5-9 5-9-5z" /><path d="M3 13l9 5 9-5" /></>,
    close: <path d="M6 6l12 12M18 6L6 18" />,
    up: <path d="M12 19V5M6 11l6-6 6 6" />,
    down: <path d="M12 5v14M6 13l6 6 6-6" />,
    trash: <><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13" /></>,
    link: <><path d="M10 14a4 4 0 005.7 0l3-3a4 4 0 00-5.7-5.7l-1 1" /><path d="M14 10a4 4 0 00-5.7 0l-3 3a4 4 0 005.7 5.7l1-1" /></>,
    bookmark: <path d="M6 4h12v16l-6-4-6 4z" />,
    plus: <path d="M12 5v14M5 12h14" />,
    menu: <path d="M4 7h16M4 12h16M4 17h16" />,
  };
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round"
         strokeLinejoin="round" className={className} aria-hidden="true">{p[name]}</svg>
  );
}

const toneClass: Record<string, string> = {
  clear: "text-clear bg-mist", caution: "text-caution bg-caution-bg", strong: "text-strong bg-strong-bg",
  unknown: "text-unknown bg-unknown-bg",
};

export function StatusPill({ status }: { status: StatusKey }) {
  const s = STATUS[status];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-semibold ${toneClass[s.tone]}`}>
      <Icon name={s.icon} className="size-4" />{s.short}
    </span>
  );
}

export function severityTone(sev: string) {
  return sev === "strong_caution" ? "strong" : sev === "caution" ? "caution" : "unknown";
}

/** Confidence: how sure the system is. Shown as a meter + label. */
export function ConfidenceBadge({ value, level, label = "Confidence" }: { value: number; level?: string; label?: string }) {
  const lvl = level ?? (value >= 0.85 ? "high" : value >= 0.6 ? "moderate" : "low");
  return (
    <div className="min-w-[9rem]">
      <div className="flex items-baseline justify-between gap-2 text-sm">
        <span className="text-ink-soft">{label}</span>
        <span className="font-semibold">{CONFIDENCE_LABEL[lvl]}</span>
      </div>
      <meter className="conf mt-1 block" min={0} max={1} low={0.6} high={0.85} optimum={1} value={value}
             aria-label={`${label}: ${CONFIDENCE_LABEL[lvl]} (${Math.round(value * 100)}%)`} />
    </div>
  );
}

/** Evidence strength: how well supported the science is. Deliberately a different shape from confidence. */
export function EvidenceBadge({ strength }: { strength: string }) {
  const steps = ["insufficient", "limited", "moderate", "high"];
  const filled = steps.indexOf(strength) + 1;
  return (
    <div className="min-w-[9rem]">
      <div className="flex items-baseline justify-between gap-2 text-sm">
        <span className="text-ink-soft">Evidence</span>
        <span className="font-semibold">{STRENGTH_LABEL[strength] ?? "Unknown"}</span>
      </div>
      <div className="mt-1 flex gap-1" aria-hidden="true">
        {steps.map((s, i) => (
          <span key={s} className={`h-2 flex-1 rounded-sm ${i < filled ? "bg-ink" : "bg-mist"}`} />
        ))}
      </div>
    </div>
  );
}

export function DemoBadge({ children = "DEMO: fictional data, not science" }: { children?: ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full bg-demo-bg px-2.5 py-0.5 text-xs font-semibold text-demo">
      {children}
    </span>
  );
}

export function Loading({ label = "Loading" }: { label?: string }) {
  return (
    <div role="status" aria-live="polite" className="py-10">
      <span className="sr-only">{label}</span>
      <div className="space-y-3" aria-hidden="true">
        {[0, 1, 2].map((i) => <div key={i} className="h-5 animate-pulse rounded bg-mist" />)}
      </div>
    </div>
  );
}

export function Empty({ title, children, action }: { title: string; children?: ReactNode; action?: ReactNode }) {
  return (
    <div className="rounded-2xl border border-dashed border-line px-6 py-10">
      <p className="text-lg font-semibold">{title}</p>
      {children && <div className="mt-1 max-w-prose text-ink-soft">{children}</div>}
      {action && <div className="mt-4 flex flex-wrap gap-2">{action}</div>}
    </div>
  );
}

export function ErrorState({ error, retry }: { error: unknown; retry?: () => void }) {
  const e = error as { message?: string; requestId?: string; code?: string };
  return (
    <div role="alert" className="rounded-2xl bg-strong-bg px-5 py-4 text-strong">
      <p className="font-semibold">{e?.message ?? "Something went wrong."}</p>
      {e?.requestId && <p className="mt-1 text-sm">Reference: {e.requestId}</p>}
      {retry && <button className="btn btn-quiet mt-3" onClick={retry}>Try again</button>}
    </div>
  );
}

export function Notice({ children, tone = "mist" }: { children: ReactNode; tone?: "mist" | "caution" | "demo" }) {
  const t = { mist: "bg-mist text-ink", caution: "bg-caution-bg text-ink", demo: "bg-demo-bg text-ink" }[tone];
  return <div className={`rounded-xl px-4 py-3 text-sm ${t}`}>{children}</div>;
}

export function PageTitle({ title, lead, children }: { title: string; lead?: ReactNode; children?: ReactNode }) {
  return (
    <header className="mb-8 max-w-3xl">
      <h1 className="text-4xl font-extrabold sm:text-5xl">{title}</h1>
      {lead && <p className="mt-3 text-lg text-ink-soft">{lead}</p>}
      {children}
    </header>
  );
}

export function TextLink({ href, children }: { href: string; children: ReactNode }) {
  return <Link href={href} className="font-semibold text-dropper underline decoration-2 underline-offset-4 hover:text-dropper-deep">{children}</Link>;
}
