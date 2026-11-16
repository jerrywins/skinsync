"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { use } from "react";
import { AlternativesResult } from "@/components/AlternativesResult";
import { Empty, ErrorState, Loading } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import type { AlternativesEnvelope } from "@/lib/types";

export default function AltResultPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const q = useQuery({ queryKey: ["alt", id], queryFn: () => api<AlternativesEnvelope>(`/alternatives/${id}`) });
  if (q.isLoading) return <Loading label="Loading alternatives" />;
  if (q.error instanceof ApiError && q.error.status === 404)
    return <Empty title="These results aren't available" action={<Link className="btn btn-primary" href="/alternatives">Start a new search</Link>}>They may have been deleted, or belong to another account.</Empty>;
  if (q.error) return <ErrorState error={q.error} retry={() => q.refetch()} />;
  return <AlternativesResult data={q.data!} />;
}
