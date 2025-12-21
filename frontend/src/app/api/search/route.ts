import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export async function GET(request: NextRequest) {
    const searchParams = request.nextUrl.searchParams;
    const q = searchParams.get('q') || '';

    if (q.length < 2) {
        return NextResponse.json([]);
    }

    try {
        const res = await fetch(`${API_URL}/search?q=${encodeURIComponent(q)}`, {
            cache: 'no-store',
        });

        if (!res.ok) {
            return NextResponse.json([]);
        }

        const data = await res.json();
        return NextResponse.json(data);
    } catch (e) {
        console.error('Search proxy error:', e);
        return NextResponse.json([]);
    }
}
