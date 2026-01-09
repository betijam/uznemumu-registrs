export const dynamic = 'force-dynamic';

export async function GET(request: Request, { params }: { params: Promise<{ id: string }> }) {
    const baseUrl = 'https://company360.lv';

    // In Next.js 15+, params is a Promise.
    // However, since we are in a sitemap-companies-[id].xml folder, 
    // we need to see what params actually captures. 
    // If the file is `app/sitemap-companies-[id].xml/route.ts`, 
    // and the URL is `/sitemap-companies-1.xml`, 
    // Dynamic segments are usually `[folder]`. 
    // Here the folder name is literal `sitemap-companies-[id].xml`. 
    // Wait, Next.js doesn't parse square brackets inside a folder name like that as a partial match usually.
    // Usually you do `app/sitemap-companies/[id]/route.ts` -> `/sitemap-companies/1`.
    // BUT the user required `/sitemap-companies-1.xml`.
    // The previous implementation relied on regex on `request.url`.
    // The previous implementation used `match` on `request.url` which is robust regardless of params.
    // BUT valid type check requires matching the Next.js signature.

    // We strictly fix the type signature first.
    const { id } = await params; // although we might not use it if we rely on regex, we must await it to satisfy type check if we destructure it. 
    // Actually, if we don't define the route with `[id]` folder properly, `params` might be empty.
    // Let's rely on the regex as implemented before, but fix the signature.

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
