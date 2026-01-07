'use client';

import { useState, useEffect, useCallback } from 'react';
import Navbar from '@/components/Navbar';
import Link from 'next/link';
import LoadingSpinner from '@/components/LoadingSpinner';

// Types
interface MacroData {
    total_turnover: number | null;
    total_turnover_formatted: string | null;
    turnover_growth: number | null;
    total_employees: number | null;
    employee_change: number | null;
    avg_salary: number | null;
    total_profit: number | null;
    total_profit_formatted: string | null;
    data_year: number | null;
}

interface TopItem {
    nace_code: string;
    name: string;
    growth_percent?: number | null;
    avg_salary?: number | null;
    turnover?: number | null;
    turnover_formatted?: string | null;
}

interface Section {
    nace_code: string;
    name: string;
    icon: string;
    turnover: number | null;
    turnover_formatted: string | null;
    turnover_growth: number | null;
    avg_salary: number | null;
    companies: number | null;
}

interface OverviewData {
    macro: MacroData;
    top_growth: TopItem[];
    top_salary: TopItem[];
    top_turnover: TopItem[];
    sections: Section[];
}

interface SearchResult {
    code: string;
    name: string;
    icon: string;
    level: number;
}

import { useTranslations } from 'next-intl';

// ... imports remain the same

export default function IndustriesPage() {
    const t = useTranslations('IndustriesPage');
    const [data, setData] = useState<OverviewData | null>(null);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
    const [showSearch, setShowSearch] = useState(false);

    // Sorting state
    const [sortConfig, setSortConfig] = useState<{ key: keyof Section; direction: 'asc' | 'desc' }>({
        key: 'nace_code',
        direction: 'asc'
    });

    useEffect(() => {
        fetchOverview();
    }, []);

    const fetchOverview = async () => {
        try {
            const res = await fetch('/api/industries/overview');
            const json = await res.json();
            setData(json);
        } catch (error) {
            console.error('Failed to fetch industries overview:', error);
        }
        setLoading(false);
    };

    const handleSearch = useCallback(async (query: string) => {
        if (query.length < 1) {
            setSearchResults([]);
            setShowSearch(false);
            return;
        }
        try {
            const res = await fetch(`/api/industries/search?q=${encodeURIComponent(query)}`);
            const json = await res.json();
            setSearchResults(json.results || []);
            setShowSearch(true);
        } catch (error) {
            console.error('Search failed:', error);
        }
    }, []);

    useEffect(() => {
        const timer = setTimeout(() => handleSearch(searchQuery), 300);
        return () => clearTimeout(timer);
    }, [searchQuery, handleSearch]);

    const handleSort = (key: keyof Section) => {
        setSortConfig(current => ({
            key,
            direction: current.key === key && current.direction === 'desc' ? 'asc' : 'desc'
        }));
    };

    const sortedSections = [...(data?.sections || [])].sort((a, b) => {
        const aValue = a[sortConfig.key];
        const bValue = b[sortConfig.key];

        if (aValue === null && bValue === null) return 0;
        if (aValue === null) return 1;
        if (bValue === null) return -1;

        if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
        if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
    });

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
        if (value >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(1)} Md €`;
        if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)} M€`;
        if (value >= 1_000) return `${(value / 1_000).toFixed(0)} k€`;
        return `€${value.toFixed(0)}`;
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <Navbar />

            {/* Compact Hero Section */}
            <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-slate-800 text-white py-12 px-4 shadow-xl">
                <div className="max-w-6xl mx-auto text-center">
                    <h1 className="text-3xl md:text-4xl font-bold mb-3">
                        {t('title')}
                    </h1>
                    <p className="text-base text-gray-300 mb-6">
                        {t('subtitle')}
                    </p>

                    {/* Search Box */}
                    <div className="max-w-xl mx-auto relative">
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder={t('search_placeholder')}
                            className="w-full px-5 py-3 rounded-lg text-gray-800 bg-white shadow-lg text-base focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />

                        {/* Search Results Dropdown */}
                        {showSearch && searchResults.length > 0 && (
                            <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-xl z-50 max-h-80 overflow-auto border border-gray-100">
                                {searchResults.map((result) => (
                                    <Link
                                        key={result.code}
                                        href={`/industries/${result.code}`}
                                        className="flex items-center px-5 py-3 hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-0"
                                        onClick={() => setShowSearch(false)}
                                    >
                                        <span className="text-xl mr-3">{result.icon}</span>
                                        <div>
                                            <span className="font-medium text-gray-800">{result.code}</span>
                                            <span className="text-gray-500 ml-2">{result.name}</span>
                                        </div>
                                    </Link>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {loading ? (
                <div className="flex justify-center items-center py-32">
                    <LoadingSpinner size="lg" />
                </div>
            ) : data ? (
                <div className="max-w-7xl mx-auto px-4 py-8 pt-12">

                    {/* Macro Grid - 4 KPIs */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-10 relative z-10">
                        {/* Total Turnover */}
                        <div className="bg-white rounded-xl shadow-lg p-5 border-t-4 border-blue-500 hover:-translate-y-1 transition-transform duration-200">
                            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
                                {t('total_turnover', { year: data.macro.data_year || '' })}
                            </p>
                            <div className="flex items-baseline gap-2">
                                <p className="text-2xl font-bold text-gray-900">
                                    {data.macro.total_turnover_formatted || '-'}
                                </p>
                                {formatGrowth(data.macro.turnover_growth)}
                            </div>
                        </div>

                        {/* Employment */}
                        <div className="bg-white rounded-xl shadow-lg p-5 border-t-4 border-green-500 hover:-translate-y-1 transition-transform duration-200">
                            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">{t('employees')}</p>
                            <div className="flex items-baseline gap-2">
                                <p className="text-2xl font-bold text-gray-900">
                                    {data.macro.total_employees?.toLocaleString() || '-'}
                                </p>
                                {formatGrowth(data.macro.employee_change)}
                            </div>
                        </div>

                        {/* Average Salary */}
                        <div className="bg-white rounded-xl shadow-lg p-5 border-t-4 border-purple-500 hover:-translate-y-1 transition-transform duration-200">
                            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">{t('avg_salary')}</p>
                            <p className="text-2xl font-bold text-gray-900">
                                {data.macro.avg_salary ? `${data.macro.avg_salary.toLocaleString()} €` : '-'}
                            </p>
                            <span className="text-xs text-gray-400 mt-1 block">{t('per_month')}</span>
                        </div>

                        {/* Total Profit */}
                        <div className="bg-white rounded-xl shadow-lg p-5 border-t-4 border-amber-500 hover:-translate-y-1 transition-transform duration-200">
                            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">{t('total_profit')}</p>
                            <p className="text-2xl font-bold text-gray-900">
                                {data.macro.total_profit_formatted || '-'}
                            </p>
                            <span className="text-xs text-gray-400 mt-1 block">{t('profitability')}</span>
                        </div>
                    </div>

                    {/* Top Lists Section */}
                    <div className="mb-12">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            {/* Fastest Growth */}
                            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
                                <div className="flex items-center mb-4 pb-2 border-b border-gray-100">
                                    <span className="text-2xl mr-2">🚀</span>
                                    <h3 className="font-semibold text-gray-800">{t('fastest_growth')}</h3>
                                </div>
                                <div className="space-y-3">
                                    {data.top_growth.map((item, idx) => (
                                        <Link
                                            key={item.nace_code}
                                            href={`/industries/${item.nace_code}`}
                                            className="flex items-center justify-between hover:bg-blue-50 p-2 -mx-2 rounded-lg transition-colors group"
                                        >
                                            <div className="flex items-center min-w-0">
                                                <span className="text-gray-400 w-6 font-mono text-sm">{idx + 1}</span>
                                                <span className="text-gray-700 ml-1 truncate group-hover:text-blue-600 text-sm font-medium">{item.name}</span>
                                            </div>
                                            <span className="text-green-600 font-bold text-sm ml-2">+{item.growth_percent}%</span>
                                        </Link>
                                    ))}
                                </div>
                            </div>

                            {/* Highest Salaries */}
                            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
                                <div className="flex items-center mb-4 pb-2 border-b border-gray-100">
                                    <span className="text-2xl mr-2">💰</span>
                                    <h3 className="font-semibold text-gray-800">{t('highest_salaries')}</h3>
                                </div>
                                <div className="space-y-3">
                                    {data.top_salary.map((item, idx) => (
                                        <Link
                                            key={item.nace_code}
                                            href={`/industries/${item.nace_code}`}
                                            className="flex items-center justify-between hover:bg-blue-50 p-2 -mx-2 rounded-lg transition-colors group"
                                        >
                                            <div className="flex items-center min-w-0">
                                                <span className="text-gray-400 w-6 font-mono text-sm">{idx + 1}</span>
                                                <span className="text-gray-700 ml-1 truncate group-hover:text-blue-600 text-sm font-medium">{item.name}</span>
                                            </div>
                                            <span className="text-purple-600 font-bold text-sm ml-2">
                                                {item.avg_salary?.toLocaleString()} €
                                            </span>
                                        </Link>
                                    ))}
                                </div>
                            </div>

                            {/* Highest Turnover */}
                            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
                                <div className="flex items-center mb-4 pb-2 border-b border-gray-100">
                                    <span className="text-2xl mr-2">📊</span>
                                    <h3 className="font-semibold text-gray-800">{t('highest_turnover')}</h3>
                                </div>
                                <div className="space-y-3">
                                    {data.top_turnover.map((item, idx) => (
                                        <Link
                                            key={item.nace_code}
                                            href={`/industries/${item.nace_code}`}
                                            className="flex items-center justify-between hover:bg-blue-50 p-2 -mx-2 rounded-lg transition-colors group"
                                        >
                                            <div className="flex items-center min-w-0">
                                                <span className="text-gray-400 w-6 font-mono text-sm">{idx + 1}</span>
                                                <span className="text-gray-700 ml-1 truncate group-hover:text-blue-600 text-sm font-medium">{item.name}</span>
                                            </div>
                                            <span className="text-blue-600 font-bold text-sm ml-2">{item.turnover_formatted}</span>
                                        </Link>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Industries Table View */}
                    <div className="bg-white rounded-xl shadow-md overflow-hidden border border-gray-200">
                        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
                            <h2 className="text-lg font-bold text-gray-900">{t('all_industries_title')}</h2>
                            <span className="text-xs text-gray-500 font-medium bg-gray-200 px-2 py-1 rounded">
                                {t('sections_count', { count: data.sections.length })}
                            </span>
                        </div>

                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th
                                            scope="col"
                                            className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700 group"
                                            onClick={() => handleSort('nace_code')}
                                        >
                                            {t('table_code')} {sortConfig.key === 'nace_code' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                                        </th>
                                        <th
                                            scope="col"
                                            className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700 group"
                                            onClick={() => handleSort('name')}
                                        >
                                            {t('table_name')} {sortConfig.key === 'name' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                                        </th>
                                        <th
                                            scope="col"
                                            className="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700 group"
                                            onClick={() => handleSort('turnover')}
                                        >
                                            {t('table_turnover')} {sortConfig.key === 'turnover' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                                        </th>
                                        <th
                                            scope="col"
                                            className="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700 group"
                                            onClick={() => handleSort('avg_salary')}
                                        >
                                            {t('table_salary')} {sortConfig.key === 'avg_salary' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                                        </th>
                                        <th
                                            scope="col"
                                            className="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700 group"
                                            onClick={() => handleSort('turnover_growth')}
                                        >
                                            {t('table_growth')} {sortConfig.key === 'turnover_growth' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                                        </th>
                                        <th scope="col" className="relative px-6 py-3">
                                            <span className="sr-only">Skatīt</span>
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {sortedSections.map((section) => (
                                        <tr key={section.nace_code} className="hover:bg-blue-50 transition-colors group">
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                                <div className="flex items-center">
                                                    <span className="text-xl mr-2">{section.icon}</span>
                                                    {section.nace_code}
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 text-sm text-gray-700 font-medium">
                                                <Link href={`/industries/${section.nace_code}`} className="group-hover:text-blue-600 hover:underline block">
                                                    {section.name}
                                                </Link>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900 font-semibold">
                                                {section.turnover_formatted || '-'}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-purple-600 font-semibold bg-purple-50 rounded-lg bg-opacity-30">
                                                {section.avg_salary ? `${section.avg_salary.toLocaleString()} €` : '-'}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                                                {formatGrowth(section.turnover_growth)}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                <Link href={`/industries/${section.nace_code}`} className="text-blue-600 hover:text-blue-900 font-bold">
                                                    →
                                                </Link>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="text-center py-32 text-gray-500">
                    {t('error_loading')}
                </div>
            )}
        </div>
    );
}
