"use client";

import { useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { track } from "@/lib/analytics";
import { takeClaims } from "./providers";
import { ErrorState, Notice } from "./ui";

function safeNext(n: string | null) {
  return n && n.startsWith("/") && !n.startsWith("//") && !n.startsWith("/auth") ? n : "/";
}

export function SignInForm() {
  const router = useRouter();
  const sp = useSearchParams();
  const qc = useQueryClient();
  const [email, setEmail] = useState("");
  const [pw, setPw] = useState("");
  const [err, setErr] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);
  const [resent, setResent] = useState(false);
  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setBusy(true); setErr(null);
    try {
      await api("/auth/login", { body: { email, password: pw, claim_tokens: takeClaims() } });
      await qc.invalidateQueries({ queryKey: ["me"] });
      router.push(safeNext(sp.get("next")));
    } catch (e2) {
      setErr(e2 instanceof ApiError ? e2 : new ApiError(0, "X", "Sign-in failed."));
    } finally { setBusy(false); }
  };
  return (
    <form onSubmit={submit} className="sheet space-y-4 p-6" noValidate>
      <h1 className="text-3xl font-extrabold">Sign in</h1>
      <div><label htmlFor="em" className="font-semibold">Email</label>
        <input id="em" type="email" autoComplete="email" required className="field mt-1" value={email} onChange={(e) => setEmail(e.target.value)} /></div>
      <div><label htmlFor="pw" className="font-semibold">Password</label>
        <input id="pw" type="password" autoComplete="current-password" required className="field mt-1" value={pw} onChange={(e) => setPw(e.target.value)} /></div>
      {err && <ErrorState error={err} />}
      {err?.code === "EMAIL_NOT_VERIFIED" && (
        <button type="button" className="text-sm font-semibold text-dropper underline" disabled={resent}
                onClick={async () => { await api("/auth/resend-verification", { body: { email } }).catch(() => undefined); setResent(true); }}>
          {resent ? "Link sent again. Check your inbox." : "Send the confirmation link again"}
        </button>
      )}
      <button className="btn btn-primary w-full" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
      <p className="flex justify-between text-sm"><Link className="underline" href="/auth/forgot">Forgot password?</Link>
        <Link className="underline" href={`/auth/signup?next=${encodeURIComponent(sp.get("next") ?? "/")}`}>Create an account</Link></p>
    </form>
  );
}

export function SignUpForm() {
  const [email, setEmail] = useState("");
  const [pw, setPw] = useState("");
  const [age, setAge] = useState(false);
  const [terms, setTerms] = useState(false);
  const [err, setErr] = useState<unknown>(null);
  const [done, setDone] = useState(false);
  useEffect(() => track("signup_started"), []);
  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setErr(null);
    try {
      await api("/auth/signup", { body: { email, password: pw, age_confirmed_18: age, accept_terms: terms } });
      setDone(true); track("signup_completed");
    } catch (e2) { setErr(e2); }
  };
  if (done) return (
    <div className="sheet space-y-3 p-6" role="status">
      <h1 className="text-3xl font-extrabold">Check your email</h1>
      <p>If this address can be registered, we&apos;ve sent a confirmation link to <strong>{email}</strong>. Open it, then sign in. Results you saved as a guest in this tab will be added to your account.</p>
      <Link className="btn btn-primary" href="/auth/signin">Go to sign in</Link>
    </div>
  );
  return (
    <form onSubmit={submit} className="sheet space-y-4 p-6">
      <h1 className="text-3xl font-extrabold">Create an account</h1>
      <p className="text-ink-soft">Save results, keep a shelf of your products, and check your routines.</p>
      <div><label htmlFor="em" className="font-semibold">Email</label>
        <input id="em" type="email" autoComplete="email" required className="field mt-1" value={email} onChange={(e) => setEmail(e.target.value)} /></div>
      <div><label htmlFor="pw" className="font-semibold">Password</label>
        <input id="pw" type="password" autoComplete="new-password" required minLength={10} className="field mt-1" aria-describedby="pw-hint"
               value={pw} onChange={(e) => setPw(e.target.value)} />
        <p id="pw-hint" className="mt-1 text-sm text-ink-soft">At least 10 characters. Common passwords are refused.</p></div>
      <label className="flex gap-3"><input type="checkbox" className="mt-0.5 size-5 accent-[var(--color-dropper)]" checked={age} onChange={(e) => setAge(e.target.checked)} required />I am 18 or older.</label>
      <label className="flex gap-3"><input type="checkbox" className="mt-0.5 size-5 accent-[var(--color-dropper)]" checked={terms} onChange={(e) => setTerms(e.target.checked)} required />
        <span>I accept the <Link className="underline" href="/terms">terms</Link> and <Link className="underline" href="/privacy">privacy notice</Link>.</span></label>
      {err != null && <ErrorState error={err} />}
      <button className="btn btn-primary w-full" disabled={!age || !terms}>Create account</button>
      <p className="text-sm">Already have one? <Link className="underline" href="/auth/signin">Sign in</Link></p>
    </form>
  );
}

export function VerifyEmail() {
  const sp = useSearchParams();
  const [state, setState] = useState<"working" | "ok" | "bad">("working");
  useEffect(() => {
    const t = sp.get("token");
    if (!t) { setState("bad"); return; }
    api("/auth/verify-email", { body: { token: t } }).then(() => setState("ok")).catch(() => setState("bad"));
  }, [sp]);
  return (
    <div className="sheet space-y-3 p-6" role="status" aria-live="polite">
      <h1 className="text-3xl font-extrabold">{state === "ok" ? "Email confirmed" : state === "bad" ? "This link didn't work" : "Confirming…"}</h1>
      {state === "ok" && <Link className="btn btn-primary" href="/auth/signin">Sign in</Link>}
      {state === "bad" && <p>The link is invalid or has expired. Sign in and choose &ldquo;Send the confirmation link again&rdquo;.</p>}
    </div>
  );
}

export function ForgotForm() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  return sent ? (
    <div className="sheet p-6" role="status"><h1 className="text-3xl font-extrabold">Check your email</h1>
      <p className="mt-2">If an account exists for {email}, a reset link is on its way. It expires in 30 minutes.</p></div>
  ) : (
    <form className="sheet space-y-4 p-6" onSubmit={async (e) => { e.preventDefault(); await api("/auth/request-password-reset", { body: { email } }).catch(() => undefined); setSent(true); }}>
      <h1 className="text-3xl font-extrabold">Reset your password</h1>
      <div><label htmlFor="em" className="font-semibold">Email</label>
        <input id="em" type="email" required className="field mt-1" value={email} onChange={(e) => setEmail(e.target.value)} /></div>
      <button className="btn btn-primary w-full">Send reset link</button>
    </form>
  );
}

export function ResetForm() {
  const sp = useSearchParams();
  const [pw, setPw] = useState("");
  const [err, setErr] = useState<unknown>(null);
  const [ok, setOk] = useState(false);
  if (ok) return <div className="sheet space-y-3 p-6" role="status"><h1 className="text-3xl font-extrabold">Password changed</h1>
    <p>You have been signed out everywhere.</p><Link className="btn btn-primary" href="/auth/signin">Sign in</Link></div>;
  return (
    <form className="sheet space-y-4 p-6" onSubmit={async (e) => { e.preventDefault(); setErr(null);
      try { await api("/auth/reset-password", { body: { token: sp.get("token") ?? "", password: pw } }); setOk(true); } catch (e2) { setErr(e2); } }}>
      <h1 className="text-3xl font-extrabold">Choose a new password</h1>
      <div><label htmlFor="pw" className="font-semibold">New password</label>
        <input id="pw" type="password" autoComplete="new-password" minLength={10} required className="field mt-1" value={pw} onChange={(e) => setPw(e.target.value)} /></div>
      {err != null && <ErrorState error={err} />}
      <Notice>At least 10 characters. Common passwords are refused.</Notice>
      <button className="btn btn-primary w-full">Change password</button>
    </form>
  );
}
