import Navbar from "@/components/Navbar";
import SearchInput from "@/components/SearchInput";
import Link from "next/link";

// Fetch real statistics from backend
async function getStats() {
  // On Railway, always use the public URL (NEXT_PUBLIC_API_URL)
  // Internal Docker network (INTERNAL_API_URL) only works locally
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

  try {
    const res = await fetch(`${API_BASE_URL}/stats`, {
      cache: "no-store",
      next: { revalidate: 3600 }
    });
    if (!res.ok) return null;
    return res.json();
  } catch (e) {
    console.error('Failed to fetch stats:', e);
    return null;
  }
}

export default async function Home() {
  const stats = await getStats();

  // Default values if API fails
  const dailyStats = stats?.daily_stats || { new_today: 0, change: 0 };
  const topCompany = stats?.top_earner || { name: "N/A", detail: "" };
  const weeklyProcurements = stats?.weekly_procurements || { amount: "0 €", detail: "Nav datu" };

  return (
    <main className="min-h-screen bg-background">
      <Navbar />

      {/* Hero Section */}
      <div className="relative bg-gradient-to-br from-primary via-primary-dark to-accent overflow-hidden">
        {/* Background decorative elements */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-96 h-96 bg-white rounded-full filter blur-3xl"></div>
          <div className="absolute bottom-0 right-0 w-96 h-96 bg-accent rounded-full filter blur-3xl"></div>
        </div>

        <div className="relative z-10 pt-24 pb-32">
          <div className="text-center">
            <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold text-white mb-6">
              Latvijas Uzņēmumu Reģistrs un<br />Analītika
            </h1>
            <p className="text-lg sm:text-xl text-gray-300 mb-10 max-w-3xl mx-auto">
              Ātra, uzticama un detalizēta informācija par vairāk nekā 200,000 Latvijas uzņēmumiem. Finanšu dati, amatpersonas un vēsture.
            </p>

            {/* Search Bar */}
            <div className="max-w-3xl mx-auto mb-8">
              <SearchInput className="shadow-2xl" />
            </div>

            {/* Popular Tags */}
            <div className="flex flex-wrap justify-center gap-2 mb-4">
              <span className="text-sm text-gray-400">Populāri:</span>
              {["Būvniecība", "IT pakalpojumi", "TOP 100", "Lauksaimniecība", "Mazumtirdzniecība"].map((tag) => (
                <Link
                  key={tag}
                  href={`/search?q=${encodeURIComponent(tag)}`}
                  className="px-3 py-1 bg-white/10 hover:bg-white/20 text-white text-sm rounded-full transition-colors backdrop-blur-sm"
                >
                  {tag}
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Professional Data Analytics Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-12 pb-16 relative z-20">
        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          {/* Daily Stats Card */}
          <div className="bg-white rounded-xl shadow-card hover:shadow-card-hover transition-shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-500">Dienas statistika</h3>
              <svg className="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <p className="text-4xl font-bold text-primary mb-1">{dailyStats.new_today}</p>
            <p className="text-xs text-gray-500">
              Jauni uzņēmumi / {dailyStats.change >= 0 ? '+' : ''}{dailyStats.change} šodien
            </p>
          </div>

          {/* Top Earner Card */}
          <div className="bg-white rounded-xl shadow-card hover:shadow-card-hover transition-shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-500">TOP Pelnošie</h3>
              <svg className="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <p className="text-2xl font-bold text-primary mb-1">{topCompany.name}</p>
            <p className="text-xs text-gray-500">{topCompany.detail}</p>
          </div>

          {/* Weekly Procurements Card */}
          <div className="bg-white rounded-xl shadow-card hover:shadow-card-hover transition-shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-500">Nedēļas iepirkumi</h3>
              <svg className="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-4xl font-bold text-primary mb-1">{weeklyProcurements.amount}</p>
            <p className="text-xs text-gray-500">{weeklyProcurements.detail}</p>
          </div>
        </div>

        {/* Professional Data Analytics Section */}
        <div className="bg-white rounded-xl shadow-card p-8">
          <h2 className="text-2xl font-bold text-primary mb-4">Profesionāla datu analītika</h2>
          <p className="text-gray-600 mb-6">
            Mūsu platforma piedāvā padziļinātu ieskatu uzņēmumu darbībā,
            apvienojot publiskos reģistrus ar viedo analītiku.
          </p>
          <ul className="space-y-3">
            <li className="flex items-start">
              <svg className="w-5 h-5 text-accent mr-3 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span className="text-gray-700">Vēsturiskie finanšu dati un tendences</span>
            </li>
            <li className="flex items-start">
              <svg className="w-5 h-5 text-accent mr-3 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span className="text-gray-700">Amatpersonu un īpašnieku tīkla kartēšana</span>
            </li>
            <li className="flex items-start">
              <svg className="w-5 h-5 text-accent mr-3 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span className="text-gray-700">Valsts iepirkumu uzraudzība un analīze</span>
            </li>
          </ul>
        </div>
      </div>
    </main>
  );
}
