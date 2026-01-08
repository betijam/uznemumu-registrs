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
        // Use local backend by default for development
        const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
        return [
            {
                source: '/api/:path*',
                destination: `${backendUrl}/:path*`,
            },
        ];
    },
};

export default withNextIntl(nextConfig);