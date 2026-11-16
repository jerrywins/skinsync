"use client";

import { useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { RequireAuth } from "@/components/RequireAuth";
import { ErrorState, Notice, PageTitle } from "@/components/ui";
import { analyticsConsent, setAnalyticsConsent } from "@/lib/analytics";
import { api } from "@/lib/api";
import type { Me } from "@/lib/types";

function Privacy({ me }: { me: Me }) {
  const qc = useQueryClient();
  const router = useRouter();
  const [counting, setCounting] = useState(analyticsConsent() === true);
  const [pw, setPw] = useState("");
  const [confirm, setConfirm] = useState("");
  const [err, setErr] = useState<unknown>(null);
  const toggle = async (v: boolean) => {
    setCounting(v); setAnalyticsConsent(v);
    await api("/me/consents", { body: { purpose: "analytics", granted: v } }).catch(() => undefined);
  };
  const del = async (e: React.FormEvent) => {
    e.preventDefault(); setErr(null);
    try {
      await api("/me", { method: "DELETE", body: { password: pw, confirm } });
      qc.clear(); router.push("/?deleted=1");
    } catch (e2) { setErr(e2); }
  };
  return (
    <div className="max-w-2xl space-y-10">
      <PageTitle title="Privacy and data" lead={`Signed in as ${me.email}.`} />
      <section className="space-y-3">
        <h2 className="text-xl font-bold">What we keep</h2>
        <ul className="list-disc space-y-1 pl-5">
          <li>Your email, password hash, profile and preferences.</li>
          <li>Your shelf, routines, saved comparisons and alternative searches.</li>
          <li>Skin analysis results. Photos are deleted after analysis unless you chose to keep them (30 days at most).</li>
        </ul>
        <p className="text-sm text-ink-soft">Details are in the <Link className="underline" href="/privacy">privacy notice</Link>. Individual results can be deleted from <Link className="underline" href="/history">History</Link>.</p>
      </section>
      <section className="space-y-3">
        <h2 className="text-xl font-bold">Usage counting</h2>
        <label className="flex gap-3"><input type="checkbox" className="mt-0.5 size-5 accent-[var(--color-dropper)]" checked={counting} onChange={(e) => toggle(e.target.checked)} />
          Allow anonymous feature counting (page and button events only, no personal or skin data).</label>
      </section>
      <section className="space-y-3 rounded-2xl border-2 border-strong/40 p-5">
        <h2 className="text-xl font-bold">Delete my account</h2>
        <p>This permanently deletes your account, profile, shelf, routines, saved results, skin analyses, stored photos and share links. It can&apos;t be undone.</p>
        <form onSubmit={del} className="space-y-3">
          <div><label htmlFor="dpw" className="font-semibold">Your password</label>
            <input id="dpw" type="password" autoComplete="current-password" required className="field mt-1" value={pw} onChange={(e) => setPw(e.target.value)} /></div>
          <div><label htmlFor="dc" className="font-semibold">Type DELETE to confirm</label>
            <input id="dc" required className="field mt-1" value={confirm} onChange={(e) => setConfirm(e.target.value)} /></div>
          {err != null && <ErrorState error={err} />}
          <button className="btn bg-strong text-white hover:bg-strong/90" disabled={confirm !== "DELETE" || !pw}>Delete my account and data</button>
        </form>
        <Notice>An audit record that an account was deleted is kept without your email, as required to show the deletion happened.</Notice>
      </section>
    </div>
  );
}

export default function PrivacySettings() {
  return <RequireAuth>{(me) => <Privacy me={me} />}</RequireAuth>;
}
