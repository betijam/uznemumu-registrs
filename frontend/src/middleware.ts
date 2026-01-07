import createMiddleware from 'next-intl/middleware';
import { routing } from './i18n/routing';
import { NextRequest, NextResponse } from 'next/server';

const intlMiddleware = createMiddleware(routing);

export default function middleware(request: NextRequest) {
    const { pathname } = request.nextUrl;

    // Check if path is for Company or Person profile (excluding API/static)
    // Matches /en/company/123 or /company/123
    const isProfilePage = /\/(company|person)\/\d+/.test(pathname) ||
        /\/(company|person)\/[^\/]+$/.test(pathname); // Handle hashes/slugs

    // Run I18n Middleware first to get the base response
    // We need to pass the request. If we want SC to see the new count, we might need to modify headers.
    // However, simplest way for SC to send to Backend is to read the header we set.

    // 1. Calculate View Count
    let viewCount = 0;
    const cookie = request.cookies.get('c360_free_views');
    if (cookie?.value) {
        viewCount = parseInt(cookie.value, 10);
        if (isNaN(viewCount)) viewCount = 0;
    }

    // Increment only on profile pages
    let newViewCount = viewCount;
    if (isProfilePage) {
        // Only increment if not already valid auth (optional optimization, but backend checks auth too)
        // We just increment blindly for simplicity, or check auth token?
        // Backend logic: "JA view_count < 2 ... Serveris pievieno".
        // If we do it in middleware, we do it here.
        newViewCount = viewCount + 1;
    }

    // 2. Prepare headers for Server Components
    const requestHeaders = new Headers(request.headers);
    requestHeaders.set('X-View-Count', newViewCount.toString());

    // Propagate Auth Token
    const token = request.cookies.get('token');
    if (token?.value) {
        requestHeaders.set('Authorization', `Bearer ${token.value}`);
    }

    // Create new request with updated headers
    const newRequest = new NextRequest(request, {
        headers: requestHeaders,
    });

    // 3. Call next-intl with new request
    const response = intlMiddleware(newRequest);

    // 4. Set Cookie on Response (if changed)
    if (isProfilePage) {
        response.cookies.set('c360_free_views', newViewCount.toString(), {
            maxAge: 60 * 60 * 24 * 30, // 30 days
            path: '/',
            sameSite: 'lax'
        });
    }

    return response;
}

export const config = {
    // Match only internationalized pathnames
    matcher: ['/((?!api|_next|_vercel|.*\\..*).*)']
};
