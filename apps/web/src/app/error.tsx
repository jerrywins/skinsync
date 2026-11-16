"use client";

import { ErrorState } from "@/components/ui";

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <ErrorState error={{ message: "This page failed to load. Search and comparison may still work.", requestId: error.digest }} retry={reset} />;
}
