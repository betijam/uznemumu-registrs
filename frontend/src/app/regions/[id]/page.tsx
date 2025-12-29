"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import Navbar from "@/components/Navbar";

interface TerritoryDetails {
    id: number;
    code: string;
    name: string;
    type: string;
    level: number;
    year: number | null;
    total_revenue: number | null;
    total_profit: number | null;
    total_employees: number | null;
    avg_salary: number | null;
    company_count: number | null;
    revenue_growth_yoy: number | null;
    employee_growth_yoy: number | null;
    salary_growth_yoy: number | null;
    history: Array<{
        year: number;
        total_revenue: number | null;
        total_employees: number | null;
        avg_salary: number | null;
        company_count: number | null;
    }>;
}

interface Industry {
    industry_code: string;
    industry_name: string | null;
    total_revenue: number | null;
    total_employees: number | null;
    company_count: number | null;
    revenue_share: number | null;
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

const formatGrowth = (num: number | null | undefined) => {
    if (num === null || num === undefined) return "-";
    const sign = num > 0 ? "+" : "";
    return `${sign}${num.toFixed(1)}%`;
};

export default function RegionDetailsPage() {
    const params = useParams();
    const id = params.id as string;

    const [territory, setTerritory] = useState<TerritoryDetails | null>(null);
    const [industries, setIndustries] = useState<Industry[]>([]);
    const [topCompanies, setTopCompanies] = useState<TopCompany[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!id) return;

        setLoading(true);

        Promise.all([
            fetch(`/api/regions/${id}`).then(r => r.json()),
            fetch(`/api/regions/${id}/industries`).then(r => r.json()),
            fetch(`/api/regions/${id}/top-companies`).then(r => r.json())
        ])
            .then(([details, industriesData, companiesData]) => {
                setTerritory(details);
                setIndustries(industriesData);
                setTopCompanies(companiesData);
                setLoading(false);
            })
            .catch(err => {
                setError("Neizdevās ielādēt reģiona datus");
                setLoading(false);
            });
    }, [id]);

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50">
                <Navbar />
                <main className="max-w-7xl mx-auto px-4 py-12 text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
                    <p className="mt-4 text-gray-500">Ielādē reģiona datus...</p>
                </main>
            </div>
        );
    }

    if (error || !territory) {
        return (
            <div className="min-h-screen bg-gray-50">
                <Navbar />
                <main className="max-w-7xl mx-auto px-4 py-12 text-center">
                    <p className="text-red-600">{error || "Reģions nav atrasts"}</p>
                    <Link href="/regions" className="text-primary hover:underline mt-4 inline-block">
                        ← Atpakaļ uz reģionu sarakstu
                    </Link>
                </main>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <Navbar />

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Breadcrumb */}
                <nav className="mb-4">
                    <Link href="/regions" className="text-primary hover:underline">
                        ← Reģioni
                    </Link>
                </nav>

                {/* Header */}
                <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900">{territory.name}</h1>
                            <span className={`inline-block mt-2 text-sm px-3 py-1 rounded-full ${territory.type === "NOVADS"
                                    ? "bg-blue-100 text-blue-700"
                                    : "bg-purple-100 text-purple-700"
                                }`}>
                                {territory.type === "NOVADS" ? "Novads" :
                                    territory.type === "VALSTSPILSĒTU_PAŠVALDĪBA" ? "Valstspilsēta" : "Pilsēta"}
                            </span>
                        </div>
                        <div className="text-right text-gray-500">
                            <div>Dati par {territory.year} gadu</div>
                        </div>
                    </div>
                </div>

                {/* KPI Cards */}
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
                    <div className="bg-white rounded-xl shadow-sm p-4">
                        <div className="text-sm text-gray-500">Apgrozījums</div>
                        <div className="text-2xl font-bold text-gray-900">
                            {formatCurrency(territory.total_revenue)}
                        </div>
                        {territory.revenue_growth_yoy !== null && (
                            <div className={`text-sm ${territory.revenue_growth_yoy >= 0 ? "text-green-600" : "text-red-600"}`}>
                                {formatGrowth(territory.revenue_growth_yoy)} YoY
                            </div>
                        )}
                    </div>

                    <div className="bg-white rounded-xl shadow-sm p-4">
                        <div className="text-sm text-gray-500">Peļņa</div>
                        <div className="text-2xl font-bold text-gray-900">
                            {formatCurrency(territory.total_profit)}
                        </div>
                    </div>

                    <div className="bg-white rounded-xl shadow-sm p-4">
                        <div className="text-sm text-gray-500">Darbinieki</div>
                        <div className="text-2xl font-bold text-gray-900">
                            {formatNumber(territory.total_employees)}
                        </div>
                        {territory.employee_growth_yoy !== null && (
                            <div className={`text-sm ${territory.employee_growth_yoy >= 0 ? "text-green-600" : "text-red-600"}`}>
                                {formatGrowth(territory.employee_growth_yoy)} YoY
                            </div>
                        )}
                    </div>

                    <div className="bg-white rounded-xl shadow-sm p-4">
                        <div className="text-sm text-gray-500">Vidējā alga</div>
                        <div className="text-2xl font-bold text-gray-900">
                            {territory.avg_salary ? `€${Math.round(territory.avg_salary)}` : "-"}
                        </div>
                        {territory.salary_growth_yoy !== null && (
                            <div className={`text-sm ${territory.salary_growth_yoy >= 0 ? "text-green-600" : "text-red-600"}`}>
                                {formatGrowth(territory.salary_growth_yoy)} YoY
                            </div>
                        )}
                    </div>

                    <div className="bg-white rounded-xl shadow-sm p-4">
                        <div className="text-sm text-gray-500">Uzņēmumi</div>
                        <div className="text-2xl font-bold text-gray-900">
                            {formatNumber(territory.company_count)}
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Industry Breakdown */}
                    <div className="bg-white rounded-xl shadow-sm p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-4">Nozaru struktūra</h2>
                        <div className="space-y-3">
                            {industries.slice(0, 8).map((industry, index) => (
                                <div key={industry.industry_code} className="flex items-center">
                                    <div className="flex-1">
                                        <div className="text-sm font-medium text-gray-900">
                                            {industry.industry_name || industry.industry_code}
                                        </div>
                                        <div className="flex items-center mt-1">
                                            <div
                                                className="h-2 bg-primary rounded-full"
                                                style={{ width: `${Math.min(industry.revenue_share || 0, 100)}%` }}
                                            ></div>
                                        </div>
                                    </div>
                                    <div className="ml-4 text-right">
                                        <div className="text-sm font-bold">{industry.revenue_share?.toFixed(1)}%</div>
                                        <div className="text-xs text-gray-500">{formatCurrency(industry.total_revenue)}</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Top Companies */}
                    <div className="bg-white rounded-xl shadow-sm p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-4">Top uzņēmumi</h2>
                        <div className="space-y-3">
                            {topCompanies.slice(0, 8).map((company, index) => (
                                <Link
                                    key={company.regcode}
                                    href={`/company/${company.regcode}`}
                                    className="flex items-center p-2 -mx-2 rounded-lg hover:bg-gray-50 transition-colors"
                                >
                                    <div className="w-6 h-6 bg-primary/10 text-primary text-sm font-bold rounded-full flex items-center justify-center">
                                        {index + 1}
                                    </div>
                                    <div className="ml-3 flex-1 min-w-0">
                                        <div className="text-sm font-medium text-gray-900 truncate">
                                            {formatCompanyName(company)}
                                        </div>
                                        <div className="text-xs text-gray-500 truncate">
                                            {company.nace_text || "-"}
                                        </div>
                                    </div>
                                    <div className="ml-2 text-right">
                                        <div className="text-sm font-bold">{formatCurrency(company.turnover)}</div>
                                        <div className="text-xs text-gray-500">{formatNumber(company.employees)} darb.</div>
                                    </div>
                                </Link>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Historical Chart Placeholder */}
                {territory.history && territory.history.length > 0 && (
                    <div className="bg-white rounded-xl shadow-sm p-6 mt-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-4">Izaugsmes tendence</h2>
                        <div className="grid grid-cols-5 gap-4">
                            {territory.history.reverse().map((h) => (
                                <div key={h.year} className="text-center">
                                    <div className="text-lg font-bold">{formatCurrency(h.total_revenue)}</div>
                                    <div className="text-sm text-gray-500">{h.year}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}
