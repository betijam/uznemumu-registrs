import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET(
    request: NextRequest,
    { params }: { params: { id: string } }
) {
    const { searchParams } = new URL(request.url);
    const year = searchParams.get('year') || '';
    const limit = searchParams.get('limit') || '10';

    try {
        const url = `${API_URL}/regions/${params.id}/industries?limit=${limit}${year ? `&year=${year}` : ''}`;
        const res = await fetch(url, {
            next: { revalidate: 900 }
        });

        if (!res.ok) {
            throw new Error(`API error: ${res.status}`);
        }

        const data = await res.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('Industries API error:', error);
        return NextResponse.json([], { status: 200 });
    }
}
