import { expect, test } from "@playwright/test";
import { ADMIN, decline, expectAccessible, pickProduct, signIn } from "./helpers";

test.beforeEach(async ({ page }) => decline(page));

test("SC-04 shelf, routine build and analyze", async ({ page }) => {
  await signIn(page);
  await page.goto("/shelf");
  await pickProduct(page, "Add a product", "calm cica", "DEMO Calm Cica Cream");
  await expect(page.getByRole("status").filter({ hasText: /Added|already/ })).toBeVisible();
  await page.goto("/routines");
  await page.getByRole("button", { name: "New evening routine" }).click();
  await expect(page).toHaveURL(/\/routines\/[0-9a-f-]{36}$/);
  await pickProduct(page, "Add a step", "renewal night", "DEMO Renewal Night Serum");
  await pickProduct(page, "Add a step", "double acid", "DEMO Double Acid Peel");
  await pickProduct(page, "Add a step", "smooth acid", "DEMO Smooth Acid Toner");
  await page.getByRole("button", { name: "Move DEMO Smooth Acid Toner up" }).click();
  await expect(page.getByRole("status").filter({ hasText: "moved to step 2" })).toBeVisible();
  await page.getByRole("button", { name: "Check this routine" }).click();
  await expect(page.getByRole("heading", { name: /caution/i })).toBeVisible();
  await expectAccessible(page);
});

test("save, history, share and revoke", async ({ page, browser }) => {
  await signIn(page);
  await page.goto("/compare");
  await pickProduct(page, "First product", "clear spot", "DEMO Clear Spot Gel");
  await pickProduct(page, "Second product", "renewal night", "DEMO Renewal Night Serum");
  await page.getByRole("button", { name: "Check this pair" }).click();
  await expect(page.getByRole("heading", { name: "Reconsider combining these" })).toBeVisible();
  await page.getByRole("button", { name: "Create share link" }).click();
  const url = await page.getByLabel("Share link").inputValue();
  const viewer = await (await browser.newContext()).newPage();
  await viewer.goto(new URL(url).pathname);
  await expect(viewer.getByText("Shared result, read-only")).toBeVisible();
  await expect(viewer.getByRole("heading", { name: "Reconsider combining these" })).toBeVisible();
  await page.goto("/history");
  await expect(page.getByText("DEMO Clear Spot Gel + DEMO Renewal Night Serum").first()).toBeVisible();
  await page.getByRole("button", { name: "Revoke link" }).first().click();
  await viewer.reload();
  await expect(viewer.getByText("This link isn't available")).toBeVisible();
});

test("personal pages require sign-in", async ({ page }) => {
  for (const p of ["/shelf", "/routines", "/history", "/profile", "/settings/privacy"]) {
    await page.goto(p);
    await expect(page.getByText("Sign in to use this")).toBeVisible();
  }
});

test("SC-05 admin sees data quality and knowledge versions; non-admin cannot", async ({ page }) => {
  await signIn(page);
  await page.goto("/admin");
  await expect(page.getByText("Administrator access is required")).toBeVisible();
  await page.locator("summary", { hasText: "Account" }).click();
  await page.getByRole("button", { name: "Sign out" }).click();
  await signIn(page, ADMIN);
  await page.goto("/admin");
  await expect(page.getByText("Products (real)")).toBeVisible();
  await page.getByRole("tab", { name: "Knowledge versions" }).click();
  await expect(page.getByText("kv-0-empty")).toBeVisible();
  await expect(page.getByText("demo-kv-1")).toBeVisible();
  await expectAccessible(page);
});
