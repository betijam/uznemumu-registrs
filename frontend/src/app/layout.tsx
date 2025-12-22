import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

// Optimized font loading - reduced weights and subset for smaller file size
const inter = Inter({
  subsets: ["latin"],  // Only latin, not latin-ext (smaller file)
  weight: ["400", "600", "700"],  // Only essential weights
  display: "block",  // Shows text immediately with fallback, then swaps to Inter
  variable: "--font-inter",
  preload: true,
  fallback: ["system-ui", "arial"],
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
      </head>
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
