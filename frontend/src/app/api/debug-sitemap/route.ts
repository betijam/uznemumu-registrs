export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
    const msgs: any = {
        timestamp: new Date().toISOString(),
        env: {
            INTERNAL_API_URL: process.env.INTERNAL_API_URL || '(not set)',
            NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || '(not set)',
        },
        resolvedApiUrl: '',
        testResult: {}
    };

    const internalApi = process.env.INTERNAL_API_URL;
    const publicApi = process.env.NEXT_PUBLIC_API_URL || 'https://company360.lv';
    const apiUrl = internalApi || publicApi;
    const apiPathPrefix = internalApi ? '' : '/api';

    msgs.resolvedApiUrl = apiUrl;
    msgs.apiPathPrefix = apiPathPrefix;

    const testUrl = `${apiUrl}${apiPathPrefix}/companies/sitemap-ids?page=1&limit=5`;

    try {
        const start = Date.now();
        const res = await fetch(testUrl, {
            cache: 'no-store',
            next: { revalidate: 0 }
        });
        const duration = Date.now() - start;

        const text = await res.text();
        let json = null;
        try {
            json = JSON.parse(text);
        } catch (e) {
            // ignore
        }

        msgs.testResult = {
            url: testUrl,
            status: res.status,
            statusText: res.statusText,
            duration: `${duration}ms`,
            responseSize: text.length,
            isJson: !!json,
            preview: json || text.substring(0, 500)
        };

    } catch (e: any) {
        msgs.testResult = {
            url: testUrl,
            error: e.message,
            cause: e.cause ? JSON.stringify(e.cause) : undefined
        };
    }

    return Response.json(msgs);
}
