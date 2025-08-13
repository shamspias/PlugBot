const createNextIntlPlugin = require('next-intl/plugin');
const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts');

const isProd = process.env.NODE_ENV === 'production';
const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
const isLocal = apiUrl.includes('localhost') || apiUrl.includes('127.0.0.1');

/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'standalone',
    reactStrictMode: true,
    swcMinify: true,
    env: {
        NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL
    },
    async headers() {
        // Only define headers if we actually need them
        if (isProd && !isLocal) {
            return [
                {
                    source: '/:path*',
                    headers: [
                        {
                            key: 'Content-Security-Policy',
                            value: 'upgrade-insecure-requests'
                        }
                    ]
                }
            ];
        }
        // No custom headers in local/dev
        return [];
    },
};

module.exports = withNextIntl(nextConfig);
