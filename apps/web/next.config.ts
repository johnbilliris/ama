import type { NextConfig } from "next";
import path from "path";

// Server-side-only: the real upstream API base URL used by the proxy rewrite.
// NEXT_PUBLIC_API_BASE_URL is set to "/api" (relative) so browser fetches hit
// the Next.js proxy instead of making a cross-origin request directly.
const API_PROXY_UPSTREAM =
  process.env.API_PROXY_UPSTREAM ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://localhost:8000/api";

const nextConfig: NextConfig = {
  output: "standalone",
  transpilePackages: ["@ama/ui"],

  // Proxy /api/* → upstream API server so browser requests stay same-origin
  // and CORS headers are never needed.  beforeFiles runs before the App Router
  // filesystem check so Next.js never reaches its not-found handler for these paths.
  async rewrites() {
    return {
      beforeFiles: [
        {
          source: "/api/:path*",
          destination: `${API_PROXY_UPSTREAM}/:path*`,
        },
      ],
      afterFiles: [],
      fallback: [],
    };
  },

  webpack(config) {
    // azure-maps-control's default ESM entry (atlas-esm.min.js) contains a
    // variable redeclaration that webpack's strict parser rejects. Alias to
    // the non-minified build so webpack can parse it cleanly.
    // Use "$" suffix for exact-match so sub-paths (e.g. /dist/atlas.min.css) resolve normally.
    config.resolve.alias = {
      ...config.resolve.alias,
      "azure-maps-control$": path.resolve(
        __dirname,
        "../../packages/ui/node_modules/azure-maps-control/dist/atlas-esm.js",
      ),
    };
    return config;
  },
};

export default nextConfig;
