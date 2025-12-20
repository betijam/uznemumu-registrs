'use client';

import { useState, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import Link from 'next/link';
import CompanySizeBadge from '@/components/CompanySizeBadge';
import LoadingSpinner from '@/components/LoadingSpinner';

interface Company {
    rank: number;
    regcode: number;
    name: string;
    industry: string;
    turnover: number | null;
    profit: number | null;
    employees: number | null;
    year: number;
    company_size: string | null;
    is_pvn_payer: boolean;
}

interface TopData {
    sort_by: string;
    total: number;
    companies: Company[];
}

export default function Top100Page() {
    const [data, setData] = useState<TopData | null>(null);
    const [loading, setLoading] = useState(true);
    const [sortBy, setSortBy] = useState<'turnover' | 'profit'>('turnover');

    const fetchData = async (sort: 'turnover' | 'profit') => {
        setLoading(true);
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
        try {
            const res = await fetch(`${API_URL}/top100?sort_by=${sort}`);
            const json = await res.json();
            setData(json);
        } catch (error) {
            console.error('Failed to fetch TOP 100 data:', error);
        }
        setLoading(false);
    };

    useEffect(() => {
        fetchData(sortBy);
    }, [sortBy]);

    const formatCurrency = (value: number | null) => {
        if (!value) return '-';
        if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)} M€`;
        if (value >= 1_000) return `${(value / 1_000).toFixed(0)} k€`;
        return `€${value.toFixed(0)}`;
    };

    const getRankBadge = (rank: number) => {
        if (rank === 1) return '🥇';
        if (rank === 2) return '🥈';
        if (rank === 3) return '🥉';
        return `#${rank}`;
    };

    return (
        <div className="min-h-screen bg-background">
            <Navbar />

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Header */}
                <div className="mb-8">
                    <Link href="/" className="text-sm text-primary hover:underline mb-4 inline-block">
                        ← Sākumlapa
                    </Link>
                    <h1 className="text-4xl font-bold text-primary mb-2">
                        🏆 TOP 100 Latvijas Uzņēmumi
                    </h1>
                    <p className="text-gray-600">
                        Lielākie uzņēmumi Latvijā pēc {sortBy === 'turnover' ? 'apgrozījuma' : 'peļņas'}
                    </p>
                </div>

                {/* Sort Toggle */}
                <div className="mb-6 flex gap-3">
                    <button
                        onClick={() => setSortBy('turnover')}
                        className={`px-6 py-2 rounded-lg font-medium transition-all ${sortBy === 'turnover'
                            ? 'bg-primary text-white shadow-md'
                            : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                            }`}
                    >
                        Apgrozījums
                    </button>
                    <button
                        onClick={() => setSortBy('profit')}
                        className={`px-6 py-2 rounded-lg font-medium transition-all ${sortBy === 'profit'
                            ? 'bg-primary text-white shadow-md'
                            : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                            }`}
                    >
                        Peļņa
                    </button>
                </div>

                {/* Companies Table */}
                {loading ? (
                    <div className="flex justify-center items-center py-20">
                        <LoadingSpinner size="lg" />
                    </div>
                ) : data && data.companies.length > 0 ? (
                    <div className="bg-white rounded-xl shadow-card overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vieta</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Uzņēmums</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nozare</th>
                                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            {sortBy === 'turnover' ? 'Apgrozījums' : 'Peļņa'}
                                        </th>
                                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Darbinieki</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Lielums</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {data.companies.map((company) => (
                                        <tr
                                            key={company.regcode}
                                            className={`hover:bg-gray-50 transition-colors ${company.rank <= 3 ? 'bg-yellow-50/30' : ''
                                                }`}
                                        >
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className={`text-sm font-bold ${company.rank <= 3 ? 'text-2xl' : 'text-gray-900'
                                                    }`}>
                                                    {getRankBadge(company.rank)}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4">
                                                <Link
                                                    href={`/company/${company.regcode}`}
                                                    className="text-primary hover:underline font-medium"
                                                >
                                                    {company.name}
                                                </Link>
                                            </td>
                                            <td className="px-6 py-4 text-sm text-gray-600">
                                                {company.industry || '-'}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-semibold text-gray-900">
                                                {formatCurrency(sortBy === 'turnover' ? company.turnover : company.profit)}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500">
                                                {company.employees || '-'}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <CompanySizeBadge size={company.company_size} />
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                ) : (
                    <div className="text-center py-20 text-gray-500">
                        Nav datu
                    </div>
                )}
            </main>
        </div>
    );
}
