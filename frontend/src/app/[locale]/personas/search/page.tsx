"use client";

import { useState, useEffect, useCallback } from "react";
import Navbar from "@/components/Navbar";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { MagnifyingGlassIcon } from "@heroicons/react/24/outline";

// Types
interface PersonResult {
    person_hash: string;
    full_name: string;
    net_worth: number;
    managed_turnover: number;
    active_companies: number;
    main_company: string;
    primary_nace: string;
    region: string;
    roles: string[];
}

interface SearchResponse {
    total: number;
    page: number;
    limit: number;
    items: PersonResult[];
}

// Formatters
const formatMoney = (val: number) => {
    if (val >= 1000000) return `€${(val / 1000000).toFixed(1)}M`;
    if (val >= 1000) return `€${(val / 1000).toFixed(0)}K`;
    return `€${val}`;
};

const REGIONS = ["Rīga", "Pierīga", "Vidzeme", "Kurzeme", "Zemgale", "Latgale"];

export default function AdvancedPersonSearch() {
    const router = useRouter();
    const searchParams = useSearchParams();

    // Filters state
    const [query, setQuery] = useState(searchParams.get("q") || "");
    const [role, setRole] = useState(searchParams.get("role") || "");
    const [region, setRegion] = useState(searchParams.get("region") || "");
    const [sort, setSort] = useState(searchParams.get("sort_by") || "wealth");
    const [minWealth, setMinWealth] = useState(searchParams.get("min_wealth") || "");

    // Data state
    const [data, setData] = useState<SearchResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);

    const fetchData = useCallback(async () => {
        setLoading(true);
        const params = new URLSearchParams({
            page: page.toString(),
            limit: "20",
            sort_by: sort,
        });

        if (query) params.append("q", query);
        if (role) params.append("role", role);
        if (region) params.append("region", region);
        if (minWealth) params.append("min_wealth", minWealth);

        try {
            const res = await fetch(`/api/analytics/people/search?${params.toString()}`);
            const json = await res.json();
            setData(json);
        } catch (err) {
            console.error("Search failed:", err);
        } finally {
            setLoading(false);
        }
    }, [page, sort, query, role, region, minWealth]);

    // Debounce search
    useEffect(() => {
        const timeout = setTimeout(fetchData, 500);
        return () => clearTimeout(timeout);
    }, [fetchData]);

    const handleSort = (key: string) => {
        setSort(key);
        setPage(1);
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            <Navbar />

            <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-8 flex gap-8">
                {/* Sidebar Filters */}
                <aside className="w-64 flex-shrink-0 space-y-8">
                    <div>
                        <h2 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-4">
                            Filtri
                        </h2>

                        {/* Name Search */}
                        <div className="mb-6">
                            <label className="block text-sm font-medium text-gray-700 mb-1">Vārds, Uzvārds</label>
                            <div className="relative">
                                <MagnifyingGlassIcon className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
                                <input
                                    type="text"
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    className="w-full pl-9 pr-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-primary/20 outline-none"
                                    placeholder="Meklēt..."
                                />
                            </div>
                        </div>

                        {/* Role */}
                        <div className="mb-6">
                            <label className="block text-sm font-medium text-gray-700 mb-2">Loma</label>
                            <div className="space-y-2">
                                {[
                                    { id: "", label: "Visas" },
                                    { id: "owner", label: "Īpašnieks (PLG)" },
                                    { id: "officer", label: "Amatpersona" },
                                ].map((r) => (
                                    <label key={r.id} className="flex items-center gap-2 text-sm cursor-pointer">
                                        <input
                                            type="radio"
                                            name="role"
                                            checked={role === r.id}
                                            onChange={() => setRole(r.id)}
                                            className="text-primary focus:ring-primary"
                                        />
                                        {r.label}
                                    </label>
                                ))}
                            </div>
                        </div>

                        {/* Region */}
                        <div className="mb-6">
                            <label className="block text-sm font-medium text-gray-700 mb-2">Reģions</label>
                            <select
                                value={region}
                                onChange={(e) => setRegion(e.target.value)}
                                className="w-full border rounded-lg p-2 text-sm"
                            >
                                <option value="">Visi reģioni</option>
                                {REGIONS.map(r => (
                                    <option key={r} value={r}>{r}</option>
                                ))}
                            </select>
                        </div>

                        {/* Wealth Slider (Simplified as input for now) */}
                        <div className="mb-6">
                            <label className="block text-sm font-medium text-gray-700 mb-2">Min. Kapitāls (€)</label>
                            <input
                                type="number"
                                placeholder="Piem. 100000"
                                value={minWealth}
                                onChange={(e) => setMinWealth(e.target.value)}
                                className="w-full border rounded-lg p-2 text-sm"
                            />
                        </div>
                    </div>
                </aside>

                {/* Main Content */}
                <div className="flex-1">
                    <div className="flex items-center justify-between mb-6">
                        <h1 className="text-2xl font-bold text-gray-900">
                            Personu Meklētājs
                            {data && <span className="text-gray-400 text-lg font-normal ml-3">{data.total} rezultāti</span>}
                        </h1>

                        {/* Sort Dropdown (Mobile) or Tabs */}
                        <div className="flex gap-2 text-sm">
                            <button
                                onClick={() => handleSort("wealth")}
                                className={`px-4 py-2 rounded-full border ${sort === "wealth" ? "bg-primary text-white border-primary" : "bg-white hover:bg-gray-50"}`}
                            >
                                Bagātākie
                            </button>
                            <button
                                onClick={() => handleSort("active")}
                                className={`px-4 py-2 rounded-full border ${sort === "active" ? "bg-primary text-white border-primary" : "bg-white hover:bg-gray-50"}`}
                            >
                                Aktīvākie
                            </button>
                            <button
                                onClick={() => handleSort("turnover")}
                                className={`px-4 py-2 rounded-full border ${sort === "turnover" ? "bg-primary text-white border-primary" : "bg-white hover:bg-gray-50"}`}
                            >
                                Apgrozījums
                            </button>
                        </div>
                    </div>

                    {/* Table */}
                    <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-sm">
                                <thead className="bg-gray-50 text-gray-500 font-medium border-b">
                                    <tr>
                                        <th className="px-6 py-4">Persona</th>
                                        <th className="px-6 py-4">Statuss</th>
                                        <th className="px-6 py-4 text-right cursor-pointer hover:text-gray-700" onClick={() => handleSort("wealth")}>
                                            Kapitāla vērtība ↓
                                        </th>
                                        <th className="px-6 py-4 text-right cursor-pointer hover:text-gray-700" onClick={() => handleSort("turnover")}>
                                            Vadītais apgroz.
                                        </th>
                                        <th className="px-6 py-4">Analītika</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y">
                                    {loading ? (
                                        [...Array(5)].map((_, i) => (
                                            <tr key={i} className="animate-pulse">
                                                <td className="px-6 py-4"><div className="h-5 bg-gray-200 rounded w-40" /></td>
                                                <td className="px-6 py-4"><div className="h-5 bg-gray-200 rounded w-20" /></td>
                                                <td className="px-6 py-4"><div className="h-5 bg-gray-200 rounded w-24 ml-auto" /></td>
                                                <td className="px-6 py-4"><div className="h-5 bg-gray-200 rounded w-24 ml-auto" /></td>
                                                <td className="px-6 py-4"><div className="h-5 bg-gray-200 rounded w-32" /></td>
                                            </tr>
                                        ))
                                    ) : (
                                        data?.items.map((person) => (
                                            <tr key={person.person_hash} className="hover:bg-gray-50 group transition-colors">
                                                <td className="px-6 py-4">
                                                    <Link href={`/person/${person.person_hash}`} className="font-bold text-gray-900 hover:text-primary hover:underline">
                                                        {person.full_name}
                                                    </Link>
                                                    <div className="text-xs text-gray-500 mt-1">
                                                        {person.main_company || "Nav aktīvu uzņēmumu"}
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="flex flex-wrap gap-1">
                                                        {person.roles && person.roles.map((role: string) => (
                                                            <span key={role} className={`px-2 py-0.5 rounded text-xs font-medium border ${role === 'member' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                                                                role === 'officer' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                                                                    'bg-gray-100 text-gray-600'
                                                                }`}>
                                                                {role === 'member' ? 'Īpašnieks' : role === 'officer' ? 'Amatpersona' : role}
                                                            </span>
                                                        ))}
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 text-right font-semibold text-gray-900">
                                                    {person.net_worth > 0 ? formatMoney(person.net_worth) : "-"}
                                                </td>
                                                <td className="px-6 py-4 text-right text-gray-600">
                                                    {person.managed_turnover > 0 ? formatMoney(person.managed_turnover) : "-"}
                                                </td>
                                                <td className="px-6 py-4 text-xs text-gray-500">
                                                    <div>{person.active_companies} aktīvi uzņēmumi</div>
                                                    <div>{person.region || "Nav reģiona"}</div>
                                                    <div className="truncate max-w-[150px]">{person.primary_nace || "Nav nozares"}</div>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>

                        {/* Pagination */}
                        {data && data.total > 20 && (
                            <div className="px-6 py-4 border-t flex items-center justify-between bg-gray-50">
                                <button
                                    onClick={() => setPage(p => Math.max(1, p - 1))}
                                    disabled={page === 1}
                                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border rounded-md hover:bg-gray-50 disabled:opacity-50"
                                >
                                    Iepriekšējā
                                </button>
                                <span className="text-sm text-gray-600">
                                    Lapa {page} no {Math.ceil(data.total / 20)}
                                </span>
                                <button
                                    onClick={() => setPage(p => p + 1)}
                                    disabled={page * 20 >= data.total}
                                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border rounded-md hover:bg-gray-50 disabled:opacity-50"
                                >
                                    Nākamā
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
