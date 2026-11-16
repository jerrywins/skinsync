import type { Metadata, Viewport } from "next";
import { headers } from "next/headers";
import type { ReactNode } from "react";
import { AnalyticsConsent, SiteFooter, SiteHeader } from "@/components/SiteChrome";
import { Providers } from "@/components/providers";
import "./globals.css";

const base = process.env.PUBLIC_BASE_URL ?? "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(base),
  title: { default: "SkinSync: check before you layer", template: "%s | SkinSync" },
  description:
    "Compare two skincare products, find alternatives, and explore ingredients, with the evidence and the gaps shown.",
  openGraph: { siteName: "SkinSync", type: "website" },
  alternates: { canonical: "/" },
};

export const viewport: Viewport = { themeColor: "#f6f7f4", width: "device-width", initialScale: 1 };

export default async function RootLayout({ children }: { children: ReactNode }) {
  // Reading request headers makes every page dynamic, so Next.js can stamp the per-request CSP nonce.
  await headers();
  return (
    <html lang="en-IN">
      <body>
        <Providers>
          <SiteHeader />
          <main id="main" className="mx-auto max-w-6xl px-4 pt-10 sm:px-6">{children}</main>
          <SiteFooter />
          <AnalyticsConsent />
        </Providers>
      </body>
    </html>
  );
}
