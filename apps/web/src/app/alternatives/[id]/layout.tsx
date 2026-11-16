import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = { title: "Alternatives", robots: { index: false } };
export default function L({ children }: { children: ReactNode }) { return children; }
