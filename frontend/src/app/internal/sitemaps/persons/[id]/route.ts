export const dynamic = 'force-dynamic';
export const revalidate = 3600;

export async function GET(request: Request, { params }: { params: Promise<{ id: string }> }) {
    console.log('[Sitemap Persons] Route called');

    const baseUrl = 'https://company360.lv';

    try {
        const { id } = await params;
        const page = parseInt(id) || 1;
        console.log('[Sitemap Persons] Page:', page);

        const apiUrl = process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || 'https://company360.lv';
        console.log('[Sitemap Persons] API URL:', apiUrl);

        let personUrls = '';

        try {
            const fetchUrl = `${apiUrl}/api/persons/sitemap-ids?page=${page}&limit=50000`;
            console.log('[Sitemap Persons] Fetching from:', fetchUrl);

            const res = await fetch(fetchUrl, {
                next: { revalidate: 3600 }
            });

            console.log('[Sitemap Persons] Fetch status:', res.status, res.statusText);

            if (res.ok) {
                const data = await res.json();
                console.log('[Sitemap Persons] Received', data.ids?.length || 0, 'persons');

                personUrls = data.ids.map((p: any) => `
  <url>
    <loc>${baseUrl}/person/${p.identifier}</loc>
    <lastmod>${p.updated_at || new Date().toISOString()}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>`).join('');

                console.log('[Sitemap Persons] Generated URLs, total XML length:', personUrls.length);
            } else {
                console.error('[Sitemap Persons] Fetch failed:', res.status, await res.text());
            }
        } catch (fetchError) {
            console.error('[Sitemap Persons] Fetch error:', fetchError);
        }

        const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  ${personUrls}
</urlset>`;

        console.log('[Sitemap Persons] Returning XML, length:', xml.length);

        return new Response(xml, {
            headers: {
                'Content-Type': 'application/xml',
                'Cache-Control': 'public, max-age=3600, s-maxage=3600',
            },
        });
    } catch (error) {
        console.error('[Sitemap Persons] Top-level error:', error);
        return new Response(`<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
</urlset>`, {
            headers: {
                'Content-Type': 'application/xml',
            },
        });
    }
}
