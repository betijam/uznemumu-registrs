"use client";

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import FinancialView from '@/components/benchmark/FinancialView';
import WorkforceView from '@/components/benchmark/WorkforceView';
import IndustryView from '@/components/benchmark/IndustryView';

interface BenchmarkData {
    yearRequested: number;
    companies: CompanyData[];
}

interface CompanyData {
    regNumber: string;
    name: string;
    industryCode: string;
    industryName: string;
    dataYear: number;
    financials: {
        revenue: number | null;
        profit: number | null;
        profitMargin: number | null;
        ebitda: number | null;
        assetsTotal: number | null;
        equityTotal: number | null;
        roe: number | null;
        roa: number | null;
    };
    workforce: {
        employees: number | null;
        avgSalary: number | null;
        revenuePerEmployee: number | null;
    };
    trend: {
        revenue: { year: number; value: number }[];
        employees: { year: number; value: number }[];
    };
    industryBenchmark: {
        avgRevenue: number | null;
        avgProfitMargin: number | null;
        avgSalary: number | null;
        avgRevenuePerEmployee: number | null;
        positionByRevenue: {
            rank: number;
            total: number;
            percentile: number;
        } | null;
    } | null;
}

type ViewMode = 'summary' | 'financial' | 'workforce' | 'industry';

export default function BenchmarkPage() {
    const searchParams = useSearchParams();
    const [benchmarkData, setBenchmarkData] = useState<BenchmarkData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [viewMode, setViewMode] = useState<ViewMode>('summary');
    const [year, setYear] = useState<number>(new Date().getFullYear());

    useEffect(() => {
        const fetchBenchmarkData = async () => {
            try {
                setLoading(true);
                setError(null);

                // Get parameters from URL
                const sessionId = searchParams.get('s');
                const companiesParam = searchParams.get('companies');
                const yearParam = searchParams.get('year');

                if (yearParam) {
                    setYear(parseInt(yearParam));
                }

                let response;

                if (sessionId) {
                    // Load from session
                    response = await fetch(`/api/benchmark/session/${sessionId}`);
                } else if (companiesParam) {
                    // Direct comparison
                    const companyRegNumbers = companiesParam.split(',');
                    const requestYear = yearParam ? parseInt(yearParam) : new Date().getFullYear();

                    response = await fetch('/api/benchmark', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            companyRegNumbers,
                            year: requestYear
                        })
                    });
                } else {
                    throw new Error('Nav norādīti uzņēmumi salīdzināšanai');
                }

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Kļūda ielādējot datus');
                }

                const data = await response.json();
                setBenchmarkData(data);
            } catch (err: any) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchBenchmarkData();
    }, [searchParams]);

    const handleYearChange = (newYear: number) => {
        setYear(newYear);
        // Reload data with new year
        const companiesParam = searchParams.get('companies');
        if (companiesParam) {
            window.location.href = `/benchmark?companies=${companiesParam}&year=${newYear}`;
        }
    };

    const handleShare = () => {
        const url = window.location.href;
        navigator.clipboard.writeText(url);
        alert('Saite nokopēta!');
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary mx-auto mb-4"></div>
                    <p className="text-gray-600">Ielādē salīdzinājuma datus...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
                <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full">
                    <div className="flex items-center gap-3 text-red-600 mb-4">
                        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <h2 className="text-xl font-bold">Kļūda</h2>
                    </div>
                    <p className="text-gray-700 mb-6">{error}</p>
                    <Link
                        href="/explore"
                        className="block w-full text-center bg-primary text-white py-2 px-4 rounded-lg hover:bg-primary-dark transition-colors"
                    >
                        Atgriezties uz uzņēmumu sarakstu
                    </Link>
                </div>
            </div>
        );
    }

    if (!benchmarkData || benchmarkData.companies.length === 0) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
                <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
                    <p className="text-gray-700 mb-6">Nav atrasti uzņēmumi salīdzināšanai</p>
                    <Link
                        href="/explore"
                        className="block w-full text-center bg-primary text-white py-2 px-4 rounded-lg hover:bg-primary-dark transition-colors"
                    >
                        Izvēlēties uzņēmumus
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 sticky top-0 z-40 shadow-sm">
                <div className="container mx-auto px-4 py-4">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-4">
                            <Link
                                href="/"
                                className="flex items-center gap-2 px-3 py-2 text-gray-600 hover:text-primary hover:bg-gray-100 rounded-lg transition-colors"
                                title="Atpakaļ uz sākumlapu"
                            >
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                                </svg>
                                <span className="hidden sm:inline">Atpakaļ</span>
                            </Link>
                            <div>
                                <h1 className="text-2xl font-bold text-gray-900">Uzņēmumu salīdzinājums</h1>
                                <p className="text-sm text-gray-600 mt-1">
                                    Salīdzina {benchmarkData.companies.length} uzņēmumus par {benchmarkData.yearRequested}. gadu
                                </p>
                            </div>
                        </div>
                        <button
                            onClick={handleShare}
                            className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                            </svg>
                            Kopēt saiti
                        </button>
                    </div>

                    {/* View Mode Tabs */}
                    <div className="flex gap-2 border-b border-gray-200">
                        {[
                            { key: 'summary', label: 'Kopsavilkums', icon: '📊' },
                            { key: 'financial', label: 'Finanšu analīze', icon: '💰' },
                            { key: 'workforce', label: 'Darbinieki un algas', icon: '👥' },
                            { key: 'industry', label: 'Nozares pozīcija', icon: '🏆' }
                        ].map((tab) => (
                            <button
                                key={tab.key}
                                onClick={() => setViewMode(tab.key as ViewMode)}
                                className={`px-4 py-2 font-medium transition-colors border-b-2 ${viewMode === tab.key
                                    ? 'border-primary text-primary'
                                    : 'border-transparent text-gray-600 hover:text-gray-900'
                                    }`}
                            >
                                <span className="mr-2">{tab.icon}</span>
                                {tab.label}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="container mx-auto px-4 py-8">
                {viewMode === 'summary' && (
                    <SummaryView companies={benchmarkData.companies} />
                )}
                {viewMode === 'financial' && (
                    <FinancialView companies={benchmarkData.companies} />
                )}
                {viewMode === 'workforce' && (
                    <WorkforceView companies={benchmarkData.companies} />
                )}
                {viewMode === 'industry' && (
                    <IndustryView companies={benchmarkData.companies} />
                )}
            </div>
        </div>
    );
}

// Placeholder view components (to be implemented)
function SummaryView({ companies }: { companies: CompanyData[] }) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
            {companies.map((company) => (
                <CompanyCard key={company.regNumber} company={company} companies={companies} />
            ))}
        </div>
    );
}

function CompanyCard({ company, companies }: { company: CompanyData; companies: CompanyData[] }) {
    const formatCurrency = (val: number | null) => {
        if (val === null || val === undefined) return '-';
        return `€${val.toLocaleString('lv-LV')}`;
    };

    const formatNumber = (val: number | null) => {
        if (val === null || val === undefined) return '-';
        return val.toLocaleString('lv-LV');
    };

    // Determine winners
    const hasHighestRevenue = companies.every(c =>
        c.regNumber === company.regNumber || (company.financials.revenue || 0) > (c.financials.revenue || 0)
    );
    const hasHighestProfit = companies.every(c =>
        c.regNumber === company.regNumber || (company.financials.profit || 0) > (c.financials.profit || 0)
    );

    return (
        <div className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow relative">
            {/* Winner Badges */}
            {(hasHighestRevenue || hasHighestProfit) && (
                <div className="absolute top-2 right-2 flex gap-1">
                    {hasHighestRevenue && (
                        <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded" title="Augstākais apgrozījums">
                            👑
                        </span>
                    )}
                    {hasHighestProfit && (
                        <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded" title="Augstākā peļņa">
                            💰
                        </span>
                    )}
                </div>
            )}

            {/* Company Name */}
            <Link href={`/company/${company.regNumber}`} className="block mb-4">
                <h3 className="font-bold text-lg text-gray-900 hover:text-primary transition-colors line-clamp-2">
                    {company.name}
                </h3>
                <p className="text-xs text-gray-500 mt-1">{company.regNumber}</p>
                <p className="text-xs text-gray-600 mt-1">{company.industryName}</p>
            </Link>

            {/* Key Metrics */}
            <div className="space-y-3">
                <div>
                    <p className="text-xs text-gray-500">Apgrozījums ({company.dataYear})</p>
                    <p className="text-lg font-bold text-gray-900">{formatCurrency(company.financials.revenue)}</p>
                </div>
                <div>
                    <p className="text-xs text-gray-500">Peļņa</p>
                    <p className={`text-lg font-bold ${(company.financials.profit || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(company.financials.profit)}
                    </p>
                </div>
                <div className="grid grid-cols-2 gap-3">
                    <div>
                        <p className="text-xs text-gray-500">Darbinieki</p>
                        <p className="text-sm font-semibold text-gray-900">{formatNumber(company.workforce.employees)}</p>
                    </div>
                    <div>
                        <p className="text-xs text-gray-500">Vid. alga</p>
                        <p className="text-sm font-semibold text-gray-900">{formatCurrency(company.workforce.avgSalary)}</p>
                    </div>
                </div>
                <div>
                    <p className="text-xs text-gray-500">Peļņas marža</p>
                    <p className="text-sm font-semibold text-gray-900">
                        {company.financials.profitMargin !== null ? `${company.financials.profitMargin.toFixed(2)}%` : '-'}
                    </p>
                </div>
            </div>
        </div>
    );
}
