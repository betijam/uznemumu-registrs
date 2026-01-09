import { MetadataRoute } from 'next';

export default function robots(): MetadataRoute.Robots {
    const baseUrl = 'https://company360.lv';

    return {
        rules: {
            userAgent: '*',
            allow: '/',
            disallow: [
                '/api/',
                '/_next/',
                '/*?*', // Prevent query parameters
                '/search',
                '/filters',
                '/sitemap-', // Don't crawl the sitemap files themselves pages
                '/auth/' // Don't crawl auth pages
            ],
        },
        sitemap: `${baseUrl}/sitemap.xml`,
    };
}
