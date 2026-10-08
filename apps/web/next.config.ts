import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  output: "standalone",
  transpilePackages: ["@ama/ui"],


  webpack(config, { isServer }) {
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

    // Suppress "Critical dependency" warnings from OpenTelemetry packages
    // which use dynamic require() internally — harmless at runtime.
    config.ignoreWarnings = [
      ...(config.ignoreWarnings ?? []),
      {
        module: /opentelemetry/,
        message: /Critical dependency/,
      },
      {
        module: /azure.*opentelemetry/,
        message: /Critical dependency/,
      },
      {
        module: /monitor-opentelemetry/,
        message: /Critical dependency/,
      },
    ];

    return config;
  },
};

export default nextConfig;
