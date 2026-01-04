import createMiddleware from 'next-intl/middleware';

export default createMiddleware({
    // A list of all locales that are supported
    locales: ['lv', 'en', 'ru'],

    // Used when no locale matches
    defaultLocale: 'lv'
});

export const config = {
    // Match only internationalized pathnames
    matcher: ['/', '/(lv|en|ru)/:path*']
};
