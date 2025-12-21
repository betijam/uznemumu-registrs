/** @type {import('next').NextConfig} */
const nextConfig = {
    output: "standalone",
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