"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";

interface Territory {
    id: number;
    code: string;
    name: string;
    type: string;
    year: number | null;
    total_revenue: number | null;
    total_profit: number | null;
    total_employees: number | null;
    avg_salary: number | null;
    company_count: number | null;
    revenue_growth_yoy: number | null;
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

const formatGrowth = (num: number | null | undefined) => {
    if (num === null || num === undefined) return "-";
    const sign = num > 0 ? "+" : "";
    return `${sign}${num.toFixed(1)}%`;
};

export default function RegionsPage() {
    const [territories, setTerritories] = useState<Territory[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedYear, setSelectedYear] = useState<number | null>(null);
    const [selectedMetric, setSelectedMetric] = useState("revenue");
    const [years, setYears] = useState<number[]>([]);
    const [sortColumn, setSortColumn] = useState("total_revenue");
    const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");

    // Fetch available years
    useEffect(() => {
        fetch("/api/regions/years")
            .then(res => res.json())
            .then(data => {
                setYears(data);
                if (data.length > 0) setSelectedYear(data[0]);
            })
            .catch(err => console.error("Failed to fetch years:", err));
    }, []);

    // Fetch territories data
    useEffect(() => {
        if (!selectedYear) return;

        setLoading(true);
        fetch(`/api/regions?year=${selectedYear}&metric=${selectedMetric}`)
            .then(res => res.json())
            .then(data => {
                setTerritories(data);
                setLoading(false);
            })
            .catch(err => {
                setError("Failed to load regions data");
                setLoading(false);
            });
    }, [selectedYear, selectedMetric]);

    // Sort territories
    const sortedTerritories = [...territories].sort((a, b) => {
        const aVal = a[sortColumn as keyof Territory] ?? 0;
        const bVal = b[sortColumn as keyof Territory] ?? 0;
        if (sortDirection === "asc") {
            return aVal > bVal ? 1 : -1;
        }
        return aVal < bVal ? 1 : -1;
    });

    const handleSort = (column: string) => {
        if (sortColumn === column) {
            setSortDirection(sortDirection === "asc" ? "desc" : "asc");
        } else {
            setSortColumn(column);
            setSortDirection("desc");
        }
    };

    const SortIcon = ({ column }: { column: string }) => (
        <span className="ml-1 text-gray-400">
            {sortColumn === column ? (sortDirection === "asc" ? "↑" : "↓") : "↕"}
        </span>
    );

    return (
        <div className="min-h-screen bg-gray-50">
            <Navbar />

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900">
                        Latvijas Ekonomika pēc Reģioniem
                    </h1>
                    <p className="mt-2 text-gray-600">
                        Ekonomikas rādītāji pa novadiem un pilsētām
                    </p>
                </div>

                {/* Filters */}
                <div className="bg-white rounded-xl shadow-sm p-4 mb-6 flex flex-wrap gap-4 items-center">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Gads
                        </label>
                        <select
                            value={selectedYear || ""}
                            onChange={(e) => setSelectedYear(Number(e.target.value))}
                            className="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary/50"
                        >
                            {years.map(year => (
                                <option key={year} value={year}>{year}</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Kārtot pēc
                        </label>
                        <select
                            value={selectedMetric}
                            onChange={(e) => setSelectedMetric(e.target.value)}
                            className="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary/50"
                        >
                            <option value="revenue">Apgrozījums</option>
                            <option value="employees">Darbinieki</option>
                            <option value="salary">Vidējā alga</option>
                            <option value="companies">Uzņēmumu skaits</option>
                            <option value="growth">Izaugsme</option>
                        </select>
                    </div>

                    <div className="ml-auto text-sm text-gray-500">
                        {territories.length} novadi/pilsētas
                    </div>
                </div>

                {/* Statistics Cards */}
                {!loading && territories.length > 0 && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                        <div className="bg-white rounded-xl shadow-sm p-4">
                            <div className="text-sm text-gray-500">Kopējais apgrozījums</div>
                            <div className="text-2xl font-bold text-gray-900">
                                {formatCurrency(territories.reduce((sum, t) => sum + (t.total_revenue || 0), 0))}
                            </div>
                        </div>
                        <div className="bg-white rounded-xl shadow-sm p-4">
                            <div className="text-sm text-gray-500">Kopējie darbinieki</div>
                            <div className="text-2xl font-bold text-gray-900">
                                {formatNumber(territories.reduce((sum, t) => sum + (t.total_employees || 0), 0))}
                            </div>
                        </div>
                        <div className="bg-white rounded-xl shadow-sm p-4">
                            <div className="text-sm text-gray-500">Kopējie uzņēmumi</div>
                            <div className="text-2xl font-bold text-gray-900">
                                {formatNumber(territories.reduce((sum, t) => sum + (t.company_count || 0), 0))}
                            </div>
                        </div>
                        <div className="bg-white rounded-xl shadow-sm p-4">
                            <div className="text-sm text-gray-500">Vidējā alga (valstī)</div>
                            <div className="text-2xl font-bold text-gray-900">
                                €{Math.round(territories.reduce((sum, t) => sum + (t.avg_salary || 0), 0) / territories.length)}
                            </div>
                        </div>
                    </div>
                )}

                {/* Table */}
                {loading ? (
                    <div className="bg-white rounded-xl shadow-sm p-12 text-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
                        <p className="mt-4 text-gray-500">Ielādē datus...</p>
                    </div>
                ) : error ? (
                    <div className="bg-red-50 rounded-xl p-8 text-center text-red-600">
                        {error}
                    </div>
                ) : (
                    <div className="bg-white rounded-xl shadow-sm overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Novads/Pilsēta
                                        </th>
                                        <th
                                            className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                            onClick={() => handleSort("total_revenue")}
                                        >
                                            Apgrozījums <SortIcon column="total_revenue" />
                                        </th>
                                        <th
                                            className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                            onClick={() => handleSort("total_employees")}
                                        >
                                            Darbinieki <SortIcon column="total_employees" />
                                        </th>
                                        <th
                                            className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                            onClick={() => handleSort("avg_salary")}
                                        >
                                            Vid. alga <SortIcon column="avg_salary" />
                                        </th>
                                        <th
                                            className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                            onClick={() => handleSort("company_count")}
                                        >
                                            Uzņēmumi <SortIcon column="company_count" />
                                        </th>
                                        <th
                                            className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                            onClick={() => handleSort("revenue_growth_yoy")}
                                        >
                                            Izaugsme <SortIcon column="revenue_growth_yoy" />
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {sortedTerritories.map((territory, index) => (
                                        <tr
                                            key={territory.id}
                                            className="hover:bg-gray-50 transition-colors"
                                        >
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <Link
                                                    href={`/regions/${territory.id}`}
                                                    className="text-primary hover:underline font-medium"
                                                >
                                                    {territory.name}
                                                </Link>
                                                <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${territory.type === "NOVADS"
                                                        ? "bg-blue-100 text-blue-700"
                                                        : "bg-purple-100 text-purple-700"
                                                    }`}>
                                                    {territory.type === "NOVADS" ? "Novads" : "Pilsēta"}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-right whitespace-nowrap font-medium">
                                                {formatCurrency(territory.total_revenue)}
                                            </td>
                                            <td className="px-6 py-4 text-right whitespace-nowrap">
                                                {formatNumber(territory.total_employees)}
                                            </td>
                                            <td className="px-6 py-4 text-right whitespace-nowrap">
                                                {territory.avg_salary ? `€${Math.round(territory.avg_salary)}` : "-"}
                                            </td>
                                            <td className="px-6 py-4 text-right whitespace-nowrap">
                                                {formatNumber(territory.company_count)}
                                            </td>
                                            <td className="px-6 py-4 text-right whitespace-nowrap">
                                                <span className={`${(territory.revenue_growth_yoy || 0) > 0
                                                        ? "text-green-600"
                                                        : (territory.revenue_growth_yoy || 0) < 0
                                                            ? "text-red-600"
                                                            : "text-gray-500"
                                                    }`}>
                                                    {formatGrowth(territory.revenue_growth_yoy)}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}
