"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";

interface Location {
    name: string;
    company_count: number;
    total_employees: number | null;
    total_revenue: number | null;
    total_profit: number | null;
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

export default function RegionsPage() {
    const [locations, setLocations] = useState<Location[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [locationType, setLocationType] = useState<"municipalities" | "cities">("cities");
    const [sortColumn, setSortColumn] = useState<keyof Location>("company_count");
    const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");

    // Fetch locations data
    useEffect(() => {
        setLoading(true);
        fetch(`/api/locations/${locationType}?limit=100`)
            .then(res => res.json())
            .then(data => {
                setLocations(data);
                setLoading(false);
            })
            .catch(err => {
                setError("Failed to load locations data");
                setLoading(false);
            });
    }, [locationType]);

    // Sort locations
    const sortedLocations = [...locations].sort((a, b) => {
        const aVal = a[sortColumn] ?? 0;
        const bVal = b[sortColumn] ?? 0;
        if (sortDirection === "asc") {
            return aVal > bVal ? 1 : -1;
        }
        return aVal < bVal ? 1 : -1;
    });

    const handleSort = (column: keyof Location) => {
        if (sortColumn === column) {
            setSortDirection(sortDirection === "asc" ? "desc" : "asc");
        } else {
            setSortColumn(column);
            setSortDirection("desc");
        }
    };

    const SortIcon = ({ column }: { column: keyof Location }) => (
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
                        Ekonomikas rādītāji pa novadiem un pilsētām (VARIS dati)
                    </p>
                </div>

                {/* Filters */}
                <div className="bg-white rounded-xl shadow-sm p-4 mb-6 flex flex-wrap gap-4 items-center">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Tips
                        </label>
                        <select
                            value={locationType}
                            onChange={(e) => setLocationType(e.target.value as "municipalities" | "cities")}
                            className="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary/50"
                        >
                            <option value="cities">Pilsētas</option>
                            <option value="municipalities">Novadi</option>
                        </select>
                    </div>

                    <div className="ml-auto text-sm text-gray-500">
                        {locations.length} {locationType === "cities" ? "pilsētas" : "novadi"}
                    </div>
                </div>

                {/* Statistics Cards */}
                {!loading && locations.length > 0 && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                        <div className="bg-white rounded-xl shadow-sm p-4">
                            <div className="text-sm text-gray-500">Kopējais apgrozījums</div>
                            <div className="text-2xl font-bold text-gray-900">
                                {formatCurrency(locations.reduce((sum, t) => sum + (t.total_revenue || 0), 0))}
                            </div>
                        </div>
                        <div className="bg-white rounded-xl shadow-sm p-4">
                            <div className="text-sm text-gray-500">Kopējie darbinieki</div>
                            <div className="text-2xl font-bold text-gray-900">
                                {formatNumber(locations.reduce((sum, t) => sum + (t.total_employees || 0), 0))}
                            </div>
                        </div>
                        <div className="bg-white rounded-xl shadow-sm p-4">
                            <div className="text-sm text-gray-500">Kopējie uzņēmumi</div>
                            <div className="text-2xl font-bold text-gray-900">
                                {formatNumber(locations.reduce((sum, t) => sum + (t.company_count || 0), 0))}
                            </div>
                        </div>
                        <div className="bg-white rounded-xl shadow-sm p-4">
                            <div className="text-sm text-gray-500">Vid. apgrozījums/uzn.</div>
                            <div className="text-2xl font-bold text-gray-900">
                                {formatCurrency(
                                    locations.reduce((sum, t) => sum + (t.total_revenue || 0), 0) /
                                    locations.reduce((sum, t) => sum + (t.company_count || 0), 0)
                                )}
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
                                            {locationType === "cities" ? "Pilsēta" : "Novads"}
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
                                            onClick={() => handleSort("total_profit")}
                                        >
                                            Peļņa <SortIcon column="total_profit" />
                                        </th>
                                        <th
                                            className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                            onClick={() => handleSort("company_count")}
                                        >
                                            Uzņēmumi <SortIcon column="company_count" />
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {sortedLocations.map((location, index) => (
                                        <tr
                                            key={location.name}
                                            className="hover:bg-gray-50 transition-colors"
                                        >
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className="font-medium text-gray-900">
                                                    {location.name}
                                                </span>
                                                <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${locationType === "cities"
                                                        ? "bg-purple-100 text-purple-700"
                                                        : "bg-blue-100 text-blue-700"
                                                    }`}>
                                                    {locationType === "cities" ? "Pilsēta" : "Novads"}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-right whitespace-nowrap font-medium">
                                                {formatCurrency(location.total_revenue)}
                                            </td>
                                            <td className="px-6 py-4 text-right whitespace-nowrap">
                                                {formatNumber(location.total_employees)}
                                            </td>
                                            <td className="px-6 py-4 text-right whitespace-nowrap">
                                                {formatCurrency(location.total_profit)}
                                            </td>
                                            <td className="px-6 py-4 text-right whitespace-nowrap">
                                                {formatNumber(location.company_count)}
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
