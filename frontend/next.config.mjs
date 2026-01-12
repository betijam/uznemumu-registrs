import createNextIntlPlugin from 'next-intl/plugin';

const withNextIntl = createNextIntlPlugin();

/** @type {import('next').NextConfig} */
const nextConfig = {
    // Using standard mode (not standalone) for proper static file serving

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
        // Default to Production, override with NEXT_PUBLIC_API_URL or BACKEND_URL env var
        const backendUrl = process.env.NEXT_PUBLIC_API_URL || process.env.BACKEND_URL || 'https://api.company360.lv';
        console.log('Proxying /api requests to:', backendUrl);
        return [
            {
                source: '/api/:path*',
                destination: `${backendUrl}/:path*`,
            },
            {
                source: '/sitemap-companies-:id.xml',
                destination: '/internal/sitemaps/companies/:id',
            },
            {
                source: '/sitemap-persons-:id.xml',
                destination: '/internal/sitemaps/persons/:id',
            },
        ];
    },
};

export default withNextIntl(nextConfig);