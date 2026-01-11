import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const token = searchParams.get('token');

        if (!token) {
            return NextResponse.json(
                { detail: 'Token is required' },
                { status: 400 }
            );
        }

        const backendUrl = process.env.BACKEND_URL || process.env.INTERNAL_API_URL || process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
        const res = await fetch(`${backendUrl}/auth/verify-email?token=${token}`, {
            method: 'GET',
        });

        const data = await res.json();

        return NextResponse.json(data, { status: res.status });
    } catch (error) {
        console.error('Verify email API error:', error);
        return NextResponse.json(
            { detail: 'Internal server error' },
            { status: 500 }
        );
    }
}
