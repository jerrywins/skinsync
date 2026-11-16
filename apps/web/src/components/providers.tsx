"use client";

import { QueryClient, QueryClientProvider, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { api, ApiError } from "@/lib/api";
import type { Me } from "@/lib/types";

export function Providers({ children }: { children: ReactNode }) {
  const [client] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        retry: (n, e) => !(e instanceof ApiError && e.status >= 400 && e.status < 500) && n < 2,
        refetchOnWindowFocus: false,
      },
    },
  }));
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      try {
        return await api<Me>("/me");
      } catch (e) {
        if (e instanceof ApiError && e.status === 401) return null;
        throw e;
      }
    },
    staleTime: 60_000,
  });
}

export function useSignOut() {
  const qc = useQueryClient();
  return async () => {
    await api("/auth/logout", { method: "POST" }).catch(() => undefined);
    qc.setQueryData(["me"], null);
    qc.removeQueries({ predicate: (q) => q.queryKey[0] !== "me" });
  };
}

/** Guest results that can be attached to an account at first sign-in. */
const CLAIMS = "ss_claims";
export function rememberClaim(token: string | null | undefined) {
  if (!token) return;
  try {
    const list: string[] = JSON.parse(sessionStorage.getItem(CLAIMS) ?? "[]");
    if (!list.includes(token)) sessionStorage.setItem(CLAIMS, JSON.stringify([...list, token].slice(-20)));
  } catch { /* storage unavailable */ }
}
export function takeClaims(): string[] {
  try {
    const list: string[] = JSON.parse(sessionStorage.getItem(CLAIMS) ?? "[]");
    sessionStorage.removeItem(CLAIMS);
    return list;
  } catch {
    return [];
  }
}
