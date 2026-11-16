import type { Metadata } from "next";
import { StaticPage } from "@/components/StaticPage";

export const metadata: Metadata = { title: "Terms", alternates: { canonical: "/terms" } };

export default function Page() {
  return (
    <StaticPage title="Terms of use" lead="The short version: SkinSync is an information tool, not advice, and you must be 18 or older to create an account.">
      <p className="text-sm text-ink-soft">Draft terms for a student project. Review with a qualified adviser before any public launch.</p>
      <h2>Using SkinSync</h2>
      <ul>
        <li>Results are general cosmetic information based on the data and knowledge version shown. They are not medical, dermatological or professional advice.</li>
        <li>Product data comes from third parties and may be incomplete or out of date. Check the product label.</li>
        <li>You need to be 18 or older to create an account.</li>
        <li>Don&apos;t upload photos of other people, or anything other than your own skin.</li>
      </ul>
      <h2>Content and data</h2>
      <p>Product data from Open Beauty Facts is available under the Open Database License; see Data sources.</p>
    </StaticPage>
  );
}
