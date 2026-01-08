import createNextIntlPlugin from 'next-intl/plugin';

const withNextIntl = createNextIntlPlugin();

/** @type {import('next').NextConfig} */
const nextConfig = {
    output: "standalone",

    // Performance optimizations
    experimental: {
        optimizePackageImports: ['lodash.debounce', '@heroicons/react'],
    },

    // Compiler optimizations
    compiler: {
        // Remove console.log in production
        removeConsole: process.env.NODE_ENV === 'production',
    },

    // Optimize images
    images: {
        formats: ['image/avif', 'image/webp'],
    },

    async rewrites() {
        // Default to production, override with BACKEND_URL env var for local dev
        const backendUrl = process.env.BACKEND_URL || 'https://uznemumu-registrs-production.up.railway.app';
        return [
            {
                source: '/api/:path*',
                destination: `${backendUrl}/:path*`,
            },
        ];
    },
};

export default withNextIntl(nextConfig);