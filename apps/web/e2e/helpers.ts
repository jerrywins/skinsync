import AxeBuilder from "@axe-core/playwright";
import { expect, type Page } from "@playwright/test";

export const USER = { email: process.env.E2E_USER ?? "e2e@example.com", password: process.env.E2E_PASSWORD ?? "E2e-Strong-Passphrase-1" };
export const ADMIN = { email: process.env.E2E_ADMIN ?? "admin@example.com", password: process.env.E2E_ADMIN_PASSWORD ?? "Adm1n-strong-passphrase" };

/** Dismiss the analytics choice so it never covers controls. */
export async function decline(page: Page) {
  await page.addInitScript(() => { try { localStorage.setItem("ss_analytics_consent", "no"); } catch { /* */ } });
}

export async function pickProduct(page: Page, label: string, query: string, name: string) {
  const box = page.getByRole("combobox", { name: label });
  await box.fill(query);
  await page.getByRole("option", { name: new RegExp(name) }).first().click();
}

export async function signIn(page: Page, who = USER) {
  await page.goto("/auth/signin");
  await page.getByLabel("Email").fill(who.email);
  await page.getByLabel("Password").fill(who.password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.locator("summary", { hasText: "Account" })).toBeVisible();
}

/** WCAG 2.1 A/AA automated checks; fails on serious or critical violations. */
export async function expectAccessible(page: Page) {
  const r = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  const bad = r.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
  expect(bad.map((v) => `${v.id}: ${v.nodes.length} node(s) ${v.nodes[0]?.target}`)).toEqual([]);
}
