/** @type {import('next').NextConfig} */
const nextConfig = {
    output: "standalone",

    // Performance optimizations
    experimental: {
        optimizePackageImports: ['lodash.debounce'],
    },

    // Compiler optimizations
    compiler: {
        // Remove console.log in production
        removeConsole: process.env.NODE_ENV === 'production',
    },

    async rewrites() {
        const backendUrl = process.env.BACKEND_URL || 'https://uznemumu-registrs-production.up.railway.app';
        return [
            {
                source: '/api/:path*',
                destination: `${backendUrl}/:path*`,
            },
        ];
    },
};

export default nextConfig;