"use client";

import { useEffect, useRef, useState } from "react";
import { Icon } from "./ui";

/** Upload or live camera capture. Camera denial always falls back to upload. */
export function PhotoInput({ onPhoto, facing = "user", label }: { onPhoto: (f: File) => void; facing?: "user" | "environment"; label: string }) {
  const [preview, setPreview] = useState<string | null>(null);
  const [camera, setCamera] = useState<"off" | "starting" | "on" | "denied">("off");
  const video = useRef<HTMLVideoElement>(null);
  const stream = useRef<MediaStream | null>(null);
  const stop = () => { stream.current?.getTracks().forEach((t) => t.stop()); stream.current = null; };
  useEffect(() => stop, []);
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);
  const pick = (f: File | undefined) => {
    if (!f) return;
    setPreview(URL.createObjectURL(f));
    onPhoto(f);
  };
  const start = async () => {
    setCamera("starting");
    try {
      stream.current = await navigator.mediaDevices.getUserMedia({ video: { facingMode: facing, width: { ideal: 1600 } } });
      if (video.current) { video.current.srcObject = stream.current; await video.current.play(); }
      setCamera("on");
    } catch {
      setCamera("denied");
    }
  };
  const capture = () => {
    const v = video.current;
    if (!v) return;
    const c = document.createElement("canvas");
    c.width = v.videoWidth; c.height = v.videoHeight;
    c.getContext("2d")!.drawImage(v, 0, 0);
    c.toBlob((b) => { if (b) pick(new File([b], "capture.jpg", { type: "image/jpeg" })); stop(); setCamera("off"); }, "image/jpeg", 0.92);
  };
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <label className="btn btn-primary cursor-pointer">
          <Icon name="plus" className="size-4" />Choose a photo
          <input type="file" accept="image/jpeg,image/png,image/webp" className="sr-only" aria-label={label}
                 onChange={(e) => pick(e.target.files?.[0])} />
        </label>
        {camera !== "on" && <button type="button" className="btn btn-quiet" onClick={start}><Icon name="camera" className="size-4" />Use camera</button>}
      </div>
      {camera === "denied" && <p role="alert" className="text-sm text-strong">Camera access was blocked or isn&apos;t available. You can choose a photo instead.</p>}
      <video ref={video} playsInline muted className={camera === "on" ? "w-full max-w-md rounded-2xl bg-ink" : "hidden"} aria-label="Camera preview" />
      {camera === "on" && <button type="button" className="btn btn-primary" onClick={capture}>Take photo</button>}
      {preview && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={preview} alt="Photo you selected" className="max-h-72 rounded-2xl border border-line object-contain" />
      )}
    </div>
  );
}
