import { defineRouting } from 'next-intl/routing';
import { createNavigation } from 'next-intl/navigation';

export const routing = defineRouting({
    // A list of all locales that are supported
    locales: ['lv', 'en', 'ru'],

    // Used when no locale matches
    defaultLocale: 'lv',

    // Always show locale in URL path (e.g., /en/industries, /lv/industries)
    localePrefix: 'always'
});

// Lightweight wrappers around Next.js' navigation APIs
// that will consider the routing configuration
export const { Link, redirect, usePathname, useRouter } =
    createNavigation(routing);
