// Browser + server API client. Browser calls are same-origin (/api/v1, rewritten to FastAPI),
// so HttpOnly session cookies are first-party. Unsafe methods send the CSRF double-submit header.
import type { components } from "./api-schema";

export type Schemas = components["schemas"];
export type ComparisonResult = Schemas["ComparisonResult"];
export type Finding = Schemas["Finding"];
export type AlternativesResult = Schemas["AlternativesResult"];
export type RankedAlternative = Schemas["RankedAlternative"];
export type SkinResult = Schemas["SkinResult"];
export type NormalizedIngredient = Schemas["NormalizedIngredient"];

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string,
              public details: Record<string, unknown> = {}, public requestId?: string) {
    super(message);
  }
}

const SERVER_BASE = `${process.env.API_INTERNAL_URL ?? "http://localhost:8000"}/api/v1`;
const isServer = typeof window === "undefined";

function readCookie(name: string): string | null {
  if (isServer) return null;
  const m = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return m ? decodeURIComponent(m[1]) : null;
}

let csrfPromise: Promise<string> | null = null;
async function csrf(): Promise<string> {
  const existing = readCookie("ss_csrf");
  if (existing) return existing;
  csrfPromise ??= fetch("/api/v1/auth/csrf", { credentials: "same-origin" })
    .then((r) => r.json()).then((j) => j.csrf_token as string).finally(() => { csrfPromise = null; });
  return csrfPromise;
}

type Opts = { method?: string; body?: unknown; form?: FormData; headers?: Record<string, string>;
              retryAuth?: boolean; next?: { revalidate?: number } };

export async function api<T = unknown>(path: string, opts: Opts = {}): Promise<T> {
  const method = opts.method ?? (opts.body || opts.form ? "POST" : "GET");
  const headers: Record<string, string> = { ...(opts.headers ?? {}) };
  if (opts.body !== undefined) headers["Content-Type"] = "application/json";
  if (!isServer && method !== "GET") headers["X-CSRF-Token"] = await csrf();
  const url = isServer ? `${SERVER_BASE}${path}` : `/api/v1${path}`;
  let res: Response;
  try {
    res = await fetch(url, {
      method, headers, credentials: "same-origin",
      body: opts.form ?? (opts.body !== undefined ? JSON.stringify(opts.body) : undefined),
      ...(isServer ? { next: opts.next ?? { revalidate: 300 } } : { cache: "no-store" }),
    });
  } catch {
    throw new ApiError(0, "NETWORK", "We could not reach SkinSync. Check your connection and try again.");
  }
  // Only try a refresh when a session might exist (non-secret hint cookie), so guests don't make a wasted call.
  if (res.status === 401 && !isServer && opts.retryAuth !== false && !path.startsWith("/auth/") && readCookie("ss_signed_in")) {
    const refreshed = await fetch("/api/v1/auth/refresh", {
      method: "POST", credentials: "same-origin", headers: { "X-CSRF-Token": await csrf() },
    });
    if (refreshed.ok) return api<T>(path, { ...opts, retryAuth: false });
  }
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) {
    throw new ApiError(res.status, data?.code ?? "HTTP_ERROR", data?.message ?? "Request failed.",
                       data?.details ?? {}, data?.request_id ?? res.headers.get("x-request-id") ?? undefined);
  }
  return data as T;
}

export async function serverApi<T>(path: string, revalidate = 300): Promise<T | null> {
  try {
    return await api<T>(path, { next: { revalidate } });
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) return null;
    throw e;
  }
}
