import type { Metadata } from "next";
import { AnalyzeFlow } from "./flow";

export const metadata: Metadata = {
  title: "Analyze visible skin features",
  description: "Upload a photo to see visible cosmetic features with confidence levels. Not a medical diagnosis.",
  alternates: { canonical: "/analyze" },
};

export default function AnalyzePage() {
  return <AnalyzeFlow />;
}
