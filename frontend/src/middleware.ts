import createMiddleware from 'next-intl/middleware';
import { routing } from './i18n/routing';
import { NextRequest, NextResponse } from 'next/server';

const intlMiddleware = createMiddleware(routing);

export default function middleware(request: NextRequest) {
    const { pathname } = request.nextUrl;

    // 1. Define profile pages (company/person detail pages)
    const isProfilePage = /^\/(en|lv|ru)?\/(company|person)\/([a-zA-Z0-9-]+)$/.test(pathname);

    // 2. ENHANCED Prefetch detection
    // Next.js App Router uses 'next-router-prefetch' and 'purpose' headers
    // Chrome/Safari sometimes send 'Sec-Purpose: prefetch'
    const headers = request.headers;
    const isPrefetch =
        headers.get('next-router-prefetch') === '1' ||
        headers.get('purpose') === 'prefetch' ||
        headers.get('sec-purpose') === 'prefetch' ||
        headers.get('sec-fetch-purpose') === 'prefetch' ||
        headers.get('x-middleware-prefetch') === '1';

    // 3. Read current view count from cookie
    let viewCount = 0;
    const cookie = request.cookies.get('c360_free_views');
    if (cookie?.value) {
        const parsed = parseInt(cookie.value, 10);
        viewCount = isNaN(parsed) ? 0 : parsed;
    }

    // 4. Increment ONLY for real page views (not prefetch)
    let newViewCount = viewCount;
    if (isProfilePage && !isPrefetch) {
        newViewCount = viewCount + 1;
        console.log(`[Middleware] Counting view for ${pathname}. New count: ${newViewCount}`);
    } else if (isProfilePage && isPrefetch) {
        console.log(`[Middleware] Ignoring prefetch for ${pathname}`);
    }

    // 5. Prepare headers for Server Components
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

    // 6. Call next-intl middleware
    const response = intlMiddleware(newRequest);

    // 7. Set Cookie on Response (only for real views, not prefetch)
    if (isProfilePage && !isPrefetch) {
        response.cookies.set('c360_free_views', newViewCount.toString(), {
            maxAge: 60 * 60 * 24, // 1 day (reset daily)
            path: '/',
            httpOnly: true,
            sameSite: 'lax'
        });
    }

    return response;
}

export const config = {
    // Exclude API routes, static files, sitemaps, and robots.txt from middleware
    matcher: ['/((?!api|_next/static|_next/image|favicon.ico|sitemap|robots|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)'],
};
