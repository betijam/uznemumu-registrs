export const dynamic = 'force-dynamic';

export async function GET() {
    const baseUrl = 'https://company360.lv';
    const lastMod = new Date().toISOString();

    const urls = [
        { loc: `${baseUrl}/`, lastmod: lastMod, changefreq: 'daily', priority: '1.0' },
        { loc: `${baseUrl}/industries`, lastmod: lastMod, changefreq: 'weekly', priority: '0.9' },
        { loc: `${baseUrl}/personas`, lastmod: lastMod, changefreq: 'daily', priority: '0.9' },
        { loc: `${baseUrl}/regions`, lastmod: lastMod, changefreq: 'weekly', priority: '0.8' },
        { loc: `${baseUrl}/top100`, lastmod: lastMod, changefreq: 'daily', priority: '0.9' },
        { loc: `${baseUrl}/explore`, lastmod: lastMod, changefreq: 'daily', priority: '0.8' },
        { loc: `${baseUrl}/benchmark`, lastmod: lastMod, changefreq: 'monthly', priority: '0.7' },
        { loc: `${baseUrl}/mvk-declaration`, lastmod: lastMod, changefreq: 'monthly', priority: '0.6' },
        { loc: `${baseUrl}/auth/login`, lastmod: lastMod, changefreq: 'monthly', priority: '0.5' },
        { loc: `${baseUrl}/auth/register`, lastmod: lastMod, changefreq: 'monthly', priority: '0.5' },
    ];

    const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  ${urls.map(url => `
  <url>
    <loc>${url.loc}</loc>
    <lastmod>${url.lastmod}</lastmod>
    <changefreq>${url.changefreq}</changefreq>
    <priority>${url.priority}</priority>
  </url>`).join('')}
</urlset>`;

    return new Response(xml, {
        headers: {
            'Content-Type': 'application/xml',
            'Cache-Control': 'public, max-age=3600, s-maxage=3600',
        },
    });
}
