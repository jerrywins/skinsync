import { expect, test } from "@playwright/test";
import { decline, expectAccessible, pickProduct } from "./helpers";

test.beforeEach(async ({ page }) => decline(page));

test("SC-01 guest compares two products and inspects evidence @mobile", async ({ page }) => {
  await page.goto("/compare");
  await pickProduct(page, "First product", "renewal night", "DEMO Renewal Night Serum");
  await pickProduct(page, "Second product", "smooth acid", "DEMO Smooth Acid Toner");
  await page.getByRole("button", { name: "Check this pair" }).click();
  await expect(page).toHaveURL(/\/compare\/[0-9a-f-]{36}$/);
  await expect(page.getByRole("heading", { name: "Use with some care" })).toBeVisible();
  await expect(page.getByText("DEMO: fictional data, not science").first()).toBeVisible();
  await page.getByRole("button", { name: "Why was this flagged?" }).first().click();
  await expect(page.getByText("Knowledge version used: demo-kv-1.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "How this result was made" })).toBeVisible();
  await expectAccessible(page);
});

test("C05 unknown ingredient is never shown as clear", async ({ page }) => {
  await page.goto("/compare");
  await pickProduct(page, "First product", "mystery botanical", "DEMO Mystery Botanical Oil");
  await pickProduct(page, "Second product", "hydra gel", "DEMO Hydra Gel Cream");
  await page.getByRole("button", { name: "Check this pair" }).click();
  await expect(page.getByRole("heading", { name: "Some of the data is missing" })).toBeVisible();
  await expect(page.getByText("Demo Unlisted Botanical Extract").first()).toBeVisible();
});

test("manual ingredient entry compares without saving", async ({ page }) => {
  await page.goto("/compare");
  await page.getByRole("button", { name: "Type the ingredients instead" }).first().click();
  await page.getByLabel("First product: ingredient list").fill("Aqua, Glycerin");
  await pickProduct(page, "Second product", "hydra gel", "DEMO Hydra Gel Cream");
  await page.getByRole("button", { name: "Check this pair" }).click();
  await expect(page.getByText("Results from typed ingredient lists are not saved.")).toBeVisible();
});

test("SC-03 cheaper alternatives show prices, dates and reasons", async ({ page }) => {
  await page.goto("/products?q=DEMO+Balance+Niacin");
  await page.getByRole("link", { name: "DEMO Balance Niacin Serum" }).first().click();
  await expect(page.getByRole("heading", { name: "DEMO Balance Niacin Serum" })).toBeVisible();
  await expectAccessible(page);
  await page.getByRole("link", { name: "Find alternatives" }).click();
  await page.getByText("Cheaper", { exact: true }).click();
  await page.getByRole("button", { name: "Find alternatives" }).click();
  await expect(page).toHaveURL(/\/alternatives\/[0-9a-f-]{36}$/);
  const first = page.getByRole("listitem").filter({ hasText: "Rank 1" });
  await expect(first).toContainText("DEMO Budget Balance Serum");
  await expect(first).toContainText("lower observed price");
  await expect(first).toContainText("Observed");
  await expectAccessible(page);
  await first.getByRole("link", { name: "Compare with mine" }).click();
  await expect(page).toHaveURL(/\/compare\?a=/);
});

test("real product search, product page and provenance", async ({ page }) => {
  await page.goto("/products?category=sunscreen");
  const first = page.locator('section[aria-label="Results"] li a').first();
  const name = (await first.textContent())!;
  await first.click();
  await expect(page.getByRole("heading", { name })).toBeVisible();
  await expect(page.getByText(/Source:/).first()).toBeVisible();
  // no unlabelled invented prices: either unavailable, or a random dev/test price carrying the TEST PRICE badge
  await expect(page.getByText("Price unavailable").or(page.getByText("TEST PRICE — not real")).first()).toBeVisible();
  const prices = page.locator('section[aria-labelledby="price-h"] li');
  for (const li of await prices.all()) {
    const t = (await li.textContent()) ?? "";
    expect(t.includes("Price unavailable") || t.includes("TEST PRICE")).toBeTruthy();
  }
});

test("SC-02 guest skin analysis with demo model, then delete", async ({ page }) => {
  await page.goto("/analyze");
  await expect(page.getByText("This is not a medical diagnosis").first()).toBeVisible();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByLabel(/I agree to my photo being processed/).check();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByLabel("Skin photo").setInputFiles("e2e/fixtures/skin-photo.jpg");
  await page.getByRole("button", { name: "Analyze photo" }).click();
  await expect(page.getByRole("heading", { name: "Visible features in your photo" })).toBeVisible({ timeout: 20_000 });
  await expect(page.getByText(/Demo model/).first()).toBeVisible();
  await expect(page.getByText("Your photo has already been deleted.", { exact: false })).toBeVisible();
  await expectAccessible(page);
  await page.getByRole("button", { name: "Delete this analysis" }).click();
  await expect(page.getByText("Analysis deleted")).toBeVisible();
});

test("invalid upload is rejected with guidance", async ({ page }) => {
  await page.goto("/analyze");
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByLabel(/I agree to my photo being processed/).check();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByLabel("Skin photo").setInputFiles({ name: "x.png", mimeType: "image/png", buffer: Buffer.from("not an image") });
  await page.getByRole("button", { name: "Analyze photo" }).click();
  await expect(page.getByRole("alert").first()).toContainText(/JPEG, PNG or WebP/);
});

test("security headers and CSP are set", async ({ page }) => {
  const res = await page.goto("/");
  const h = res!.headers();
  expect(h["content-security-policy"]).toMatch(/script-src 'self' 'nonce-/);
  expect(h["content-security-policy"]).toContain("frame-ancestors 'none'");
  expect(h["x-content-type-options"]).toBe("nosniff");
  expect(h["permissions-policy"]).toContain("camera=()");
  const scan = await page.goto("/scan");
  expect(scan!.headers()["permissions-policy"]).toContain("camera=(self)");
});

test("static and SEO pages are accessible", async ({ page }) => {
  for (const path of ["/", "/how-it-works", "/methodology", "/safety", "/privacy", "/data-sources", "/ingredients", "/scan", "/auth/signin"]) {
    await page.goto(path);
    await expectAccessible(page);
  }
  const robots = await page.request.get("/robots.txt");
  expect(await robots.text()).toContain("Disallow: /analyze/");
  const sitemap = await page.request.get("/sitemap.xml");
  expect(await sitemap.text()).toContain("/products/");
});
