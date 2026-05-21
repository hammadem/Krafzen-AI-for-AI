import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload'
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin'
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(self), geolocation=()'
          }
        ],
      },
    ];
  },
  async redirects() {
    return [];
  },
  // Configure webpack for module resolution (fallback for non-Turbopack builds)
  webpack: (config) => {
    // Ensure webpack resolves modules from the frontend directory first
    const frontendDir = path.resolve(__dirname);
    config.resolve.modules = [
      path.join(frontendDir, 'node_modules'),
      ...(Array.isArray(config.resolve.modules) ? config.resolve.modules : ['node_modules']),
    ];
    
    return config;
  },
  // Turbopack configuration (empty - Turbopack handles module resolution automatically)
  turbopack: {},
};

export default nextConfig;
