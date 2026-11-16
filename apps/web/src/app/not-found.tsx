import Link from "next/link";
import { Empty } from "@/components/ui";

export default function NotFound() {
  return <Empty title="We couldn't find that page" action={<><Link className="btn btn-primary" href="/products">Search products</Link><Link className="btn btn-quiet" href="/">Home</Link></>}>
    The link may be old, or the product may have been removed.</Empty>;
}
