"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import debounce from "lodash.debounce";

interface Company {
    regcode: number;
    name: string;
    status?: string;
}

interface MVKData {
    scenario: {
        company_type: "AUTONOMOUS" | "PARTNER" | "LINKED";
        has_partners: boolean;
        has_linked: boolean;
        has_consolidation: boolean;
        required_sections: string[];
    };
    identification: {
        name: string;
        address: string;
        regcode: string;
        authorized_person: string | null;
        authorized_position: string | null;
    };
    own_financials: {
        employees: number | null;
        turnover: number | null;
        balance: number | null;
    };
    section_a: {
        partners: any[];
        totals: { employees: number; turnover: number; balance: number };
    };
    section_b: {
        type: "B1" | "B2";
        consolidated: { employees: number; turnover: number; balance: number } | null;
        entities: any[];
    };
    summary_table: {
        row_2_1: { employees: number | null; turnover: number | null; balance: number | null };
        row_2_2: { employees: number; turnover: number; balance: number };
        row_2_3: { employees: number; turnover: number; balance: number };
        total: { employees: number; turnover: number; balance: number };
    };
    year: number;
}

// Format currency helper
function formatCurrency(value: number | null | undefined): string {
    if (value === null || value === undefined) return "—";
    return new Intl.NumberFormat("lv-LV", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(value);
}

// Format number helper
function formatNumber(value: number | null | undefined): string {
    if (value === null || value === undefined) return "—";
    return new Intl.NumberFormat("lv-LV").format(value);
}

export default function MVKDeclarationPage() {
    const [searchQuery, setSearchQuery] = useState("");
    const [suggestions, setSuggestions] = useState<Company[]>([]);
    const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
    const [mvkData, setMvkData] = useState<MVKData | null>(null);
    const [loading, setLoading] = useState(false);
    const [showDropdown, setShowDropdown] = useState(false);
    const [copySuccess, setCopySuccess] = useState<string | null>(null);

    // Debounced search
    const searchCompanies = useCallback(
        debounce(async (query: string) => {
            if (query.length < 2) {
                setSuggestions([]);
                return;
            }
            try {
                const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                const data = await res.json();
                setSuggestions(data.slice(0, 8));
                setShowDropdown(true);
            } catch (e) {
                console.error("Search failed:", e);
            }
        }, 300),
        []
    );

    useEffect(() => {
        searchCompanies(searchQuery);
    }, [searchQuery, searchCompanies]);

    // Load MVK data when company selected
    const loadMVKData = async (regcode: number) => {
        setLoading(true);
        try {
            const res = await fetch(`/api/mvk-declaration/${regcode}`);
            if (!res.ok) throw new Error("Failed to load MVK data");
            const data = await res.json();
            setMvkData(data);
        } catch (e) {
            console.error("MVK load failed:", e);
            setMvkData(null);
        } finally {
            setLoading(false);
        }
    };

    const handleSelectCompany = (company: Company) => {
        setSelectedCompany(company);
        setSearchQuery(company.name);
        setShowDropdown(false);
        loadMVKData(company.regcode);
    };

    // Copy to clipboard
    const copyToClipboard = async (text: string, label: string) => {
        try {
            await navigator.clipboard.writeText(text);
            setCopySuccess(label);
            setTimeout(() => setCopySuccess(null), 2000);
        } catch (e) {
            console.error("Copy failed:", e);
        }
    };

    // Generate identification text
    const getIdentificationText = () => {
        if (!mvkData) return "";
        const { identification } = mvkData;
        return `Komercsabiedrības nosaukums: ${identification.name}
Juridiskā adrese: ${identification.address}
Reģistrācijas numurs: ${identification.regcode}
Paraksttiesīgā persona: ${identification.authorized_person || "—"} (${identification.authorized_position || "—"})`;
    };

    // Generate summary table text
    const getSummaryTableText = () => {
        if (!mvkData) return "";
        const { summary_table } = mvkData;
        return `2.1. Pašas komercsabiedrības dati\t${formatNumber(summary_table.row_2_1.employees)}\t${formatCurrency(summary_table.row_2_1.turnover)}\t${formatCurrency(summary_table.row_2_1.balance)}
2.2. Partneruzņēmumu dati (proporcionāli)\t${formatNumber(summary_table.row_2_2.employees)}\t${formatCurrency(summary_table.row_2_2.turnover)}\t${formatCurrency(summary_table.row_2_2.balance)}
2.3. Saistīto uzņēmumu dati (100%)\t${formatNumber(summary_table.row_2_3.employees)}\t${formatCurrency(summary_table.row_2_3.turnover)}\t${formatCurrency(summary_table.row_2_3.balance)}
KOPĀ\t${formatNumber(summary_table.total.employees)}\t${formatCurrency(summary_table.total.turnover)}\t${formatCurrency(summary_table.total.balance)}`;
    };

    // Status badge component
    const StatusBadge = ({ type }: { type: string }) => {
        const config = {
            AUTONOMOUS: { color: "bg-green-100 text-green-800 border-green-300", label: "🟢 Autonoms" },
            PARTNER: { color: "bg-yellow-100 text-yellow-800 border-yellow-300", label: "🟡 Partneruzņēmumi" },
            LINKED: { color: "bg-red-100 text-red-800 border-red-300", label: "🔴 Saistīti uzņēmumi" },
        }[type] || { color: "bg-gray-100 text-gray-800", label: type };

        return (
            <span className={`px-3 py-1 rounded-full text-sm font-medium border ${config.color}`}>
                {config.label}
            </span>
        );
    };

    return (
        <main className="min-h-screen bg-gray-50">
            <Navbar />

            {/* Hero Section */}
            <div className="bg-gradient-to-br from-primary via-primary-dark to-accent py-16">
                <div className="max-w-4xl mx-auto px-4 text-center">
                    <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">
                        Saistīto Subjektu Lapa
                    </h1>
                    <p className="text-gray-200 text-lg mb-8">
                        Šī lapa palīdz sagatavot MVK/MVU deklarācijas pielikumus. Atlasiet uzņēmumu,
                        un sistēma automātiski parādīs tikai tās sadaļas, kuras jums jāaizpilda.
                    </p>

                    {/* Search Input */}
                    <div className="relative max-w-2xl mx-auto">
                        <div className="relative">
                            <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                onFocus={() => suggestions.length > 0 && setShowDropdown(true)}
                                placeholder="Ievadiet uzņēmuma nosaukumu vai reģ. numuru"
                                className="w-full pl-12 pr-4 py-4 rounded-xl text-gray-900 border-0 focus:ring-2 focus:ring-accent shadow-lg"
                            />
                        </div>

                        {/* Dropdown */}
                        {showDropdown && suggestions.length > 0 && (
                            <div className="absolute w-full mt-2 bg-white rounded-xl shadow-xl z-50 overflow-hidden">
                                {suggestions.map((company) => (
                                    <button
                                        key={company.regcode}
                                        onClick={() => handleSelectCompany(company)}
                                        className="w-full px-4 py-3 text-left hover:bg-gray-50 flex items-center justify-between border-b last:border-0"
                                    >
                                        <div>
                                            <span className="font-medium text-gray-900">{company.name}</span>
                                            <span className="text-sm text-gray-500 ml-2">({company.regcode})</span>
                                        </div>
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="max-w-5xl mx-auto px-4 py-8">
                {loading && (
                    <div className="flex justify-center py-12">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                    </div>
                )}

                {mvkData && !loading && (
                    <div className="space-y-6">
                        {/* Scenario Summary */}
                        <div className="bg-white rounded-xl shadow-lg p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-xl font-bold text-gray-900">🧠 MVK Scenārija Kopsavilkums</h2>
                                <StatusBadge type={mvkData.scenario.company_type} />
                            </div>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div className="bg-gray-50 rounded-lg p-4">
                                    <p className="text-sm text-gray-500">Uzņēmuma tips</p>
                                    <p className="font-semibold">{mvkData.scenario.company_type}</p>
                                </div>
                                <div className="bg-gray-50 rounded-lg p-4">
                                    <p className="text-sm text-gray-500">Partneruzņēmumi</p>
                                    <p className="font-semibold">{mvkData.scenario.has_partners ? "✅ Jā" : "❌ Nē"}</p>
                                </div>
                                <div className="bg-gray-50 rounded-lg p-4">
                                    <p className="text-sm text-gray-500">Saistītie uzņēmumi</p>
                                    <p className="font-semibold">{mvkData.scenario.has_linked ? "✅ Jā" : "❌ Nē"}</p>
                                </div>
                                <div className="bg-gray-50 rounded-lg p-4">
                                    <p className="text-sm text-gray-500">Aizpildāmās sadaļas</p>
                                    <p className="font-semibold">{mvkData.scenario.required_sections.length > 0 ? mvkData.scenario.required_sections.join(", ") : "Nav (Autonoms)"}</p>
                                </div>
                            </div>
                        </div>

                        {/* Section 0: Identification */}
                        <div className="bg-white rounded-xl shadow-lg p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-xl font-bold text-gray-900">📋 0. Sadaļa – Identifikācija</h2>
                                <button
                                    onClick={() => copyToClipboard(getIdentificationText(), "identification")}
                                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${copySuccess === "identification"
                                        ? "bg-green-100 text-green-800"
                                        : "bg-gray-100 hover:bg-gray-200 text-gray-700"
                                        }`}
                                >
                                    {copySuccess === "identification" ? "✓ Nokopēts!" : "📋 Kopēt"}
                                </button>
                            </div>
                            <div className="bg-gray-50 rounded-lg p-4 font-mono text-sm whitespace-pre-line">
                                {getIdentificationText()}
                            </div>
                        </div>

                        {/* Section 1: Autonomous (if applicable) */}
                        {mvkData.scenario.company_type === "AUTONOMOUS" && (
                            <div className="bg-green-50 border border-green-200 rounded-xl p-6">
                                <h2 className="text-xl font-bold text-green-800 mb-2">✅ 1. Sadaļa – Autonoms Uzņēmums</h2>
                                <p className="text-green-700 mb-4">
                                    Šim uzņēmumam nav jāaizpilda deklarācijas pielikumi (A/B sadaļa).
                                </p>
                                <div className="grid grid-cols-3 gap-4">
                                    <div className="bg-white rounded-lg p-4 text-center">
                                        <p className="text-sm text-gray-500">Darbinieki</p>
                                        <p className="text-2xl font-bold text-gray-900">{formatNumber(mvkData.own_financials.employees)}</p>
                                    </div>
                                    <div className="bg-white rounded-lg p-4 text-center">
                                        <p className="text-sm text-gray-500">Apgrozījums</p>
                                        <p className="text-2xl font-bold text-gray-900">{formatCurrency(mvkData.own_financials.turnover)}</p>
                                    </div>
                                    <div className="bg-white rounded-lg p-4 text-center">
                                        <p className="text-sm text-gray-500">Bilance</p>
                                        <p className="text-2xl font-bold text-gray-900">{formatCurrency(mvkData.own_financials.balance)}</p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Section A: Partners (if applicable) */}
                        {mvkData.scenario.has_partners && (
                            <div className="bg-white rounded-xl shadow-lg p-6">
                                <div className="flex items-center justify-between mb-4">
                                    <h2 className="text-xl font-bold text-gray-900">📊 A Sadaļa – Partneruzņēmumi (25-50%)</h2>
                                    <button
                                        onClick={() => {
                                            const text = mvkData.section_a.partners
                                                .map((p, i) => `${i + 1}. ${p.name}\t${formatNumber(p.employees)}\t${formatCurrency(p.turnover)}\t${formatCurrency(p.balance)}\t${p.ownership_percent}%`)
                                                .join("\n");
                                            copyToClipboard(text, "section_a");
                                        }}
                                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${copySuccess === "section_a"
                                            ? "bg-green-100 text-green-800"
                                            : "bg-gray-100 hover:bg-gray-200 text-gray-700"
                                            }`}
                                    >
                                        {copySuccess === "section_a" ? "✓ Nokopēts!" : "📋 Kopēt A tabulu"}
                                    </button>
                                </div>

                                <table className="w-full text-sm">
                                    <thead className="bg-gray-100">
                                        <tr>
                                            <th className="px-4 py-3 text-left">Nr.</th>
                                            <th className="px-4 py-3 text-left">Partnerkomercsabiedrība</th>
                                            <th className="px-4 py-3 text-right">Darbinieki</th>
                                            <th className="px-4 py-3 text-right">Apgrozījums</th>
                                            <th className="px-4 py-3 text-right">Bilance</th>
                                            <th className="px-4 py-3 text-right">%</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {mvkData.section_a.partners.map((partner, idx) => (
                                            <tr key={idx} className="border-b hover:bg-gray-50">
                                                <td className="px-4 py-3">{idx + 1}</td>
                                                <td className="px-4 py-3 font-medium">
                                                    {partner.regcode ? (
                                                        <Link href={`/company/${partner.regcode}`} className="text-primary hover:underline">
                                                            {partner.name}
                                                        </Link>
                                                    ) : (
                                                        partner.name
                                                    )}
                                                    {partner.entity_type === "physical_person" && (
                                                        <span className="ml-2 text-xs bg-gray-200 px-2 py-0.5 rounded">Fiziska persona</span>
                                                    )}
                                                </td>
                                                <td className="px-4 py-3 text-right">{formatNumber(partner.employees)}</td>
                                                <td className="px-4 py-3 text-right">{formatCurrency(partner.turnover)}</td>
                                                <td className="px-4 py-3 text-right">{formatCurrency(partner.balance)}</td>
                                                <td className="px-4 py-3 text-right font-medium">{partner.ownership_percent}%</td>
                                            </tr>
                                        ))}
                                        <tr className="bg-yellow-50 font-semibold">
                                            <td className="px-4 py-3" colSpan={2}>KOPĀ (proporcionāli)</td>
                                            <td className="px-4 py-3 text-right">{formatNumber(mvkData.section_a.totals.employees)}</td>
                                            <td className="px-4 py-3 text-right">{formatCurrency(mvkData.section_a.totals.turnover)}</td>
                                            <td className="px-4 py-3 text-right">{formatCurrency(mvkData.section_a.totals.balance)}</td>
                                            <td className="px-4 py-3"></td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        )}

                        {/* Section B: Linked (if applicable) */}
                        {mvkData.scenario.has_linked && (
                            <div className="bg-white rounded-xl shadow-lg p-6">
                                <div className="flex items-center justify-between mb-4">
                                    <h2 className="text-xl font-bold text-gray-900">
                                        🔗 B Sadaļa – Saistītie Uzņēmumi (&gt;50%)
                                        <span className="ml-2 text-sm font-normal text-gray-500">
                                            Tipa {mvkData.section_b.type === "B1" ? "B(1) - Konsolidēts" : "B(2) - Nekonsolidēts"}
                                        </span>
                                    </h2>
                                    <button
                                        onClick={() => {
                                            const text = mvkData.section_b.entities
                                                .map((e, i) => `${i + 1}. ${e.name}\t${formatNumber(e.employees)}\t${formatCurrency(e.turnover)}\t${formatCurrency(e.balance)}\t${e.ownership_percent}%`)
                                                .join("\n");
                                            copyToClipboard(text, "section_b");
                                        }}
                                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${copySuccess === "section_b"
                                            ? "bg-green-100 text-green-800"
                                            : "bg-gray-100 hover:bg-gray-200 text-gray-700"
                                            }`}
                                    >
                                        {copySuccess === "section_b" ? "✓ Nokopēts!" : "📋 Kopēt B tabulu"}
                                    </button>
                                </div>

                                <table className="w-full text-sm">
                                    <thead className="bg-gray-100">
                                        <tr>
                                            <th className="px-4 py-3 text-left">Nr.</th>
                                            <th className="px-4 py-3 text-left">Saistītā komercsabiedrība</th>
                                            <th className="px-4 py-3 text-right">Darbinieki</th>
                                            <th className="px-4 py-3 text-right">Apgrozījums</th>
                                            <th className="px-4 py-3 text-right">Bilance</th>
                                            <th className="px-4 py-3 text-right">%</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {mvkData.section_b.entities.map((entity, idx) => (
                                            <tr key={idx} className="border-b hover:bg-gray-50">
                                                <td className="px-4 py-3">{idx + 1}</td>
                                                <td className="px-4 py-3 font-medium">
                                                    {entity.regcode ? (
                                                        <Link href={`/company/${entity.regcode}`} className="text-primary hover:underline">
                                                            {entity.name}
                                                        </Link>
                                                    ) : (
                                                        entity.name
                                                    )}
                                                    <span className="ml-2 text-xs text-gray-500">
                                                        {entity.relation === "owner" ? "👆 Īpašnieks" : "👇 Meitassab."}
                                                    </span>
                                                </td>
                                                <td className="px-4 py-3 text-right">{formatNumber(entity.employees)}</td>
                                                <td className="px-4 py-3 text-right">{formatCurrency(entity.turnover)}</td>
                                                <td className="px-4 py-3 text-right">{formatCurrency(entity.balance)}</td>
                                                <td className="px-4 py-3 text-right font-medium">{entity.ownership_percent}%</td>
                                            </tr>
                                        ))}
                                        <tr className="bg-red-50 font-semibold">
                                            <td className="px-4 py-3" colSpan={2}>KOPĀ (100%)</td>
                                            <td className="px-4 py-3 text-right">{formatNumber(mvkData.summary_table.row_2_3.employees)}</td>
                                            <td className="px-4 py-3 text-right">{formatCurrency(mvkData.summary_table.row_2_3.turnover)}</td>
                                            <td className="px-4 py-3 text-right">{formatCurrency(mvkData.summary_table.row_2_3.balance)}</td>
                                            <td className="px-4 py-3"></td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        )}

                        {/* Summary Table 2.1-2.3 */}
                        <div className="bg-white rounded-xl shadow-lg p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-xl font-bold text-gray-900">📈 Gala Kopsavilkums (2.1–2.3)</h2>
                                <button
                                    onClick={() => copyToClipboard(getSummaryTableText(), "summary")}
                                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${copySuccess === "summary"
                                        ? "bg-green-100 text-green-800"
                                        : "bg-primary text-white hover:bg-primary-dark"
                                        }`}
                                >
                                    {copySuccess === "summary" ? "✓ Nokopēts!" : "📋 Kopēt deklarācijas 3. sadaļai"}
                                </button>
                            </div>

                            <table className="w-full text-sm">
                                <thead className="bg-gray-100">
                                    <tr>
                                        <th className="px-4 py-3 text-left">Rinda</th>
                                        <th className="px-4 py-3 text-left">Apraksts</th>
                                        <th className="px-4 py-3 text-right">Darbinieki</th>
                                        <th className="px-4 py-3 text-right">Apgrozījums</th>
                                        <th className="px-4 py-3 text-right">Bilance</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr className="border-b">
                                        <td className="px-4 py-3 font-medium">2.1</td>
                                        <td className="px-4 py-3">Pašas komercsabiedrības dati</td>
                                        <td className="px-4 py-3 text-right">{formatNumber(mvkData.summary_table.row_2_1.employees)}</td>
                                        <td className="px-4 py-3 text-right">{formatCurrency(mvkData.summary_table.row_2_1.turnover)}</td>
                                        <td className="px-4 py-3 text-right">{formatCurrency(mvkData.summary_table.row_2_1.balance)}</td>
                                    </tr>
                                    <tr className="border-b bg-yellow-50">
                                        <td className="px-4 py-3 font-medium">2.2</td>
                                        <td className="px-4 py-3">Partneruzņēmumu dati (proporcionāli)</td>
                                        <td className="px-4 py-3 text-right">{formatNumber(mvkData.summary_table.row_2_2.employees)}</td>
                                        <td className="px-4 py-3 text-right">{formatCurrency(mvkData.summary_table.row_2_2.turnover)}</td>
                                        <td className="px-4 py-3 text-right">{formatCurrency(mvkData.summary_table.row_2_2.balance)}</td>
                                    </tr>
                                    <tr className="border-b bg-red-50">
                                        <td className="px-4 py-3 font-medium">2.3</td>
                                        <td className="px-4 py-3">Saistīto uzņēmumu dati (100%)</td>
                                        <td className="px-4 py-3 text-right">{formatNumber(mvkData.summary_table.row_2_3.employees)}</td>
                                        <td className="px-4 py-3 text-right">{formatCurrency(mvkData.summary_table.row_2_3.turnover)}</td>
                                        <td className="px-4 py-3 text-right">{formatCurrency(mvkData.summary_table.row_2_3.balance)}</td>
                                    </tr>
                                    <tr className="bg-primary text-white font-bold">
                                        <td className="px-4 py-3" colSpan={2}>KOPĀ</td>
                                        <td className="px-4 py-3 text-right">{formatNumber(mvkData.summary_table.total.employees)}</td>
                                        <td className="px-4 py-3 text-right">{formatCurrency(mvkData.summary_table.total.turnover)}</td>
                                        <td className="px-4 py-3 text-right">{formatCurrency(mvkData.summary_table.total.balance)}</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>

                        {/* MVK Size Classification */}
                        <div className="bg-gradient-to-r from-primary to-primary-dark rounded-xl shadow-lg p-6 text-white">
                            <h2 className="text-xl font-bold mb-4">🏢 MVK Klasifikācijas Rezultāts ({mvkData.year}. gads)</h2>
                            <div className="grid grid-cols-3 gap-4 mb-4">
                                <div className="text-center">
                                    <p className="text-3xl font-bold">{formatNumber(mvkData.summary_table.total.employees)}</p>
                                    <p className="text-sm opacity-80">Darbinieki</p>
                                </div>
                                <div className="text-center">
                                    <p className="text-3xl font-bold">{formatCurrency(mvkData.summary_table.total.turnover)}</p>
                                    <p className="text-sm opacity-80">Apgrozījums</p>
                                </div>
                                <div className="text-center">
                                    <p className="text-3xl font-bold">{formatCurrency(mvkData.summary_table.total.balance)}</p>
                                    <p className="text-sm opacity-80">Bilances kopsumma</p>
                                </div>
                            </div>
                            <p className="text-sm opacity-80 text-center">
                                Šie dati ir jāizmanto MVK/MVU statusa noteikšanai saskaņā ar ES regulu Nr. 651/2014
                            </p>
                        </div>
                    </div>
                )}

                {/* Empty State */}
                {!mvkData && !loading && (
                    <div className="text-center py-16">
                        <div className="text-6xl mb-4">🔍</div>
                        <h2 className="text-2xl font-bold text-gray-700 mb-2">Izvēlieties uzņēmumu</h2>
                        <p className="text-gray-500">
                            Ievadiet uzņēmuma nosaukumu vai reģistrācijas numuru meklēšanas laukā
                        </p>
                    </div>
                )}
            </div>
        </main>
    );
}
