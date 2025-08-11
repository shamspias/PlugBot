const createNextIntlPlugin = require('next-intl/plugin');
const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts');

/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'standalone',
    reactStrictMode: true,
    swcMinify: true,
    experimental: {
        outputFileTracingRoot: undefined,
    },
    // Remove rewrites - we'll use direct API calls instead
    // This prevents any HTTP/HTTPS confusion

    // Ensure environment variables are available at build time
    env: {
        NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    },

    // Add security headers
    async headers() {
        return [
            {
                source: '/:path*',
                headers: [
                    {
                        key: 'Content-Security-Policy',
                        value: "upgrade-insecure-requests",
                    },
                ],
            },
        ];
    },
};

module.exports = withNextIntl(nextConfig);