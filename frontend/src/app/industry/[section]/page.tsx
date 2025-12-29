'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Navbar from '@/components/Navbar';
import Link from 'next/link';
import { notFound } from "next/navigation";
import { formatCompanyName } from "@/utils/formatCompanyName";
import CompanySizeBadge from '@/components/CompanySizeBadge';
import LoadingSpinner from '@/components/LoadingSpinner';

interface Company {
    rank: number;
    regcode: number;
    name: string;
    turnover: number | null;
    profit: number | null;
    employees: number | null;
    year: number;
    company_size: string | null;
    is_pvn_payer: boolean;
}

interface IndustryData {
    section: string;
    section_name: string;
    total_companies: number;
    sort_by: string;
    companies: Company[];
}

export default function IndustryPage() {
    // useParams hook - stable way to access route params in client components
    const params = useParams();
    const section = params.section as string;

    const [data, setData] = useState<IndustryData | null>(null);
    const [loading, setLoading] = useState(true);
    const [sortBy, setSortBy] = useState<'turnover' | 'profit'>('turnover');

    const fetchData = async (sort: 'turnover' | 'profit') => {
        if (!section) return;
        setLoading(true);
        try {
            // Use /api prefix - proxied through Next.js server
            const res = await fetch(`/api/industries/${section}?sort_by=${sort}`);
            const json = await res.json();
            setData(json);
        } catch (error) {
            console.error('Failed to fetch industry data:', error);
        }
        setLoading(false);
    };

    useEffect(() => {
        fetchData(sortBy);
    }, [sortBy, section]);

    const formatCurrency = (value: number | null) => {
        if (!value) return '-';
        if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)} M€`;
        if (value >= 1_000) return `${(value / 1_000).toFixed(0)} k€`;
        return `€${value.toFixed(0)}`;
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
                    {data && (
                        <>
                            <h1 className="text-4xl font-bold text-primary mb-2">
                                🏭 {data.section_name || `Nozare ${data.section}`}
                            </h1>
                            <p className="text-gray-600">
                                Kopā {data.total_companies.toLocaleString()} uzņēmumi
                            </p>
                        </>
                    )}
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
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">#</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Uzņēmums</th>
                                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            {sortBy === 'turnover' ? 'Apgrozījums' : 'Peļņa'}
                                        </th>
                                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Darbinieki</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Lielums</th>
                                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">PVN</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {data.companies.map((company) => (
                                        <tr key={company.regcode} className="hover:bg-gray-50 transition-colors">
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">
                                                {company.rank}
                                            </td>
                                            <td className="px-6 py-4">
                                                <Link
                                                    href={`/company/${company.regcode}`}
                                                    className="text-primary hover:underline font-medium"
                                                >
                                                    {formatCompanyName(company)}
                                                </Link>
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
                                            <td className="px-6 py-4 whitespace-nowrap text-center">
                                                {company.is_pvn_payer ? (
                                                    <span className="text-xs text-green-600">✓</span>
                                                ) : (
                                                    <span className="text-xs text-gray-300">-</span>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                ) : (
                    <div className="text-center py-20 text-gray-500">
                        Nav datu par šo nozari
                    </div>
                )}
            </main>
        </div>
    );
}
