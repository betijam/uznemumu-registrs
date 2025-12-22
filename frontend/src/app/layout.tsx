import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

// Optimized font loading - eliminates render-blocking request
const inter = Inter({
  subsets: ["latin"],
  display: "swap",  // Shows fallback font immediately
  variable: "--font-inter",
  preload: true,
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
