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

export default function IndustriesPage() {
    const [data, setData] = useState<OverviewData | null>(null);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
    const [showSearch, setShowSearch] = useState(false);

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

            {/* Hero Section */}
            <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-slate-800 text-white py-20 px-4">
                <div className="max-w-6xl mx-auto text-center">
                    <h1 className="text-4xl md:text-5xl font-bold mb-4">
                        Latvijas Ekonomikas Analītika
                    </h1>
                    <p className="text-lg text-gray-300 mb-10">
                        Izpēti tirgus tendences, algas un līderus 88 nozarēs
                    </p>

                    {/* Search Box */}
                    <div className="max-w-2xl mx-auto relative">
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Meklēt nozari (piem., 'IT', 'Būvniecība', 'Mežsaimniecība')..."
                            className="w-full px-6 py-4 rounded-xl text-gray-800 bg-white shadow-lg text-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />

                        {/* Search Results Dropdown */}
                        {showSearch && searchResults.length > 0 && (
                            <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-xl z-50 max-h-80 overflow-auto">
                                {searchResults.map((result) => (
                                    <Link
                                        key={result.code}
                                        href={`/industries/${result.code}`}
                                        className="flex items-center px-6 py-3 hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-0"
                                        onClick={() => setShowSearch(false)}
                                    >
                                        <span className="text-2xl mr-3">{result.icon}</span>
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
                <div className="max-w-7xl mx-auto px-4 py-8 -mt-8">

                    {/* Macro Grid - 4 KPIs */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-12">
                        {/* Total Turnover */}
                        <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-blue-500">
                            <p className="text-xs font-medium text-gray-500 uppercase mb-1">
                                Kopējais Apgrozījums ({data.macro.data_year})
                            </p>
                            <p className="text-3xl font-bold text-gray-900 mb-1">
                                {data.macro.total_turnover_formatted || '-'}
                            </p>
                            {formatGrowth(data.macro.turnover_growth)}
                            {data.macro.turnover_growth && (
                                <span className="text-xs text-gray-500 ml-1">pret {(data.macro.data_year || 2023) - 1}</span>
                            )}
                        </div>

                        {/* Employment */}
                        <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-green-500">
                            <p className="text-xs font-medium text-gray-500 uppercase mb-1">Nodarbinātie</p>
                            <p className="text-3xl font-bold text-gray-900 mb-1">
                                {data.macro.total_employees?.toLocaleString() || '-'}
                            </p>
                            {formatGrowth(data.macro.employee_change)}
                            {data.macro.employee_change !== null && (
                                <span className="text-xs text-gray-500 ml-1">izmaiņas</span>
                            )}
                        </div>

                        {/* Average Salary */}
                        <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-purple-500">
                            <p className="text-xs font-medium text-gray-500 uppercase mb-1">Vid. Bruto Alga</p>
                            <p className="text-3xl font-bold text-gray-900 mb-1">
                                {data.macro.avg_salary ? `${data.macro.avg_salary.toLocaleString()} €` : '-'}
                            </p>
                            <span className="text-xs text-gray-500">mēnesī (vidēji)</span>
                        </div>

                        {/* Total Profit */}
                        <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-amber-500">
                            <p className="text-xs font-medium text-gray-500 uppercase mb-1">Kopējā Peļņa</p>
                            <p className="text-3xl font-bold text-gray-900 mb-1">
                                {data.macro.total_profit_formatted || '-'}
                            </p>
                            <span className="text-xs text-gray-500">rentabilitāte</span>
                        </div>
                    </div>

                    {/* Top Lists Section */}
                    <div className="mb-12">
                        <h2 className="text-2xl font-bold text-gray-900 mb-6">Nozaru Topi</h2>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

                            {/* Fastest Growth */}
                            <div className="bg-white rounded-xl shadow-md p-6">
                                <div className="flex items-center mb-4">
                                    <span className="text-2xl mr-2">🚀</span>
                                    <h3 className="font-semibold text-gray-800">Straujākā Izaugsme</h3>
                                    <span className="ml-auto text-xs font-medium text-gray-500">YoY</span>
                                </div>
                                <div className="space-y-3">
                                    {data.top_growth.length > 0 ? data.top_growth.map((item, idx) => (
                                        <Link
                                            key={item.nace_code}
                                            href={`/industries/${item.nace_code}`}
                                            className="flex items-center justify-between hover:bg-gray-50 p-2 rounded-lg transition-colors"
                                        >
                                            <div className="flex items-center">
                                                <span className="text-gray-500 w-5">{idx + 1}</span>
                                                <span className="text-gray-700 ml-2">{item.name} ({item.nace_code})</span>
                                            </div>
                                            <span className="text-green-600 font-semibold">+{item.growth_percent}%</span>
                                        </Link>
                                    )) : (
                                        <p className="text-gray-400 text-sm">Nav datu</p>
                                    )}
                                </div>
                            </div>

                            {/* Highest Salaries */}
                            <div className="bg-white rounded-xl shadow-md p-6">
                                <div className="flex items-center mb-4">
                                    <span className="text-2xl mr-2">💰</span>
                                    <h3 className="font-semibold text-gray-800">Lielākās Algas (Bruto)</h3>
                                    <span className="ml-auto text-xs font-medium text-gray-500">€</span>
                                </div>
                                <div className="space-y-3">
                                    {data.top_salary.map((item, idx) => (
                                        <Link
                                            key={item.nace_code}
                                            href={`/industries/${item.nace_code}`}
                                            className="flex items-center justify-between hover:bg-gray-50 p-2 rounded-lg transition-colors"
                                        >
                                            <div className="flex items-center">
                                                <span className="text-gray-500 w-5">{idx + 1}</span>
                                                <span className="text-gray-700 ml-2">{item.name} ({item.nace_code})</span>
                                            </div>
                                            <span className="text-purple-600 font-semibold">
                                                {item.avg_salary?.toLocaleString()} €
                                                <span className="text-xs text-gray-400 ml-1">vidēji</span>
                                            </span>
                                        </Link>
                                    ))}
                                </div>
                            </div>

                            {/* Highest Turnover */}
                            <div className="bg-white rounded-xl shadow-md p-6">
                                <div className="flex items-center mb-4">
                                    <span className="text-2xl mr-2">📊</span>
                                    <h3 className="font-semibold text-gray-800">Lielākais Apgrozījums</h3>
                                    <span className="ml-auto text-xs font-medium text-gray-500">Vol</span>
                                </div>
                                <div className="space-y-3">
                                    {data.top_turnover.map((item, idx) => (
                                        <Link
                                            key={item.nace_code}
                                            href={`/industries/${item.nace_code}`}
                                            className="flex items-center justify-between hover:bg-gray-50 p-2 rounded-lg transition-colors"
                                        >
                                            <div className="flex items-center">
                                                <span className="text-gray-500 w-5">{idx + 1}</span>
                                                <span className="text-gray-700 ml-2">{item.name} ({item.nace_code})</span>
                                            </div>
                                            <span className="text-blue-600 font-semibold">{item.turnover_formatted}</span>
                                        </Link>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* All Industries Grid */}
                    <div>
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-2xl font-bold text-gray-900">Visas Nozares (NACE Klasifikators)</h2>
                            <button className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                                Kārtot A-Z
                            </button>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                            {data.sections.map((section) => (
                                <Link
                                    key={section.nace_code}
                                    href={`/industries/${section.nace_code}`}
                                    className="bg-white rounded-xl shadow-md hover:shadow-lg transition-all p-6 border border-gray-100 group"
                                >
                                    <div className="flex items-start mb-4">
                                        <span className="text-3xl mr-3">{section.icon}</span>
                                        <div>
                                            <h3 className="font-semibold text-gray-800 group-hover:text-blue-600 transition-colors">
                                                {section.nace_code}. {section.name}
                                            </h3>
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-3 gap-2 text-sm">
                                        <div>
                                            <p className="text-xs text-gray-500 uppercase">Apgrozījums</p>
                                            <p className="font-semibold text-gray-800">{section.turnover_formatted || '-'}</p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-gray-500 uppercase">Vid. Alga</p>
                                            <p className="font-semibold text-gray-800">
                                                {section.avg_salary ? `${section.avg_salary.toLocaleString()} €` : '-'}
                                            </p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-gray-500 uppercase">Izaugsme</p>
                                            <p className={`font-semibold ${section.turnover_growth !== null
                                                    ? section.turnover_growth >= 0
                                                        ? 'text-green-600'
                                                        : 'text-red-600'
                                                    : 'text-gray-400'
                                                }`}>
                                                {section.turnover_growth !== null
                                                    ? `${section.turnover_growth >= 0 ? '▲' : '▼'} ${Math.abs(section.turnover_growth)}%`
                                                    : '-'}
                                            </p>
                                        </div>
                                    </div>
                                </Link>
                            ))}
                        </div>
                    </div>
                </div>
            ) : (
                <div className="text-center py-32 text-gray-500">
                    Neizdevās ielādēt datus
                </div>
            )}
        </div>
    );
}
