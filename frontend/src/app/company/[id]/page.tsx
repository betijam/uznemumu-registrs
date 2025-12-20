import Navbar from "@/components/Navbar";
import { notFound } from "next/navigation";
import Link from "next/link";
import CompanyTabs from "@/components/CompanyTabs";
import CompanySizeBadge from "@/components/CompanySizeBadge";
import CompanyMap from "@/components/CompanyMap";

// Data Fetching
async function getCompany(id: string) {
    // On Railway, always use the public URL (NEXT_PUBLIC_API_URL)
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    try {
        const res = await fetch(`${API_BASE_URL}/companies/${id}`, { cache: 'no-store' });
        if (!res.ok) return null;
        return res.json();
    } catch (e) {
        return null;
    }
}

async function getGraph(id: string) {
    // On Railway, always use the public URL (NEXT_PUBLIC_API_URL)
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    try {
        const res = await fetch(`${API_BASE_URL}/companies/${id}/graph`, { cache: 'no-store' });
        if (!res.ok) return { parents: [], children: [] };
        return res.json();
    } catch (e) {
        return { parents: [], children: [] };
    }
}

async function getBenchmark(id: string) {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    try {
        const res = await fetch(`${API_BASE_URL}/companies/${id}/benchmark`, { cache: 'no-store' });
        if (!res.ok) return null;
        return res.json();
    } catch (e) {
        return null;
    }
}

async function getCompetitors(id: string) {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    try {
        const res = await fetch(`${API_BASE_URL}/companies/${id}/competitors?limit=5`, { cache: 'no-store' });
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
    const company = await getCompany(id);
    const graph = await getGraph(id);
    const benchmark = await getBenchmark(id);
    const competitors = await getCompetitors(id);

    if (!company) {
        notFound();
    }

    return (
        <div className="min-h-screen bg-background pb-12">
            <Navbar />

            {/* Header */}
            <div className="bg-white border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                    <div className="md:flex md:items-start md:justify-between">
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-3">
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
                            {company.sepa_identifier && (
                                <div className="mt-2 flex items-center gap-2 text-sm">
                                    <span className="text-gray-500">PVN:</span>
                                    <span className="font-mono text-sm text-primary">
                                        {company.sepa_identifier}
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

            {/* Metric Cards */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6 mb-8 relative z-10">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    {/* Revenue Card */}
                    <div className="bg-white rounded-xl shadow-card p-5">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium text-gray-500">Apgrozījums ({company.finances?.year || 'N/A'})</span>
                            <svg className="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                        <p className="text-2xl font-bold text-primary mb-1">
                            {formatCurrency(company.finances?.turnover)}
                        </p>
                        {company.finances?.turnover_change && (
                            <span className={`text-xs flex items-center ${company.finances.turnover_change >= 0 ? 'text-success' : 'text-danger'}`}>
                                <svg className={`w-3 h-3 mr-1 ${company.finances.turnover_change < 0 ? 'rotate-180' : ''}`} fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                                </svg>
                                {Math.abs(company.finances.turnover_change).toFixed(1)}% pret 2022
                            </span>
                        )}
                    </div>

                    {/* Profit Card */}
                    <div className="bg-white rounded-xl shadow-card p-5">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium text-gray-500">Peļņa</span>
                            <svg className="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                            </svg>
                        </div>
                        <p className={`text-2xl font-bold mb-1 ${(company.finances?.profit || 0) >= 0 ? 'text-success' : 'text-danger'}`}>
                            {formatCurrency(company.finances?.profit)}
                        </p>
                        {company.finances?.profit_change && (
                            <span className={`text-xs flex items-center ${company.finances.profit_change >= 0 ? 'text-success' : 'text-danger'}`}>
                                <svg className={`w-3 h-3 mr-1 ${company.finances.profit_change < 0 ? 'rotate-180' : ''}`} fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                                </svg>
                                {Math.abs(company.finances.profit_change).toFixed(1)}%
                            </span>
                        )}
                    </div>

                    {/* Employees Card */}
                    <div className="bg-white rounded-xl shadow-card p-5">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium text-gray-500">Darbinieki</span>
                            <svg className="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                            </svg>
                        </div>
                        <p className="text-2xl font-bold text-primary mb-1">
                            {company.finances?.employees || '-'}
                        </p>
                        <span className="text-xs text-gray-500">Samazinās vairāk</span>
                    </div>

                    {/* Tax/Other Card */}
                    <div className="bg-white rounded-xl shadow-card p-5">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium text-gray-500">Nodokļi (Gada)</span>
                            <svg className="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                            </svg>
                        </div>
                        <p className="text-2xl font-bold text-primary mb-1">
                            {company.finances?.taxes ? `${(company.finances.taxes / 1000).toFixed(0)} k€` : '-'}
                        </p>
                        {company.finances?.taxes_change && (
                            <span className={`text-xs flex items-center ${company.finances.taxes_change >= 0 ? 'text-success' : 'text-danger'}`}>
                                <svg className={`w-3 h-3 mr-1 ${company.finances.taxes_change < 0 ? 'rotate-180' : ''}`} fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                                </svg>
                                {Math.abs(company.finances.taxes_change).toFixed(1)}%
                            </span>
                        )}
                    </div>
                </div>
            </div>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                {/* Industry Benchmarking & Competitors */}
                {(benchmark?.has_data || competitors.length > 0) && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                        {/* Benchmarking Card */}
                        {benchmark?.has_data && (
                            <div className="bg-white rounded-xl shadow-card p-6">
                                <h3 className="text-lg font-bold text-primary mb-4">Pozīcija Nozarē</h3>
                                <p className="text-sm text-gray-600 mb-4">
                                    {benchmark.industry.name} • {benchmark.industry.total_companies} uzņēmumi
                                </p>

                                <div className="grid grid-cols-2 gap-4 mb-4">
                                    {benchmark.percentiles.turnover && (
                                        <div className="bg-gradient-to-br from-accent/10 to-primary/10 rounded-lg p-4">
                                            <p className="text-xs text-gray-600 mb-1">Apgrozījums</p>
                                            <p className="text-3xl font-bold text-primary">Top {benchmark.percentiles.turnover}%</p>
                                        </div>
                                    )}
                                    {benchmark.percentiles.employees && (
                                        <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg p-4">
                                            <p className="text-xs text-gray-600 mb-1">Darbinieki</p>
                                            <p className="text-3xl font-bold text-primary">Top {benchmark.percentiles.employees}%</p>
                                        </div>
                                    )}
                                </div>

                                <div className="border-t pt-4">
                                    <p className="text-xs font-medium text-gray-500 mb-2">Nozares Vidējie Rādītāji</p>
                                    <div className="flex justify-between text-sm">
                                        <span className="text-gray-600">Apgrozījums:</span>
                                        <span className="font-semibold">{formatCurrency(benchmark.industry_averages.turnover)}</span>
                                    </div>
                                    <div className="flex justify-between text-sm mt-1">
                                        <span className="text-gray-600">Darbinieki:</span>
                                        <span className="font-semibold">{Math.round(benchmark.industry_averages.employees || 0)}</span>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Top Competitors */}
                        {competitors.length > 0 && (
                            <div className="bg-white rounded-xl shadow-card p-6">
                                <h3 className="text-lg font-bold text-primary mb-4">Tuvākie Konkurenti</h3>
                                <p className="text-sm text-gray-600 mb-4">
                                    {company.nace_section_text} nozarē
                                </p>

                                <div className="space-y-3">
                                    {competitors.map((comp: any, idx: number) => (
                                        <Link
                                            key={comp.regcode}
                                            href={`/company/${comp.regcode}`}
                                            className="block p-3 hover:bg-gray-50 rounded-lg transition-colors border border-gray-100"
                                        >
                                            <div className="flex items-start justify-between">
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-xs font-bold text-gray-400">#{idx + 1}</span>
                                                        <p className="font-medium text-gray-900">{comp.name}</p>
                                                    </div>
                                                    <div className="flex gap-4 mt-1 text-xs text-gray-500">
                                                        {comp.turnover && (
                                                            <span>Apgr.: {formatCurrency(comp.turnover)}</span>
                                                        )}
                                                        {comp.employee_count > 0 && (
                                                            <span>Darb.: {comp.employee_count}</span>
                                                        )}
                                                    </div>
                                                </div>
                                                <svg className="w-4 h-4 text-gray-400 flex-shrink-0 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                                </svg>
                                            </div>
                                        </Link>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                <CompanyTabs company={company} related={graph} />
            </main>
        </div>
    );
}
