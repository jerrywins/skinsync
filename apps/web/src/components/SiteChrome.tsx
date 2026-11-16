"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { analyticsConsent, setAnalyticsConsent, track } from "@/lib/analytics";
import { useMe, useSignOut } from "./providers";
import { Icon } from "./ui";

const PRIMARY = [
  { href: "/analyze", label: "Analyze skin" },
  { href: "/compare", label: "Compare" },
  { href: "/alternatives", label: "Alternatives" },
  { href: "/products", label: "Products" },
  { href: "/ingredients", label: "Ingredients" },
];
const MINE = [
  { href: "/shelf", label: "My Shelf" },
  { href: "/routines", label: "Routines" },
  { href: "/history", label: "History" },
];

export function SiteHeader() {
  const path = usePathname();
  const me = useMe();
  const signOut = useSignOut();
  const [open, setOpen] = useState(false);
  useEffect(() => setOpen(false), [path]);
  const links = [...PRIMARY, ...(me.data ? MINE : [])];
  const mobileLinks = [...links, { href: "/scan", label: "Scan a product" }];
  const isActive = (h: string) => path === h || path.startsWith(`${h}/`);
  return (
    <header className="border-b border-line bg-paper/95 backdrop-blur supports-[backdrop-filter]:bg-paper/80 sticky top-0 z-30">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-3 focus:z-50 focus:rounded focus:bg-sheet focus:px-3 focus:py-2">Skip to content</a>
      <div className="mx-auto flex max-w-6xl items-center gap-6 px-4 py-3 sm:px-6">
        <Link href="/" className="flex items-center gap-2 text-xl font-extrabold tracking-tight" aria-label="SkinSync home">
          <span aria-hidden="true" className="grid size-8 place-items-center rounded-full bg-ink text-paper"><Icon name="layers" className="size-4" /></span>
          SkinSync
        </Link>
        <nav aria-label="Main" className="hidden flex-1 lg:block">
          <ul className="flex flex-wrap gap-1">
            {links.map((l) => (
              <li key={l.href}>
                <Link href={l.href} aria-current={isActive(l.href) ? "page" : undefined}
                      className={`rounded-full px-3 py-2 text-sm font-medium hover:bg-mist ${isActive(l.href) ? "bg-ink text-paper hover:bg-ink" : ""}`}>
                  {l.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
        <div className="ml-auto flex items-center gap-2">
          <Link href="/scan" className="btn btn-quiet hidden min-h-10 px-3 text-sm sm:inline-flex"><Icon name="scan" className="size-4" />Scan</Link>
          {me.data ? (
            <details className="relative">
              <summary className="btn btn-quiet min-h-10 cursor-pointer list-none px-3 text-sm">Account</summary>
              <div className="absolute right-0 mt-2 w-56 rounded-xl border border-line bg-sheet p-2 shadow-lg">
                <p className="truncate px-3 py-2 text-xs text-ink-soft">{me.data.email}</p>
                <Link className="block rounded-lg px-3 py-2 text-sm hover:bg-mist" href="/profile">Profile</Link>
                <Link className="block rounded-lg px-3 py-2 text-sm hover:bg-mist" href="/settings/privacy">Privacy and data</Link>
                {me.data.role === "admin" && <Link className="block rounded-lg px-3 py-2 text-sm hover:bg-mist" href="/admin">Admin</Link>}
                <button className="block w-full rounded-lg px-3 py-2 text-left text-sm hover:bg-mist" onClick={signOut}>Sign out</button>
              </div>
            </details>
          ) : (
            <Link href={`/auth/signin?next=${encodeURIComponent(path)}`} className="btn btn-primary min-h-10 whitespace-nowrap px-4 text-sm">Sign in</Link>
          )}
          <button className="btn btn-quiet min-h-10 px-3 lg:hidden" aria-expanded={open} aria-controls="mobile-nav"
                  onClick={() => setOpen((o) => !o)}>
            <Icon name={open ? "close" : "menu"} /><span className="sr-only">Menu</span>
          </button>
        </div>
      </div>
      {open && (
        <nav id="mobile-nav" aria-label="Main" className="border-t border-line px-4 pb-4 lg:hidden">
          <ul className="grid gap-1 pt-2">
            {mobileLinks.map((l) => (
              <li key={l.href}>
                <Link href={l.href} aria-current={isActive(l.href) ? "page" : undefined}
                      className="block rounded-lg px-3 py-2.5 font-medium hover:bg-mist">{l.label}</Link>
              </li>
            ))}
          </ul>
        </nav>
      )}
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="mt-24 border-t border-line">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-10 text-sm sm:px-6 md:grid-cols-[2fr_1fr_1fr]">
        <div className="max-w-md">
          <p className="font-bold">SkinSync</p>
          <p className="mt-2 text-ink-soft">
            Cosmetic decision support, not medical advice. Results describe our current knowledge base and the
            formulations we hold, never universal safety.
          </p>
          <p className="mt-3 text-ink-soft">
            Product data from <a className="underline" href="https://world.openbeautyfacts.org">Open Beauty Facts</a>,
            available under the Open Database License. <Link className="underline" href="/data-sources">Data sources</Link>
          </p>
        </div>
        <nav aria-label="About">
          <ul className="space-y-2">
            <li><Link href="/how-it-works" className="hover:underline">How it works</Link></li>
            <li><Link href="/methodology" className="hover:underline">Evidence and methodology</Link></li>
            <li><Link href="/safety" className="hover:underline">Safety and medical boundary</Link></li>
            <li><Link href="/about" className="hover:underline">About</Link></li>
          </ul>
        </nav>
        <nav aria-label="Legal">
          <ul className="space-y-2">
            <li><Link href="/privacy" className="hover:underline">Privacy</Link></li>
            <li><Link href="/terms" className="hover:underline">Terms</Link></li>
            <li><Link href="/data-sources" className="hover:underline">Data sources and licences</Link></li>
          </ul>
        </nav>
      </div>
    </footer>
  );
}

export function AnalyticsConsent() {
  const [state, setState] = useState<boolean | null | undefined>(undefined);
  const path = usePathname();
  useEffect(() => setState(analyticsConsent()), []);
  useEffect(() => { if (path === "/") track("landing_view"); }, [path]);
  if (state !== null) return null;
  const choose = (yes: boolean) => { setAnalyticsConsent(yes); setState(yes); };
  return (
    <div role="region" aria-label="Analytics choice"
         className="fixed inset-x-3 bottom-3 z-40 mx-auto max-w-xl rounded-2xl border border-line bg-sheet p-4 shadow-xl sm:inset-x-auto sm:right-4">
      <p className="text-sm">
        May we count which features are used? We record page and button events only, with no personal details
        and nothing about your skin. Essential cookies for signing in are always on.
      </p>
      <div className="mt-3 flex gap-2">
        <button className="btn btn-primary min-h-10 text-sm" onClick={() => choose(true)}>Allow counting</button>
        <button className="btn btn-quiet min-h-10 text-sm" onClick={() => choose(false)}>No thanks</button>
      </div>
    </div>
  );
}
