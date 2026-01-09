export const dynamic = 'force-dynamic';

export async function GET(request: Request, { params }: { params: Promise<{ id: string }> }) {
    const baseUrl = 'https://company360.lv';

    // Await params to satisfy Next.js 15+ type requirements
    await params;

    // Extract ID/Page from URL pattern "sitemap-persons-1.xml"
    const url = new URL(request.url);
    const path = url.pathname;
    const match = path.match(/sitemap-persons-(\d+)\.xml/);
    const page = match ? parseInt(match[1]) : 1;

    const apiUrl = process.env.INTERNAL_API_URL || 'http://backend:8000';
    let personUrls = '';

    try {
        const res = await fetch(`${apiUrl}/api/persons/sitemap-ids?page=${page}&limit=50000`, {
            next: { revalidate: 3600 }
        });

        if (res.ok) {
            const data = await res.json();
            // data.ids is Array<{identifier, updated_at}>
            personUrls = data.ids.map((p: any) => `
  <url>
    <loc>${baseUrl}/person/${p.identifier}</loc>
    <lastmod>${p.updated_at || new Date().toISOString()}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>`).join('');
        } else {
            console.error('Failed to fetch persons sitemap:', res.statusText);
        }
    } catch (error) {
        console.error(`Failed to fetch persons sitemap page ${page}`, error);
    }

    const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  ${personUrls}
</urlset>`;

    return new Response(xml, {
        headers: {
            'Content-Type': 'application/xml',
            'Cache-Control': 'public, max-age=3600, s-maxage=3600',
        },
    });
}
