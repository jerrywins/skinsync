// Guest poll tokens for private async results. Kept in this tab only (sessionStorage), never in the URL.
export function savePollToken(id: string, token: string | null) {
  if (!token) return;
  try { sessionStorage.setItem(`ss_poll_${id}`, token); } catch { /* unavailable */ }
}
export function pollHeaders(id: string): Record<string, string> {
  try {
    const t = sessionStorage.getItem(`ss_poll_${id}`);
    return t ? { "X-Poll-Token": t } : {};
  } catch {
    return {};
  }
}
export function forgetPollToken(id: string) {
  try { sessionStorage.removeItem(`ss_poll_${id}`); } catch { /* unavailable */ }
}
