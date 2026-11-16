import Link from "next/link";
import { CompareForm } from "@/components/CompareForm";
import { Icon } from "@/components/ui";

export default function Home() {
  return (
    <div className="space-y-20">
      <section aria-labelledby="hero" className="grid gap-10 lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)] lg:items-start">
        <div className="lg:pt-6">
          <h1 id="hero" className="text-display font-extrabold">Check before you layer.</h1>
          <p className="mt-5 max-w-md text-lg text-ink-soft">
            Pick two products and see what their ingredient lists say together: shared ingredients, known
            interactions, and what we simply don&apos;t know yet. No account needed.
          </p>
          <p className="mt-4 max-w-md text-sm text-ink-soft">
            SkinSync describes cosmetic products and visible skin features. It does not diagnose or treat any condition.
          </p>
        </div>
        <CompareForm />
      </section>

      <section aria-labelledby="more" className="grid gap-px overflow-hidden rounded-2xl border border-line bg-line md:grid-cols-3">
        <h2 id="more" className="sr-only">Other things you can do</h2>
        {[
          { href: "/analyze", icon: "camera", title: "Analyze my skin",
            body: "Upload a photo to see visible features such as shine or uneven tone, with how sure we are about each." },
          { href: "/alternatives", icon: "swap", title: "Find alternatives",
            body: "See cheaper, similar or pricier options with closely matching ingredients, and why each one was picked." },
          { href: "/scan", icon: "scan", title: "Scan a label",
            body: "Photograph a barcode or an ingredient list. You check what we read before anything is used." },
        ].map((t) => (
          <Link key={t.href} href={t.href} className="group bg-sheet p-6 hover:bg-mist">
            <Icon name={t.icon} className="size-6 text-dropper" />
            <p className="mt-3 text-lg font-bold group-hover:underline">{t.title}</p>
            <p className="mt-1 text-ink-soft">{t.body}</p>
          </Link>
        ))}
      </section>

      <section aria-labelledby="trust" className="grid gap-10 md:grid-cols-[1fr_2fr]">
        <h2 id="trust" className="text-2xl font-extrabold">What you can rely on, and what you can&apos;t</h2>
        <div className="grid gap-6 sm:grid-cols-2">
          {[
            ["Every result shows its sources", "Each finding lists the rule, the evidence behind it, and the knowledge version used."],
            ["Confidence and evidence are separate", "How sure we are about the data is shown apart from how strong the science is."],
            ["Unknown stays unknown", "An ingredient we can't recognise is marked, never assumed harmless."],
            ["Product data has a date", "Formulations change. Results name the version and tell you when they go out of date."],
          ].map(([t, b]) => (
            <div key={t}>
              <p className="font-bold">{t}</p>
              <p className="mt-1 text-ink-soft">{b}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
