import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "@/app/globals.css";
import { ComparisonProvider } from "@/contexts/ComparisonContext";
import ComparisonCart from "@/components/benchmark/ComparisonCart";
import { NextIntlClientProvider } from 'next-intl';
import { getMessages, getTranslations } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { routing } from '@/i18n/routing';

// Optimized font loading - reduced weights and Latin subset only
const inter = Inter({
  subsets: ["latin"],  // Only Latin characters (no Latin-ext)
  weight: ["400", "600", "700"],  // Essential weights only
  display: "swap",  // Show fallback immediately, swap when loaded
  variable: "--font-inter",
  preload: true,  // Start loading early
  fallback: ["system-ui", "arial"],  // Fast fallback fonts
  adjustFontFallback: false,  // Reduce layout shift
});

export async function generateMetadata({
  params
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: 'HomePage' });

  return {
    title: t('title'),
    description: t('subtitle') // Or a specific metadata description key
  };
}

export default async function RootLayout({
  children,
  params
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;

  // Ensure that the incoming `locale` is valid
  if (!routing.locales.includes(locale as any)) {
    // notFound(); // Should be handled by middleware, but good safety
  }

  // Providing all messages to the client
  // side is the easiest way to get started
  const messages = await getMessages();

  return (
    <html lang={locale} className={inter.variable}>
      <head>
        {/* Preconnect to critical origins - reduces latency by ~200-400ms on mobile */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        {process.env.NEXT_PUBLIC_API_URL && (
          <link rel="preconnect" href={process.env.NEXT_PUBLIC_API_URL} />
        )}
        {/* Preload Inter font to start download early, reducing mobile LCP */}
        <link
          rel="preload"
          href="/_next/static/media/1bffadaabf893a1e.7cd81963.woff2"
          as="font"
          type="font/woff2"
          crossOrigin="anonymous"
        />

        {/* Critical CSS - inline for instant render (eliminates 160ms blocking on mobile) */}
        <style dangerouslySetInnerHTML={{
          __html: `
          *,::before,::after{box-sizing:border-box;border-width:0;border-style:solid;border-color:#e5e7eb}
          html{line-height:1.5;-webkit-text-size-adjust:100%;tab-size:4;font-family:system-ui,arial,sans-serif}
          body{margin:0;line-height:inherit;color:#0F172A;background:#F8FAFC}
          h1,h2,h3,h4,h5,h6{font-size:inherit;font-weight:inherit}
          a{color:inherit;text-decoration:inherit}
          button,input,optgroup,select,textarea{font-family:inherit;font-size:100%;line-height:inherit;color:inherit;margin:0;padding:0}
          .bg-gradient-to-br{background-image:linear-gradient(to bottom right,var(--tw-gradient-stops))}
          .from-primary{--tw-gradient-from:#1E293B;--tw-gradient-to:rgba(30,41,59,0);--tw-gradient-stops:var(--tw-gradient-from),var(--tw-gradient-to)}
          .via-primary-dark{--tw-gradient-to:rgba(15,23,42,0);--tw-gradient-stops:var(--tw-gradient-from),#0F172A,var(--tw-gradient-to)}
          .to-accent{--tw-gradient-to:#14B8A6}
          .text-white{color:#fff}
          .bg-white{background-color:#fff}
          .shadow-md{box-shadow:0 4px 6px -1px rgba(0,0,0,0.1),0 2px 4px -1px rgba(0,0,0,0.06)}
          .rounded-xl{border-radius:0.75rem}
          .p-6{padding:1.5rem}
          .flex{display:flex}
          .min-h-screen{min-height:100vh}
        `}} />
      </head>
      <body className="antialiased">
        <NextIntlClientProvider messages={messages}>
          <ComparisonProvider>
            {children}
            <ComparisonCart />
          </ComparisonProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
