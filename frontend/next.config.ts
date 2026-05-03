import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Produce a self-contained server bundle in .next/standalone so the
  // production Docker image stays small (~150MB instead of ~1GB).
  output: "standalone",
};

export default nextConfig;
