import type { Metadata } from "next";
import Script from "next/script";
import { Inter } from "next/font/google";
import "@/app/globals.css";
import "leaflet/dist/leaflet.css";
import { ComparisonProvider } from "@/contexts/ComparisonContext";
import ComparisonCart from "@/components/benchmark/ComparisonCart";
import CookieBanner from "@/components/CookieBanner";
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

  // Clean title: Remove HTML tags (like <gradient>) for metadata
  const cleanTitle = t('title').replace(/<[^>]+>/g, '');

  return {
    title: cleanTitle,
    description: t('subtitle'),
    metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || 'https://company360.lv'),
    icons: {
      icon: '/icon.png',
      apple: '/apple-icon.png'
    },
    openGraph: {
      title: cleanTitle,
      description: t('subtitle'),
      url: process.env.NEXT_PUBLIC_APP_URL || 'https://company360.lv',
      siteName: 'Company 360',
      images: [
        {
          url: '/icon.png', // Fallback to icon if OG image missing
          width: 512,       // Standard icon size usually
          height: 512,
        }
      ],
      locale: locale,
      type: 'website',
    },
  };
}

import Footer from "@/components/Footer";
import FeedbackButton from "@/components/FeedbackButton";

// ... existing imports ...

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
        {/* Microsoft Clarity Analytics */}
        <Script id="ms-clarity" strategy="afterInteractive">
          {`
            (function(c,l,a,r,i,t,y){
                c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
                t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
                y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
            })(window, document, "clarity", "script", "v0agfq27f6");
          `}
        </Script>

        {/* Google Analytics (GA4) */}
        <Script
          src="https://www.googletagmanager.com/gtag/js?id=G-3ZVGKT4KYF"
          strategy="afterInteractive"
        />
        <Script id="google-analytics" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'G-3ZVGKT4KYF');
          `}
        </Script>
      </head>
      <body className="antialiased flex flex-col min-h-screen">
        <NextIntlClientProvider messages={messages}>
          <ComparisonProvider>
            {children}
            <Footer />
            <ComparisonCart />
            <CookieBanner />
            <FeedbackButton />
          </ComparisonProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
