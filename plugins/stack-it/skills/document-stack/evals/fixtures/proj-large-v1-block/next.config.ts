import { withSentryConfig } from "@sentry/nextjs";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  typedRoutes: true,
  redirects: async () => [
    { source: "/docs/getting-started", destination: "/docs/quickstart", permanent: true },
  ],
};

export default withSentryConfig(nextConfig, { silent: true });
