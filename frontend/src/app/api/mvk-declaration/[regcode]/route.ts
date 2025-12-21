import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ regcode: string }> }
) {
    const { regcode } = await params;
    const searchParams = request.nextUrl.searchParams;
    const year = searchParams.get('year') || '2024';

    const targetUrl = `${API_URL}/companies/${regcode}/mvk-declaration?year=${year}`;
    console.log('[MVK-PROXY] API_URL env:', API_URL);
    console.log('[MVK-PROXY] Target URL:', targetUrl);
    console.log('[MVK-PROXY] Regcode:', regcode);

    try {
        console.log('[MVK-PROXY] Fetching...');
        const res = await fetch(targetUrl, {
            cache: 'no-store',
        });

        console.log('[MVK-PROXY] Response status:', res.status);

        if (!res.ok) {
            const errorText = await res.text();
            console.error('[MVK-PROXY] Error response:', errorText);
            return NextResponse.json({ error: 'Company not found', details: errorText }, { status: 404 });
        }

        const data = await res.json();
        console.log('[MVK-PROXY] Success, returning data');
        return NextResponse.json(data);
    } catch (e) {
        console.error('[MVK-PROXY] Fetch error:', e);
        return NextResponse.json({ error: 'Failed to fetch', details: String(e) }, { status: 500 });
    }
}
