import Navbar from "@/components/Navbar";
import { notFound } from "next/navigation";
import Link from "next/link";
import dynamic from "next/dynamic";
import CompanySizeBadge from "@/components/CompanySizeBadge";
import CompanySearchBar from "@/components/CompanySearchBar";

// Dynamic import for heavy component - reduces initial bundle
const CompanyTabs = dynamic(() => import("@/components/CompanyTabs"), {
    loading: () => (
        <div className="mt-6 bg-white rounded-lg shadow-md p-6">
            <div className="h-8 w-48 bg-gray-200 rounded animate-pulse mb-4"></div>
            <div className="space-y-3">
                <div className="h-4 w-full bg-gray-200 rounded animate-pulse"></div>
                <div className="h-4 w-3/4 bg-gray-200 rounded animate-pulse"></div>
            </div>
        </div>
    ),
    ssr: true  // Keep SSR for SEO
});

// Cache configuration - revalidate every 60 seconds for fresher data with caching
const CACHE_CONFIG = { next: { revalidate: 60 } };

// Data Fetching with caching
async function getCompany(id: string) {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    try {
        const res = await fetch(`${API_BASE_URL}/companies/${id}`, CACHE_CONFIG);
        if (!res.ok) return null;
        return res.json();
    } catch (e) {
        return null;
    }
}

async function getGraph(id: string) {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    try {
        const res = await fetch(`${API_BASE_URL}/companies/${id}/graph`, CACHE_CONFIG);
        if (!res.ok) return { parents: [], children: [] };
        return res.json();
    } catch (e) {
        return { parents: [], children: [] };
    }
}

async function getBenchmark(id: string) {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    try {
        const res = await fetch(`${API_BASE_URL}/companies/${id}/benchmark`, CACHE_CONFIG);
        if (!res.ok) return null;
        return res.json();
    } catch (e) {
        return null;
    }
}

async function getCompetitors(id: string) {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    try {
        const res = await fetch(`${API_BASE_URL}/companies/${id}/competitors?limit=5`, CACHE_CONFIG);
        if (!res.ok) return [];
        return res.json();
    } catch (e) {
        return [];
    }
}

// Adaptive currency formatting: M€ for millions, k€ for thousands, € for smaller
function formatCurrency(value: number | null | undefined): string {
    if (value === null || value === undefined) return '-';
    const absValue = Math.abs(value);
    const sign = value < 0 ? '-' : '';
    if (absValue >= 1000000) {
        return `${sign}${(absValue / 1000000).toFixed(1)} M€`;
    } else if (absValue >= 1000) {
        return `${sign}${Math.round(absValue / 1000)} k€`;
    } else if (absValue > 0) {
        return `${sign}${Math.round(absValue)} €`;
    }
    return '-';
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }) {
    const { id } = await params;
    const company = await getCompany(id);
    if (!company) return { title: "Uzņēmums nav atrasts" };
    return {
        title: `${company.name} (${company.regcode}) - UR Portāls`,
        description: `Finanšu dati, amatpersonas un riski uzņēmumam ${company.name}.`,
    };
}

export default async function CompanyPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = await params;

    // Parallel data fetching - all requests run simultaneously
    // This reduces total wait time from sum of all requests to max of all requests
    const [company, graph, benchmark, competitors] = await Promise.all([
        getCompany(id),
        getGraph(id),
        getBenchmark(id),
        getCompetitors(id)
    ]);

    if (!company) {
        notFound();
    }

    return (
        <div className="min-h-screen bg-background pb-12">
            <Navbar />

            {/* Header */}
            <div className="bg-white border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                    {/* Search Bar for quick navigation */}
                    <div className="mb-4 max-w-md">
                        <CompanySearchBar />
                    </div>

                    <div className="md:flex md:items-start md:justify-between">
                        <div className="flex-1 min-w-0">
                            <div className="flex flex-wrap items-center gap-1.5 sm:gap-2 mb-3">
                                <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${company.status === 'active' ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'
                                    }`}>
                                    {company.status === 'active' ? 'AKTĪVS' : 'LIKVIDĒTS'}
                                </span>
                                {company.company_type && (
                                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
                                        {company.company_type}
                                    </span>
                                )}
                                <CompanySizeBadge size={company.company_size} />
                                {/* PVN Taxpayer Badge */}
                                {company.is_pvn_payer ? (
                                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-700 border border-green-300">
                                        ✓ PVN MAKSĀTĀJS
                                    </span>
                                ) : (
                                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-500">
                                        NAV PVN
                                    </span>
                                )}
                                {company.nace_section_text && (
                                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-50 text-purple-700">
                                        🏭 {company.nace_section_text}
                                    </span>
                                )}
                            </div>
                            <h1 className="text-3xl font-bold text-primary mb-2">
                                {company.name}
                            </h1>
                            <div className="flex items-center gap-4 text-sm text-gray-600">
                                <span className="flex items-center gap-1">
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                    </svg>
                                    Reģ. Nr. {company.regcode}
                                </span>
                                <span className="flex items-center gap-1">
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                                    </svg>
                                    {company.address}
                                </span>
                            </div>

                            {/* NACE Industry Classification */}
                            {company.nace_code && company.nace_code !== '0000' && (
                                <div className="mt-3 flex items-center gap-2 text-sm">
                                    <span className="text-gray-500">Nozare:</span>
                                    <span className="font-semibold text-primary">
                                        🏭 {company.nace_code} · {company.nace_text}
                                    </span>
                                </div>
                            )}

                            {/* PVN Number */}
                            {company.pvn_number && (
                                <div className="mt-2 flex items-center gap-2 text-sm">
                                    <span className="text-gray-500">PVN:</span>
                                    <span className="font-mono text-sm text-primary">
                                        {company.pvn_number}
                                    </span>
                                </div>
                            )}
                        </div>
                        <div className="mt-4 flex gap-3 md:mt-0 md:ml-4">
                            <button className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors shadow-sm">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                                </svg>
                                Monitorēt
                            </button>
                        </div>
                    </div>

                    {/* Risk Alert Bar */}
                    {company.risks && (
                        company.risks.sanctions?.length > 0 ||
                        company.risks.liquidations?.length > 0 ||
                        company.risks.suspensions?.length > 0
                    ) && (
                            <div className="mt-6 bg-danger/10 border-l-4 border-danger rounded-r-lg p-4">
                                <div className="flex">
                                    <div className="flex-shrink-0">
                                        <svg className="h-5 w-5 text-danger" viewBox="0 0 20 20" fill="currentColor">
                                            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                        </svg>
                                    </div>
                                    <div className="ml-3">
                                        <p className="text-sm text-danger font-medium">
                                            Uzņēmumam ir reģistrēti aktīvi riski (Sankcijas, Likvidācija vai Aizliegumi).
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}
                </div>
            </div>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
                <CompanyTabs company={company} related={graph} competitors={competitors} benchmark={benchmark} />
            </main>
        </div>
    );
}
