import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Vercel handles dynamic routes automatically
  trailingSlash: false,
  
  // Ensure all routes are included in the build
  generateBuildId: async () => {
    return 'build-' + Date.now();
  },
  
  // Configure page extensions
  pageExtensions: ['tsx', 'ts', 'jsx', 'js'],
};

export default nextConfig;
