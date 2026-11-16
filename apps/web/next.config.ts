import type { NextConfig } from "next";

const api = process.env.API_INTERNAL_URL ?? "http://localhost:8000";

const config: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  reactStrictMode: true,
  // Browser calls stay same-origin (/api/...), so session cookies are first-party.
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${api}/api/:path*` }];
  },
  images: { remotePatterns: [{ protocol: "https", hostname: "images.openbeautyfacts.org" }] },
};

export default config;
