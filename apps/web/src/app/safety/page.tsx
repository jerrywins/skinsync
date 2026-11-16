import type { Metadata } from "next";
import { StaticPage } from "@/components/StaticPage";

export const metadata: Metadata = { title: "Safety and medical boundary", alternates: { canonical: "/safety" } };

export default function Page() {
  return (
    <StaticPage title="Safety and medical boundary" lead="SkinSync is for cosmetic decisions. It is not a medical device and gives no medical advice.">
      <ul>
        <li>Skin analysis shows estimates of visible cosmetic features in one photo. Lighting, camera quality, makeup, filters and angle all affect them.</li>
        <li>We never name, diagnose or suggest treatment for acne, rosacea, melasma, eczema or any other condition.</li>
        <li>&ldquo;No notable interaction identified&rdquo; refers only to our current knowledge base and the formulations we hold. It does not mean a combination is safe for you.</li>
        <li>New products can irritate any skin. Many people patch-test a new product on a small area first.</li>
      </ul>
      <p>For persistent, painful or worrying skin problems, see a qualified professional such as a dermatologist. In an emergency, contact local emergency services.</p>
    </StaticPage>
  );
}
