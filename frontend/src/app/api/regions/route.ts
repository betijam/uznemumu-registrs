import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
    const { searchParams } = new URL(request.url);
    const year = searchParams.get('year') || '';
    const metric = searchParams.get('metric') || 'revenue';

    try {
        const url = `${API_URL}/regions/overview?metric=${metric}${year ? `&year=${year}` : ''}`;
        const res = await fetch(url, {
            next: { revalidate: 900 } // Cache for 15 minutes
        });

        if (!res.ok) {
            throw new Error(`API error: ${res.status}`);
        }

        const data = await res.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('Regions API error:', error);
        return NextResponse.json(
            { error: 'Failed to fetch regions data' },
            { status: 500 }
        );
    }
}
