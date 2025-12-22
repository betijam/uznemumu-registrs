"use client";

import { useState } from "react";
import Link from "next/link";
import GaugeChart from './GaugeChart';
import RisksTab from './RisksTab';

// Helper function for formatting currency
const formatCurrency = (value: number | null | undefined, decimals = 0) => {
    if (value === null || value === undefined) return "-";
    return `€ ${value.toLocaleString('lv-LV', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}`;
};

// Growth indicator component
const GrowthIndicator = ({ value }: { value: number | null }) => {
    if (value === null || value === undefined) return <span className="text-gray-400">-</span>;
    const isPositive = value >= 0;
    return (
        <span className={`inline-flex items-center text-xs font-medium ${isPositive ? 'text-success' : 'text-danger'}`}>
            <svg className={`w-3 h-3 mr-0.5 ${!isPositive ? 'rotate-180' : ''}`} fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
            {Math.abs(value).toFixed(1)}%
        </span>
    );
};

// Rating badge component
const RatingBadge = ({ grade }: { grade: string | null }) => {
    if (!grade) return null;
    const colors: Record<string, string> = {
        'A': 'bg-success/10 text-success border-success/20',
        'B': 'bg-blue-50 text-blue-700 border-blue-200',
        'C': 'bg-yellow-50 text-yellow-700 border-yellow-200',
        'N': 'bg-gray-50 text-gray-700 border-gray-200',
    };
    return (
        <span className={`inline-flex items-center px-3 py-1 rounded-lg text-sm font-bold border ${colors[grade] || colors['N']}`}>
            VID Reitings: {grade}
        </span>
    );
};

// Sparkline component
const Sparkline = ({ data }: { data: number[] }) => {
    const filtered = data.filter(v => v !== null && v !== undefined);
    if (!filtered || filtered.length === 0) return <span className="text-gray-400">-</span>;

    const max = Math.max(...filtered);
    const min = Math.min(...filtered);
    const range = max - min || 1;

    const points = filtered.map((val, idx) => {
        const x = (idx / Math.max(filtered.length - 1, 1)) * 60;
        const y = 20 - ((val - min) / range) * 15;
        return `${x},${y}`;
    }).join(' ');

    return (
        <svg viewBox="0 0 60 20" className="w-16 h-6 inline-block">
            <polyline
                points={points}
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                className="text-primary"
            />
        </svg>
    );
};

export default function CompanyTabs({ company, related }: { company: any, related: any }) {
    const [activeTab, setActiveTab] = useState("overview");
    const [selectedSignatory, setSelectedSignatory] = useState<string>("");
    const [copied, setCopied] = useState(false);

    // Get signatories from officers (those with signing rights INDIVIDUALLY or CHAIR positions)
    const positionLabels: { [key: string]: string } = {
        'BOARD_MEMBER': 'Valdes loceklis',
        'CHAIR_OF_BOARD': 'Valdes priekšsēdētājs',
        'COUNCIL_MEMBER': 'Padomes loceklis',
        'CHAIR_OF_COUNCIL': 'Padomes priekšsēdētājs',
        'PROCURATOR': 'Prokūrists',
        'LIQUIDATOR': 'Likvidators',
        'ADMINISTRATOR': 'Administrators',
        'AUTHORISED_REPRESENTATIVE': 'Pilnvarotais pārstāvis'
    };

    const signatories = (company.officers || []).filter((o: any) =>
        o.rights_of_representation === 'INDIVIDUALLY' ||
        o.position === 'CHAIR_OF_BOARD' ||
        o.position === 'PROCURATOR'
    );

    // Copy requisites to clipboard
    const copyRequisites = () => {
        const signatory = signatories.find((s: any) => s.name === selectedSignatory);
        const positionText = signatory ? (positionLabels[signatory.position] || signatory.position) : '';
        const text = `${company.name}
Juridiskā adrese: ${company.address || '-'}
Reģistrācijas numurs: ${company.regcode}
${signatory ? `Parakstiesīgā persona: ${signatory.name}, ${positionText}` : ''}`;

        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };
    const tabs = [
        { id: "overview", label: "Pārskats" },
        { id: "finances", label: "Finanses", badge: company.rating?.grade },
        { id: "risks", label: "Riski", badge: company.risk_level !== 'NONE' ? company.risk_level : null },
        { id: "management", label: "Amatpersonas & Īpašnieki" },
        { id: "related", label: "Saistītie Subjekti" },
        { id: "procurements", label: "Valsts Iepirkumi" },
    ];

    const financialHistory = company.financial_history || [];
    const latest = financialHistory[0] || {};

    // Format helpers
    const formatPercent = (val: number | null) => {
        if (val === null || val === undefined) return '-';
        return `${val.toFixed(2)}%`;
    };

    const formatRatio = (val: number | null) => {
        if (val === null || val === undefined) return '-';
        return val.toFixed(2);
    };

    return (
        <div className="mt-6">
            <div className="border-b border-gray-200 bg-white rounded-t-lg">
                <nav className="-mb-px flex space-x-4 sm:space-x-8 px-4 sm:px-6 overflow-x-auto scrollbar-hide" aria-label="Tabs">
                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`${activeTab === tab.id
                                ? "border-accent text-accent"
                                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors flex items-center gap-2`}
                        >
                            {tab.label}
                            {tab.badge && <span className="px-1.5 py-0.5 text-xs font-bold bg-success/10 text-success rounded">{tab.badge}</span>}
                        </button>
                    ))}
                </nav>
            </div>

            <div className="mt-0 bg-white rounded-b-lg shadow-card p-6">
                {/* OVERVIEW TAB */}
                {activeTab === "overview" && (
                    <div className="space-y-6">
                        {/* Copyable Requisites Section */}
                        <div className="border border-gray-200 rounded-lg p-5 bg-gray-50">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-semibold text-gray-900">📋 Rekvizīti (Līgumiem)</h3>
                                <button
                                    onClick={copyRequisites}
                                    className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${copied
                                        ? 'bg-success text-white'
                                        : 'bg-primary text-white hover:bg-primary/90'
                                        }`}
                                >
                                    {copied ? (
                                        <>
                                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                            </svg>
                                            Nokopēts!
                                        </>
                                    ) : (
                                        <>
                                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                            </svg>
                                            Kopēt
                                        </>
                                    )}
                                </button>
                            </div>

                            <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-3 font-mono text-sm">
                                <div>
                                    <span className="font-bold text-gray-900">{company.name}</span>
                                </div>
                                <div>
                                    <span className="text-gray-600">Juridiskā adrese: </span>
                                    <span className="text-gray-900">{company.address || '-'}</span>
                                </div>
                                <div>
                                    <span className="text-gray-600">Reģistrācijas numurs: </span>
                                    <span className="text-gray-900">{company.regcode}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="text-gray-600">Parakstiesīgā persona: </span>
                                    {signatories.length > 0 ? (
                                        <select
                                            value={selectedSignatory}
                                            onChange={(e) => setSelectedSignatory(e.target.value)}
                                            className="flex-1 px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-primary bg-white"
                                        >
                                            <option value="">-- Izvēlieties --</option>
                                            {signatories.map((s: any, idx: number) => (
                                                <option key={idx} value={s.name}>
                                                    {s.name} ({positionLabels[s.position] || s.position})
                                                </option>
                                            ))}
                                        </select>
                                    ) : (
                                        <span className="text-gray-400 italic">Nav datu</span>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Financial Chart - Dual-Panel Stacked Bars */}
                        <div className="border border-gray-200 rounded-lg p-4 sm:p-6">
                            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
                                <h3 className="text-lg font-semibold text-primary">Apgrozījums vs Peļņa</h3>
                                {company.rating && <RatingBadge grade={company.rating.grade} />}
                            </div>

                            {financialHistory.length > 0 ? (
                                <div className="space-y-6">
                                    {/* Turnover Section */}
                                    <div>
                                        <div className="flex items-center gap-2 mb-2">
                                            <div className="w-3 h-3 bg-blue-500 rounded"></div>
                                            <span className="text-sm font-medium text-gray-700">Apgrozījums</span>
                                        </div>
                                        <div className="h-32 flex items-end gap-2">
                                            {financialHistory.slice(0, 7).reverse().map((f: any, idx: number) => {
                                                const maxTurnover = Math.max(...financialHistory.slice(0, 7).map((x: any) => x.turnover || 0), 1);
                                                const barHeight = f.turnover ? (f.turnover / maxTurnover) * 120 : 4; // 120px max height

                                                return (
                                                    <div key={f.year} className="flex-1 flex flex-col items-center group relative h-full justify-end">
                                                        <div
                                                            className="w-full bg-blue-500 hover:bg-blue-600 rounded-t transition-all cursor-pointer relative"
                                                            style={{ height: `${Math.max(barHeight, 4)}px` }}
                                                        >
                                                            {/* Tooltip */}
                                                            <div className="absolute -top-12 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-xs px-3 py-1.5 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-20 pointer-events-none">
                                                                <div className="font-semibold">{f.year}</div>
                                                                <div>{formatCurrency(f.turnover)}</div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </div>

                                    {/* Profit Section */}
                                    <div>
                                        <div className="flex items-center gap-2 mb-2">
                                            <div className="w-3 h-3 bg-emerald-500 rounded"></div>
                                            <span className="text-sm font-medium text-gray-700">Peļņa</span>
                                            <span className="text-xs text-gray-400">(sarkans = zaudējumi)</span>
                                        </div>
                                        <div className="h-24 flex items-center gap-2 relative">
                                            {/* Zero line */}
                                            <div className="absolute left-0 right-0 top-1/2 h-px bg-gray-300 z-0"></div>

                                            {financialHistory.slice(0, 7).reverse().map((f: any, idx: number) => {
                                                const profits = financialHistory.slice(0, 7).map((x: any) => x.profit || 0);
                                                const maxAbsProfit = Math.max(...profits.map((p: number) => Math.abs(p)), 1);
                                                const profit = f.profit || 0;
                                                const isPositive = profit >= 0;
                                                const barHeight = (Math.abs(profit) / maxAbsProfit) * 40; // Max 40px height

                                                return (
                                                    <div key={f.year} className="flex-1 h-full group relative z-10" style={{ position: 'relative' }}>
                                                        {/* Positive profit bar (grows upward from center) */}
                                                        {isPositive && (
                                                            <div
                                                                className="w-full bg-emerald-500 hover:bg-emerald-600 rounded-t transition-all cursor-pointer absolute left-0 right-0"
                                                                style={{
                                                                    height: `${Math.max(barHeight, 3)}px`,
                                                                    bottom: '50%'
                                                                }}
                                                            ></div>
                                                        )}
                                                        {/* Negative profit bar (grows downward from center) */}
                                                        {!isPositive && (
                                                            <div
                                                                className="w-full bg-red-500 hover:bg-red-600 rounded-b transition-all cursor-pointer absolute left-0 right-0"
                                                                style={{
                                                                    height: `${Math.max(barHeight, 3)}px`,
                                                                    top: '50%'
                                                                }}
                                                            ></div>
                                                        )}
                                                        {/* Tooltip */}
                                                        <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-xs px-3 py-1.5 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-30 pointer-events-none">
                                                            <div className="font-semibold">{f.year}</div>
                                                            <div className={isPositive ? 'text-emerald-300' : 'text-red-300'}>{formatCurrency(profit)}</div>
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </div>

                                    {/* Year Labels */}
                                    <div className="flex gap-2 border-t border-gray-100 pt-3">
                                        {financialHistory.slice(0, 7).reverse().map((f: any, idx: number) => (
                                            <div key={f.year} className="flex-1 text-center">
                                                <span className="text-xs font-medium text-gray-600">{f.year}</span>
                                                {f.turnover_growth !== null && (
                                                    <div className="mt-0.5"><GrowthIndicator value={f.turnover_growth} /></div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ) : (
                                <div className="h-64 flex items-center justify-center text-gray-500">
                                    Nav finanšu datu
                                </div>
                            )}
                        </div>

                        {/* Quick Info Cards */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="border border-gray-200 rounded-lg p-5">
                                <h4 className="text-md font-semibold text-gray-900 mb-4">Finanšu Rādītāji ({company.finances?.year || "N/A"})</h4>
                                <dl className="space-y-3">
                                    <div className="flex justify-between">
                                        <dt className="text-sm text-gray-600">Apgrozījums</dt>
                                        <dd className="text-sm font-semibold text-primary flex items-center gap-2">
                                            {formatCurrency(company.finances?.turnover)}
                                            <GrowthIndicator value={company.finances?.turnover_growth} />
                                        </dd>
                                    </div>
                                    <div className="flex justify-between">
                                        <dt className="text-sm text-gray-600">Peļņa</dt>
                                        <dd className={`text-sm font-semibold flex items-center gap-2 ${(company.finances?.profit || 0) >= 0 ? 'text-success' : 'text-danger'}`}>
                                            {formatCurrency(company.finances?.profit)}
                                            <GrowthIndicator value={company.finances?.profit_growth} />
                                        </dd>
                                    </div>
                                    <div className="flex justify-between">
                                        <dt className="text-sm text-gray-600">Darbinieki</dt>
                                        <dd className="text-sm font-semibold text-primary">{company.finances?.employees || "-"}</dd>
                                    </div>
                                </dl>
                            </div>

                            <div className="border border-gray-200 rounded-lg p-5">
                                <h4 className="text-md font-semibold text-gray-900 mb-4">Papildu Informācija</h4>
                                <dl className="space-y-3">
                                    <div className="flex justify-between">
                                        <dt className="text-sm text-gray-600">Reģistrācijas datums</dt>
                                        <dd className="text-sm font-semibold text-gray-900">{company.registration_date || "-"}</dd>
                                    </div>
                                    <div className="flex justify-between">
                                        <dt className="text-sm text-gray-600">Statuss</dt>
                                        <dd className="text-sm font-semibold text-success">{company.status === "active" ? "Aktīvs" : company.status}</dd>
                                    </div>
                                    <div className="flex justify-between">
                                        <dt className="text-sm text-gray-600">VID Reitings</dt>
                                        <dd className="text-sm font-semibold text-gray-900">{company.rating?.grade || "-"}</dd>
                                    </div>
                                </dl>
                            </div>
                        </div>
                    </div>
                )}

                {/* COMBINED FINANCES TAB (Finanses + Finanšu Veselība) */}
                {activeTab === "finances" && (
                    <div className="space-y-8">
                        {/* VID Rating Banner */}
                        {company.rating && (
                            <div className="border border-success rounded-lg p-4 bg-success/5">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <div className="flex items-center gap-3">
                                            <RatingBadge grade={company.rating.grade} />
                                            <span className="text-sm text-gray-600">{company.rating.explanation}</span>
                                        </div>
                                        <div className="text-xs text-gray-500 mt-1">
                                            Atjaunots: {company.rating.date}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Key Gauges */}
                        <div>
                            <h3 className="text-lg font-semibold text-gray-900 mb-4">Finanšu Veselības Rādītāji</h3>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                <GaugeChart
                                    value={latest.current_ratio}
                                    min={0}
                                    max={3}
                                    thresholds={{ good: 1.2, warning: 1.0 }}
                                    label="Likviditāte"
                                    subtitle="Current Ratio"
                                    format={(v) => v.toFixed(2)}
                                />

                                <GaugeChart
                                    value={latest.roe}
                                    min={-20}
                                    max={30}
                                    thresholds={{ good: 10, warning: 5 }}
                                    label="ROE"
                                    subtitle="Pašu kapitāla atdeve"
                                    format={(v) => `${v.toFixed(1)}%`}
                                />

                                <GaugeChart
                                    value={latest.debt_to_equity}
                                    min={0}
                                    max={3}
                                    thresholds={{ good: 1.0, warning: 2.0 }}
                                    label="Parāda Slodze"
                                    subtitle="Debt-to-Equity"
                                    format={(v) => v.toFixed(2)}
                                    invertColors={true}
                                />
                            </div>
                        </div>

                        {/* Detailed Metrics Table */}
                        <div className="border border-gray-200 rounded-lg overflow-hidden">
                            <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                                <h3 className="text-lg font-semibold text-gray-900">Detalizēti Finanšu Rādītāji</h3>
                            </div>
                            <div className="overflow-x-auto -mx-4 sm:mx-0">
                                <table className="w-full min-w-[500px]">
                                    <thead className="bg-gray-50 border-b border-gray-200">
                                        <tr>
                                            <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rādītājs</th>
                                            <th className="px-3 sm:px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Vērtība</th>
                                            <th className="px-3 sm:px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Tendence</th>
                                            <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Norma</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-200">
                                        <tr className="bg-blue-50/30">
                                            <td colSpan={4} className="px-6 py-2 text-sm font-semibold text-gray-700">💧 Likviditāte</td>
                                        </tr>
                                        <tr>
                                            <td className="px-6 py-3 text-sm text-gray-900">Current Ratio</td>
                                            <td className="px-6 py-3 text-sm text-right font-semibold">{formatRatio(latest.current_ratio)}</td>
                                            <td className="px-6 py-3 text-center"><Sparkline data={financialHistory.slice(0, 5).map((f: any) => f.current_ratio)} /></td>
                                            <td className="px-6 py-3 text-sm text-gray-600">&gt; 1.2</td>
                                        </tr>
                                        <tr>
                                            <td className="px-6 py-3 text-sm text-gray-900">Quick Ratio</td>
                                            <td className="px-6 py-3 text-sm text-right font-semibold">{formatRatio(latest.quick_ratio)}</td>
                                            <td className="px-6 py-3 text-center"><Sparkline data={financialHistory.slice(0, 5).map((f: any) => f.quick_ratio)} /></td>
                                            <td className="px-6 py-3 text-sm text-gray-600">&gt; 0.8</td>
                                        </tr>

                                        <tr className="bg-green-50/30">
                                            <td colSpan={4} className="px-6 py-2 text-sm font-semibold text-gray-700">💰 Rentabilitāte</td>
                                        </tr>
                                        <tr>
                                            <td className="px-6 py-3 text-sm text-gray-900">Net Profit Margin</td>
                                            <td className="px-6 py-3 text-sm text-right font-semibold">{formatPercent(latest.net_profit_margin)}</td>
                                            <td className="px-6 py-3 text-center"><Sparkline data={financialHistory.slice(0, 5).map((f: any) => f.net_profit_margin)} /></td>
                                            <td className="px-6 py-3 text-sm text-gray-600">Atkarīgs no nozares</td>
                                        </tr>
                                        <tr>
                                            <td className="px-6 py-3 text-sm text-gray-900">ROE</td>
                                            <td className="px-6 py-3 text-sm text-right font-semibold">{formatPercent(latest.roe)}</td>
                                            <td className="px-6 py-3 text-center"><Sparkline data={financialHistory.slice(0, 5).map((f: any) => f.roe)} /></td>
                                            <td className="px-6 py-3 text-sm text-gray-600">&gt; 10%</td>
                                        </tr>
                                        <tr>
                                            <td className="px-6 py-3 text-sm text-gray-900">ROA</td>
                                            <td className="px-6 py-3 text-sm text-right font-semibold">{formatPercent(latest.roa)}</td>
                                            <td className="px-6 py-3 text-center"><Sparkline data={financialHistory.slice(0, 5).map((f: any) => f.roa)} /></td>
                                            <td className="px-6 py-3 text-sm text-gray-600">&gt; 5%</td>
                                        </tr>

                                        <tr className="bg-orange-50/30">
                                            <td colSpan={4} className="px-6 py-2 text-sm font-semibold text-gray-700">📈 Maksātspēja</td>
                                        </tr>
                                        <tr>
                                            <td className="px-6 py-3 text-sm text-gray-900">Debt-to-Equity</td>
                                            <td className="px-6 py-3 text-sm text-right font-semibold">{formatRatio(latest.debt_to_equity)}</td>
                                            <td className="px-6 py-3 text-center"><Sparkline data={financialHistory.slice(0, 5).map((f: any) => f.debt_to_equity)} /></td>
                                            <td className="px-6 py-3 text-sm text-gray-600">&lt; 1.5</td>
                                        </tr>

                                        <tr className="bg-purple-50/30">
                                            <td colSpan={4} className="px-6 py-2 text-sm font-semibold text-gray-700">🚀 Naudas Plūsma</td>
                                        </tr>
                                        <tr>
                                            <td className="px-6 py-3 text-sm text-gray-900">EBITDA</td>
                                            <td className="px-6 py-3 text-sm text-right font-semibold">{formatCurrency(latest.ebitda)}</td>
                                            <td className="px-6 py-3 text-center"><Sparkline data={financialHistory.slice(0, 5).map((f: any) => f.ebitda)} /></td>
                                            <td className="px-6 py-3 text-sm text-gray-600">Pozitīvs</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        {/* Financial History Table */}
                        <div className="border border-gray-200 rounded-lg overflow-hidden">
                            <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                                <h3 className="text-lg font-semibold text-gray-900">Finanšu Vēsture</h3>
                            </div>
                            {financialHistory.length > 0 ? (
                                <div className="overflow-x-auto -mx-4 sm:mx-0">
                                    <table className="w-full min-w-[400px]">
                                        <thead className="bg-gray-50 border-b border-gray-200">
                                            <tr>
                                                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Gads</th>
                                                <th className="px-3 sm:px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Apgrozījums</th>
                                                <th className="px-3 sm:px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Peļņa</th>
                                                <th className="px-3 sm:px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Darbinieki</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-200">
                                            {financialHistory.map((f: any) => (
                                                <tr key={f.year} className="hover:bg-gray-50">
                                                    <td className="px-6 py-4 text-sm font-medium text-gray-900">{f.year}</td>
                                                    <td className="px-6 py-4 text-sm text-right">
                                                        <div className="flex items-center justify-end gap-2">
                                                            {formatCurrency(f.turnover)}
                                                            <GrowthIndicator value={f.turnover_growth} />
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-4 text-sm text-right">
                                                        <div className="flex items-center justify-end gap-2">
                                                            <span className={(f.profit || 0) >= 0 ? 'text-success' : 'text-danger'}>
                                                                {formatCurrency(f.profit)}
                                                            </span>
                                                            <GrowthIndicator value={f.profit_growth} />
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-4 text-sm text-right">{f.employees || "-"}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            ) : (
                                <div className="p-6 text-center text-gray-500">Nav pieejami finanšu dati</div>
                            )}
                        </div>

                        {/* Tax History */}
                        {company.tax_history && company.tax_history.length > 0 && (
                            <div className="border border-gray-200 rounded-lg overflow-hidden">
                                <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                                    <h3 className="text-lg font-semibold text-gray-900">VID Samaksātie Nodokļi</h3>
                                </div>
                                <div className="overflow-x-auto -mx-4 sm:mx-0">
                                    <table className="w-full min-w-[500px]">
                                        <thead className="bg-gray-50 border-b border-gray-200">
                                            <tr>
                                                <th className="px-2 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Gads</th>
                                                <th className="px-2 sm:px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">IIN</th>
                                                <th className="px-2 sm:px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">VSAOI</th>
                                                <th className="px-2 sm:px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase whitespace-nowrap">Vid. Darb.</th>
                                                <th className="px-2 sm:px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase whitespace-nowrap">Vid. Alga</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-200">
                                            {company.tax_history.map((t: any) => (
                                                <tr key={t.year} className="hover:bg-gray-50">
                                                    <td className="px-6 py-4 text-sm font-medium text-gray-900">{t.year}</td>
                                                    <td className="px-6 py-4 text-sm text-right">{formatCurrency(t.labor_tax_iin)}</td>
                                                    <td className="px-6 py-4 text-sm text-right">{formatCurrency(t.social_tax_vsaoi)}</td>
                                                    <td className="px-6 py-4 text-sm text-right">{t.avg_employees || "-"}</td>
                                                    <td className="px-6 py-4 text-sm text-right text-primary font-semibold">{formatCurrency(t.avg_gross_salary)}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* RISKS TAB */}
                {activeTab === "risks" && (
                    <RisksTab company={company} />
                )}

                {/* MANAGEMENT TAB - 3 Sections: UBOs, Members, Officers */}
                {activeTab === "management" && (
                    <div className="space-y-8">

                        {/* === 1. PATIESIE LABUMA GUVĒJI (UBOs) === */}
                        <div>
                            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                                <span className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center text-purple-600">👤</span>
                                Patiesie Labuma Guvēji (PLG)
                            </h3>
                            {company.ubos && company.ubos.length > 0 ? (
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                    {company.ubos.map((ubo: any, idx: number) => (
                                        <div key={idx} className="border border-gray-200 rounded-lg p-4 bg-gradient-to-br from-purple-50 to-white">
                                            <div className="flex items-start justify-between">
                                                <div className="font-semibold text-gray-900">{ubo.name}</div>
                                                {ubo.nationality && (
                                                    <span className="text-xs px-2 py-0.5 bg-gray-100 rounded font-medium">
                                                        {ubo.nationality === 'LV' ? '🇱🇻' : ubo.nationality === 'EE' ? '🇪🇪' : ubo.nationality === 'LT' ? '🇱🇹' : ubo.nationality}
                                                    </span>
                                                )}
                                            </div>
                                            <div className="text-sm text-purple-600 font-medium mt-1">Patiesais labuma guvējs</div>
                                            <div className="text-sm text-gray-600 mt-2">
                                                {ubo.residence && <div>Dzīvesvieta: {ubo.residence}</div>}
                                                {ubo.registered_on && <div>Reģistrēts: {ubo.registered_on}</div>}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-8 bg-gray-50 rounded-lg border border-gray-200">
                                    <p className="text-gray-500">Nav reģistrētu patieso labuma guvēju</p>
                                </div>
                            )}
                        </div>

                        {/* === 2. DALĪBNIEKI (Members/Shareholders) === */}
                        <div>
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                                    <span className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600">💼</span>
                                    Dalībnieki (Īpašnieki)
                                </h3>
                                {company.total_capital > 0 && (
                                    <div className="text-sm text-gray-600">
                                        Pamatkapitāls: <span className="font-semibold">{company.total_capital.toLocaleString('lv-LV')} EUR</span>
                                    </div>
                                )}
                            </div>
                            {company.members && company.members.length > 0 ? (
                                <div className="border border-gray-200 rounded-lg overflow-hidden">
                                    <table className="w-full">
                                        <thead className="bg-gray-50 border-b border-gray-200">
                                            <tr>
                                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Dalībnieks</th>
                                                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Daļas</th>
                                                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Vērtība</th>
                                                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">%</th>
                                                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Reģ.</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-200">
                                            {company.members.map((member: any, idx: number) => (
                                                <tr key={idx} className="hover:bg-gray-50">
                                                    <td className="px-4 py-3 text-sm">
                                                        {member.legal_entity_regcode ? (
                                                            <a href={`/company/${member.legal_entity_regcode}`} className="text-primary hover:underline font-medium flex items-center gap-1">
                                                                {member.name}
                                                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                                                            </a>
                                                        ) : (
                                                            <span className="text-gray-900">{member.name}</span>
                                                        )}
                                                    </td>
                                                    <td className="px-4 py-3 text-sm text-right text-gray-600">{member.number_of_shares?.toLocaleString('lv-LV') || '-'}</td>
                                                    <td className="px-4 py-3 text-sm text-right text-gray-600">{member.share_value > 0 ? `${member.share_value.toLocaleString('lv-LV')} ${member.share_currency}` : '-'}</td>
                                                    <td className="px-4 py-3 text-sm text-right font-semibold text-gray-900">{member.percent > 0 ? `${member.percent}%` : '-'}</td>
                                                    <td className="px-4 py-3 text-sm text-right text-gray-500">{member.date_from || '-'}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            ) : (
                                <div className="text-center py-8 bg-gray-50 rounded-lg border border-gray-200">
                                    <p className="text-gray-500">Nav reģistrētu dalībnieku</p>
                                </div>
                            )}
                        </div>

                        {/* === 3. AMATPERSONAS (Officers) === */}
                        <div>
                            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                                <span className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center text-green-600">✍️</span>
                                Amatpersonas
                            </h3>
                            {company.officers && company.officers.length > 0 ? (
                                <div className="border border-gray-200 rounded-lg overflow-hidden">
                                    <table className="w-full">
                                        <thead className="bg-gray-50 border-b border-gray-200">
                                            <tr>
                                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amats</th>
                                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vārds, Uzvārds</th>
                                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Pārstāvības tiesības</th>
                                                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Iecelts</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-200">
                                            {company.officers.map((officer: any, idx: number) => {
                                                // Position translations
                                                const positionLabels: { [key: string]: string } = {
                                                    'BOARD_MEMBER': 'Valdes loceklis',
                                                    'CHAIR_OF_BOARD': 'Valdes priekšsēdētājs',
                                                    'COUNCIL_MEMBER': 'Padomes loceklis',
                                                    'CHAIR_OF_COUNCIL': 'Padomes priekšsēdētājs',
                                                    'PROCURATOR': 'Prokūrists',
                                                    'LIQUIDATOR': 'Likvidators',
                                                    'ADMINISTRATOR': 'Administrators',
                                                    'AUTHORISED_REPRESENTATIVE': 'Pilnvarotais pārstāvis'
                                                };

                                                // Representation rights
                                                const getRepresentation = () => {
                                                    switch (officer.rights_of_representation) {
                                                        case 'INDIVIDUALLY': return { text: 'Atsevišķi', icon: '✅', color: 'text-green-600 bg-green-50' };
                                                        case 'WITH_ALL': return { text: 'Kopā ar visiem', icon: '👥', color: 'text-orange-600 bg-orange-50' };
                                                        case 'WITH_AT_LEAST': return { text: `Kopā ar vismaz ${officer.representation_with_at_least}`, icon: '👥', color: 'text-yellow-600 bg-yellow-50' };
                                                        default: return { text: '-', icon: '', color: 'text-gray-500' };
                                                    }
                                                };
                                                const repr = getRepresentation();

                                                return (
                                                    <tr key={idx} className="hover:bg-gray-50">
                                                        <td className="px-4 py-3 text-sm font-medium text-gray-900">{positionLabels[officer.position] || officer.position || '-'}</td>
                                                        <td className="px-4 py-3 text-sm text-gray-900">{officer.name}</td>
                                                        <td className="px-4 py-3 text-sm">
                                                            <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${repr.color}`}>
                                                                {repr.icon} {repr.text}
                                                            </span>
                                                        </td>
                                                        <td className="px-4 py-3 text-sm text-right text-gray-500">{officer.registered_on || '-'}</td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </div>
                            ) : (
                                <div className="text-center py-8 bg-gray-50 rounded-lg border border-gray-200">
                                    <p className="text-gray-500">Nav reģistrētu amatpersonu</p>
                                </div>
                            )}
                        </div>

                    </div>
                )}

                {/* RELATED COMPANIES TAB - ES MVU Classification */}
                {activeTab === "related" && (
                    <div className="space-y-6">
                        {/* Status Header */}
                        <div className="flex items-center justify-between">
                            <h3 className="text-lg font-semibold text-gray-900">Saistītie Subjekti (ES MVU / De Minimis)</h3>
                            <div className={`px-4 py-2 rounded-lg text-sm font-bold ${(related?.status === 'AUTONOMOUS' || !related?.status || related?.status === 'NOT_FOUND') ? 'bg-green-100 text-green-700' :
                                related?.status === 'PARTNER' ? 'bg-yellow-100 text-yellow-700' :
                                    related?.status === 'LINKED' ? 'bg-red-100 text-red-700' :
                                        'bg-green-100 text-green-700'
                                }`}>
                                {related?.status === 'PARTNER' ? '🤝 PARTNERI' :
                                    related?.status === 'LINKED' ? '🔗 SAISTĪTA' : '✅ AUTONOMA'}
                            </div>
                        </div>
                        {/* AUTONOMOUS Status - Big Display */}
                        {(related?.status === 'AUTONOMOUS' || !related?.status || related?.status === 'NOT_FOUND') && !related?.linked?.length && !related?.partners?.length && (
                            <div className="text-center py-12 bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 rounded-lg">
                                <span className="text-5xl">✅</span>
                                <h3 className="text-2xl font-bold text-green-700 mt-4">
                                    AUTONOMA KOMERCSABIEDRĪBA
                                </h3>
                                <p className="text-green-600 mt-2 max-w-md mx-auto">
                                    Šim uzņēmumam nav identificētas partnerkomercsabiedrības (25-50% daļu)
                                    vai saistītās komercsabiedrības (&gt;50% daļu).
                                </p>
                                {related?.total_capital > 0 && (
                                    <p className="text-sm text-green-500 mt-4">
                                        Pamatkapitāls: {related.total_capital.toLocaleString('lv-LV')} EUR
                                    </p>
                                )}
                            </div>
                        )}

                        {/* LINKED Companies Table (>50%) */}
                        {related?.linked && related.linked.length > 0 && (
                            <div>
                                <h4 className="text-md font-semibold text-gray-700 mb-3 flex items-center gap-2">
                                    <span className="w-6 h-6 rounded-full bg-red-100 flex items-center justify-center text-red-600 text-sm">🔗</span>
                                    Saistītās Komercsabiedrības (&gt;50% kapitāldaļu)
                                </h4>
                                <div className="border border-gray-200 rounded-lg overflow-hidden">
                                    <table className="w-full">
                                        <thead className="bg-red-50 border-b border-gray-200">
                                            <tr>
                                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Uzņēmums</th>
                                                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Tips</th>
                                                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">%</th>
                                                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Darbinieki</th>
                                                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Apgrozījums</th>
                                                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Bilance</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-200">
                                            {related.linked.map((item: any, idx: number) => (
                                                <tr key={idx} className="hover:bg-gray-50">
                                                    <td className="px-4 py-3 text-sm">
                                                        <div className="flex items-center gap-2">
                                                            <span className="text-lg">{item.entity_type === 'physical_person' ? '👤' : '🏢'}</span>
                                                            {item.regcode ? (
                                                                <Link href={`/company/${item.regcode}`} className="text-primary hover:underline font-medium">
                                                                    {item.name}
                                                                </Link>
                                                            ) : (
                                                                <span className="text-gray-900">
                                                                    {item.name}
                                                                    {item.entity_type === 'legal_entity' && <span className="text-gray-400 text-xs ml-1">(ārvalstu)</span>}
                                                                </span>
                                                            )}
                                                        </div>
                                                    </td>
                                                    <td className="px-4 py-3 text-center">
                                                        <span className={`text-xs px-2 py-1 rounded-full font-medium ${item.entity_type === 'physical_person'
                                                            ? 'bg-purple-100 text-purple-700'
                                                            : item.relation === 'owner'
                                                                ? 'bg-purple-100 text-purple-700'
                                                                : 'bg-blue-100 text-blue-700'
                                                            }`}>
                                                            {item.entity_type === 'physical_person'
                                                                ? 'Fiziska persona'
                                                                : item.relation === 'owner' ? 'Mātes' : 'Meitas'}
                                                        </span>
                                                    </td>
                                                    <td className="px-4 py-3 text-sm text-right font-bold text-red-600">{item.ownership_percent}%</td>
                                                    {item.entity_type === 'physical_person' ? (
                                                        <td colSpan={3} className="px-4 py-3 text-sm text-center text-gray-400 italic bg-gray-50">Nav attiecināms</td>
                                                    ) : (
                                                        <>
                                                            <td className="px-4 py-3 text-sm text-right text-gray-600">{item.employees || '-'}</td>
                                                            <td className="px-4 py-3 text-sm text-right text-gray-600">{item.turnover ? `${(item.turnover / 1000).toLocaleString('lv-LV')} k€` : '-'}</td>
                                                            <td className="px-4 py-3 text-sm text-right text-gray-600">{item.balance ? `${(item.balance / 1000).toLocaleString('lv-LV')} k€` : '-'}</td>
                                                        </>
                                                    )}
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}

                        {/* PARTNER Companies Table (25-50%) */}
                        {related?.partners && related.partners.length > 0 && (
                            <div>
                                <h4 className="text-md font-semibold text-gray-700 mb-3 flex items-center gap-2">
                                    <span className="w-6 h-6 rounded-full bg-yellow-100 flex items-center justify-center text-yellow-600 text-sm">🤝</span>
                                    Partnerkomercsabiedrības (25-50% kapitāldaļu)
                                </h4>
                                <div className="border border-gray-200 rounded-lg overflow-hidden">
                                    <table className="w-full">
                                        <thead className="bg-yellow-50 border-b border-gray-200">
                                            <tr>
                                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Uzņēmums</th>
                                                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Tips</th>
                                                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">%</th>
                                                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Darbinieki</th>
                                                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Apgrozījums</th>
                                                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Bilance</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-200">
                                            {related.partners.map((item: any, idx: number) => (
                                                <tr key={idx} className="hover:bg-gray-50">
                                                    <td className="px-4 py-3 text-sm">
                                                        <div className="flex items-center gap-2">
                                                            <span className="text-lg">{item.entity_type === 'physical_person' ? '👤' : '🏢'}</span>
                                                            {item.regcode ? (
                                                                <Link href={`/company/${item.regcode}`} className="text-primary hover:underline font-medium">
                                                                    {item.name}
                                                                </Link>
                                                            ) : (
                                                                <span className="text-gray-900">
                                                                    {item.name}
                                                                    {item.entity_type === 'legal_entity' && <span className="text-gray-400 text-xs ml-1">(ārvalstu)</span>}
                                                                </span>
                                                            )}
                                                        </div>
                                                    </td>
                                                    <td className="px-4 py-3 text-center">
                                                        <span className={`text-xs px-2 py-1 rounded-full font-medium ${item.entity_type === 'physical_person'
                                                            ? 'bg-purple-100 text-purple-700'
                                                            : item.relation === 'owner'
                                                                ? 'bg-yellow-100 text-yellow-700'
                                                                : 'bg-blue-100 text-blue-700'
                                                            }`}>
                                                            {item.entity_type === 'physical_person'
                                                                ? 'Fiziska persona'
                                                                : item.relation === 'owner' ? 'Dalībnieks' : 'Meitas'}
                                                        </span>
                                                    </td>
                                                    <td className="px-4 py-3 text-sm text-right font-semibold text-yellow-600">{item.ownership_percent}%</td>
                                                    {item.entity_type === 'physical_person' ? (
                                                        <td colSpan={3} className="px-4 py-3 text-sm text-center text-gray-400 italic bg-gray-50">Nav attiecināms</td>
                                                    ) : (
                                                        <>
                                                            <td className="px-4 py-3 text-sm text-right text-gray-600">{item.employees || '-'}</td>
                                                            <td className="px-4 py-3 text-sm text-right text-gray-600">{item.turnover ? `${(item.turnover / 1000).toLocaleString('lv-LV')} k€` : '-'}</td>
                                                            <td className="px-4 py-3 text-sm text-right text-gray-600">{item.balance ? `${(item.balance / 1000).toLocaleString('lv-LV')} k€` : '-'}</td>
                                                        </>
                                                    )}
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}

                        {/* Capital Info */}
                        {(related?.status === 'PARTNER' || related?.status === 'LINKED') && related?.total_capital > 0 && (
                            <div className="text-center text-sm text-gray-500 pt-4 border-t border-gray-200">
                                Pamatkapitāls: <span className="font-semibold">{related.total_capital.toLocaleString('lv-LV')} EUR</span>
                            </div>
                        )}
                    </div>
                )}

                {/* PROCUREMENTS TAB */}
                {activeTab === "procurements" && (
                    <div className="space-y-6">
                        {/* Header */}
                        <div className="flex items-center justify-between">
                            <div>
                                <h3 className="text-lg font-semibold text-gray-900">Valsts Iepirkumi</h3>
                                <p className="text-sm text-gray-500 mt-1">Parāda 10 jaunākos uzvarētos iepirkumus (periods: 2018-2025)</p>
                            </div>
                        </div>

                        {company.procurements && company.procurements.length > 0 ? (
                            <>
                                {/* KPI Cards */}
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    {/* Total Amount Card */}
                                    <div className="bg-gradient-to-br from-emerald-50 to-green-50 border border-green-200 rounded-lg p-5">
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm font-medium text-green-700">Uzvarēto iepirkumu summa</span>
                                            <span className="text-2xl">💰</span>
                                        </div>
                                        <p className="text-3xl font-bold text-green-700 mt-2">
                                            {formatCurrency(company.procurements.reduce((sum: number, p: any) => sum + (p.amount || 0), 0))}
                                        </p>
                                    </div>

                                    {/* Contract Count Card */}
                                    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-5">
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm font-medium text-blue-700">Līgumu skaits</span>
                                            <span className="text-2xl">📄</span>
                                        </div>
                                        <p className="text-3xl font-bold text-blue-700 mt-2">
                                            {company.procurements.length}
                                        </p>
                                    </div>

                                    {/* Top Buyer Card */}
                                    <div className="bg-gradient-to-br from-purple-50 to-violet-50 border border-purple-200 rounded-lg p-5">
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm font-medium text-purple-700">Lielākais pasūtītājs</span>
                                            <span className="text-2xl">🏢</span>
                                        </div>
                                        <p className="text-lg font-bold text-purple-700 mt-2 line-clamp-2">
                                            {(() => {
                                                const byAuthority = company.procurements.reduce((acc: any, p: any) => {
                                                    const auth = p.authority || 'Nav norādīts';
                                                    acc[auth] = (acc[auth] || 0) + (p.amount || 0);
                                                    return acc;
                                                }, {});
                                                const topAuth = Object.entries(byAuthority).sort((a: any, b: any) => b[1] - a[1])[0];
                                                return topAuth ? topAuth[0] : '-';
                                            })()}
                                        </p>
                                    </div>
                                </div>

                                {/* Blurred Analytics Teaser - Upsell */}
                                <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
                                    <h4 className="text-md font-semibold text-gray-700 mb-4">🔒 Detalizētā Analītika</h4>
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                        <div className="relative bg-white border border-gray-200 rounded-lg p-4 overflow-hidden">
                                            <div className="filter blur-sm pointer-events-none">
                                                <span className="text-xs text-gray-500">Uzvaru rādītājs</span>
                                                <p className="text-2xl font-bold text-gray-800">67%</p>
                                            </div>
                                            <div className="absolute inset-0 bg-white/70 flex items-center justify-center">
                                                <span className="text-sm font-medium text-gray-600">🔒 Pro</span>
                                            </div>
                                        </div>
                                        <div className="relative bg-white border border-gray-200 rounded-lg p-4 overflow-hidden">
                                            <div className="filter blur-sm pointer-events-none">
                                                <span className="text-xs text-gray-500">Galvenie konkurenti</span>
                                                <p className="text-lg font-bold text-gray-800">3 uzņēmumi</p>
                                            </div>
                                            <div className="absolute inset-0 bg-white/70 flex items-center justify-center">
                                                <span className="text-sm font-medium text-gray-600">🔒 Pro</span>
                                            </div>
                                        </div>
                                        <div className="relative bg-white border border-gray-200 rounded-lg p-4 overflow-hidden">
                                            <div className="filter blur-sm pointer-events-none">
                                                <span className="text-xs text-gray-500">Vidējā cenu nobīde</span>
                                                <p className="text-2xl font-bold text-gray-800">-12%</p>
                                            </div>
                                            <div className="absolute inset-0 bg-white/70 flex items-center justify-center">
                                                <span className="text-sm font-medium text-gray-600">🔒 Pro</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Recent Contracts Table */}
                                <div>
                                    <h4 className="text-md font-semibold text-gray-700 mb-3">Pēdējie uzvarētie iepirkumi</h4>
                                    <div className="border border-gray-200 rounded-lg overflow-hidden">
                                        <table className="w-full">
                                            <thead className="bg-gray-50 border-b border-gray-200">
                                                <tr>
                                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Pasūtītājs</th>
                                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Priekšmets</th>
                                                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Summa</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-gray-200">
                                                {company.procurements.slice(0, 5).map((proc: any, idx: number) => (
                                                    <tr key={idx} className="hover:bg-gray-50">
                                                        <td className="px-4 py-3 text-sm text-gray-900">{proc.authority}</td>
                                                        <td className="px-4 py-3 text-sm text-gray-600 max-w-xs truncate">{proc.subject}</td>
                                                        <td className="px-4 py-3 text-sm text-right font-semibold text-success">{formatCurrency(proc.amount)}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>

                                {/* CTA Button */}
                                <div className="bg-gradient-to-r from-primary to-accent rounded-lg p-6 text-center">
                                    <p className="text-white text-lg font-medium mb-3">
                                        Vēlies redzēt, kuros konkursos {company.name.split('"')[1] || company.name} zaudēja un kas ir viņu sīvākie konkurenti?
                                    </p>
                                    <a
                                        href={`https://www.iepirkumi.animas.lv/${company.regcode}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="inline-flex items-center gap-2 px-6 py-3 bg-white text-primary font-bold rounded-lg hover:bg-gray-100 transition-colors shadow-lg"
                                    >
                                        <span>🚀</span>
                                        Atvērt Pilno Iepirkumu Analītiku
                                    </a>
                                    <p className="text-white/80 text-sm mt-3">
                                        Salīdzini uzņēmumus, atrodi apakšuzņēmēju ķēdes un prognozē nākamos uzvarētājus
                                    </p>
                                </div>
                            </>
                        ) : (
                            <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
                                <span className="text-4xl">📋</span>
                                <h3 className="mt-4 text-lg font-semibold text-gray-900">Nav iepirkumu datu</h3>
                                <p className="mt-2 text-sm text-gray-500 max-w-md mx-auto">
                                    Šim uzņēmumam nav reģistrēti valsts iepirkumi vai dati vēl nav pieejami.
                                </p>
                                <a
                                    href={`https://www.iepirkumi.animas.lv/${company.regcode}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-2 mt-4 px-4 py-2 text-sm font-medium text-white bg-primary hover:bg-primary/90 rounded-lg transition-colors"
                                >
                                    Pārbaudīt Iepirkumu platformā
                                </a>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
