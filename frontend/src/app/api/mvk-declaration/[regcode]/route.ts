import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ regcode: string }> }
) {
    const { regcode } = await params;
    const searchParams = request.nextUrl.searchParams;
    const year = searchParams.get('year') || '2024';

    try {
        const res = await fetch(`${API_URL}/companies/${regcode}/mvk-declaration?year=${year}`, {
            cache: 'no-store',
        });

        if (!res.ok) {
            return NextResponse.json({ error: 'Company not found' }, { status: 404 });
        }

        const data = await res.json();
        return NextResponse.json(data);
    } catch (e) {
        console.error('MVK declaration proxy error:', e);
        return NextResponse.json({ error: 'Failed to fetch' }, { status: 500 });
    }
}
