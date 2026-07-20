import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Bundle the captured API snapshots with the proxy route so the labeled
  // fallback works on Vercel's serverless runtime (blueprint §11).
  outputFileTracingIncludes: {
    "/api/proxy/[...path]": ["./snapshots/**/*"],
  },
};

export default nextConfig;
