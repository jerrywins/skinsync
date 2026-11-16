import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = { robots: { index: false } };
export default function AuthLayout({ children }: { children: ReactNode }) {
  return <div className="mx-auto max-w-md">{children}</div>;
}
