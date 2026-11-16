"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import { track } from "@/lib/analytics";
import { rememberClaim, useMe } from "./providers";
import { Icon } from "./ui";

/** Save / share actions. Shown only after a result is delivered (value first, account second). */
export function SaveShareBar({ kind, id, saved, saveable = true, claimToken, shareable = true }: {
  kind: "comparison" | "alternative_search"; id: string | null; saved: boolean; saveable?: boolean;
  claimToken?: string | null; shareable?: boolean;
}) {
  const me = useMe();
  const path = usePathname();
  const [isSaved, setSaved] = useState(saved);
  const [link, setLink] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  if (!id || !saveable) {
    return <p className="text-sm text-ink-soft">Results from typed ingredient lists are not saved.</p>;
  }
  const endpoint = kind === "comparison" ? `/comparisons/${id}/save` : `/alternatives/${id}/save`;
  const save = async () => {
    try {
      await api(endpoint, { method: "POST" });
      setSaved(true);
      setMsg("Saved to your history.");
      track("product_saved", { kind });
    } catch (e) {
      setMsg(e instanceof ApiError ? e.message : "Could not save. Try again.");
    }
  };
  const share = async () => {
    try {
      if (!isSaved) await api(endpoint, { method: "POST" });
      setSaved(true);
      const r = await api<{ url: string }>("/shares", { body: { target_type: kind, target_id: id } });
      setLink(r.url);
      track("share_created", { kind });
    } catch (e) {
      setMsg(e instanceof ApiError ? e.message : "Could not create a link. Try again.");
    }
  };
  if (me.isLoading) return null;
  if (!me.data) {
    return (
      <div className="rounded-xl border border-line bg-sheet p-4">
        <p className="font-semibold">Keep this result</p>
        <p className="text-sm text-ink-soft">Create a free account to save it, share it, and get told when it goes out of date.</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <Link className="btn btn-primary min-h-10 text-sm" href={`/auth/signup?next=${encodeURIComponent(path)}`}
                onClick={() => rememberClaim(claimToken)}>Create account and save</Link>
          <Link className="btn btn-quiet min-h-10 text-sm" href={`/auth/signin?next=${encodeURIComponent(path)}`}
                onClick={() => rememberClaim(claimToken)}>Sign in</Link>
        </div>
      </div>
    );
  }
  return (
    <div className="flex flex-wrap items-center gap-2">
      <button className="btn btn-quiet" onClick={save} disabled={isSaved}>
        <Icon name="bookmark" className="size-4" />{isSaved ? "Saved" : "Save result"}
      </button>
      {shareable && <button className="btn btn-quiet" onClick={share}><Icon name="link" className="size-4" />Create share link</button>}
      {link && (
        <div className="flex w-full flex-wrap items-center gap-2">
          <input className="field max-w-md text-sm" readOnly value={link} aria-label="Share link" onFocus={(e) => e.target.select()} />
          <button className="btn btn-quiet min-h-10 text-sm" onClick={() => navigator.clipboard?.writeText(link)}>Copy link</button>
          <span className="text-xs text-ink-soft">Anyone with the link can view it. You can revoke it in History.</span>
        </div>
      )}
      {msg && <p role="status" className="w-full text-sm text-ink-soft">{msg}</p>}
    </div>
  );
}
