import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = { title: "Your skin analysis", robots: { index: false, follow: false } };
export default function L({ children }: { children: ReactNode }) { return children; }
