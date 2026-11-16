"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { PhotoInput } from "@/components/PhotoInput";
import { ProductRow } from "@/components/ProductCard";
import { ErrorState, Icon, Notice, PageTitle } from "@/components/ui";
import { api, ApiError, type NormalizedIngredient } from "@/lib/api";
import { pollHeaders, savePollToken } from "@/lib/poll";
import type { ProductSummary } from "@/lib/types";

type Lookup = { status: "found" | "ambiguous" | "not_found"; candidates: ProductSummary[] };

function BarcodeScanner({ onCode }: { onCode: (c: string) => void }) {
  const video = useRef<HTMLVideoElement>(null);
  const [state, setState] = useState<"idle" | "starting" | "scanning" | "denied" | "unsupported">("idle");
  const stopRef = useRef<() => void>(() => undefined);
  useEffect(() => () => stopRef.current(), []);
  const start = async () => {
    setState("starting");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
      const v = video.current!;
      v.srcObject = stream; await v.play();
      setState("scanning");
      let stopped = false;
      stopRef.current = () => { stopped = true; stream.getTracks().forEach((t) => t.stop()); };
      const Native = (window as unknown as { BarcodeDetector?: new (o: object) => { detect: (s: CanvasImageSource) => Promise<{ rawValue: string }[]> } }).BarcodeDetector;
      if (Native) {
        const det = new Native({ formats: ["ean_13", "ean_8", "upc_a", "upc_e"] });
        const loop = async () => {
          if (stopped) return;
          const found = await det.detect(v).catch(() => []);
          if (found[0]) { stopRef.current(); setState("idle"); onCode(found[0].rawValue); return; }
          setTimeout(loop, 250);
        };
        loop();
      } else {
        const { BrowserMultiFormatReader } = await import("@zxing/browser");
        const reader = new BrowserMultiFormatReader();
        const controls = await reader.decodeFromVideoElement(v, (res) => {
          if (res && !stopped) { controls.stop(); stopRef.current(); setState("idle"); onCode(res.getText()); }
        });
        const prev = stopRef.current;
        stopRef.current = () => { controls.stop(); prev(); };
      }
    } catch {
      setState("denied");
    }
  };
  return (
    <div className="space-y-3">
      <video ref={video} playsInline muted className={state === "scanning" ? "w-full max-w-md rounded-2xl bg-ink" : "hidden"} aria-label="Camera preview" />
      {state === "scanning" ? (
        <div className="flex items-center gap-3" role="status" aria-live="polite"><span>Point the camera at the barcode…</span>
          <button className="btn btn-quiet min-h-9 text-sm" onClick={() => { stopRef.current(); setState("idle"); }}>Stop</button></div>
      ) : (
        <button className="btn btn-primary" onClick={start} disabled={state === "starting"}><Icon name="camera" className="size-4" />{state === "starting" ? "Starting camera…" : "Scan with camera"}</button>
      )}
      {state === "denied" && <p role="alert" className="text-sm text-strong">The camera isn&apos;t available or access was blocked. Type the barcode digits below instead.</p>}
    </div>
  );
}

export function ScanFlow() {
  const [code, setCode] = useState("");
  const [lookup, setLookup] = useState<Lookup | null>(null);
  const [err, setErr] = useState<unknown>(null);
  const [scanId, setScanId] = useState<string | null>(null);
  const [ocr, setOcr] = useState<{ status: string; raw_text: string; mean_confidence: number; needs_review: boolean; notice: string; ingredients: NormalizedIngredient[] } | null>(null);
  const [text, setText] = useState("");
  const [confirmed, setConfirmed] = useState<{ resolved: number; total: number; ingredients: NormalizedIngredient[]; product_candidates: { product_id: string; slug: string; name: string; brand: string | null; ingredient_match: number }[] } | null>(null);
  const [busy, setBusy] = useState(false);

  const find = async (c: string) => {
    setCode(c); setErr(null); setLookup(null);
    try { setLookup(await api<Lookup>(`/products/barcode/${encodeURIComponent(c.trim())}`)); } catch (e) { setErr(e); }
  };
  const upload = async (f: File) => {
    setBusy(true); setErr(null); setOcr(null); setConfirmed(null);
    try {
      const form = new FormData(); form.set("image", f);
      const r = await api<{ id: string; poll_token: string }>("/scan/label", { form });
      savePollToken(r.id, r.poll_token); setScanId(r.id);
    } catch (e) { setErr(e); setBusy(false); }
  };
  useEffect(() => {
    if (!scanId) return;
    let t: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const r = await api<NonNullable<typeof ocr>>(`/scan/label/${scanId}`, { headers: pollHeaders(scanId) });
        if (r.status === "processing") { t = setTimeout(poll, 1200); return; }
        setOcr(r); setText(r.raw_text); setBusy(false);
      } catch (e) { setErr(e); setBusy(false); }
    };
    poll();
    return () => clearTimeout(t);
  }, [scanId]);
  const confirm = async () => {
    try { setConfirmed(await api(`/scan/label/${scanId}/confirm`, { body: { text }, headers: pollHeaders(scanId!) })); }
    catch (e) { setErr(e); }
  };

  return (
    <div className="max-w-3xl space-y-10">
      <PageTitle title="Scan a product" lead="Use the barcode to find a product we know, or photograph the ingredient list. You always check what we read." />
      <section aria-labelledby="bc-h" className="sheet space-y-4 p-5 sm:p-7">
        <h2 id="bc-h" className="text-xl font-bold">Barcode</h2>
        <BarcodeScanner onCode={find} />
        <form onSubmit={(e) => { e.preventDefault(); find(code); }} className="flex max-w-md gap-2">
          <label htmlFor="bc" className="sr-only">Barcode digits</label>
          <input id="bc" inputMode="numeric" pattern="[0-9]{6,14}" className="field" placeholder="Or type the digits" value={code} onChange={(e) => setCode(e.target.value)} />
          <button className="btn btn-quiet">Look up</button>
        </form>
        {lookup?.status === "not_found" && <Notice tone="caution">We don&apos;t have this barcode yet. Photograph the ingredient list below, or search by name.</Notice>}
        {lookup?.status === "ambiguous" && <Notice>This barcode matches more than one product. Choose yours:</Notice>}
        {lookup && lookup.candidates.length > 0 && <ul>{lookup.candidates.map((p) => <ProductRow key={p.id} p={p} />)}</ul>}
      </section>

      <section aria-labelledby="lb-h" className="sheet space-y-4 p-5 sm:p-7">
        <h2 id="lb-h" className="text-xl font-bold">Ingredient label</h2>
        <p className="text-sm text-ink-soft">Photograph the ingredient list flat and in good light. The photo is deleted after the text is read.</p>
        <PhotoInput onPhoto={upload} facing="environment" label="Ingredient label photo" />
        {busy && <p role="status" aria-live="polite">Reading the label…</p>}
        {ocr && (
          <div className="space-y-3">
            {ocr.status === "failed" ? <ErrorState error={{ message: "We couldn't read this photo. Try a sharper, flatter photo, or type the list." }} /> : (
              <>
                <Notice tone={ocr.needs_review ? "caution" : "mist"}>
                  {ocr.needs_review ? "Parts of this were hard to read. " : ""}{ocr.notice}
                </Notice>
                <label htmlFor="ocr-text" className="font-semibold">Text we read: correct anything that&apos;s wrong</label>
                <textarea id="ocr-text" className="field label-voice min-h-40" value={text} onChange={(e) => setText(e.target.value)} />
                <button className="btn btn-primary" onClick={confirm} disabled={!text.trim()}>This is correct</button>
              </>
            )}
          </div>
        )}
        {confirmed && (
          <div className="space-y-3">
            <p className="font-semibold">{confirmed.resolved} of {confirmed.total} ingredients recognised.</p>
            <ul className="label-voice flex flex-wrap gap-x-1">
              {confirmed.ingredients.map((i) => (
                <li key={i.position} className="after:content-[','] last:after:content-['']">
                  {i.canonical_id ? i.inci_name : <span className="text-unknown line-through" title={i.candidate ? `Possible match: ${i.candidate}` : undefined}>{i.raw}?</span>}
                  {!i.canonical_id && i.candidate && <span className="font-sans text-xs text-ink-soft"> (maybe {i.candidate})</span>}
                </li>
              ))}
            </ul>
            {confirmed.product_candidates.length > 0 && (
              <div>
                <p className="font-semibold">Is it one of these?</p>
                <p className="text-sm text-ink-soft">These have similar ingredient lists. Pick one only if it really is your product.</p>
                <ul className="mt-2 space-y-1">
                  {confirmed.product_candidates.map((c) => (
                    <li key={c.product_id}><Link className="font-semibold text-dropper hover:underline" href={`/products/${c.slug}`}>{c.name}</Link>
                      <span className="text-sm text-ink-soft"> {c.brand}, {Math.round(c.ingredient_match * 100)}% ingredient match</span></li>
                  ))}
                </ul>
              </div>
            )}
            <Link className="btn btn-quiet" href="/compare?from=scan"
                  onClick={() => { try { sessionStorage.setItem("ss_manual_a", text); } catch { /* unavailable */ } }}>
              Compare this list with a product</Link>
          </div>
        )}
      </section>
      {err != null && <ErrorState error={err instanceof ApiError ? err : { message: "Something went wrong." }} />}
    </div>
  );
}
