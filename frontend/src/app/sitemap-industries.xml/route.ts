export const dynamic = 'force-dynamic';

export async function GET() {
    const baseUrl = 'https://company360.lv';
    const lastMod = new Date().toISOString();

    // NACE Sections (Manual list or fetched if dynamic)
    const naceCodes = [
        "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U"
    ];

    const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  ${naceCodes.map(code => `
  <url>
    <loc>${baseUrl}/industries/${code}</loc>
    <lastmod>${lastMod}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>`).join('')}
</urlset>`;

    return new Response(xml, {
        headers: {
            'Content-Type': 'application/xml',
            'Cache-Control': 'public, max-age=86400, s-maxage=86400',
        },
    });
}
