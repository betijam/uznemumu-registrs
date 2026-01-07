import { NextRequest, NextResponse } from 'next/server';

// Check all possible env var names for backend URL
const API_BASE_URL = process.env.BACKEND_URL || process.env.INTERNAL_API_URL || process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export async function POST(request: NextRequest) {
    try {
        const formData = await request.formData();

        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();

        if (!response.ok) {
            return NextResponse.json(data, { status: response.status });
        }

        return NextResponse.json(data);
    } catch (error) {
        console.error('Login error:', error);
        return NextResponse.json(
            { detail: 'Login failed. Please try again.' },
            { status: 500 }
        );
    }
}
