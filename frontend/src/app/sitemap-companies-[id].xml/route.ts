export const dynamic = 'force-dynamic';

export async function GET(request: Request, { params }: { params: { id: string } }) {
    const baseUrl = 'https://company360.lv';
    // params.id will be "1", "2", etc. from the filename sitemap-companies-[id].xml
    // But strictly, Next.js dynamic routes for [folder] matching "sitemap-companies-[id].xml" 
    // might struggle if the route parameter isn't cleanly extracted. 
    // Next.js Route Handlers don't support regex filenames like [name].xml directly easily.
    // We need to verify if `app/sitemap-companies-[id].xml/route.ts` works or if `app/sitemap-companies/[id]/route.ts` is needed alongside a rewrite.
    // The user requirement is `/sitemap-companies-1.xml`. 
    // Standard Next.js pattern: `app/sitemap-companies-[id]/route.ts` (if supported? No, [id] folder means /sitemap-companies-id/...)
    // Wait, Next.js `sitemap.ts` (generation) supports generating multiple sitemaps via `generateSitemaps`.
    // BUT valid XML response is needed.
    // If we assume a Rewrite or strict folder naming, `app/sitemap-companies-[id]/route.ts` would map to `/sitemap-companies-[id]`.
    // To get `.xml` extension, we typically do `app/sitemap-companies-[id].xml/route.ts` which treats `[id]` as dynamic part.

    // EXTRACT ID from URL since [id] folder param logic can be tricky with extensions.
    const url = new URL(request.url);
    const path = url.pathname; // "/sitemap-companies-1.xml"
    const match = path.match(/sitemap-companies-(\d+)\.xml/);
    const page = match ? parseInt(match[1]) : 1;

    const apiUrl = process.env.INTERNAL_API_URL || 'http://backend:8000';
    let companyUrls = '';

    try {
        const res = await fetch(`${apiUrl}/api/companies/sitemap-ids?page=${page}&limit=50000`, {
            next: { revalidate: 3600 }
        });

        if (res.ok) {
            const data = await res.json();
            // data.ids is Array<{regcode, updated_at}>
            companyUrls = data.ids.map((c: any) => `
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
