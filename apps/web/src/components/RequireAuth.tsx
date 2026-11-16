"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useMe } from "./providers";
import { Empty, Loading } from "./ui";
import type { Me } from "@/lib/types";

export function RequireAuth({ children, admin = false }: { children: (me: Me) => ReactNode; admin?: boolean }) {
  const me = useMe();
  const path = usePathname();
  if (me.isLoading) return <Loading />;
  if (!me.data) return (
    <Empty title="Sign in to use this" action={<><Link className="btn btn-primary" href={`/auth/signin?next=${encodeURIComponent(path)}`}>Sign in</Link>
      <Link className="btn btn-quiet" href="/auth/signup">Create an account</Link></>}>
      Your shelf, routines and saved results are kept in your account.
    </Empty>
  );
  if (admin && me.data.role !== "admin") return <Empty title="Administrator access is required" />;
  return <>{children(me.data)}</>;
}
