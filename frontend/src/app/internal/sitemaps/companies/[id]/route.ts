export const dynamic = 'force-dynamic';
export const revalidate = 3600;

export async function GET(request: Request, { params }: { params: Promise<{ id: string }> }) {
    console.log('[Sitemap Companies] Route called');

    const baseUrl = 'https://company360.lv';

    try {
        // Await params to satisfy Next.js 15+ type requirements
        const { id } = await params;
        const page = parseInt(id) || 1;
        console.log('[Sitemap Companies] Page:', page);

        const apiUrl = process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || 'https://company360.lv';
        console.log('[Sitemap Companies] API URL:', apiUrl);

        let companyUrls = '';

        try {
            const fetchUrl = `${apiUrl}/api/companies/sitemap-ids?page=${page}&limit=50000`;
            console.log('[Sitemap Companies] Fetching from:', fetchUrl);

            const res = await fetch(fetchUrl, {
                next: { revalidate: 3600 }
            });

            console.log('[Sitemap Companies] Fetch status:', res.status, res.statusText);

            if (res.ok) {
                const data = await res.json();
                console.log('[Sitemap Companies] Received', data.ids?.length || 0, 'companies');

                // data.ids is Array<{regcode, updated_at}>
                companyUrls = data.ids.map((c: any) => `
  <url>
    <loc>${baseUrl}/company/${c.regcode}</loc>
    <lastmod>${c.updated_at || new Date().toISOString()}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>`).join('');

                console.log('[Sitemap Companies] Generated URLs, total XML length:', companyUrls.length);
            } else {
                console.error('[Sitemap Companies] Fetch failed:', res.status, await res.text());
            }
        } catch (fetchError) {
            console.error('[Sitemap Companies] Fetch error:', fetchError);
        }

        const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  ${companyUrls}
</urlset>`;

        console.log('[Sitemap Companies] Returning XML, length:', xml.length);

        return new Response(xml, {
            headers: {
                'Content-Type': 'application/xml',
                'Cache-Control': 'public, max-age=3600, s-maxage=3600',
            },
        });
    } catch (error) {
        console.error('[Sitemap Companies] Top-level error:', error);
        // Return empty sitemap on error
        return new Response(`<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
</urlset>`, {
            headers: {
                'Content-Type': 'application/xml',
            },
        });
    }
}
