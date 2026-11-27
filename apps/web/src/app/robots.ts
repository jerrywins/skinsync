import type { MetadataRoute } from "next";

// Rendered per request so PUBLIC_BASE_URL comes from the running container, not the image build.
export const dynamic = "force-dynamic";

export default function robots(): MetadataRoute.Robots {
  const base = process.env.PUBLIC_BASE_URL ?? "http://localhost:3000";
  return {
    rules: { userAgent: "*", allow: "/", disallow: ["/api/", "/admin", "/analyze/", "/compare/", "/alternatives/", "/share/",
                                                   "/shelf", "/routines", "/history", "/profile", "/settings", "/auth/"] },
    sitemap: `${base}/sitemap.xml`,
  };
}
