import createMiddleware from 'next-intl/middleware';
import { routing } from './i18n/routing';
import { NextRequest, NextResponse } from 'next/server';

const intlMiddleware = createMiddleware(routing);

export default function middleware(request: NextRequest) {
    const { pathname } = request.nextUrl;

    // 1. Define what counts as a profile page view
    // Regex: Only /company/digits or /person/code, with optional locale
    // Does NOT match: /company/.../graph, /api/..., etc.
    const isProfilePage = /^\/(en|lv|ru)?\/(company|person)\/([a-zA-Z0-9-]+)$/.test(pathname);

    // 2. Check if this is a prefetch/data request (don't count these!)
    const isPrefetch =
        request.headers.get('next-router-prefetch') === 'true' ||
        request.headers.get('purpose') === 'prefetch' ||
        request.headers.get('x-middleware-prefetch') === '1';

    // 3. Calculate View Count
    let viewCount = 0;
    const cookie = request.cookies.get('c360_free_views');
    if (cookie?.value) {
        const parsed = parseInt(cookie.value, 10);
        viewCount = isNaN(parsed) ? 0 : parsed;
    }

    // Increment only on actual profile page loads (not prefetch)
    let newViewCount = viewCount;
    if (isProfilePage && !isPrefetch) {
        newViewCount = viewCount + 1;
    }

    // 4. Prepare headers for Server Components
    const requestHeaders = new Headers(request.headers);
    requestHeaders.set('X-View-Count', newViewCount.toString());

    // Propagate Auth Token from cookie to header
    const token = request.cookies.get('token');
    if (token?.value) {
        requestHeaders.set('Authorization', `Bearer ${token.value}`);
    }

    // Create new request with updated headers
    const newRequest = new NextRequest(request, {
        headers: requestHeaders,
    });

    // 5. Call next-intl middleware
    const response = intlMiddleware(newRequest);

    // 6. Set Cookie on Response (if profile page and not prefetch)
    if (isProfilePage && !isPrefetch) {
        response.cookies.set('c360_free_views', newViewCount.toString(), {
            maxAge: 60 * 60 * 24 * 30, // 30 days
            path: '/',
            httpOnly: true,  // Security: not accessible via JS
            sameSite: 'lax'
        });
        // Debug header
        response.headers.set('X-Debug-View-Count', newViewCount.toString());
    }

    return response;
}

export const config = {
    // Exclude static files and API routes from middleware
    matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
