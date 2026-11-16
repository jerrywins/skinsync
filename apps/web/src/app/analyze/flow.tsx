"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { PhotoInput } from "@/components/PhotoInput";
import { useMe } from "@/components/providers";
import { ErrorState, Notice, PageTitle } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { track } from "@/lib/analytics";
import { SKIN_TYPES } from "@/lib/format";
import { savePollToken } from "@/lib/poll";

export function AnalyzeFlow() {
  const router = useRouter();
  const me = useMe();
  const [step, setStep] = useState(1);
  const [skinType, setSkinType] = useState("unsure");
  const [consent, setConsent] = useState(false);
  const [keep, setKeep] = useState(false);
  const [photo, setPhoto] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<ApiError | null>(null);

  const submit = async () => {
    if (!photo) return;
    setBusy(true); setErr(null);
    const form = new FormData();
    form.set("image", photo); form.set("skin_type", skinType); form.set("consent", String(consent));
    form.set("keep_image", String(keep && !!me.data));
    track("skin_image_uploaded");
    try {
      const r = await api<{ id: string; poll_token: string | null }>("/skin-analyses", { form });
      savePollToken(r.id, r.poll_token);
      router.push(`/analyze/${r.id}`);
    } catch (e) {
      if (e instanceof ApiError && e.status === 422) track("skin_image_quality_failed", { code: e.code });
      setErr(e instanceof ApiError ? e : new ApiError(0, "UNKNOWN", "Upload failed. Try again."));
      setBusy(false);
    }
  };

  return (
    <div className="max-w-3xl">
      <PageTitle title="What does my skin appear to need?"
                 lead="We look for visible cosmetic features in one photo, such as shine or uneven tone, and say how sure we are about each." />
      <Notice>
        This is not a medical diagnosis and does not detect any condition. Lighting, camera quality, makeup, filters and
        angle all change the result. For persistent or worrying skin problems, see a qualified professional.
      </Notice>
      <ol className="mt-8 space-y-6" aria-label="Steps">
        <li className={`sheet p-5 ${step === 1 ? "" : "opacity-70"}`} aria-current={step === 1 ? "step" : undefined}>
          <h2 className="text-lg font-bold">1. Your skin type</h2>
          <fieldset className="mt-3" disabled={step !== 1}>
            <legend className="sr-only">Skin type</legend>
            <div className="flex flex-wrap gap-2">
              {SKIN_TYPES.map((t) => (
                <label key={t.id} className={`cursor-pointer rounded-full border-2 px-4 py-2 text-sm font-medium ${skinType === t.id ? "border-dropper bg-mist" : "border-line"}`}>
                  <input type="radio" name="skin" value={t.id} className="sr-only" checked={skinType === t.id}
                         onChange={() => setSkinType(t.id)} />{t.label}
                </label>
              ))}
            </div>
          </fieldset>
          {step === 1 && <button className="btn btn-primary mt-4" onClick={() => { setStep(2); track("skin_analysis_started"); }}>Continue</button>}
        </li>

        <li className={`sheet p-5 ${step === 2 ? "" : step < 2 ? "opacity-40" : "opacity-70"}`} aria-current={step === 2 ? "step" : undefined}>
          <h2 className="text-lg font-bold">2. How we handle your photo</h2>
          {step >= 2 && (
            <div className="mt-3 space-y-3 text-sm">
              <ul className="list-disc space-y-1 pl-5">
                <li>The photo is checked, stripped of location and camera data, and encrypted before storage.</li>
                <li>It is deleted as soon as the analysis finishes{me.data ? ", unless you choose to keep it below" : ""}. Guest photos are always deleted.</li>
                <li>Results stay private. Skin analyses can never be shared through a link.</li>
                <li>We never use your photo to train any model.</li>
              </ul>
              <label className="flex gap-3">
                <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} disabled={step !== 2}
                       className="mt-0.5 size-5 accent-[var(--color-dropper)]" />
                <span>I agree to my photo being processed this way. I am 18 or older.</span>
              </label>
              {me.data && (
                <label className="flex gap-3">
                  <input type="checkbox" checked={keep} onChange={(e) => setKeep(e.target.checked)} disabled={step !== 2}
                         className="mt-0.5 size-5 accent-[var(--color-dropper)]" />
                  <span>Keep my photo for 30 days so I can see it with the result (you can delete it any time).</span>
                </label>
              )}
              {step === 2 && <button className="btn btn-primary" disabled={!consent} onClick={() => setStep(3)}>Continue</button>}
            </div>
          )}
        </li>

        <li className={`sheet p-5 ${step === 3 ? "" : "opacity-40"}`} aria-current={step === 3 ? "step" : undefined}>
          <h2 className="text-lg font-bold">3. Your photo</h2>
          {step === 3 && (
            <div className="mt-3 space-y-4">
              <ul className="grid gap-1 text-sm text-ink-soft sm:grid-cols-2">
                <li>Face a window or soft, even light</li><li>No beauty filters or heavy makeup</li>
                <li>Face the camera, nothing covering your face</li><li>Hold steady so the photo is sharp</li>
              </ul>
              <PhotoInput onPhoto={setPhoto} label="Skin photo" />
              {err && (
                <div role="alert">
                  <ErrorState error={err} />
                  {typeof err.details?.guidance === "string" && <p className="mt-2 text-sm">{err.details.guidance}</p>}
                </div>
              )}
              <button className="btn btn-primary" disabled={!photo || busy} onClick={submit}>{busy ? "Uploading…" : "Analyze photo"}</button>
            </div>
          )}
        </li>
      </ol>
      {!me.data && <p className="mt-6 text-sm text-ink-soft"><Link href="/auth/signin?next=/analyze" className="underline">Sign in</Link> to keep your results in your history.</p>}
    </div>
  );
}
