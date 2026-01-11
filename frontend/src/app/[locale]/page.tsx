import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import HeroSearch from "@/components/dashboard/HeroSearch";
import MarketPulse from "@/components/dashboard/MarketPulse";
import BentoGrid from "@/components/dashboard/BentoGrid";
import Roadmap from "@/components/dashboard/Roadmap";
import { Link } from "@/i18n/routing";
import { getTranslations } from "next-intl/server";

interface DashboardData {
  pulse: {
    active_companies: number;
    total_employees: number;
    avg_salary: number;
    total_turnover: number;
    data_year?: number;
  };
  tops: {
    turnover: any[];
    profit: any[];
    salaries: any[];
  };
  gazeles: any[];
  latest_registered: any[];
}

// Server-side data fetching
async function getDashboardData(): Promise<DashboardData | null> {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

  try {
    const res = await fetch(`${API_BASE_URL}/home/dashboard`, {
      cache: 'no-store', // Always get fresh data
      next: { revalidate: 300 } // Revalidate every 5 minutes
    });

    if (res.ok) {
      return res.json();
    }

    console.error("Dashboard fetch failed:", res.status);
    return null;
  } catch (error) {
    console.error("Dashboard error:", error);
    return null;
  }
}

export default async function Home() {
  const t = await getTranslations('HomePage');
  const data = await getDashboardData();

  return (
    <div className="min-h-screen bg-gray-50/50">
      <Navbar />

      {/* Hero Section */}
      <div className="relative pt-20 pb-16 md:pt-32 md:pb-24 bg-gradient-to-b from-gray-50 to-white z-20">
        {/* Background Decor - Radial Gradients */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-radial from-purple-200/40 via-purple-100/20 to-transparent rounded-full blur-3xl opacity-60"></div>
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-gradient-radial from-blue-200/40 via-blue-100/20 to-transparent rounded-full blur-3xl opacity-60"></div>

        <div className="container mx-auto px-4 text-center relative z-10">
          <h1 className="text-4xl md:text-6xl font-extrabold text-gray-900 mb-6 tracking-tight">
            {t.rich('title', {
              gradient: (chunks) => <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-blue-500">{chunks}</span>
            })}
          </h1>
          <p className="text-lg md:text-xl text-gray-600 mb-10 max-w-2xl mx-auto">
            {t('subtitle')}
          </p>

          <HeroSearch />

          <div className="mt-8 flex justify-center gap-4 text-sm text-gray-500 flex-wrap">
            <span>{t('popular')}</span>
            <Link href="/explore?sort_by=turnover&order=desc" className="hover:text-purple-600 hover:underline">{t('top100')}</Link>
            <Link href="/industries/47" className="hover:text-purple-600 hover:underline">{t('retail')}</Link>
            <Link href="/industries/41" className="hover:text-purple-600 hover:underline">{t('construction')}</Link>
            <Link href="/industries/62" className="hover:text-purple-600 hover:underline">{t('it_services')}</Link>
          </div>
        </div>
      </div>

      {/* Dashboard Content */}
      <div className="container mx-auto px-4 pb-20 relative z-10">
        <MarketPulse data={data ? data.pulse : null} loading={false} />

        {data ? (
          <BentoGrid
            tops={data.tops}
            latest={data.latest_registered}
            gazeles={data.gazeles}
            year={new Date().getFullYear()}
          />
        ) : (
          <div className="text-center py-20 text-gray-500">
            {t('error_loading')}
          </div>
        )}
      </div>

      {/* Roadmap Section */}
      <Roadmap />

      {/* Footer space if needed */}
      <div className="h-12"></div>
    </div>
  );
}
