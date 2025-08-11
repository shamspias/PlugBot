const createNextIntlPlugin = require('next-intl/plugin');
const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts');

// Wrap your existing config with withNextIntl
module.exports = withNextIntl(nextConfig);