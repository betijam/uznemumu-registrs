import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

// Optimized font loading - reduced weights for smaller file size
const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "600", "700"],  // Only essential weights, reduces file size
  display: "optional",  // Faster LCP on slow mobile connections
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
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
