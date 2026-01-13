"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import DataDiggingLoader from "@/components/DataDiggingLoader";

interface LocationStats {
    name: string;
    location_type: string;
    company_count: number;
    total_employees: number | null;
    total_revenue: number | null;
    total_profit: number | null;
    avg_salary: number | null;
    avg_revenue_per_company: number | null;
}

interface TopCompany {
    regcode: number;
    name: string;
    turnover: number | null;
    profit: number | null;
    employees: number | null;
    nace_text: string | null;
}

const formatNumber = (num: number | null | undefined) => {
    if (num === null || num === undefined) return "-";
    if (num >= 1000000000) return `${(num / 1000000000).toFixed(1)}B`;
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toLocaleString();
};

const formatCurrency = (num: number | null | undefined) => {
    if (num === null || num === undefined) return "-";
    return `€${formatNumber(num)}`;
};

export default function LocationDetailPage() {
    const params = useParams();
    const router = useRouter();
    const type = params.type as string;
    const name = decodeURIComponent(params.name as string);

    const [stats, setStats] = useState<LocationStats | null>(null);
    const [topCompanies, setTopCompanies] = useState<TopCompany[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                // Fetch location stats
                const statsRes = await fetch(`/api/locations/${type}/${encodeURIComponent(name)}/stats`);
                const statsData = await statsRes.json();
                setStats(statsData);

                // Fetch top companies
                const companiesRes = await fetch(`/api/locations/${type}/${encodeURIComponent(name)}/top-companies?limit=20`);
                const companiesData = await companiesRes.json();
                setTopCompanies(companiesData);

                setLoading(false);
            } catch (err) {
                setError("Failed to load location data");
                setLoading(false);
            }
        };

        fetchData();
    }, [type, name]);

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <Navbar />
                <DataDiggingLoader />
            </div>
        );
    }

    if (error || !stats) {
        return (
            <div className="min-h-screen bg-gray-50">
                <Navbar />
                <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="bg-red-50 rounded-xl p-8 text-center text-red-600">
                        {error || "Neizdevās ielādēt datus"}
                    </div>
                </main>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <Navbar />

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Header */}
                <div className="mb-8">
                    <Link
                        href="/regions"
                        className="text-primary hover:underline mb-4 inline-block"
                    >
                        ← Atpakaļ uz reģioniem
                    </Link>
                    <h1 className="text-3xl font-bold text-gray-900">
                        {stats.name}
                    </h1>
                    <p className="mt-2 text-gray-600">
                        {type === "city" ? "Pilsēta" : "Novads"}
                    </p>
                </div>

                {/* KPI Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                    <div className="bg-white rounded-xl shadow-sm p-6">
                        <div className="text-sm text-gray-500">Uzņēmumi</div>
                        <div className="text-3xl font-bold text-gray-900 mt-2">
                            {formatNumber(stats.company_count)}
                        </div>
                    </div>
                    <div className="bg-white rounded-xl shadow-sm p-6">
                        <div className="text-sm text-gray-500">Kopējais apgrozījums</div>
                        <div className="text-3xl font-bold text-gray-900 mt-2">
                            {formatCurrency(stats.total_revenue)}
                        </div>
                    </div>
                    <div className="bg-white rounded-xl shadow-sm p-6">
                        <div className="text-sm text-gray-500">Darbinieki</div>
                        <div className="text-3xl font-bold text-gray-900 mt-2">
                            {formatNumber(stats.total_employees)}
                        </div>
                    </div>
                    <div className="bg-white rounded-xl shadow-sm p-6">
                        <div className="text-sm text-gray-500">Vid. bruto alga</div>
                        <div className="text-3xl font-bold text-gray-900 mt-2">
                            {stats.avg_salary ? `€${Math.round(stats.avg_salary)}` : "-"}
                        </div>
                    </div>
                </div>

                {/* Additional Stats */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                    <div className="bg-white rounded-xl shadow-sm p-6">
                        <div className="text-sm text-gray-500">Kopējā peļņa</div>
                        <div className="text-2xl font-bold text-gray-900 mt-2">
                            {formatCurrency(stats.total_profit)}
                        </div>
                    </div>
                    <div className="bg-white rounded-xl shadow-sm p-6">
                        <div className="text-sm text-gray-500">Vid. apgrozījums/uzņēmums</div>
                        <div className="text-2xl font-bold text-gray-900 mt-2">
                            {formatCurrency(stats.avg_revenue_per_company)}
                        </div>
                    </div>
                </div>

                {/* Top Companies */}
                <div className="bg-white rounded-xl shadow-sm overflow-hidden">
                    <div className="px-6 py-4 border-b border-gray-200">
                        <h2 className="text-xl font-bold text-gray-900">
                            Top {topCompanies.length} uzņēmumi pēc apgrozījuma
                        </h2>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Uzņēmums
                                    </th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Apgrozījums
                                    </th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Peļņa
                                    </th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Darbinieki
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Nozare
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {topCompanies.map((company, index) => (
                                    <tr key={company.regcode} className="hover:bg-gray-50">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center">
                                                <span className="text-xs text-gray-400 mr-3">#{index + 1}</span>
                                                <Link
                                                    href={`/company/${company.regcode}`}
                                                    className="text-primary hover:underline font-medium"
                                                >
                                                    {company.name}
                                                </Link>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-right font-medium">
                                            {formatCurrency(company.turnover)}
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            {formatCurrency(company.profit)}
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            {formatNumber(company.employees)}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-gray-600">
                                            {company.nace_text || "-"}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </main>
        </div>
    );
}
