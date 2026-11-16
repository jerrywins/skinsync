"use client";

import Link from "next/link";
import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import { track } from "@/lib/analytics";
import { useMe } from "./providers";
import { Icon } from "./ui";

export function ProductActions({ id, name }: { id: string; name: string }) {
  const me = useMe();
  const [msg, setMsg] = useState<string | null>(null);
  const add = async (status: "owned" | "wishlist") => {
    try {
      await api("/shelf", { body: { product_id: id, status } });
      setMsg(status === "owned" ? `Added ${name} to My Shelf.` : `Added ${name} to your wishlist.`);
      track("product_saved", { kind: "shelf" });
    } catch (e) {
      setMsg(e instanceof ApiError ? e.message : "Could not add it. Try again.");
    }
  };
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        <Link className="btn btn-primary" href={`/compare?a=${id}`}><Icon name="layers" className="size-4" />Compare with another product</Link>
        <Link className="btn btn-quiet" href={`/alternatives?ref=${id}`}><Icon name="swap" className="size-4" />Find alternatives</Link>
        {me.data ? (
          <>
            <button className="btn btn-quiet" onClick={() => add("owned")}><Icon name="bookmark" className="size-4" />Add to My Shelf</button>
            <button className="btn btn-quiet" onClick={() => add("wishlist")}>Add to wishlist</button>
          </>
        ) : (
          <Link className="btn btn-quiet" href={`/auth/signin?next=/products`}>Sign in to save</Link>
        )}
      </div>
      {msg && <p role="status" className="text-sm text-ink-soft">{msg}</p>}
    </div>
  );
}

export function ReportData({ targetType, targetRef }: { targetType: "product" | "product_version" | "ingredient"; targetRef: string }) {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");
  const [done, setDone] = useState<string | null>(null);
  const send = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api("/reports", { body: { target_type: targetType, target_ref: targetRef, message: text } });
      setDone("Thanks. A reviewer will check it.");
      setOpen(false);
    } catch (err) {
      setDone(err instanceof ApiError ? err.message : "Could not send the report.");
    }
  };
  return (
    <div className="text-sm">
      {!open && <button className="font-semibold text-dropper underline underline-offset-4" onClick={() => setOpen(true)}>Report incorrect data</button>}
      {open && (
        <form onSubmit={send} className="mt-2 max-w-lg space-y-2">
          <label htmlFor="report" className="font-semibold">What looks wrong?</label>
          <textarea id="report" className="field min-h-20" required minLength={3} maxLength={1000} value={text}
                    onChange={(e) => setText(e.target.value)} />
          <div className="flex gap-2">
            <button className="btn btn-primary min-h-10 text-sm">Send report</button>
            <button type="button" className="btn btn-quiet min-h-10 text-sm" onClick={() => setOpen(false)}>Cancel</button>
          </div>
        </form>
      )}
      {done && <p role="status" className="mt-2 text-ink-soft">{done}</p>}
    </div>
  );
}
