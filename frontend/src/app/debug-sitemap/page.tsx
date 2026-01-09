import { headers } from 'next/headers';

export const dynamic = 'force-dynamic';

export default async function DebugSitemap() {
    const headersList = await headers();
    const msgs: string[] = [];

    msgs.push('--- Debug Sitemap Start ---');
    msgs.push(`Time: ${new Date().toISOString()}`);

    const internalApiUrl = process.env.INTERNAL_API_URL;
    const publicApiUrl = process.env.NEXT_PUBLIC_API_URL;
    const defaultUrl = 'https://company360.lv';

    msgs.push(`Env INTERNAL_API_URL: ${internalApiUrl ? internalApiUrl : '(not set)'}`);
    msgs.push(`Env NEXT_PUBLIC_API_URL: ${publicApiUrl ? publicApiUrl : '(not set)'}`);

    const apiUrl = internalApiUrl || publicApiUrl || defaultUrl;
    msgs.push(`Resolved API URL: ${apiUrl}`);

    // Test 1: Fetch small batch
    const testUrl = `${apiUrl}/api/companies/sitemap-ids?page=1&limit=5`;
    msgs.push(`\nTest 1: Fetching ${testUrl}`);

    try {
        const start = Date.now();
        const res = await fetch(testUrl, {
            cache: 'no-store',
            headers: {
                'Cache-Control': 'no-cache'
            }
        });
        const duration = Date.now() - start;
        msgs.push(`Status: ${res.status} ${res.statusText}`);
        msgs.push(`Duration: ${duration}ms`);

        const text = await res.text();
        msgs.push(`Response Size: ${text.length} chars`);

        if (res.ok) {
            try {
                const json = JSON.parse(text);
                msgs.push(`JSON Valid: Yes`);
                msgs.push(`Arrays Ids Length: ${json.ids?.length}`);
                if (json.ids?.length > 0) {
                    msgs.push(`First ID: ${JSON.stringify(json.ids[0])}`);
                }
            } catch (e) {
                msgs.push(`JSON Parse Error: ${e}`);
                msgs.push(`Preview: ${text.substring(0, 200)}...`);
            }
        } else {
            msgs.push(`Error Body: ${text.substring(0, 500)}`);
        }
    } catch (e: any) {
        msgs.push(`FETCH EXCEPTION: ${e.message}`);
        if (e.cause) msgs.push(`Cause: ${JSON.stringify(e.cause)}`);
    }

    return (
        <div className="p-10 font-mono text-sm">
            <h1 className="text-xl font-bold mb-4">Sitemap Debugger</h1>
            <div className="bg-gray-100 p-4 rounded whitespace-pre-wrap border border-gray-300">
                {msgs.join('\n')}
            </div>
            <div className="mt-4 text-gray-500 text-xs">
                Generated at {new Date().toLocaleString()}
            </div>
        </div>
    );
}
