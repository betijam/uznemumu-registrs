"use client";

import { useState, useEffect } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer"; // Assuming we have a footer, or I should omit it if not certain
import HeroSearch from "@/components/dashboard/HeroSearch";
import MarketPulse from "@/components/dashboard/MarketPulse";
import BentoGrid from "@/components/dashboard/BentoGrid";
import Link from "next/link";

interface DashboardData {
  pulse: {
    active_companies: number;
    new_this_week: number;
    liquidated_this_week: number;
    total_turnover: number;
  };
  tops: {
    turnover: any[];
    profit: any[];
    salaries: any[];
  };
  gazeles: any[];
  latest_registered: any[];
}

export default function Home() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchDashboard() {
      try {
        const res = await fetch('/api/home/dashboard');
        if (res.ok) {
          const json = await res.json();
          setData(json);
        } else {
          console.error("Dashboard fetch failed");
        }
      } catch (error) {
        console.error("Dashboard error:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchDashboard();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50/50">
      <Navbar />

      {/* Hero Section */}
      <div className="relative pt-20 pb-16 md:pt-32 md:pb-24 overflow-hidden">
        {/* Background Decor */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[500px] bg-gradient-to-b from-purple-50 to-transparent -z-10"></div>
        <div className="absolute top-20 right-0 w-64 h-64 bg-purple-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
        <div className="absolute top-20 left-0 w-64 h-64 bg-yellow-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>

        <div className="container mx-auto px-4 text-center relative z-10">
          <h1 className="text-4xl md:text-6xl font-extrabold text-gray-900 mb-6 tracking-tight">
            Latvijas Uzņēmumu <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-blue-500">Reģistrs 2.0</span>
          </h1>
          <p className="text-lg md:text-xl text-gray-600 mb-10 max-w-2xl mx-auto">
            Gudrāka meklēšana. Dziļāka analītika. Visi dati vienuviet.
          </p>

          <HeroSearch />

          <div className="mt-8 flex justify-center gap-4 text-sm text-gray-500 flex-wrap">
            <span>Populāri:</span>
            <Link href="/explore?sort_by=turnover&order=desc" className="hover:text-purple-600 hover:underline">TOP 100</Link>
            <Link href="/industries/47" className="hover:text-purple-600 hover:underline">Mazumtirdzniecība</Link>
            <Link href="/industries/41" className="hover:text-purple-600 hover:underline">Būvniecība</Link>
            <Link href="/industries/62" className="hover:text-purple-600 hover:underline">IT pakalpojumi</Link>
          </div>
        </div>
      </div>

      {/* Dashboard Content */}
      <div className="container mx-auto px-4 pb-20">
        <MarketPulse data={data ? data.pulse : null} loading={loading} />

        {loading ? (
          <div className="w-full h-96 bg-gray-100 rounded-2xl animate-pulse"></div>
        ) : data ? (
          <BentoGrid
            tops={data.tops}
            latest={data.latest_registered}
            gazeles={data.gazeles}
            year={new Date().getFullYear()}
          />
        ) : (
          <div className="text-center py-20 text-gray-500">
            Neizdevās ielādēt datus. Lūdzu mēģiniet vēlāk.
          </div>
        )}
      </div>

      {/* Footer space if needed */}
      <div className="h-12"></div>
    </div>
  );
}
