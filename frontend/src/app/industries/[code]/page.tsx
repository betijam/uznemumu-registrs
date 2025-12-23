'use client';

import { useState, useEffect, use } from 'react';
import Navbar from '@/components/Navbar';
import Link from 'next/link';
import LoadingSpinner from '@/components/LoadingSpinner';

interface KPI {
    total_turnover: number | null;
    total_turnover_formatted: string | null;
    turnover_growth: number | null;
    total_profit: number | null;
    total_profit_formatted: string | null;
    profit_growth: number | null;
    active_companies: number | null;
    new_companies: number;
    avg_salary: number | null;
    salary_ratio: number | null;
}

interface Leader {
    rank: number;
    regcode: number;
    name: string;
    turnover: number | null;
    turnover_formatted: string | null;
    profit: number | null;
    profit_formatted: string | null;
    employees: number | null;
}

interface SalaryAnalytics {
    industry_avg: number | null;
    national_avg: number | null;
    ratio: number | null;
    ratio_text: string | null;
}

interface IndustryDetailData {
    nace_code: string;
    data_year: number;
    available_years: number[];
    meta: {
        name: string;
        icon: string;
        description: string;
    };
    kpi: KPI;
    leaders: Leader[];
    salary_analytics: SalaryAnalytics;
    tax_burden: {
        percent: number | null;
        description: string;
    };
    market_concentration: {
        top5_percent: number | null;
        level: string | null;
        description: string;
    };
}

export default function IndustryDetailPage({ params }: { params: Promise<{ code: string }> }) {
    const resolvedParams = use(params);
    const code = resolvedParams.code;

    const [data, setData] = useState<IndustryDetailData | null>(null);
    const [loading, setLoading] = useState(true);
    const [selectedYear, setSelectedYear] = useState<number>(2023);

    const fetchData = async (year: number) => {
        setLoading(true);
        try {
            const res = await fetch(`/api/industries/${code}/detail?year=${year}`);
            const json = await res.json();
            setData(json);
            if (json.data_year) setSelectedYear(json.data_year);
        } catch (error) {
            console.error('Failed to fetch industry detail:', error);
        }
        setLoading(false);
    };

    useEffect(() => {
        fetchData(selectedYear);
    }, [code, selectedYear]);

    const formatGrowth = (value: number | null | undefined) => {
        if (value === null || value === undefined) return null;
        const isPositive = value >= 0;
        return (
            <span className={`text-sm font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                {isPositive ? '▲' : '▼'} {Math.abs(value).toFixed(1)}%
            </span>
        );
    };

    const formatCurrency = (value: number | null) => {
        if (!value) return '-';
        if (value >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(2)} Md €`;
        if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)} M€`;
        if (value >= 1_000) return `${(value / 1_000).toFixed(0)} k€`;
        return `€${value.toFixed(0)}`;
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50">
                <Navbar />
                <div className="flex justify-center items-center py-32">
                    <LoadingSpinner size="lg" />
                </div>
            </div>
        );
    }

    if (!data || !data.meta) {
        return (
            <div className="min-h-screen bg-gray-50">
                <Navbar />
                <div className="max-w-7xl mx-auto px-4 py-16 text-center">
                    <h1 className="text-4xl font-bold text-gray-800 mb-4">Nozare nav atrasta</h1>
                    <Link href="/industries" className="text-blue-600 hover:underline">
                        ← Atpakaļ uz nozaru pārskatu
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <Navbar />

            {/* Header */}
            <div className="bg-white border-b">
                <div className="max-w-7xl mx-auto px-4 py-6">
                    <div className="flex items-center text-sm text-gray-500 mb-2">
                        <Link href="/industries" className="hover:text-blue-600">🔍 {code}</Link>
                        <span className="mx-2">›</span>
                        <span>{data.meta.name}</span>
                        <span className="ml-auto px-3 py-1 bg-blue-50 text-blue-700 rounded-lg text-xs font-medium">
                            NACE {code}
                        </span>
                    </div>

                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900 mb-1">
                                {data.meta.name}
                            </h1>
                            <p className="text-gray-500">{data.meta.description}</p>
                        </div>

                        {/* Year Switcher */}
                        <div className="flex items-center bg-gray-100 rounded-lg p-1">
                            {data.available_years.map((year) => (
                                <button
                                    key={year}
                                    onClick={() => fetchData(year)}
                                    className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${selectedYear === year
                                            ? 'bg-white shadow text-gray-900'
                                            : 'text-gray-600 hover:text-gray-900'
                                        }`}
                                >
                                    {year}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-4 py-8">
                {/* KPI Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                    {/* Turnover */}
                    <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
                        <p className="text-xs font-medium text-gray-500 uppercase mb-1">Kopējais Apgrozījums</p>
                        <p className="text-3xl font-bold text-gray-900 mb-1">
                            {data.kpi.total_turnover_formatted || '-'}
                        </p>
                        {formatGrowth(data.kpi.turnover_growth)}
                    </div>

                    {/* Profit */}
                    <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
                        <p className="text-xs font-medium text-gray-500 uppercase mb-1">Kopējā Peļņa</p>
                        <p className="text-3xl font-bold text-gray-900 mb-1">
                            {data.kpi.total_profit_formatted || '-'}
                        </p>
                        {formatGrowth(data.kpi.profit_growth)}
                    </div>

                    {/* Companies */}
                    <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
                        <p className="text-xs font-medium text-gray-500 uppercase mb-1">Aktīvie Uzņēmumi</p>
                        <p className="text-3xl font-bold text-gray-900 mb-1">
                            {data.kpi.active_companies?.toLocaleString() || '-'}
                        </p>
                        {data.kpi.new_companies > 0 && (
                            <span className="text-sm text-gray-500">+{data.kpi.new_companies} jauni</span>
                        )}
                    </div>

                    {/* Salary */}
                    <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl shadow-sm p-6 text-white">
                        <p className="text-xs font-medium text-purple-100 uppercase mb-1">Vid. Bruto Alga</p>
                        <p className="text-3xl font-bold mb-1">
                            {data.kpi.avg_salary ? `${data.kpi.avg_salary.toLocaleString()} €` : '-'}
                        </p>
                        {data.kpi.salary_ratio && (
                            <span className="text-sm text-purple-100">{data.kpi.salary_ratio}x pret vidējo</span>
                        )}
                    </div>
                </div>

                {/* Main Content Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Left Column - Leaders (2/3) */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* TOP 5 Leaders */}
                        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                            <div className="flex items-center justify-between px-6 py-4 border-b">
                                <h2 className="font-semibold text-gray-800">Nozares Līderi (TOP 5)</h2>
                                <Link
                                    href={`/industry/${code}`}
                                    className="text-sm text-blue-600 hover:underline"
                                >
                                    Skatīt visus →
                                </Link>
                            </div>
                            <table className="min-w-full divide-y divide-gray-100">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">#</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Uzņēmums</th>
                                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Apgrozījums</th>
                                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Peļņa</th>
                                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Darbinieki</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100">
                                    {data.leaders.map((leader) => (
                                        <tr key={leader.regcode} className="hover:bg-gray-50">
                                            <td className="px-6 py-4">
                                                <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-sm font-bold ${leader.rank <= 3
                                                        ? 'bg-yellow-100 text-yellow-700'
                                                        : 'bg-gray-100 text-gray-600'
                                                    }`}>
                                                    {leader.rank}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4">
                                                <Link
                                                    href={`/company/${leader.regcode}`}
                                                    className="font-medium text-gray-900 hover:text-blue-600"
                                                >
                                                    {leader.name}
                                                </Link>
                                            </td>
                                            <td className="px-6 py-4 text-right font-semibold text-gray-800">
                                                {leader.turnover_formatted || '-'}
                                            </td>
                                            <td className={`px-6 py-4 text-right font-semibold ${leader.profit && leader.profit >= 0 ? 'text-green-600' : 'text-red-600'
                                                }`}>
                                                {leader.profit_formatted || '-'}
                                            </td>
                                            <td className="px-6 py-4 text-right text-gray-600">
                                                {leader.employees?.toLocaleString() || '-'}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Right Column - Analytics (1/3) */}
                    <div className="space-y-6">
                        {/* Salary Comparison */}
                        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
                            <h3 className="font-semibold text-gray-800 mb-4">Algu Analītika</h3>
                            <p className="text-xs text-gray-500 mb-4">
                                Salīdzinājums ar valsts vidējo ({data.salary_analytics.national_avg?.toLocaleString() || '-'}€)
                            </p>

                            {/* Industry */}
                            <div className="mb-4">
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-gray-600">Šī nozare</span>
                                    <span className="font-semibold text-gray-900">
                                        {data.salary_analytics.industry_avg?.toLocaleString() || '-'}€
                                    </span>
                                </div>
                                <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-purple-500 rounded-full"
                                        style={{
                                            width: `${Math.min(100, (data.salary_analytics.industry_avg || 0) / (data.salary_analytics.national_avg || 1500) * 50)}%`
                                        }}
                                    />
                                </div>
                            </div>

                            {/* National */}
                            <div>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-gray-600">Valsts vid.</span>
                                    <span className="font-semibold text-gray-500">
                                        {data.salary_analytics.national_avg?.toLocaleString() || '-'}€
                                    </span>
                                </div>
                                <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-gray-300 rounded-full"
                                        style={{ width: '50%' }}
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Tax Burden */}
                        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
                            <h3 className="font-semibold text-gray-800 mb-2">Nodokļu Slogs</h3>
                            <p className="text-4xl font-bold text-gray-900 mb-1">
                                {data.tax_burden.percent !== null ? `${data.tax_burden.percent}%` : '-'}
                            </p>
                            <p className="text-sm text-gray-500">{data.tax_burden.description}</p>
                        </div>

                        {/* Market Concentration */}
                        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
                            <h3 className="font-semibold text-gray-800 mb-4">Tirgus Koncentrācija</h3>
                            <p className="text-5xl font-bold text-blue-600 text-center mb-2">
                                {data.market_concentration.top5_percent !== null
                                    ? `${data.market_concentration.top5_percent}%`
                                    : '-'}
                            </p>
                            <p className="text-center text-sm text-gray-500 mb-4">
                                TOP 5 uzņēmumi sastāda<br />
                                {data.market_concentration.top5_percent}% no kopējā apgrozījuma
                            </p>
                            {data.market_concentration.level && (
                                <div className={`text-center px-4 py-2 rounded-lg ${data.market_concentration.level === 'Augsta'
                                        ? 'bg-red-50 text-red-700'
                                        : data.market_concentration.level === 'Vidēja'
                                            ? 'bg-yellow-50 text-yellow-700'
                                            : 'bg-green-50 text-green-700'
                                    }`}>
                                    <span className="text-sm font-medium">
                                        {data.market_concentration.level === 'Augsta' && '⚠️ '}
                                        {data.market_concentration.level === 'Vidēja' && '⚡ '}
                                        {data.market_concentration.level === 'Zema' && '✅ '}
                                        {data.market_concentration.level} koncentrācija.
                                        {data.market_concentration.level === 'Zema' && ' Tirgus ir sadrumstalots, ar augstu konkurenci.'}
                                        {data.market_concentration.level === 'Vidēja' && ' Vidēja konkurences intensitāte.'}
                                        {data.market_concentration.level === 'Augsta' && ' Dominē nelieli spēlētāji.'}
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
