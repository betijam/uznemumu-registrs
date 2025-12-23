import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

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

export const metadata: Metadata = {
  title: "UR Portāls - Uzņēmumu Reģistrs",
  description: "Latvijas uzņēmumu reģistra dati, finanšu rādītāji un MVK deklarācijas",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="lv" className={inter.variable}>
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
      </head>
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
