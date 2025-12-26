import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET(
    request: NextRequest,
    context: { params: Promise<{ id: string }> }
) {
    const { id } = await context.params;
    const { searchParams } = new URL(request.url);
    const year = searchParams.get('year') || '';
    const limit = searchParams.get('limit') || '10';

    try {
        const url = `${API_URL}/regions/${id}/top-companies?limit=${limit}${year ? `&year=${year}` : ''}`;
        const res = await fetch(url, {
            next: { revalidate: 900 }
        });

        if (!res.ok) {
            throw new Error(`API error: ${res.status}`);
        }

        const data = await res.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('Top companies API error:', error);
        return NextResponse.json([], { status: 200 });
    }
}
