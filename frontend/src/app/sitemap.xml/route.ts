export const revalidate = 3600; // Cache for 1 hour

function escapeXml(str: string) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

async function fetchTotal(apiUrl: string, path: string): Promise<number> {
  const res = await fetch(`${apiUrl}${path}`, { next: { revalidate: 3600 } });
  if (!res.ok) return 0;
  const data = await res.json();
  return Number(data.total || 0);
}

export async function GET() {
  const baseUrl = 'https://company360.lv';
  const sitemaps: string[] = [
    `${baseUrl}/sitemap-static.xml`,
    `${baseUrl}/sitemap-industries.xml`,
  ];

  // Determine API URL and path prefix
  // If INTERNAL_API_URL is set, we assume it matches the backend directly (no /api prefix)
  // If not, we fall back to NEXT_PUBLIC_API_URL or default, which are likely frontend proxies (requiring /api)
  const internalApi = process.env.INTERNAL_API_URL;
  const publicApi = process.env.NEXT_PUBLIC_API_URL || 'https://company360.lv';

  const apiUrl = internalApi || publicApi;
  const apiPathPrefix = internalApi ? '' : '/api';

  const limit = 50000;

  console.log('[Sitemap Index] Using API URL:', apiUrl, 'Prefix:', apiPathPrefix);

  // 1) Company sitemaps
  try {
    const endpoint = `${apiPathPrefix}/companies/sitemap-info`;
    console.log('[Sitemap Index] Fetching companies count from:', `${apiUrl}${endpoint}`);
    const totalCompanies = await fetchTotal(apiUrl, endpoint);
    console.log('[Sitemap Index] Total companies:', totalCompanies);
    if (totalCompanies > 0) {
      const pages = Math.ceil(totalCompanies / limit);
      console.log('[Sitemap Index] Generating', pages, 'company sitemap pages');
      for (let i = 1; i <= pages; i++) {
        sitemaps.push(`${baseUrl}/sitemap-companies-${i}.xml`);
      }
    }
  } catch (error) {
    console.error('Failed to fetch total companies for sitemap index:', error);
  }

  // 2) Person sitemaps
  try {
    const endpoint = `${apiPathPrefix}/persons/sitemap-info`;
    console.log('[Sitemap Index] Fetching persons count from:', `${apiUrl}${endpoint}`);
    const totalPersons = await fetchTotal(apiUrl, endpoint);
    console.log('[Sitemap Index] Total persons:', totalPersons);
    if (totalPersons > 0) {
      const pages = Math.ceil(totalPersons / limit);
      console.log('[Sitemap Index] Generating', pages, 'person sitemap pages');
      for (let i = 1; i <= pages; i++) {
        sitemaps.push(`${baseUrl}/sitemap-persons-${i}.xml`);
      }
    }
  } catch (error) {
    console.error('Failed to fetch total persons for sitemap index:', error);
  }

  console.log('[Sitemap Index] Final sitemap list:', sitemaps);

  const xml =
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
    sitemaps
      .map((url) => {
        const loc = escapeXml(url);
        return `  <sitemap><loc>${loc}</loc></sitemap>`;
      })
      .join('\n') +
    `\n</sitemapindex>\n`;

  return new Response(xml, {
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
      'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=86400',
    },
  });
}
