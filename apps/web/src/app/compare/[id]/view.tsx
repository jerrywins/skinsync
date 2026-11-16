"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { CompareResult } from "@/components/CompareResult";
import { Empty, ErrorState, Loading } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import type { ComparisonEnvelope } from "@/lib/types";

export function CompareView({ id }: { id: string }) {
  const q = useQuery({ queryKey: ["comparison", id], queryFn: () => api<ComparisonEnvelope>(`/comparisons/${id}`) });
  if (q.isLoading) return <Loading label="Loading comparison" />;
  if (q.error instanceof ApiError && q.error.status === 404) {
    return <Empty title="This comparison isn't available" action={<Link className="btn btn-primary" href="/compare">Start a new comparison</Link>}>
      It may have been deleted, or it belongs to another account.
    </Empty>;
  }
  if (q.error) return <ErrorState error={q.error} retry={() => q.refetch()} />;
  return <CompareResult data={q.data!} />;
}
