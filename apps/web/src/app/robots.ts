import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  const base = process.env.PUBLIC_BASE_URL ?? "http://localhost:3000";
  return {
    rules: { userAgent: "*", allow: "/", disallow: ["/api/", "/admin", "/analyze/", "/compare/", "/alternatives/", "/share/",
                                                   "/shelf", "/routines", "/history", "/profile", "/settings", "/auth/"] },
    sitemap: `${base}/sitemap.xml`,
  };
}
