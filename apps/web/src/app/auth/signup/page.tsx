import { Suspense } from "react";
import { SignUpForm } from "@/components/AuthForms";

export default function Page() {
  return <Suspense><SignUpForm /></Suspense>;
}
