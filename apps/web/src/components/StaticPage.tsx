import type { ReactNode } from "react";

export function StaticPage({ title, lead, children }: { title: string; lead?: string; children: ReactNode }) {
  return (
    <article className="max-w-[68ch]">
      <h1 className="text-4xl font-extrabold sm:text-5xl">{title}</h1>
      {lead && <p className="mt-3 text-lg text-ink-soft">{lead}</p>}
      <div className="prose-ui mt-8 leading-relaxed">{children}</div>
    </article>
  );
}
