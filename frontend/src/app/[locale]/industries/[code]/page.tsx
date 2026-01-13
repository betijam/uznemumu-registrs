'use client';

import { useState, useEffect, use } from 'react';
import Navbar from '@/components/Navbar';
import { Link } from '@/i18n/routing';
import DataDiggingLoader from '@/components/DataDiggingLoader';
import FinancialHistoryChart from '@/components/FinancialHistoryChart';
import SubIndustryList from '@/components/SubIndustryList';
import { useTranslations } from 'next-intl';

interface KPI {
    total_turnover: number | null;
    total_turnover_formatted: string | null;
    turnover_growth: number | null;
    total_profit: number | null;
    total_profit_formatted: string | null;
    profit_growth?: number | null;
    active_companies: number | null;
    total_employees: number | null;
    new_companies?: number;
    avg_salary: number | null;
    national_avg_salary: number | null;
    salary_ratio: number | null;
    concentration_level?: string;
    concentration_val?: number;
    tax_burden?: number | null;
}

interface Leader {
    regcode: number;
    name: string;
    turnover: number | null;
    turnover_formatted: string | null;
    profit: number | null;
    profit_formatted: string | null;
    employees: number | null;
    market_share: number;
}

interface HistoryPoint {
    year: number;
    turnover: number | null;
    profit: number | null;
}

interface SubIndustry {
    code: string;
    name: string;
    turnover: number | null;
    formatted_turnover: string | null;
    share: number;
}

interface IndustryDetailData {
    nace_code: string;
    nace_name: string;
    icon: string;
    year: number;
    stats: KPI;
    leaders: Leader[];
    history: HistoryPoint[];
    sub_industries: SubIndustry[];
}

export default function IndustryDetailPage({ params }: { params: Promise<{ code: string }> }) {
    const t = useTranslations('IndustryDetail');
    const resolvedParams = use(params);
    const code = resolvedParams.code;

    const [data, setData] = useState<IndustryDetailData | null>(null);
    const [loading, setLoading] = useState(true);

    // Generate years: [CurrentYear-1, ..., 2021]
    const currentYear = new Date().getFullYear();
    const availableYears = Array.from({ length: (currentYear - 1) - 2021 + 1 }, (_, i) => (currentYear - 1) - i);
    const [selectedYear, setSelectedYear] = useState<number>(availableYears[0]); // Default to latest complete year

    const fetchData = async (year: number) => {
        setLoading(true);
        try {
            const res = await fetch(`/api/industries/${code}/detail?year=${year}`);
            if (!res.ok) throw new Error('API Error');
            const json = await res.json();
            setData(json);
            if (json.year) setSelectedYear(json.year);
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

    if (loading && !data) {
        return (
            <div className="min-h-screen flex flex-col bg-gray-50">
                <Navbar />
                <div className="flex-1 flex items-center justify-center">
                    <DataDiggingLoader />
                </div>
            </div>
        );
    }

    if (!data) {
        return (
            <div className="min-h-screen bg-gray-50">
                <Navbar />
                <div className="max-w-7xl mx-auto px-4 py-16 text-center">
                    <h1 className="text-4xl font-bold text-gray-800 mb-4">{t('not_found')}</h1>
                    <Link href="/industries" className="text-blue-600 hover:underline">
                        {t('back_to_industries')}
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
                        <span>{data.nace_name}</span>
                        <span className="ml-auto px-3 py-1 bg-blue-50 text-blue-700 rounded-lg text-xs font-medium">
                            NACE {code}
                        </span>
                    </div>

                    <div className="flex items-center justify-between flex-wrap gap-4">
                        <div>
                            <div className="flex items-center gap-3 mb-1">
                                <span className="text-4xl">{data.icon}</span>
                                <h1 className="text-3xl font-bold text-gray-900">
                                    {data.nace_name}
                                </h1>
                            </div>
                        </div>

                        {/* Year Switcher */}
                        <div className="flex items-center bg-gray-100 rounded-lg p-1 overflow-x-auto">
                            {availableYears.map((year) => (
                                <button
                                    key={year}
                                    onClick={() => setSelectedYear(year)}
                                    className={`px-4 py-2 text-sm font-medium rounded-md transition-colors whitespace-nowrap ${selectedYear === year
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

            <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
                {/* KPI Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {/* Turnover */}
                    <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
                        <p className="text-xs font-medium text-gray-500 uppercase mb-1">{t('total_turnover')}</p>
                        <p className="text-3xl font-bold text-gray-900 mb-1">
                            {data.stats.total_turnover_formatted || '-'}
                        </p>
                        {formatGrowth(data.stats.turnover_growth)}
                    </div>

                    {/* Profit */}
                    <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
                        <p className="text-xs font-medium text-gray-500 uppercase mb-1">{t('total_profit')}</p>
                        <p className={`text-3xl font-bold mb-1 ${(data.stats.total_profit || 0) >= 0 ? 'text-gray-900' : 'text-red-600'}`}>
                            {data.stats.total_profit_formatted || '-'}
                        </p>
                    </div>

                    {/* Companies */}
                    <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
                        <p className="text-xs font-medium text-gray-500 uppercase mb-1">{t('active_companies')}</p>
                        <p className="text-3xl font-bold text-gray-900 mb-1">
                            {data.stats.active_companies?.toLocaleString() || '-'}
                        </p>
                        <span className="text-sm text-gray-500">
                            {data.stats.total_employees?.toLocaleString() || 0} {t('employees')}
                        </span>
                    </div>

                    {/* Salary */}
                    <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl shadow-sm p-6 text-white">
                        <p className="text-xs font-medium text-purple-100 uppercase mb-1">{t('avg_salary')}</p>
                        <p className="text-3xl font-bold mb-1">
                            {data.stats.avg_salary ? `${data.stats.avg_salary.toLocaleString()} €` : '-'}
                        </p>
                        {data.stats.salary_ratio && (
                            <span className="text-sm text-purple-100">{data.stats.salary_ratio}x {t('vs_national')}</span>
                        )}
                    </div>
                </div>

                {/* Financial History Chart */}
                <div className="w-full">
                    <FinancialHistoryChart data={data.history} />
                </div>

                {/* Main Content Grid - Leaders & Sub-Industries */}
                <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
                    {/* Leaders (3/5 width) */}
                    <div className="lg:col-span-3">
                        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden h-full">
                            <div className="flex items-center justify-between px-6 py-4 border-b">
                                <h2 className="font-semibold text-gray-800">{t('industry_leaders')}</h2>
                                <Link
                                    href={`/industry/${code}`}
                                    className="text-sm text-blue-600 hover:underline"
                                >
                                    {t('view_more')} →
                                </Link>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="min-w-full divide-y divide-gray-100">
                                    <thead className="bg-gray-50">
                                        <tr>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">#</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('company')}</th>
                                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('turnover')}</th>
                                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('market_share')}</th>
                                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('profit')}</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-100">
                                        {data.leaders.map((leader, idx) => (
                                            <tr key={leader.regcode} className="hover:bg-gray-50">
                                                <td className="px-6 py-4">
                                                    <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-sm font-bold ${idx < 3
                                                        ? 'bg-yellow-100 text-yellow-700'
                                                        : 'bg-gray-100 text-gray-600'
                                                        }`}>
                                                        {idx + 1}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <Link
                                                        href={`/company/${leader.regcode}`}
                                                        className="font-medium text-gray-900 hover:text-blue-600"
                                                    >
                                                        {leader.name}
                                                    </Link>
                                                    <div className="text-xs text-gray-500 mt-0.5">
                                                        {leader.employees} {t('employees')}
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 text-right font-semibold text-gray-800">
                                                    {leader.turnover_formatted || '-'}
                                                </td>
                                                <td className="px-6 py-4 text-right text-gray-600">
                                                    {leader.market_share}%
                                                </td>
                                                <td className={`px-6 py-4 text-right font-semibold ${leader.profit && leader.profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                                    {leader.profit_formatted || '-'}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                    {/* Sub-Industries (2/5 width) */}
                    <div className="lg:col-span-2">
                        <SubIndustryList subIndustries={data.sub_industries} />
                    </div>
                </div>

                {/* Secondary Metrics Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Salary Comparison */}
                    <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
                        <h3 className="font-semibold text-gray-800 mb-4">{t('salary_analytics')}</h3>
                        <p className="text-xs text-gray-500 mb-4">
                            {t('comparison_with_national', { avg: data.stats.national_avg_salary?.toLocaleString() || '-' })}
                        </p>

                        {/* Industry */}
                        <div className="mb-4">
                            <div className="flex justify-between text-sm mb-1">
                                <span className="text-gray-600">{t('this_industry')}</span>
                                <span className="font-semibold text-gray-900">
                                    {data.stats.avg_salary?.toLocaleString() || '-'}€
                                </span>
                            </div>
                            <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-purple-500 rounded-full"
                                    style={{
                                        width: `${Math.min(100, (data.stats.avg_salary || 0) / (data.stats.national_avg_salary || 1500) * 50)}%`
                                    }}
                                />
                            </div>
                        </div>

                        {/* National */}
                        <div>
                            <div className="flex justify-between text-sm mb-1">
                                <span className="text-gray-600">{t('national_avg')}</span>
                                <span className="font-semibold text-gray-500">
                                    {data.stats.national_avg_salary?.toLocaleString() || '-'}€
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
                        <h3 className="font-semibold text-gray-800 mb-2">{t('tax_burden')}</h3>
                        <p className="text-4xl font-bold text-gray-900 mb-1">
                            {data.stats.tax_burden !== null ? `${data.stats.tax_burden}%` : '-'}
                        </p>
                        <p className="text-sm text-gray-500">{t('of_turnover_paid_as_tax')}</p>
                    </div>

                    {/* Market Concentration */}
                    <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
                        <h3 className="font-semibold text-gray-800 mb-4">Tirgus Koncentrācija</h3>
                        <p className="text-5xl font-bold text-blue-600 text-center mb-2">
                            {data.stats.concentration_val !== undefined
                                ? `${data.stats.concentration_val}%`
                                : '-'}
                        </p>
                        <p className="text-center text-sm text-gray-500 mb-4">
                            TOP 5 līderi aizņem<br />
                            {data.stats.concentration_val}% no tirgus
                        </p>
                        {data.stats.concentration_level && (
                            <div className={`text-center px-4 py-2 rounded-lg ${data.stats.concentration_level === 'Augsta'
                                ? 'bg-red-50 text-red-700'
                                : data.stats.concentration_level === 'Vidēja'
                                    ? 'bg-yellow-50 text-yellow-700'
                                    : 'bg-green-50 text-green-700'
                                }`}>
                                <span className="text-sm font-medium">
                                    {data.stats.concentration_level} koncentrācija
                                </span>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
