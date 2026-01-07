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
        authorized_person_hash?: string | null;
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
    company_size?: string | null;
}

// User confirmation for control criteria
type ConfirmationValue = 'yes' | 'no' | 'unknown';

interface ControlCriteria {
    companyRegcode: number;
    companyName: string;
    naceCode?: string;                     // NACE kods uzņēmumam
    sameMarket?: boolean;                  // Vai tā pati nozare
    needsConfirmation?: boolean;           // Vai prasa apstiprinājumu
    boardControl: ConfirmationValue;       // Tiesības iecelt/atlaist vadības vairākumu
    contractControl: ConfirmationValue;    // Noteicoša ietekme ar līgumu vai statūtiem
    agreementControl: ConfirmationValue;   // Kontrole ar vienošanos ar citiem dalībniekiem
    explanation: string;
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

    // User control criteria confirmations
    const [userConfirmations, setUserConfirmations] = useState<ControlCriteria[]>([]);
    const [showConfirmationWarning, setShowConfirmationWarning] = useState(false);

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

    // Initialize user confirmations when MVK data loads
    const initializeConfirmations = (data: MVKData) => {
        const allEntities: ControlCriteria[] = [];
        const companyNace = (data as any).company_nace || '';

        // Get target company NACE for comparison
        const targetNace = (data as any).company_nace || '';
        const targetNacePrefix = targetNace ? targetNace.substring(0, 2) : '';

        // Helper function to check if same market (first 2 digits match)
        const isSameMarket = (naceCode: string | null | undefined): boolean => {
            if (!targetNacePrefix || !naceCode) return false;
            const otherPrefix = naceCode.substring(0, 2);
            return targetNacePrefix === otherPrefix;
        };

        // Add partners (25-50%)
        data.section_a.partners.forEach((p: any) => {
            if (p.regcode) {
                const pNace = p.nace_code || '';
                const same = isSameMarket(pNace);
                allEntities.push({
                    companyRegcode: p.regcode,
                    companyName: p.name || 'Unknown',
                    naceCode: pNace,
                    sameMarket: same,
                    needsConfirmation: !same && pNace !== '',  // Needs confirmation if different NACE
                    boardControl: 'unknown',
                    contractControl: 'unknown',
                    agreementControl: 'unknown',
                    explanation: ''
                });
            }
        });

        // Add linked entities
        data.section_b.entities.forEach((e: any) => {
            if (e.regcode && !allEntities.find(x => x.companyRegcode === e.regcode)) {
                const eNace = e.nace_code || '';
                const same = e.same_market ?? isSameMarket(eNace);
                allEntities.push({
                    companyRegcode: e.regcode,
                    companyName: e.name || 'Unknown',
                    naceCode: eNace,
                    sameMarket: same,
                    needsConfirmation: e.needs_confirmation ?? (!same && eNace !== ''),
                    boardControl: 'unknown',
                    contractControl: 'unknown',
                    agreementControl: 'unknown',
                    explanation: ''
                });
            }
        });

        // Add needs_confirmation entities (different NACE)
        const needsConf = (data as any).needs_confirmation || [];
        needsConf.forEach((e: any) => {
            if (e.regcode && !allEntities.find(x => x.companyRegcode === e.regcode)) {
                allEntities.push({
                    companyRegcode: e.regcode,
                    companyName: e.name || 'Unknown',
                    naceCode: e.nace_code || '',
                    sameMarket: false,
                    needsConfirmation: true,
                    boardControl: 'unknown',
                    contractControl: 'unknown',
                    agreementControl: 'unknown',
                    explanation: ''
                });
            }
        });

        setUserConfirmations(allEntities);
        setShowConfirmationWarning(allEntities.length > 0);
    };

    // Load MVK data when company selected
    const loadMVKData = async (regcode: number) => {
        setLoading(true);
        try {
            const res = await fetch(`/api/mvk-declaration/${regcode}`);
            if (!res.ok) throw new Error("Failed to load MVK data");
            const data = await res.json();
            setMvkData(data);
            initializeConfirmations(data);
        } catch (e) {
            console.error("MVK load failed:", e);
            setMvkData(null);
            setUserConfirmations([]);
        } finally {
            setLoading(false);
        }
    };

    // Update user confirmation
    const updateConfirmation = (
        regcode: number,
        field: 'boardControl' | 'contractControl' | 'agreementControl' | 'explanation',
        value: ConfirmationValue | string
    ) => {
        setUserConfirmations(prev => prev.map(c =>
            c.companyRegcode === regcode
                ? { ...c, [field]: value }
                : c
        ));
    };

    // Check if any confirmation is "yes" (elevates to LINKED)
    const hasAnyYesConfirmation = (regcode: number): boolean => {
        const conf = userConfirmations.find(c => c.companyRegcode === regcode);
        if (!conf) return false;
        return conf.boardControl === 'yes' || conf.contractControl === 'yes' || conf.agreementControl === 'yes';
    };

    // Check if any confirmation is "unknown" (show warning)
    const hasUnknownConfirmations = (): boolean => {
        return userConfirmations.some(c =>
            c.boardControl === 'unknown' || c.contractControl === 'unknown' || c.agreementControl === 'unknown'
        );
    };

    // Get effective company type (considering user confirmations)
    const getEffectiveCompanyType = (): string => {
        if (!mvkData) return 'AUTONOMOUS';

        // If user confirmed any control criteria, it's LINKED
        const anyYes = userConfirmations.some(c =>
            c.boardControl === 'yes' || c.contractControl === 'yes' || c.agreementControl === 'yes'
        );
        if (anyYes) return 'LINKED';

        return mvkData.scenario.company_type;
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

    // Company size badge
    const SizeBadge = ({ size }: { size: string | null | undefined }) => {
        const config: Record<string, { color: string; icon: string }> = {
            "Mikro": { color: "bg-blue-500", icon: "🔹" },
            "Mazs": { color: "bg-green-500", icon: "🟢" },
            "Vidējs": { color: "bg-yellow-500", icon: "🟡" },
            "Liels": { color: "bg-red-500", icon: "🔴" },
        };
        const c = config[size || ""] || { color: "bg-gray-500", icon: "⚪" };
        return (
            <span className={`${c.color} text-white px-4 py-2 rounded-lg text-lg font-bold shadow-lg`}>
                {c.icon} {size || "Nav datu"} uzņēmums
            </span>
        );
    };

    // Generate HTML table for clipboard (works in Word/Excel)
    const copyTableAsHtml = async (tableId: string, label: string) => {
        const table = document.getElementById(tableId);
        if (!table) return;

        try {
            // Create a blob with HTML content
            const html = table.outerHTML;
            const blob = new Blob([html], { type: 'text/html' });

            await navigator.clipboard.write([
                new ClipboardItem({
                    'text/html': blob,
                    'text/plain': new Blob([table.innerText], { type: 'text/plain' })
                })
            ]);
            setCopySuccess(label);
            setTimeout(() => setCopySuccess(null), 2000);
        } catch (e) {
            // Fallback to text
            await navigator.clipboard.writeText(table.innerText);
            setCopySuccess(label);
            setTimeout(() => setCopySuccess(null), 2000);
        }
    };

    // Download as Word document
    const downloadAsWord = (content: string, filename: string) => {
        const html = `
            <html xmlns:o="urn:schemas-microsoft-com:office:office" 
                  xmlns:w="urn:schemas-microsoft-com:office:word" 
                  xmlns="http://www.w3.org/TR/REC-html40">
            <head><meta charset="utf-8"><title>${filename}</title></head>
            <body>${content}</body>
            </html>
        `;
        const blob = new Blob([html], { type: 'application/msword' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${filename}.doc`;
        a.click();
        URL.revokeObjectURL(url);
    };

    // Generate full Word content
    const downloadFullDeclaration = () => {
        if (!mvkData) return;
        const { identification, summary_table, section_a, section_b } = mvkData;

        let html = `
            <h1>MVK Deklarācijas Pielikumi</h1>
            <h2>Uzņēmuma informācija</h2>
            <p><strong>Nosaukums:</strong> ${identification.name}</p>
            <p><strong>Reģ. nr.:</strong> ${identification.regcode}</p>
            <p><strong>Adrese:</strong> ${identification.address}</p>
            <p><strong>Paraksttiesīgā persona:</strong> ${identification.authorized_person || "—"}</p>
            <p><strong>MVK statuss:</strong> ${mvkData.company_size || "Nav noteikts"}</p>
            <hr/>
            <h2>Kopsavilkuma tabula (2.1-2.3)</h2>
            <table border="1" cellpadding="5" style="border-collapse:collapse;">
                <tr style="background:#eee;"><th>Rinda</th><th>Apraksts</th><th>Darbinieki</th><th>Apgrozījums</th><th>Bilance</th></tr>
                <tr><td>2.1</td><td>Pašas komercsabiedrības dati</td><td>${summary_table.row_2_1.employees || 0}</td><td>${formatCurrency(summary_table.row_2_1.turnover)}</td><td>${formatCurrency(summary_table.row_2_1.balance)}</td></tr>
                <tr style="background:#fffde7;"><td>2.2</td><td>Partneruzņēmumu dati</td><td>${summary_table.row_2_2.employees}</td><td>${formatCurrency(summary_table.row_2_2.turnover)}</td><td>${formatCurrency(summary_table.row_2_2.balance)}</td></tr>
                <tr style="background:#ffebee;"><td>2.3</td><td>Saistīto uzņēmumu dati</td><td>${summary_table.row_2_3.employees}</td><td>${formatCurrency(summary_table.row_2_3.turnover)}</td><td>${formatCurrency(summary_table.row_2_3.balance)}</td></tr>
                <tr style="background:#1a365d;color:white;font-weight:bold;"><td colspan="2">KOPĀ</td><td>${summary_table.total.employees}</td><td>${formatCurrency(summary_table.total.turnover)}</td><td>${formatCurrency(summary_table.total.balance)}</td></tr>
            </table>
        `;

        if (section_a.partners.length > 0) {
            html += `<h2>A Sadaļa - Partneruzņēmumi</h2><table border="1" cellpadding="5" style="border-collapse:collapse;"><tr style="background:#eee;"><th>Nr.</th><th>Nosaukums</th><th>Darbinieki</th><th>Apgrozījums</th><th>Bilance</th><th>%</th></tr>`;
            section_a.partners.forEach((p, i) => {
                html += `<tr><td>${i + 1}</td><td>${p.name}</td><td>${p.employees || 0}</td><td>${formatCurrency(p.turnover)}</td><td>${formatCurrency(p.balance)}</td><td>${p.ownership_percent}%</td></tr>`;
            });
            html += `</table>`;
        }

        if (section_b.entities.length > 0) {
            html += `<h2>B Sadaļa - Saistītie uzņēmumi</h2><table border="1" cellpadding="5" style="border-collapse:collapse;"><tr style="background:#eee;"><th>Nr.</th><th>Nosaukums</th><th>Darbinieki</th><th>Apgrozījums</th><th>Bilance</th><th>%</th></tr>`;
            section_b.entities.forEach((e, i) => {
                html += `<tr><td>${i + 1}</td><td>${e.name}</td><td>${e.employees || 0}</td><td>${formatCurrency(e.turnover)}</td><td>${formatCurrency(e.balance)}</td><td>${e.ownership_percent}%</td></tr>`;
            });
            html += `</table>`;
        }

        downloadAsWord(html, `MVK_${identification.regcode}_${mvkData.year}`);
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
                        {/* Company Size Hero */}
                        <div className="bg-gradient-to-r from-primary to-primary-dark rounded-xl shadow-lg p-6 text-white">
                            <div className="flex items-center justify-between flex-wrap gap-4">
                                <div>
                                    <h2 className="text-2xl font-bold mb-2">{mvkData.identification.name}</h2>
                                    <p className="opacity-80">Reģ. nr. {mvkData.identification.regcode}</p>
                                </div>
                                <div className="flex items-center gap-4">
                                    <SizeBadge size={mvkData.company_size} />
                                    <button
                                        onClick={downloadFullDeclaration}
                                        className="bg-white text-primary px-4 py-2 rounded-lg font-medium hover:bg-gray-100 transition-colors flex items-center gap-2"
                                    >
                                        📄 Lejupielādēt Word
                                    </button>
                                </div>
                            </div>
                            <div className="mt-4 grid grid-cols-3 gap-4 text-center">
                                <div className="bg-white/10 rounded-lg p-3">
                                    <p className="text-2xl font-bold">{formatNumber(mvkData.summary_table.total.employees)}</p>
                                    <p className="text-sm opacity-80">Darbinieki (kopā)</p>
                                </div>
                                <div className="bg-white/10 rounded-lg p-3">
                                    <p className="text-2xl font-bold">{formatCurrency(mvkData.summary_table.total.turnover)}</p>
                                    <p className="text-sm opacity-80">Apgrozījums (kopā)</p>
                                </div>
                                <div className="bg-white/10 rounded-lg p-3">
                                    <p className="text-2xl font-bold">{formatCurrency(mvkData.summary_table.total.balance)}</p>
                                    <p className="text-sm opacity-80">Bilance (kopā)</p>
                                </div>
                            </div>
                        </div>

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

                        {/* 0️⃣ Status Detection Summary */}
                        <div className="bg-white rounded-xl shadow-lg p-6">
                            <h2 className="text-xl font-bold text-gray-900 mb-4">📊 Kā sistēma noteica jūsu MVK statusu</h2>

                            <div className="overflow-x-auto -mx-4 sm:mx-0">
                                <table className="w-full text-sm mb-4 min-w-[400px]">
                                    <thead className="bg-gray-100">
                                        <tr>
                                            <th className="px-3 sm:px-4 py-3 text-left font-semibold">Kritērijs</th>
                                            <th className="px-3 sm:px-4 py-3 text-left font-semibold">Statuss</th>
                                            <th className="px-3 sm:px-4 py-3 text-left font-semibold">Avots</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr className="border-b">
                                            <td className="px-4 py-3">Kapitāldaļu attiecības</td>
                                            <td className="px-4 py-3">
                                                <span className="text-green-600 font-medium">✅ Noteikts automātiski</span>
                                            </td>
                                            <td className="px-4 py-3 text-gray-500">Uzņēmumu reģistra dati</td>
                                        </tr>
                                        <tr className="border-b">
                                            <td className="px-4 py-3">Saistītie uzņēmumi (&gt;50%)</td>
                                            <td className="px-4 py-3">
                                                {mvkData.scenario.has_linked ? (
                                                    <span className="text-red-600 font-medium">🔴 {mvkData.section_b.entities.length} atrasti</span>
                                                ) : (
                                                    <span className="text-gray-500">⚪ Nav atrasti</span>
                                                )}
                                            </td>
                                            <td className="px-4 py-3 text-gray-500">UR API</td>
                                        </tr>
                                        <tr className="border-b">
                                            <td className="px-4 py-3">Partneruzņēmumi (25–50%)</td>
                                            <td className="px-4 py-3">
                                                {mvkData.scenario.has_partners ? (
                                                    <span className="text-yellow-600 font-medium">🟡 {mvkData.section_a.partners.length} atrasti</span>
                                                ) : (
                                                    <span className="text-gray-500">⚪ Nav atrasti</span>
                                                )}
                                            </td>
                                            <td className="px-4 py-3 text-gray-500">UR API</td>
                                        </tr>
                                        <tr className="border-b bg-yellow-50">
                                            <td className="px-4 py-3">Vadības / līgumu kontrole</td>
                                            <td className="px-4 py-3">
                                                <span className="text-orange-600 font-medium">⚠️ Nav iespējams noteikt automātiski</span>
                                            </td>
                                            <td className="px-4 py-3 text-gray-500">Lietotāja apliecinājums</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>

                            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-800">
                                <p className="font-medium mb-1">⚠️ Svarīgi</p>
                                <p>Uzņēmumu reģistra publiskie dati nesatur informāciju par noteicošu ietekmi ar līgumiem, statūtiem vai dalībnieku vienošanos. Šie kritēriji jāapstiprina uzņēmumam pašam.</p>
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
                            <div className="bg-gray-50 rounded-lg p-4 font-mono text-sm space-y-1">
                                <p><span className="font-semibold">Komercsabiedrības nosaukums:</span> {mvkData.identification.name}</p>
                                <p><span className="font-semibold">Juridiskā adrese:</span> {mvkData.identification.address}</p>
                                <p><span className="font-semibold">Reģistrācijas numurs:</span> {mvkData.identification.regcode}</p>
                                <p>
                                    <span className="font-semibold">Paraksttiesīgā persona:</span>{' '}
                                    {mvkData.identification.authorized_person_hash ? (
                                        <Link href={`/person/${mvkData.identification.authorized_person_hash}`} className="text-blue-600 hover:underline">
                                            {mvkData.identification.authorized_person}
                                        </Link>
                                    ) : (
                                        mvkData.identification.authorized_person || "—"
                                    )}
                                    {' '}
                                    ({mvkData.identification.authorized_position || "—"})
                                </p>
                            </div>
                        </div>

                        {/* 2️⃣ User Confirmation Section */}
                        {userConfirmations.length > 0 && (
                            <div className="bg-white rounded-xl shadow-lg p-6 border-2 border-orange-200">
                                <h2 className="text-xl font-bold text-gray-900 mb-2">
                                    ⚠️ Papildu kontroles kritēriji
                                </h2>
                                <p className="text-sm text-gray-600 mb-4">
                                    Pamatojoties uz uzņēmuma statūtiem, līgumiem vai dalībnieku vienošanos.
                                    Šī informācija nav pieejama publiskajos reģistros.
                                    Atzīmējiet tikai tos gadījumus, kas faktiski pastāv.
                                </p>

                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead className="bg-gray-100">
                                            <tr>
                                                <th className="px-3 py-2 text-left font-semibold">Uzņēmums</th>
                                                <th className="px-3 py-2 text-left font-semibold">Kritērijs</th>
                                                <th className="px-3 py-2 text-center font-semibold">Jā</th>
                                                <th className="px-3 py-2 text-center font-semibold">Nē</th>
                                                <th className="px-3 py-2 text-center font-semibold">Nezinu</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {userConfirmations.map((conf) => (
                                                <>
                                                    <tr key={`${conf.companyRegcode}-board`} className={`border-b ${conf.needsConfirmation ? 'bg-orange-50' : ''}`}>
                                                        <td className="px-3 py-2 font-medium" rowSpan={3}>
                                                            <div className="flex flex-col gap-1">
                                                                <span>{conf.companyName}</span>
                                                                <span className="text-xs text-gray-500">{conf.companyRegcode}</span>
                                                                {conf.naceCode && (
                                                                    <span className="text-xs text-blue-600">NACE: {conf.naceCode}</span>
                                                                )}
                                                                {conf.needsConfirmation && (
                                                                    <span className="inline-block px-2 py-0.5 text-xs bg-orange-200 text-orange-800 rounded">
                                                                        ⚠️ Cita nozare
                                                                    </span>
                                                                )}
                                                                {conf.sameMarket && !conf.needsConfirmation && (
                                                                    <span className="inline-block px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded">
                                                                        ✓ Tā pati nozare
                                                                    </span>
                                                                )}
                                                            </div>
                                                        </td>
                                                        <td className="px-3 py-2">Tiesības iecelt/atlaist vadības vairākumu</td>
                                                        <td className="px-3 py-2 text-center">
                                                            <input
                                                                type="radio"
                                                                name={`board-${conf.companyRegcode}`}
                                                                checked={conf.boardControl === 'yes'}
                                                                onChange={() => updateConfirmation(conf.companyRegcode, 'boardControl', 'yes')}
                                                                className="w-4 h-4 text-green-600"
                                                            />
                                                        </td>
                                                        <td className="px-3 py-2 text-center">
                                                            <input
                                                                type="radio"
                                                                name={`board-${conf.companyRegcode}`}
                                                                checked={conf.boardControl === 'no'}
                                                                onChange={() => updateConfirmation(conf.companyRegcode, 'boardControl', 'no')}
                                                                className="w-4 h-4 text-red-600"
                                                            />
                                                        </td>
                                                        <td className="px-3 py-2 text-center">
                                                            <input
                                                                type="radio"
                                                                name={`board-${conf.companyRegcode}`}
                                                                checked={conf.boardControl === 'unknown'}
                                                                onChange={() => updateConfirmation(conf.companyRegcode, 'boardControl', 'unknown')}
                                                                className="w-4 h-4 text-gray-600"
                                                            />
                                                        </td>
                                                    </tr>
                                                    <tr key={`${conf.companyRegcode}-contract`} className="border-b">
                                                        <td className="px-3 py-2">Noteicoša ietekme ar līgumu vai statūtiem</td>
                                                        <td className="px-3 py-2 text-center">
                                                            <input
                                                                type="radio"
                                                                name={`contract-${conf.companyRegcode}`}
                                                                checked={conf.contractControl === 'yes'}
                                                                onChange={() => updateConfirmation(conf.companyRegcode, 'contractControl', 'yes')}
                                                                className="w-4 h-4 text-green-600"
                                                            />
                                                        </td>
                                                        <td className="px-3 py-2 text-center">
                                                            <input
                                                                type="radio"
                                                                name={`contract-${conf.companyRegcode}`}
                                                                checked={conf.contractControl === 'no'}
                                                                onChange={() => updateConfirmation(conf.companyRegcode, 'contractControl', 'no')}
                                                                className="w-4 h-4 text-red-600"
                                                            />
                                                        </td>
                                                        <td className="px-3 py-2 text-center">
                                                            <input
                                                                type="radio"
                                                                name={`contract-${conf.companyRegcode}`}
                                                                checked={conf.contractControl === 'unknown'}
                                                                onChange={() => updateConfirmation(conf.companyRegcode, 'contractControl', 'unknown')}
                                                                className="w-4 h-4 text-gray-600"
                                                            />
                                                        </td>
                                                    </tr>
                                                    <tr key={`${conf.companyRegcode}-agreement`} className="border-b bg-gray-50">
                                                        <td className="px-3 py-2">Kontrole ar vienošanos ar citiem dalībniekiem</td>
                                                        <td className="px-3 py-2 text-center">
                                                            <input
                                                                type="radio"
                                                                name={`agreement-${conf.companyRegcode}`}
                                                                checked={conf.agreementControl === 'yes'}
                                                                onChange={() => updateConfirmation(conf.companyRegcode, 'agreementControl', 'yes')}
                                                                className="w-4 h-4 text-green-600"
                                                            />
                                                        </td>
                                                        <td className="px-3 py-2 text-center">
                                                            <input
                                                                type="radio"
                                                                name={`agreement-${conf.companyRegcode}`}
                                                                checked={conf.agreementControl === 'no'}
                                                                onChange={() => updateConfirmation(conf.companyRegcode, 'agreementControl', 'no')}
                                                                className="w-4 h-4 text-red-600"
                                                            />
                                                        </td>
                                                        <td className="px-3 py-2 text-center">
                                                            <input
                                                                type="radio"
                                                                name={`agreement-${conf.companyRegcode}`}
                                                                checked={conf.agreementControl === 'unknown'}
                                                                onChange={() => updateConfirmation(conf.companyRegcode, 'agreementControl', 'unknown')}
                                                                className="w-4 h-4 text-gray-600"
                                                            />
                                                        </td>
                                                    </tr>
                                                    {hasAnyYesConfirmation(conf.companyRegcode) && (
                                                        <tr key={`${conf.companyRegcode}-explanation`} className="bg-green-50">
                                                            <td colSpan={5} className="px-3 py-2">
                                                                <label className="block text-xs text-gray-600 mb-1">Paskaidrojums (ieteicams):</label>
                                                                <textarea
                                                                    value={conf.explanation}
                                                                    onChange={(e) => updateConfirmation(conf.companyRegcode, 'explanation', e.target.value)}
                                                                    className="w-full px-3 py-2 border rounded-lg text-sm"
                                                                    rows={2}
                                                                    placeholder="Aprakstiet kontroles pamatu..."
                                                                />
                                                            </td>
                                                        </tr>
                                                    )}
                                                </>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>

                                {hasUnknownConfirmations() && (
                                    <div className="mt-4 bg-orange-50 border border-orange-200 rounded-lg p-3 text-sm text-orange-800">
                                        ⚠️ Daļa kontroles kritēriju nav izvērtēti. Atbildība par MVK statusa pareizību paliek uzņēmumam.
                                    </div>
                                )}
                            </div>
                        )}

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
                                        onClick={() => copyTableAsHtml("table-section-a", "section_a")}
                                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${copySuccess === "section_a"
                                            ? "bg-green-100 text-green-800"
                                            : "bg-gray-100 hover:bg-gray-200 text-gray-700"
                                            }`}
                                    >
                                        {copySuccess === "section_a" ? "✓ Nokopēts!" : "📋 Kopēt A tabulu"}
                                    </button>
                                </div>

                                <div className="overflow-x-auto -mx-4 sm:mx-0">
                                    <table id="table-section-a" className="w-full text-sm min-w-[600px]">
                                        <thead className="bg-gray-100">
                                            <tr>
                                                <th className="px-2 sm:px-4 py-3 text-left">Nr.</th>
                                                <th className="px-2 sm:px-4 py-3 text-left">Partnerkomercsabiedrība</th>
                                                <th className="px-2 sm:px-4 py-3 text-right">Darbinieki</th>
                                                <th className="px-2 sm:px-4 py-3 text-right">Apgrozījums</th>
                                                <th className="px-2 sm:px-4 py-3 text-right">Bilance</th>
                                                <th className="px-2 sm:px-4 py-3 text-right">%</th>
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
                                                        ) : partner.person_hash ? (
                                                            <Link href={`/person/${partner.person_hash}`} className="text-primary hover:underline">
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
                                        onClick={() => copyTableAsHtml("table-section-b", "section_b")}
                                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${copySuccess === "section_b"
                                            ? "bg-green-100 text-green-800"
                                            : "bg-gray-100 hover:bg-gray-200 text-gray-700"
                                            }`}
                                    >
                                        {copySuccess === "section_b" ? "✓ Nokōpēts!" : "📋 Kopēt B tabulu"}
                                    </button>
                                </div>

                                <div className="overflow-x-auto -mx-4 sm:mx-0">
                                    <table id="table-section-b" className="w-full text-sm min-w-[600px]">
                                        <thead className="bg-gray-100">
                                            <tr>
                                                <th className="px-2 sm:px-4 py-3 text-left">Nr.</th>
                                                <th className="px-2 sm:px-4 py-3 text-left">Saistītā komercsabiedrība</th>
                                                <th className="px-2 sm:px-4 py-3 text-right">Darbinieki</th>
                                                <th className="px-2 sm:px-4 py-3 text-right">Apgrozījums</th>
                                                <th className="px-2 sm:px-4 py-3 text-right">Bilance</th>
                                                <th className="px-2 sm:px-4 py-3 text-right">%</th>
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
                                                        ) : entity.person_hash ? (
                                                            <Link href={`/person/${entity.person_hash}`} className="text-primary hover:underline">
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
                            </div>
                        )}

                        {/* Summary Table 2.1-2.3 */}
                        <div className="bg-white rounded-xl shadow-lg p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-xl font-bold text-gray-900">📈 Gala Kopsavilkums (2.1–2.3)</h2>
                                <button
                                    onClick={() => copyTableAsHtml("table-summary", "summary")}
                                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${copySuccess === "summary"
                                        ? "bg-green-100 text-green-800"
                                        : "bg-primary text-white hover:bg-primary-dark"
                                        }`}
                                >
                                    {copySuccess === "summary" ? "✓ Nokopēts!" : "📋 Kopēt deklarācijas 3. sadaļai"}
                                </button>
                            </div>

                            <div className="overflow-x-auto -mx-4 sm:mx-0">
                                <table id="table-summary" className="w-full text-sm min-w-[600px]">
                                    <thead className="bg-gray-100">
                                        <tr>
                                            <th className="px-2 sm:px-4 py-3 text-left">Rinda</th>
                                            <th className="px-2 sm:px-4 py-3 text-left">Apraksts</th>
                                            <th className="px-2 sm:px-4 py-3 text-right">Darbinieki</th>
                                            <th className="px-2 sm:px-4 py-3 text-right">Apgrozījums</th>
                                            <th className="px-2 sm:px-4 py-3 text-right">Bilance</th>
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
