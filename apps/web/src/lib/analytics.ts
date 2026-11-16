import { api } from "./api";

// Funnel analytics: off until the visitor opts in. No personal or skin data is ever sent.
const KEY = "ss_analytics_consent";

export function analyticsConsent(): boolean | null {
  try {
    const v = localStorage.getItem(KEY);
    return v === null ? null : v === "yes";
  } catch {
    return null;
  }
}

export function setAnalyticsConsent(yes: boolean) {
  try {
    localStorage.setItem(KEY, yes ? "yes" : "no");
  } catch {
    /* storage unavailable: treated as no consent */
  }
}

function session(): string {
  try {
    let s = sessionStorage.getItem("ss_sid");
    if (!s) {
      s = crypto.randomUUID();
      sessionStorage.setItem("ss_sid", s);
    }
    return s;
  } catch {
    return "anonymous-session";
  }
}

export function track(name: string, metadata: Record<string, string | number | boolean> = {}) {
  if (typeof window === "undefined" || analyticsConsent() !== true) return;
  const route = window.location.pathname.replace(/[0-9a-f-]{36}/g, "[id]").slice(0, 120);
  api("/events", { body: { name, consent: true, session_id: session(), route, metadata } }).catch(() => undefined);
}
