import { Suspense } from "react";
import { SignInForm } from "@/components/AuthForms";

export default function Page() {
  return <Suspense><SignInForm /></Suspense>;
}
