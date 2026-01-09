export const dynamic = 'force-dynamic';
export const revalidate = 3600;

export async function GET(request: Request, { params }: { params: Promise<{ id: string }> }) {
    const baseUrl = 'https://company360.lv';

    // Await params to satisfy Next.js 15+ type requirements
    const { id } = await params;
    const page = parseInt(id) || 1;

    const apiUrl = process.env.INTERNAL_API_URL || 'http://backend:8000';
    let companyUrls = '';

    try {
        const res = await fetch(`${apiUrl}/api/companies/sitemap-ids?page=${page}&limit=50000`, {
            next: { revalidate: 3600 }
        });

        if (res.ok) {
            const data = await res.json();
            // data.ids is Array<{regcode, updated_at}>
            companyUrls = data.ids.map((c) => `
  <url>
    <loc>${baseUrl}/company/${c.regcode}</loc>
    <lastmod>${c.updated_at || new Date().toISOString()}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>`).join('');
        }
    } catch (error) {
        console.error(`Failed to fetch companies sitemap page ${page}`, error);
    }

    const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  ${companyUrls}
</urlset>`;

    return new Response(xml, {
        headers: {
            'Content-Type': 'application/xml',
            'Cache-Control': 'public, max-age=3600, s-maxage=3600',
        },
    });
}
