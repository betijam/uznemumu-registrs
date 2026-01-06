"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";

interface PersonHighlight {
    person_hash: string;
    full_name: string;
    value: number;
    label: string;
    subtitle: string;
    main_company: string | null;
    primary_nace: string | null;
}

interface PersonRanking {
    rank: number;
    person_hash: string;
    full_name: string;
    value: number;
    main_company: string | null;
    primary_nace: string | null;
    active_companies: number;
}

const formatValue = (value: number, type: "money" | "count") => {
    if (type === "count") return value.toLocaleString();
    if (value >= 1000000000) return `€${(value / 1000000000).toFixed(1)} Md`;
    if (value >= 1000000) return `€${(value / 1000000).toFixed(1)} M`;
    if (value >= 1000) return `€${(value / 1000).toFixed(0)} K`;
    return `€${value.toFixed(0)}`;
};

const getInitials = (name: string) => {
    return name.split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();
};

const CARD_COLORS = [
    { bg: "bg-gradient-to-br from-emerald-500 to-teal-600", text: "text-white" },
    { bg: "bg-gradient-to-br from-blue-500 to-indigo-600", text: "text-white" },
    { bg: "bg-gradient-to-br from-orange-500 to-red-600", text: "text-white" },
];

export default function PersonasPage() {
    const [highlights, setHighlights] = useState<any>(null);
    const [wealthRankings, setWealthRankings] = useState<PersonRanking[]>([]);
    const [activeRankings, setActiveRankings] = useState<PersonRanking[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        Promise.all([
            fetch("/api/analytics/people/highlights").then(r => r.json()),
            fetch("/api/analytics/people/rankings?type=wealth&limit=10").then(r => r.json()),
            fetch("/api/analytics/people/rankings?type=active&limit=10").then(r => r.json()),
        ]).then(([h, w, a]) => {
            setHighlights(h);
            setWealthRankings(w);
            setActiveRankings(a);
            setLoading(false);
        }).catch(err => {
            console.error("Failed to load data:", err);
            setLoading(false);
        });
    }, []);

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50">
                <Navbar />
                <main className="max-w-7xl mx-auto px-4 py-12">
                    <div className="animate-pulse">
                        <div className="h-10 bg-gray-200 rounded w-1/3 mb-8" />
                        <div className="grid md:grid-cols-3 gap-6 mb-12">
                            {[1, 2, 3].map(i => (
                                <div key={i} className="h-48 bg-gray-200 rounded-2xl" />
                            ))}
                        </div>
                    </div>
                </main>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <Navbar />

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Hero */}
                <div className="text-center mb-12">
                    <h1 className="text-4xl font-bold text-gray-900 mb-3">
                        Latvijas Biznesa Elite
                    </h1>
                    <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                        Izpēti patiesos labuma guvējus, sērijveida uzņēmējus un ietekmīgākās personas
                    </p>
                </div>

                {/* Elite Grid - Top 3 Cards */}
                {highlights && (
                    <div className="grid md:grid-cols-3 gap-6 mb-12">
                        {[highlights.top_wealth, highlights.top_active, highlights.top_manager].map((person, idx) => (
                            person && (
                                <div key={idx} className={`${CARD_COLORS[idx].bg} rounded-2xl p-6 shadow-lg ${CARD_COLORS[idx].text}`}>
                                    <div className="flex items-start gap-4">
                                        <div className="w-14 h-14 rounded-full bg-white/20 flex items-center justify-center text-xl font-bold">
                                            {getInitials(person.full_name)}
                                        </div>
                                        <div className="flex-1">
                                            <div className="text-xs uppercase tracking-wide opacity-80">
                                                {person.label}
                                            </div>
                                            <Link
                                                href={`/person/${person.person_hash}`}
                                                className="text-xl font-bold hover:underline"
                                            >
                                                {person.full_name}
                                            </Link>
                                        </div>
                                    </div>
                                    <div className="mt-6">
                                        <div className="text-4xl font-bold">
                                            {idx === 1
                                                ? person.value.toLocaleString()
                                                : formatValue(person.value, "money")}
                                        </div>
                                        <div className="text-sm opacity-80 mt-1">
                                            {person.subtitle}
                                        </div>
                                    </div>
                                    <div className="mt-4 text-sm opacity-80">
                                        <span>Nozare: {person.primary_nace}</span>
                                        {person.main_company && (
                                            <span className="block mt-1">• {person.main_company}</span>
                                        )}
                                    </div>
                                </div>
                            )
                        ))}
                    </div>
                )}

                {/* Rankings Tables */}
                <div className="grid lg:grid-cols-2 gap-8">
                    {/* Wealth Rankings */}
                    <div className="bg-white rounded-xl shadow-sm overflow-hidden">
                        <div className="px-6 py-4 border-b flex items-center justify-between">
                            <h2 className="font-semibold text-gray-900 flex items-center gap-2">
                                💰 Top 100 Īpašnieki (pēc Kapitāla)
                            </h2>
                            <Link href="/personas/wealth" className="text-primary text-sm hover:underline">
                                Skatīt visus →
                            </Link>
                        </div>
                        <div className="divide-y">
                            {wealthRankings.map((person) => (
                                <div key={person.person_hash} className="px-6 py-3 flex items-center gap-4 hover:bg-gray-50">
                                    <span className="w-8 text-center font-semibold text-gray-500">
                                        {person.rank}
                                    </span>
                                    <div className="flex-1 min-w-0">
                                        <Link
                                            href={`/person/${person.person_hash}`}
                                            className="font-medium text-gray-900 hover:text-primary truncate block"
                                        >
                                            {person.full_name}
                                        </Link>
                                        <div className="text-xs text-gray-500 truncate">
                                            {person.main_company || person.primary_nace}
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <div className="font-semibold text-gray-900">
                                            {formatValue(person.value, "money")}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Activity Rankings */}
                    <div className="bg-white rounded-xl shadow-sm overflow-hidden">
                        <div className="px-6 py-4 border-b flex items-center justify-between">
                            <h2 className="font-semibold text-gray-900 flex items-center gap-2">
                                ⚡ Aktīvākie (Sērijveida uzņēmēji)
                            </h2>
                            <Link href="/personas/active" className="text-primary text-sm hover:underline">
                                Skatīt visus →
                            </Link>
                        </div>
                        <div className="divide-y">
                            {activeRankings.map((person) => (
                                <div key={person.person_hash} className="px-6 py-3 flex items-center gap-4 hover:bg-gray-50">
                                    <span className="w-8 text-center font-semibold text-gray-500">
                                        {person.rank}
                                    </span>
                                    <div className="flex-1 min-w-0">
                                        <Link
                                            href={`/person/${person.person_hash}`}
                                            className="font-medium text-gray-900 hover:text-primary truncate block"
                                        >
                                            {person.full_name}
                                        </Link>
                                        <div className="text-xs text-gray-500 truncate">
                                            {person.main_company || person.primary_nace}
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <div className="font-semibold text-gray-900">
                                            {person.active_companies}
                                        </div>
                                        <div className="text-xs text-gray-500">uzņēmumi</div>
                                    </div>
                                    <div className="text-xs text-gray-500 hidden md:block w-24 truncate">
                                        {person.primary_nace}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
