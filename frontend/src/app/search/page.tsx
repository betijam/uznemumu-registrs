import Navbar from "@/components/Navbar";
import SearchInput from "@/components/SearchInput";
import Link from "next/link";
import { formatCompanyName } from "@/utils/formatCompanyName";

async function getSearchResults(query: string) {
    // On Railway, always use the public URL (NEXT_PUBLIC_API_URL)
    // Internal Docker network (INTERNAL_API_URL) only works locally
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

    try {
        const res = await fetch(`${API_BASE_URL}/search?q=${encodeURIComponent(query)}`, {
            cache: "no-store", // Search results should be fresh
        });
        if (!res.ok) return [];
        return res.json();
    } catch (e) {
        console.error(e);
        return [];
    }
}

export default async function SearchPage({
    searchParams,
}: {
    searchParams: Promise<{ q?: string }>;
}) {
    const { q } = await searchParams;
    const query = q || "";
    const results = query ? await getSearchResults(query) : [];

    return (
        <div className="min-h-screen bg-background pb-12">
            <Navbar />

            {/* Search Header */}
            <div className="bg-white border-b border-gray-200 shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                    <div className="flex items-center justify-between mb-4">
                        <h1 className="text-2xl font-bold text-primary">Meklēšana</h1>
                        <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                            </svg>
                            Filtri
                        </button>
                    </div>
                    <SearchInput />
                </div>
            </div>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
                <div className="mb-6">
                    <h2 className="text-lg font-medium text-gray-900">
                        Meklēšanas rezultāti
                    </h2>
                    <p className="text-sm text-gray-500 mt-1">
                        Atrasti {results.length} uzņēmumi {query && `priekš "${query}"`}
                    </p>
                </div>

                {results.length === 0 ? (
                    <div className="bg-white rounded-lg shadow-card p-12 text-center">
                        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                        <h3 className="mt-4 text-lg font-medium text-gray-900">Nav rezultātu</h3>
                        <p className="mt-2 text-sm text-gray-500">
                            Mēģiniet mainīt meklēšanas vaicājumu vai izmantojiet citus atslēgvārdus.
                        </p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 gap-4">
                        {results.map((company: any) => (
                            <Link
                                key={company.regcode}
                                href={`/company/${company.regcode}`}
                                className="block bg-white rounded-lg shadow-card hover:shadow-card-hover transition-all p-6 border border-gray-100"
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-2">
                                            {/* Company Icon */}
                                            <div className="w-12 h-12 bg-gradient-to-br from-accent to-primary rounded-lg flex items-center justify-center flex-shrink-0">
                                                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                                                </svg>
                                            </div>
                                            <div>
                                                <h3 className="text-xl font-semibold text-primary mb-1">{formatCompanyName(company)}</h3>
                                                <p className="text-sm text-gray-500">
                                                    Reģ. Nr. {company.regcode}
                                                </p>
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-2 text-sm text-gray-600 mb-3">
                                            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                                            </svg>
                                            {company.address}
                                        </div>

                                        {/* Financial Metrics */}
                                        {company.finances && (
                                            <div className="flex gap-6 text-sm">
                                                {company.finances.turnover && (
                                                    <div>
                                                        <span className="text-gray-500">Apgrozījums ({company.finances.year}):</span>
                                                        <span className="ml-2 font-semibold text-primary">€ {company.finances.turnover.toLocaleString()}</span>
                                                    </div>
                                                )}
                                                {company.finances.employees && (
                                                    <div>
                                                        <span className="text-gray-500">Darbinieki:</span>
                                                        <span className="ml-2 font-semibold text-primary">{company.finances.employees}</span>
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                    </div>

                                    {/* Status Badge */}
                                    <div className="flex flex-col items-end gap-2">
                                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${company.status === 'active'
                                            ? 'bg-success/10 text-success'
                                            : company.status === 'monitoring'
                                                ? 'bg-warning/10 text-warning'
                                                : 'bg-danger/10 text-danger'
                                            }`}>
                                            {company.status === 'active' ? 'AKTĪVS' : company.status === 'monitoring' ? 'MONITORINGS' : 'LIKVIDĒTS'}
                                        </span>

                                        {/* Arrow Icon */}
                                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                        </svg>
                                    </div>
                                </div>
                            </Link>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}
