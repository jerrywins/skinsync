import type { Metadata } from "next";
import { ScanFlow } from "./flow";

export const metadata: Metadata = { title: "Scan a product", description: "Identify a product from its barcode or ingredient label." };

export default function ScanPage() {
  return <ScanFlow />;
}
