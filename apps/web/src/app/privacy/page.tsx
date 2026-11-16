import type { Metadata } from "next";
import { StaticPage } from "@/components/StaticPage";

export const metadata: Metadata = { title: "Privacy notice", alternates: { canonical: "/privacy" } };

export default function Page() {
  return (
    <StaticPage title="Privacy notice" lead="What we collect, why, for how long, and how to delete it. Written with India's Digital Personal Data Protection Act in mind.">
      <p className="text-sm text-ink-soft">This notice describes how the software behaves. Before a public launch, the operator must review it with a qualified adviser.</p>
      <h2>Without an account</h2>
      <ul>
        <li>Comparisons and alternative searches are stored without any personal identifier and deleted after 30 days unless saved or shared.</li>
        <li>Guest skin photos are deleted as soon as the analysis finishes; guest analyses are deleted after 7 days.</li>
        <li>Anonymous usage counting happens only if you allow it.</li>
      </ul>
      <h2>With an account</h2>
      <ul>
        <li>Email address and a password hash (Argon2id). We never store your password.</li>
        <li>Profile, preferences, shelf, routines and saved results, to provide those features.</li>
        <li>Consent records with the date and policy version.</li>
        <li>Skin photos: deleted after analysis unless you choose to keep one, for at most 30 days. Photos are encrypted at rest and stripped of location and camera data.</li>
      </ul>
      <h2>What we never do</h2>
      <ul><li>Sell personal data.</li><li>Use your photos to train models.</li><li>Make skin analyses shareable.</li><li>Put personal data, tokens or images in logs.</li></ul>
      <h2>Your rights</h2>
      <p>You can delete any saved result, any skin analysis or photo, or your whole account from Privacy and data in your account settings. Account deletion removes all associated personal data immediately. A record that a deletion happened is kept without your email.</p>
    </StaticPage>
  );
}
