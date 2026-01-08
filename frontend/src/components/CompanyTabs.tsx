"use client";

import { useState, useEffect } from "react";
import { Link } from "@/i18n/routing";
import GaugeChart from './GaugeChart';
import RisksTab from './RisksTab';
import CompanySizeBadge from './CompanySizeBadge';
import { parseBirthDateFromPersonCode } from '../utils/parseBirthDate';
import { generatePersonUrlSync } from '../utils/personUrl';
import { useTranslations } from "next-intl";
import TeaserOverlay from './TeaserOverlay';
import { RatingBadge } from './RatingBadge';
import { Sparkline } from './Sparkline';
import { GrowthIndicator } from './GrowthIndicator';

// Helper function for formatting currency
const formatCurrency = (value: number | null | undefined, decimals = 0) => {
    if (value === null || value === undefined) return "-";
    return `€ ${value.toLocaleString('lv-LV', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}`;
};

// ... existing components ...

export default function CompanyTabs({
    company: initialCompany,
    related: initialRelated,
    competitors: initialCompetitors = [],
    benchmark: initialBenchmark = null
}: {
    company: any,
    related: any,
    competitors?: any[],
    benchmark?: any
}) {
    const t = useTranslations('CompanyTabs');
    const [company, setCompany] = useState(initialCompany);
    const [related, setRelated] = useState(initialRelated);
    const [competitors, setCompetitors] = useState<any[]>(initialCompetitors);
    const [benchmark, setBenchmark] = useState(initialBenchmark);
    const [activeTab, setActiveTab] = useState<string>("overview");

    // Lazy loading state
    const [isLoadingDetails, setIsLoadingDetails] = useState(false);

    useEffect(() => {
        // If we only have "quick" data (missing financial hash/history), fetch the rest
        if (!company.financial_history || company.financial_history.length === 0) {
            const fetchDetails = async () => {
                setIsLoadingDetails(true);
                const API_BASE_URL = '/api';
                try {
                    const headers = { 'Content-Type': 'application/json' };

                    // parallel fetch
                    const [finHistoryRes, personsRes, risksRes, graphRes, benchRes, compRes] = await Promise.all([
                        fetch(`${API_BASE_URL}/companies/${company.regcode}/financial-history`, { headers }),
                        fetch(`${API_BASE_URL}/companies/${company.regcode}/persons`, { headers }),
                        fetch(`${API_BASE_URL}/companies/${company.regcode}/risks`, { headers }),
                        fetch(`${API_BASE_URL}/companies/${company.regcode}/graph`, { headers }),
                        fetch(`${API_BASE_URL}/companies/${company.regcode}/benchmark`, { headers }),
                        fetch(`${API_BASE_URL}/companies/${company.regcode}/competitors`, { headers })
                    ]);

                    const [finData, personsData, risksData, graphData, benchData, compData] = await Promise.all([
                        finHistoryRes.ok ? (await finHistoryRes.json()) || [] : [],
                        personsRes.ok ? personsRes.json() : { officers: [], members: [], ubos: [] },
                        risksRes.ok ? risksRes.json() : {},
                        graphRes.ok ? graphRes.json() : { parents: [], children: [], related: { linked: [], partners: [] } },
                        benchRes.ok ? benchRes.json() : null,
                        compRes.ok ? compRes.json() : []
                    ]);

                    // Update company state with new data
                    setCompany((prev: any) => ({
                        ...prev,
                        financial_history: finData,
                        officers: personsData.officers,
                        members: personsData.members,
                        ubos: personsData.ubos,
                        risk_level: (risksData as any).risk_level || prev.risk_level,
                        // Merge any other missing fields if necessary
                    }));

                    setRelated(graphData);
                    setBenchmark(benchData);
                    setCompetitors(compData);

                } catch (error) {
                    console.error("Failed to lazy load company details:", error);
                } finally {
                    setIsLoadingDetails(false);
                }
            };

            fetchDetails();
        }
    }, [company.regcode]);

    const signatories = (company.officers || []).filter((o: any) =>
        o.rights_of_representation === 'INDIVIDUALLY' ||
        o.position === 'CHAIR_OF_BOARD' ||
        o.position === 'PROCURATOR'
    );

    const [selectedSignatory, setSelectedSignatory] = useState<string>(
        signatories.length > 0 ? signatories[0].name : ""
    );

    // Update selected signatory when officers data arrives
    useEffect(() => {
        if (signatories.length > 0 && !selectedSignatory) {
            setSelectedSignatory(signatories[0].name);
        }
    }, [company.officers]);

    const [copied, setCopied] = useState(false);
    const [chartMode, setChartMode] = useState<'turnover' | 'profit'>('turnover');

    // Access Check
    // Default to true if property is missing (backward compatibility), but backend sends it.
    const hasAccess = company.has_full_access !== false;

    // Restricted tabs list
    const restrictedTabs = ['finances', 'management', 'risks', 'related'];

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


    // Copy requisites to clipboard
    const copyRequisites = () => {
        const signatory = signatories.find((s: any) => s.name === selectedSignatory);
        const positionText = signatory ? (positionLabels[signatory.position] || signatory.position) : '';
        const text = `${company.name}
${t('legal_address')}: ${company.address || '-'}
${t('reg_no_short', { defaultMessage: 'Reģ. Nr.' })}: ${company.regcode}
${signatory ? `${t('signing_person')}: ${signatory.name}, ${positionText}` : ''}`;

        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };
    const tabs = [
        { id: "overview", label: t('overview') },
        { id: "finances", label: t('finances'), badge: company.rating?.grade, restricted: true },
        { id: "risks", label: t('risks'), badge: company.risk_level !== 'NONE' ? company.risk_level : null, restricted: true },
        { id: "management", label: t('management'), restricted: true },
        { id: "related", label: t('related'), restricted: true },
        { id: "procurements", label: t('procurements') },
    ];

    const financialHistory = company.financial_history || [];
    const latest = financialHistory[0] || {};
    // ... (rest of helpers like getContractStatus, calculateProgress, getDaysRemaining, procurementStats, formatPercent, formatRatio)
    // Need to include them because I'm replacing the start of the function.

    // Procurement Helpers
    const getContractStatus = (p: any) => {
        if (p.termination_date) return 'ENDED';
        if (!p.end_date) return 'ACTIVE';
        const end = new Date(p.end_date);
        const now = new Date();
        const warningDate = new Date();
        warningDate.setMonth(now.getMonth() + 9);
        if (end < now) return 'ENDED';
        if (end <= warningDate) return 'EXPIRING';
        return 'ACTIVE';
    };

    const calculateProgress = (startStr: string, endStr: string) => {
        if (!startStr || !endStr) return 0;
        const start = new Date(startStr).getTime();
        const end = new Date(endStr).getTime();
        const now = new Date().getTime();
        if (now >= end) return 100;
        if (now <= start) return 0;
        const total = end - start;
        const elapsed = now - start;
        return Math.min(Math.round((elapsed / total) * 100), 100);
    };

    const getDaysRemaining = (endStr: string) => {
        if (!endStr) return null;
        const end = new Date(endStr).getTime();
        const now = new Date().getTime();
        const diff = end - now;
        if (diff < 0) return 0;
        return Math.ceil(diff / (1000 * 60 * 60 * 24));
    };

    // Calculate Procurement KPIs
    const procurementStats = (() => {
        const procs = company.procurements || [];
        const active = procs.filter((p: any) => {
            const status = getContractStatus(p);
            return status === 'ACTIVE' || status === 'EXPIRING';
        });
        const expiring = active.filter((p: any) => getContractStatus(p) === 'EXPIRING');
        const activeValue = active.reduce((sum: number, p: any) => sum + (p.amount || 0), 0);
        return {
            activeCount: active.length,
            expiringCount: expiring.length,
            activeValue: activeValue,
            expiring: expiring
        };
    })();

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
                            {/* Lock Icon for restricted tabs */}
                            {/* @ts-ignore */}
                            {tab.restricted && !hasAccess && (
                                <svg className="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                                </svg>
                            )}
                            {tab.badge && <span className="px-1.5 py-0.5 text-xs font-bold bg-success/10 text-success rounded">{tab.badge}</span>}
                        </button>
                    ))}
                </nav>
            </div>

            <div className="mt-0 bg-white rounded-b-lg shadow-card p-6">


                {restrictedTabs.includes(activeTab) && !hasAccess ? (
                    <TeaserOverlay />
                ) : (
                    <>
                        {/* OVERVIEW TAB */}
                        {activeTab === "overview" && (
                            <div className="space-y-6">
                                {/* Copyable Requisites Section */}
                                <div className="border border-gray-200 rounded-lg p-5 bg-gray-50">
                                    <div className="flex items-center justify-between mb-4">
                                        <div className="space-y-1">
                                            <div className="text-sm text-gray-600">
                                                <span className="font-bold text-gray-900">
                                                    {company.name_in_quotes && company.type ? `${company.name_in_quotes}, ${company.type}` : company.name}
                                                </span>, {t('reg_no_short', { defaultMessage: 'Reģ. Nr.' })} <span className="font-semibold">{company.regcode}</span>
                                            </div>
                                            {company.name_in_quotes && company.type && (
                                                <div className="text-xs text-gray-500">
                                                    {t('full_name')}: {company.name}
                                                </div>
                                            )}
                                            <div className="text-sm text-gray-500">
                                                {t('legal_address')}: {company.address || '-'}, LV-{company.address?.match(/LV-(\d+)/)?.[1] || '1001'}
                                            </div>
                                        </div>
                                        <button
                                            onClick={copyRequisites}
                                            className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${copied
                                                ? 'bg-success text-white'
                                                : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                                                }`}
                                        >
                                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                            </svg>
                                            {copied ? t('copied') : t('copy_details')}
                                        </button>
                                    </div>

                                    {/* Signatory Dropdown - Hidden but included for copy function */}
                                    {signatories.length > 0 && (
                                        <div className="flex items-center gap-2 text-sm">
                                            <span className="text-gray-600">{t('signing_person')}:</span>
                                            <select
                                                value={selectedSignatory}
                                                onChange={(e) => setSelectedSignatory(e.target.value)}
                                                className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-primary bg-white"
                                            >
                                                {signatories.map((s: any, idx: number) => (
                                                    <option key={idx} value={s.name}>
                                                        {s.name} ({positionLabels[s.position] || s.position})
                                                    </option>
                                                ))}
                                            </select>
                                        </div>
                                    )}
                                </div>

                                {/* KPI Cards Row */}
                                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                                    {/* Apgrozījums */}
                                    <div className="border border-gray-200 rounded-lg p-4 bg-white">
                                        <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">
                                            {t('turnover')} '{String(company.finances?.year || 23).slice(-2)}
                                        </div>
                                        <div className="text-2xl font-bold text-gray-900">
                                            {company.finances?.turnover
                                                ? (company.finances.turnover >= 1000000
                                                    ? `${(company.finances.turnover / 1000000).toFixed(1)} M€`
                                                    : `${(company.finances.turnover / 1000).toFixed(0)} k€`)
                                                : 'N/A'}
                                        </div>
                                        {company.finances?.turnover_growth !== null && company.finances?.turnover_growth !== undefined && (
                                            <div className={`text-sm font-medium ${company.finances.turnover_growth >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                                                {company.finances.turnover_growth >= 0 ? '▲' : '▼'} {Math.abs(company.finances.turnover_growth).toFixed(1)}%
                                            </div>
                                        )}
                                    </div>

                                    {/* Peļņa */}
                                    <div className="border border-gray-200 rounded-lg p-4 bg-white">
                                        <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">
                                            {t('profit')} '{String(company.finances?.year || 23).slice(-2)}
                                        </div>
                                        <div className={`text-2xl font-bold ${(company.finances?.profit || 0) >= 0 ? 'text-gray-900' : 'text-red-600'}`}>
                                            {company.finances?.profit
                                                ? (Math.abs(company.finances.profit) >= 1000000
                                                    ? `${(company.finances.profit / 1000000).toFixed(1)} M€`
                                                    : `${(company.finances.profit / 1000).toFixed(0)} k€`)
                                                : 'N/A'}
                                        </div>
                                        {company.finances?.profit_growth !== null && company.finances?.profit_growth !== undefined && (
                                            <div className={`text-sm font-medium ${company.finances.profit_growth >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                                                {company.finances.profit_growth >= 0 ? '▲' : '▼'} {Math.abs(company.finances.profit_growth).toFixed(0)}%
                                            </div>
                                        )}
                                    </div>

                                    {/* Darbinieki */}
                                    <div className="border border-gray-200 rounded-lg p-4 bg-white">
                                        <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">
                                            {t('employees')}
                                        </div>
                                        <div className="text-2xl font-bold text-gray-900">
                                            {company.finances?.employees || company.employee_count || 'N/A'}
                                        </div>
                                        {/* Employee change from previous year */}
                                        {financialHistory.length >= 2 && financialHistory[1]?.employees && (
                                            <div className={`text-sm font-medium ${(company.finances?.employees || 0) >= (financialHistory[1]?.employees || 0)
                                                ? 'text-emerald-600' : 'text-red-600'
                                                }`}>
                                                {(company.finances?.employees || 0) >= (financialHistory[1]?.employees || 0) ? '▲' : '▼'} {
                                                    Math.abs((company.finances?.employees || 0) - (financialHistory[1]?.employees || 0))
                                                }
                                            </div>
                                        )}
                                    </div>

                                    {/* Vid. Bruto Alga */}
                                    <div className="border border-gray-200 rounded-lg p-4 bg-white">
                                        <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">
                                            {t('avg_salary')}
                                        </div>
                                        <div className="text-2xl font-bold text-gray-900">
                                            {company.tax_history?.[0]?.avg_gross_salary
                                                ? `${Math.round(company.tax_history[0].avg_gross_salary).toLocaleString('lv-LV')} €`
                                                : 'N/A'}
                                        </div>
                                        <div className="text-xs text-gray-500">
                                            {company.tax_history?.[0]?.avg_gross_salary && company.nace_text
                                                ? t('vs_industry')
                                                : ''}
                                        </div>
                                    </div>

                                    {/* VID Reitings */}
                                    <div className={`rounded-lg p-4 ${company.rating?.grade === 'A' ? 'bg-emerald-500 text-white' :
                                        company.rating?.grade === 'B' ? 'bg-yellow-500 text-white' :
                                            company.rating?.grade === 'C' ? 'bg-orange-500 text-white' :
                                                company.rating?.grade === 'D' ? 'bg-red-500 text-white' :
                                                    'bg-gray-100 text-gray-700'
                                        }`}>
                                        <div className="text-xs uppercase tracking-wide mb-1 opacity-80">
                                            {t('vid_rating')}
                                        </div>
                                        <div className="text-2xl font-bold">
                                            <div className="text-2xl font-bold">
                                                {company.rating?.grade ? `${company.rating.grade} ${t('class')}` : t('no_data')}
                                            </div>
                                            <div className="text-sm opacity-80">
                                                {company.rating?.grade === 'A' ? t('low_risk') :
                                                    company.rating?.grade === 'B' ? t('medium_risk') :
                                                        company.rating?.grade === 'C' ? t('high_risk') :
                                                            company.rating?.grade === 'D' ? t('very_high_risk') : ''}
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Two Column Layout: Chart + Market Position */}
                                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                    {/* Finanšu Dinamika Chart - 2 columns */}
                                    <div className="lg:col-span-2 border border-gray-200 rounded-lg p-5 bg-white">
                                        <div className="flex items-center justify-between mb-4">
                                            <h3 className="text-lg font-semibold text-gray-900">{t('financial_dynamic')}</h3>
                                            <div className="flex gap-1">
                                                <button
                                                    onClick={() => setChartMode('turnover')}
                                                    className={`px-3 py-1 text-sm rounded-full transition-colors ${chartMode === 'turnover'
                                                        ? 'bg-violet-100 text-violet-700 font-medium'
                                                        : 'bg-gray-50 text-gray-500 hover:bg-gray-100'
                                                        }`}
                                                >
                                                    {t('turnover')}
                                                </button>
                                                <button
                                                    onClick={() => setChartMode('profit')}
                                                    className={`px-3 py-1 text-sm rounded-full transition-colors ${chartMode === 'profit'
                                                        ? 'bg-emerald-100 text-emerald-700 font-medium'
                                                        : 'bg-gray-50 text-gray-500 hover:bg-gray-100'
                                                        }`}
                                                >
                                                    {t('profit')}
                                                </button>
                                            </div>
                                        </div>

                                        {financialHistory.length > 0 ? (
                                            <div className="h-64 flex items-end gap-3 px-4">
                                                {(company.financial_history || []).slice(0, 5).reverse().map((f: any, idx: number) => {
                                                    const dataKey = chartMode === 'turnover' ? 'turnover' : 'profit';
                                                    const values = (company.financial_history || []).slice(0, 5).map((x: any) => Math.abs(x[dataKey] || 0));
                                                    const maxValue = Math.max(...values, 1);
                                                    const value = f[dataKey] || 0;
                                                    const barHeight = Math.abs(value) ? (Math.abs(value) / maxValue) * 200 : 8;
                                                    const isLatest = idx === (company.financial_history || []).slice(0, 5).length - 1;
                                                    const isNegative = value < 0;
                                                    const barColor = chartMode === 'profit'
                                                        ? (isNegative ? 'bg-red-400 hover:bg-red-500' : (isLatest ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-emerald-300 hover:bg-emerald-400'))
                                                        : (isLatest ? 'bg-violet-600 hover:bg-violet-700' : 'bg-violet-300 hover:bg-violet-400');

                                                    return (
                                                        <div key={f.year} className="flex-1 flex flex-col items-center group relative h-full justify-end">
                                                            <div
                                                                className={`w-full rounded-t-lg transition-all cursor-pointer ${barColor}`}
                                                                style={{ height: `${Math.max(barHeight, 8)}px` }}
                                                            >
                                                                {/* Tooltip */}
                                                                <div className="absolute -top-12 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-xs px-3 py-1.5 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-20">
                                                                    <div className="font-semibold">{f.year}</div>
                                                                    <div className={isNegative ? 'text-red-300' : ''}>{formatCurrency(value)}</div>
                                                                </div>
                                                            </div>
                                                            <div className="mt-2 text-sm text-gray-600">{f.year}</div>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        ) : (
                                            <div className="h-64 flex items-center justify-center text-gray-500">
                                                {t('no_data')}
                                            </div>
                                        )}
                                    </div>

                                    {/* Tirgus Pozīcija - 1 column */}
                                    <div className="border border-gray-200 rounded-lg p-5 bg-white">
                                        <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('market_position')}</h3>

                                        <div className="space-y-4">
                                            <div className="flex justify-between items-center">
                                                <span className="text-sm text-gray-500">{t('industry')}</span>
                                                <span className="text-sm font-medium text-gray-900 text-right max-w-[180px] truncate">{company.nace_text || company.nace_section_text || t('no_data')}</span>
                                            </div>

                                            <div className="flex justify-between items-center">
                                                <span className="text-sm text-gray-500">{t('size')}</span>
                                                <CompanySizeBadge size={company.company_size} />
                                            </div>

                                            <div className="flex justify-between items-center">
                                                <span className="text-sm text-gray-500">{t('top_rank')}</span>
                                                <span className="text-sm font-bold text-emerald-600">
                                                    {benchmark?.percentiles?.turnover ? `TOP ${benchmark.percentiles.turnover}%` :
                                                        company.finances?.turnover && company.finances.turnover > 10000000 ? 'TOP 5%' :
                                                            company.finances?.turnover && company.finances.turnover > 1000000 ? 'TOP 15%' :
                                                                company.finances?.turnover && company.finances.turnover > 100000 ? 'TOP 40%' : 'N/A'}
                                                </span>
                                            </div>

                                            <div className="pt-3 border-t border-gray-100">
                                                <div className="text-xs text-gray-400 uppercase tracking-wide mb-2">{t('closest_competitors')}</div>
                                                {isLoadingDetails ? (
                                                    <div className="space-y-2 animate-pulse">
                                                        <div className="h-6 bg-gray-100 rounded"></div>
                                                        <div className="h-6 bg-gray-100 rounded"></div>
                                                        <div className="h-6 bg-gray-100 rounded"></div>
                                                    </div>
                                                ) : competitors && competitors.length > 0 ? (
                                                    <div className="space-y-2">
                                                        {competitors.slice(0, 3).map((comp: any, idx: number) => (
                                                            <Link
                                                                key={comp.regcode}
                                                                href={`/company/${comp.regcode}`}
                                                                className="flex justify-between items-center text-sm hover:bg-gray-50 rounded px-1 -mx-1 py-0.5 transition-colors"
                                                            >
                                                                <span className="text-gray-700 hover:text-primary">#{idx + 1} {comp.name}</span>
                                                                <span className="text-gray-500 font-medium">
                                                                    {comp.turnover >= 1000000
                                                                        ? `${(comp.turnover / 1000000).toFixed(1)} M€`
                                                                        : `${Math.round(comp.turnover / 1000)} k€`}
                                                                </span>
                                                            </Link>
                                                        ))}
                                                    </div>
                                                ) : (
                                                    <div className="text-sm text-gray-500 italic">{t('no_data')}</div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Amatpersonas & Īpašnieki Table */}
                                <div className="border border-gray-200 rounded-lg p-5 bg-white">
                                    <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('officers_owners')}</h3>

                                    <div className="overflow-x-auto">
                                        <table className="min-w-full">
                                            <thead>
                                                <tr className="border-b border-gray-100">
                                                    <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wide pb-3">{t('name_surname')}</th>
                                                    <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wide pb-3">{t('position')}</th>
                                                    <th className="text-right text-xs font-medium text-gray-500 uppercase tracking-wide pb-3">{t('since')}</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-gray-50">
                                                {isLoadingDetails ? (
                                                    // Skeleton rows
                                                    [1, 2, 3].map((i) => (
                                                        <tr key={`skeleton-${i}`} className="animate-pulse">
                                                            <td className="py-3"><div className="h-4 bg-gray-100 rounded w-32"></div></td>
                                                            <td className="py-3"><div className="h-4 bg-gray-100 rounded w-24"></div></td>
                                                            <td className="py-3"><div className="h-4 bg-gray-100 rounded w-16 ml-auto"></div></td>
                                                        </tr>
                                                    ))
                                                ) : (
                                                    <>
                                                        {/* Officers first */}
                                                        {(company.officers || []).slice(0, 5).map((officer: any, idx: number) => (
                                                            <tr key={`officer-${idx}`} className="hover:bg-gray-50">
                                                                <td className="py-3 text-sm font-medium">
                                                                    <Link
                                                                        href={generatePersonUrlSync(officer.person_code, officer.name, officer.birth_date)}
                                                                        className="text-primary hover:underline"
                                                                        prefetch={false}
                                                                    >
                                                                        {officer.name}
                                                                    </Link>
                                                                </td>
                                                                <td className="py-3 text-sm text-gray-600">
                                                                    {positionLabels[officer.position] || officer.position}
                                                                    {officer.rights_of_representation === 'INDIVIDUALLY' && (
                                                                        <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700">
                                                                            {t('signing_rights')}
                                                                        </span>
                                                                    )}
                                                                </td>
                                                                <td className="py-3 text-sm text-gray-500 text-right">{officer.registered_on || '-'}</td>
                                                            </tr>
                                                        ))}
                                                        {/* Members/Shareholders */}
                                                        {(company.members || []).slice(0, 3).map((member: any, idx: number) => (
                                                            <tr key={`member-${idx}`} className="hover:bg-gray-50">
                                                                <td className="py-3 text-sm font-medium">
                                                                    {member.legal_entity_regcode ? (
                                                                        // If it's a legal entity, link to company
                                                                        <a href={`/company/${member.legal_entity_regcode}`} className="text-primary hover:underline flex items-center gap-1">
                                                                            {member.name}
                                                                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                                                                        </a>
                                                                    ) : (
                                                                        // If it's a person, link to person profile
                                                                        <Link
                                                                            href={generatePersonUrlSync(member.person_code, member.name, member.birth_date)}
                                                                            className="text-primary hover:underline"
                                                                            prefetch={false}
                                                                        >
                                                                            {member.name}
                                                                        </Link>
                                                                    )}
                                                                </td>
                                                                <td className="py-3 text-sm text-gray-600">
                                                                    {t('member')} ({member.percent || 0}%)
                                                                </td>
                                                                <td className="py-3 text-sm text-gray-500 text-right">{member.date_from || '-'}</td>
                                                            </tr>
                                                        ))}
                                                    </>
                                                )}
                                                {(!isLoadingDetails && company.officers?.length === 0 && company.members?.length === 0) && (
                                                    <tr>
                                                        <td colSpan={3} className="py-4 text-center text-sm text-gray-500 italic">{t('no_data')}</td>
                                                    </tr>
                                                )}
                                            </tbody>
                                        </table>
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
                                                    {t('updated')}: {company.rating.date}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Key Gauges */}
                                <div>
                                    <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('financial_health')}</h3>
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                        <GaugeChart
                                            value={latest.current_ratio}
                                            min={0}
                                            max={3}
                                            thresholds={{ good: 1.2, warning: 1.0 }}
                                            label={t('liquidity')}
                                            subtitle="Current Ratio"
                                            format={(v) => v.toFixed(2)}
                                        />

                                        <GaugeChart
                                            value={latest.roe}
                                            min={-20}
                                            max={30}
                                            thresholds={{ good: 10, warning: 5 }}
                                            label="ROE"
                                            subtitle={t('return_on_equity')}
                                            format={(v) => `${v.toFixed(1)}%`}
                                        />

                                        <GaugeChart
                                            value={latest.debt_to_equity}
                                            min={0}
                                            max={3}
                                            thresholds={{ good: 1.0, warning: 2.0 }}
                                            label={t('debt_load')}
                                            subtitle="Debt-to-Equity"
                                            format={(v) => v.toFixed(2)}
                                            invertColors={true}
                                        />
                                    </div>
                                </div>

                                {/* Detailed Metrics Table */}
                                <div className="border border-gray-200 rounded-lg overflow-hidden">
                                    <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                                        <h3 className="text-lg font-semibold text-gray-900">{t('detailed_metrics')}</h3>
                                    </div>
                                    <div className="overflow-x-auto -mx-4 sm:mx-0">
                                        <table className="w-full min-w-[500px]">
                                            <thead className="bg-gray-50 border-b border-gray-200">
                                                <tr>
                                                    <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('metric')}</th>
                                                    <th className="px-3 sm:px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('value')}</th>
                                                    <th className="px-3 sm:px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">{t('trend')}</th>
                                                    <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('norm')}</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-gray-200">
                                                <tr className="bg-blue-50/30">
                                                    <td colSpan={4} className="px-6 py-2 text-sm font-semibold text-gray-700">💧 {t('liquidity')}</td>
                                                </tr>
                                                <tr>
                                                    <td className="px-6 py-3 text-sm text-gray-900">Current Ratio</td>
                                                    <td className="px-6 py-3 text-sm text-right font-semibold">{formatRatio(latest.current_ratio)}</td>
                                                    <td className="px-6 py-3 text-center"><Sparkline data={(company.financial_history || []).slice(0, 5).map((f: any) => f.current_ratio)} /></td>
                                                    <td className="px-6 py-3 text-sm text-gray-600">&gt; 1.2</td>
                                                </tr>
                                                <tr>
                                                    <td className="px-6 py-3 text-sm text-gray-900">Quick Ratio</td>
                                                    <td className="px-6 py-3 text-sm text-right font-semibold">{formatRatio(latest.quick_ratio)}</td>
                                                    <td className="px-6 py-3 text-center"><Sparkline data={(company.financial_history || []).slice(0, 5).map((f: any) => f.quick_ratio)} /></td>
                                                    <td className="px-6 py-3 text-sm text-gray-600">&gt; 0.8</td>
                                                </tr>

                                                <tr className="bg-green-50/30">
                                                    <td colSpan={4} className="px-6 py-2 text-sm font-semibold text-gray-700">💰 {t('profitability')}</td>
                                                </tr>
                                                <tr>
                                                    <td className="px-6 py-3 text-sm text-gray-900">Net Profit Margin</td>
                                                    <td className="px-6 py-3 text-sm text-right font-semibold">{formatPercent(latest.net_profit_margin)}</td>
                                                    <td className="px-6 py-3 text-center"><Sparkline data={(company.financial_history || []).slice(0, 5).map((f: any) => f.net_profit_margin)} /></td>
                                                    <td className="px-6 py-3 text-sm text-gray-600">{t('depends_on_industry')}</td>
                                                </tr>
                                                <tr>
                                                    <td className="px-6 py-3 text-sm text-gray-900">ROE</td>
                                                    <td className="px-6 py-3 text-sm text-right font-semibold">{formatPercent(latest.roe)}</td>
                                                    <td className="px-6 py-3 text-center"><Sparkline data={(company.financial_history || []).slice(0, 5).map((f: any) => f.roe)} /></td>
                                                    <td className="px-6 py-3 text-sm text-gray-600">&gt; 10%</td>
                                                </tr>
                                                <tr>
                                                    <td className="px-6 py-3 text-sm text-gray-900">ROA</td>
                                                    <td className="px-6 py-3 text-sm text-right font-semibold">{formatPercent(latest.roa)}</td>
                                                    <td className="px-6 py-3 text-center"><Sparkline data={(company.financial_history || []).slice(0, 5).map((f: any) => f.roa)} /></td>
                                                    <td className="px-6 py-3 text-sm text-gray-600">&gt; 5%</td>
                                                </tr>

                                                <tr className="bg-orange-50/30">
                                                    <td colSpan={4} className="px-6 py-2 text-sm font-semibold text-gray-700">📈 {t('solvency')}</td>
                                                </tr>
                                                <tr>
                                                    <td className="px-6 py-3 text-sm text-gray-900">Debt-to-Equity</td>
                                                    <td className="px-6 py-3 text-sm text-right font-semibold">{formatRatio(latest.debt_to_equity)}</td>
                                                    <td className="px-6 py-3 text-center"><Sparkline data={(company.financial_history || []).slice(0, 5).map((f: any) => f.debt_to_equity)} /></td>
                                                    <td className="px-6 py-3 text-sm text-gray-600">&lt; 1.5</td>
                                                </tr>

                                                <tr className="bg-purple-50/30">
                                                    <td colSpan={4} className="px-6 py-2 text-sm font-semibold text-gray-700">🚀 {t('cash_flow')}</td>
                                                </tr>
                                                <tr>
                                                    <td className="px-6 py-3 text-sm text-gray-900">EBITDA</td>
                                                    <td className="px-6 py-3 text-sm text-right font-semibold">{formatCurrency(latest.ebitda)}</td>
                                                    <td className="px-6 py-3 text-center"><Sparkline data={(company.financial_history || []).slice(0, 5).map((f: any) => f.ebitda)} /></td>
                                                    <td className="px-6 py-3 text-sm text-gray-600">{t('positive')}</td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>

                                {/* Financial History Table */}
                                <div className="border border-gray-200 rounded-lg overflow-hidden">
                                    <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                                        <h3 className="text-lg font-semibold text-gray-900">{t('financial_history')}</h3>
                                    </div>
                                    {financialHistory.length > 0 ? (
                                        <div className="overflow-x-auto -mx-4 sm:mx-0">
                                            <table className="w-full min-w-[400px]">
                                                <thead className="bg-gray-50 border-b border-gray-200">
                                                    <tr>
                                                        <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('year')}</th>
                                                        <th className="px-3 sm:px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('turnover')}</th>
                                                        <th className="px-3 sm:px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('profit')}</th>
                                                        <th className="px-3 sm:px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('employees')}</th>
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
                                        <div className="p-6 text-center text-gray-500">{t('no_data')}</div>
                                    )}
                                </div>

                                {/* Tax History */}
                                {company.tax_history && company.tax_history.length > 0 && (
                                    <div className="border border-gray-200 rounded-lg overflow-hidden">
                                        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                                            <h3 className="text-lg font-semibold text-gray-900">{t('taxes_paid')}</h3>
                                        </div>
                                        <div className="overflow-x-auto -mx-4 sm:mx-0">
                                            <table className="w-full min-w-[500px]">
                                                <thead className="bg-gray-50 border-b border-gray-200">
                                                    <tr>
                                                        <th className="px-2 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('year')}</th>
                                                        <th className="px-2 sm:px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">IIN</th>
                                                        <th className="px-2 sm:px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">VSAOI</th>
                                                        <th className="px-2 sm:px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase whitespace-nowrap">{t('avg_employees')}</th>
                                                        <th className="px-2 sm:px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase whitespace-nowrap">{t('avg_salary')}</th>
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
                        )
                        }

                        {/* RISKS TAB */}
                        {
                            activeTab === "risks" && (
                                <RisksTab company={company} />
                            )
                        }

                        {/* MANAGEMENT TAB - 3 Sections: UBOs, Members, Officers */}
                        {
                            activeTab === "management" && (
                                <div className="space-y-8">

                                    {/* === 1. PATIESIE LABUMA GUVĒJI (UBOs) === */}
                                    <div>
                                        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                                            <span className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center text-purple-600">👤</span>
                                            {t('ubo')}
                                        </h3>
                                        {company.ubos && company.ubos.length > 0 ? (
                                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                                {company.ubos.map((ubo: any, idx: number) => (
                                                    <div key={idx} className="border border-gray-200 rounded-lg p-4 bg-gradient-to-br from-purple-50 to-white">
                                                        <div className="flex items-start justify-between">
                                                            <Link
                                                                href={generatePersonUrlSync(ubo.person_code, ubo.name, ubo.birth_date)}
                                                                className="font-semibold text-primary hover:underline"
                                                            >
                                                                {ubo.name}
                                                            </Link>
                                                            {ubo.nationality && (
                                                                <span className="text-xs px-2 py-0.5 bg-gray-100 rounded font-medium">
                                                                    {ubo.nationality === 'LV' ? '🇱🇻' : ubo.nationality === 'EE' ? '🇪🇪' : ubo.nationality === 'LT' ? '🇱🇹' : ubo.nationality}
                                                                </span>
                                                            )}
                                                        </div>
                                                        <div className="text-sm text-purple-600 font-medium mt-1">{t('ubo_label')}</div>
                                                        <div className="text-sm text-gray-600 mt-2">
                                                            {(ubo.birth_date || parseBirthDateFromPersonCode(ubo.person_code)) && (
                                                                <div>{t('birth_date')}: {ubo.birth_date ? ubo.birth_date.split('-').reverse().join('.') : parseBirthDateFromPersonCode(ubo.person_code)}</div>
                                                            )}
                                                            {ubo.residence && <div>{t('residence')}: {ubo.residence}</div>}
                                                            {ubo.registered_on && <div>{t('registered')}: {ubo.registered_on}</div>}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        ) : (
                                            <div className="text-center py-8 bg-gray-50 rounded-lg border border-gray-200">
                                                <p className="text-gray-500">{t('no_ubos')}</p>
                                            </div>
                                        )}
                                    </div>

                                    {/* === 2. DALĪBNIEKI (Members/Shareholders) === */}
                                    <div>
                                        <div className="flex items-center justify-between mb-4">
                                            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                                                <span className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600">💼</span>
                                                {t('members_owners_title')}
                                            </h3>
                                            {company.total_capital > 0 && (
                                                <div className="text-sm text-gray-600">
                                                    {t('share_capital')}: <span className="font-semibold">{company.total_capital.toLocaleString('lv-LV')} EUR</span>
                                                </div>
                                            )}
                                        </div>
                                        {company.members && company.members.length > 0 ? (
                                            <div className="border border-gray-200 rounded-lg overflow-hidden">
                                                <table className="w-full">
                                                    <thead className="bg-gray-50 border-b border-gray-200">
                                                        <tr>
                                                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('shareholder')}</th>
                                                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('birth_date')}</th>
                                                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('shares')}</th>
                                                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('value')}</th>
                                                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">%</th>
                                                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('reg_short')}</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody className="divide-y divide-gray-200">
                                                        {company.members.map((member: any, idx: number) => (
                                                            <tr key={idx} className="hover:bg-gray-50">
                                                                <td className="px-4 py-3 text-sm">
                                                                    {member.legal_entity_regcode ? (
                                                                        <Link href={`/company/${member.legal_entity_regcode}`} className="text-primary hover:underline font-medium flex items-center gap-1">
                                                                            {member.name}
                                                                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                                                                        </Link>
                                                                    ) : (
                                                                        <Link
                                                                            href={generatePersonUrlSync(member.person_code, member.name, member.birth_date)}
                                                                            className="text-primary hover:underline font-medium"
                                                                        >
                                                                            {member.name}
                                                                        </Link>
                                                                    )}
                                                                </td>
                                                                <td className="px-4 py-3 text-sm text-gray-600">
                                                                    {member.birth_date
                                                                        ? member.birth_date.split('-').reverse().join('.')
                                                                        : parseBirthDateFromPersonCode(member.person_code) || '-'}
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
                                                <p className="text-gray-500">{t('no_members')}</p>
                                            </div>
                                        )}
                                    </div>

                                    {/* === 3. AMATPERSONAS (Officers) === */}
                                    <div>
                                        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                                            <span className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center text-green-600">✍️</span>
                                            {t('officers_title')}
                                        </h3>
                                        {company.officers && company.officers.length > 0 ? (
                                            <div className="border border-gray-200 rounded-lg overflow-hidden">
                                                <table className="w-full">
                                                    <thead className="bg-gray-50 border-b border-gray-200">
                                                        <tr>
                                                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('position_label')}</th>
                                                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('name_surname')}</th>
                                                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('birth_date')}</th>
                                                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('representation_rights')}</th>
                                                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('appointed')}</th>
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
                                                                    case 'INDIVIDUALLY': return { text: t('rights.individually'), icon: '✅', color: 'text-green-600 bg-green-50' };
                                                                    case 'WITH_ALL': return { text: t('rights.with_all'), icon: '👥', color: 'text-orange-600 bg-orange-50' };
                                                                    case 'WITH_AT_LEAST': return { text: t('rights.with_at_least', { count: officer.representation_with_at_least }), icon: '👥', color: 'text-yellow-600 bg-yellow-50' };
                                                                    default: return { text: '-', icon: '', color: 'text-gray-500' };
                                                                }
                                                            };
                                                            const repr = getRepresentation();

                                                            {/* Helper to display birth date */ }
                                                            const displayBirthDate = (dateStr: string | null | undefined, personCode: string | null | undefined) => {
                                                                if (dateStr) {
                                                                    // Format YYYY-MM-DD to DD.MM.YYYY
                                                                    return dateStr.split('-').reverse().join('.');
                                                                }
                                                                return parseBirthDateFromPersonCode(personCode);
                                                            };

                                                            return (
                                                                <tr key={idx} className="hover:bg-gray-50">
                                                                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{positionLabels[officer.position] || officer.position || '-'}</td>
                                                                    <td className="px-4 py-3 text-sm">
                                                                        <Link
                                                                            href={generatePersonUrlSync(officer.person_code, officer.name, officer.birth_date)}
                                                                            className="text-primary hover:underline font-medium"
                                                                        >
                                                                            {officer.name}
                                                                        </Link>
                                                                    </td>
                                                                    <td className="px-4 py-3 text-sm text-gray-600">{displayBirthDate(officer.birth_date, officer.person_code) || '-'}</td>
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
                                                <p className="text-gray-500">{t('no_officers')}</p>
                                            </div>
                                        )}
                                    </div>

                                </div>
                            )
                        }

                        {/* RELATED COMPANIES TAB - ES MVU Classification */}
                        {
                            activeTab === "related" && (
                                <div className="space-y-6">
                                    {/* Status Header */}
                                    <div className="flex items-center justify-between">
                                        <h3 className="text-lg font-semibold text-gray-900">{t('related_entities_title')}</h3>
                                        <div className={`px-4 py-2 rounded-lg text-sm font-bold ${(related?.status === 'AUTONOMOUS' || !related?.status || related?.status === 'NOT_FOUND') ? 'bg-green-100 text-green-700' :
                                            related?.status === 'PARTNER' ? 'bg-yellow-100 text-yellow-700' :
                                                related?.status === 'LINKED' ? 'bg-red-100 text-red-700' :
                                                    'bg-green-100 text-green-700'
                                            }`}>
                                            {related?.status === 'PARTNER' ? t('status.partners') :
                                                related?.status === 'LINKED' ? t('status.linked') : t('status.autonomous')}
                                        </div>
                                    </div>
                                    {/* AUTONOMOUS Status - Big Display */}
                                    {(related?.status === 'AUTONOMOUS' || !related?.status || related?.status === 'NOT_FOUND') && !related?.linked?.length && !related?.partners?.length && (
                                        <div className="text-center py-12 bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 rounded-lg">
                                            <span className="text-5xl">✅</span>
                                            <h3 className="text-2xl font-bold text-green-700 mt-4">
                                                {t('autonomous_company')}
                                            </h3>
                                            <p className="text-green-600 mt-2 max-w-md mx-auto">
                                                {t('autonomous_desc')}
                                            </p>
                                            {related?.total_capital > 0 && (
                                                <p className="text-sm text-green-500 mt-4">
                                                    {t('share_capital')}: {related.total_capital.toLocaleString('lv-LV')} EUR
                                                </p>
                                            )}
                                        </div>
                                    )}

                                    {/* LINKED Companies Table (>50%) */}
                                    {related?.linked && related.linked.length > 0 && (
                                        <div>
                                            <h4 className="text-md font-semibold text-gray-700 mb-3 flex items-center gap-2">
                                                <span className="w-6 h-6 rounded-full bg-red-100 flex items-center justify-center text-red-600 text-sm">🔗</span>
                                                {t('linked_companies_title')}
                                            </h4>
                                            <div className="border border-gray-200 rounded-lg overflow-hidden">
                                                <table className="w-full">
                                                    <thead className="bg-red-50 border-b border-gray-200">
                                                        <tr>
                                                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('company')}</th>
                                                            <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">{t('type')}</th>
                                                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">%</th>
                                                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('employees')}</th>
                                                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('turnover')}</th>
                                                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('balance')}</th>
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
                                                                            ? t('physical_person')
                                                                            : item.relation === 'owner' ? t('parent') : t('daughter')}
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
                                                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('company')}</th>
                                                            <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">{t('type')}</th>
                                                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">%</th>
                                                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('employees')}</th>
                                                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('turnover')}</th>
                                                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('balance')}</th>
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
                                                                            ? t('physical_person')
                                                                            : item.relation === 'owner' ? t('shareholder') : t('daughter')}
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
                                            {t('share_capital')}: <span className="font-semibold">{related.total_capital.toLocaleString('lv-LV')} EUR</span>
                                        </div>
                                    )}
                                </div>
                            )
                        }

                        {/* PROCUREMENTS TAB */}
                        {
                            activeTab === "procurements" && (
                                <div className="space-y-6">
                                    {/* Header */}
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <h3 className="text-lg font-semibold text-gray-900">{t('procurements_title')}</h3>
                                            <p className="text-sm text-gray-500 mt-1">{t('procurements_desc')}</p>
                                        </div>
                                    </div>

                                    {company.procurements && company.procurements.length > 0 ? (
                                        <>
                                            {/* KPI Cards (Original Design) */}
                                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                                {/* Total Amount Card */}
                                                <div className="bg-gradient-to-br from-emerald-50 to-green-50 border border-green-200 rounded-lg p-5">
                                                    <div className="flex items-center justify-between">
                                                        <span className="text-sm font-medium text-green-700">{t('won_amount')}</span>
                                                        <span className="text-2xl">💰</span>
                                                    </div>
                                                    <p className="text-3xl font-bold text-green-700 mt-2">
                                                        {formatCurrency(company.procurements.reduce((sum: number, p: any) => sum + (p.amount || 0), 0))}
                                                    </p>
                                                </div>

                                                {/* Contract Count Card */}
                                                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-5">
                                                    <div className="flex items-center justify-between">
                                                        <span className="text-sm font-medium text-blue-700">{t('contract_count')}</span>
                                                        <span className="text-2xl">📄</span>
                                                    </div>
                                                    <p className="text-3xl font-bold text-blue-700 mt-2">
                                                        {company.procurements.length}
                                                    </p>
                                                </div>

                                                {/* Top Buyer Card */}
                                                <div className="bg-gradient-to-br from-purple-50 to-violet-50 border border-purple-200 rounded-lg p-5">
                                                    <div className="flex items-center justify-between">
                                                        <span className="text-sm font-medium text-purple-700">{t('top_authority')}</span>
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

                                            {/* NEW: Contract Execution Status (Inserted Section) */}
                                            {procurementStats.expiringCount > 0 && (
                                                <div className="border border-orange-200 rounded-lg overflow-hidden shadow-sm bg-orange-50">
                                                    <div className="px-6 py-4 border-b border-orange-200 flex items-center justify-between">
                                                        <div className="flex items-center gap-2">
                                                            <span className="text-xl">⚠️</span>
                                                            <div>
                                                                <h3 className="text-lg font-bold text-orange-900">{t('expiring_contracts')}</h3>
                                                                <p className="text-sm text-orange-700">{t('expiring_warning', { count: procurementStats.expiringCount })}</p>
                                                            </div>
                                                        </div>
                                                        <span className="bg-orange-100 text-orange-800 text-xs font-semibold px-2.5 py-0.5 rounded border border-orange-200">
                                                            {t('hot_leads')}
                                                        </span>
                                                    </div>
                                                    <div className="overflow-x-auto">
                                                        <table className="w-full">
                                                            <thead className="bg-orange-100/50 border-b border-orange-200">
                                                                <tr>
                                                                    <th className="px-6 py-3 text-left text-xs font-medium text-orange-800 uppercase">{t('authority')}</th>
                                                                    <th className="px-6 py-3 text-left text-xs font-medium text-orange-800 uppercase">{t('subject')}</th>
                                                                    <th className="px-6 py-3 text-right text-xs font-medium text-orange-800 uppercase">{t('end_date')}</th>
                                                                    <th className="px-6 py-3 text-left text-xs font-medium text-orange-800 uppercase w-40">{t('remaining')}</th>
                                                                </tr>
                                                            </thead>
                                                            <tbody className="divide-y divide-orange-200/50 bg-white">
                                                                {procurementStats.expiring.map((p: any, idx: number) => {
                                                                    const progress = calculateProgress(p.date, p.end_date);
                                                                    const daysLeft = getDaysRemaining(p.end_date);
                                                                    return (
                                                                        <tr key={idx} className="hover:bg-orange-50">
                                                                            <td className="px-6 py-3 text-sm font-medium text-gray-900">{p.authority}</td>
                                                                            <td className="px-6 py-3 text-sm text-gray-600 max-w-xs truncate" title={p.subject}>{p.subject}</td>
                                                                            <td className="px-6 py-3 text-sm text-right text-gray-900 font-medium">{p.end_date}</td>
                                                                            <td className="px-6 py-3">
                                                                                <div className="flex flex-col gap-1">
                                                                                    <div className="flex justify-between text-xs font-medium">
                                                                                        <span className="text-orange-700">{daysLeft} {t('days')}</span>
                                                                                        <span className="text-gray-500">{progress}%</span>
                                                                                    </div>
                                                                                    <div className="w-full bg-gray-200 rounded-full h-1.5">
                                                                                        <div
                                                                                            className="bg-orange-500 h-1.5 rounded-full"
                                                                                            style={{ width: `${progress}%` }}
                                                                                        ></div>
                                                                                    </div>
                                                                                </div>
                                                                            </td>
                                                                        </tr>
                                                                    );
                                                                })}
                                                            </tbody>
                                                        </table>
                                                    </div>
                                                </div>
                                            )}

                                            {/* Blurred Analytics Teaser - Upsell (Restored) */}
                                            <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
                                                <h4 className="text-md font-semibold text-gray-700 mb-4">🔒 {t('detailed_analytics')}</h4>
                                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                                    <div className="relative bg-white border border-gray-200 rounded-lg p-4 overflow-hidden">
                                                        <div className="filter blur-sm pointer-events-none">
                                                            <span className="text-xs text-gray-500">{t('win_rate')}</span>
                                                            <p className="text-2xl font-bold text-gray-800">67%</p>
                                                        </div>
                                                        <div className="absolute inset-0 bg-white/70 flex items-center justify-center">
                                                            <span className="text-sm font-medium text-gray-600">🔒 Pro</span>
                                                        </div>
                                                    </div>
                                                    <div className="relative bg-white border border-gray-200 rounded-lg p-4 overflow-hidden">
                                                        <div className="filter blur-sm pointer-events-none">
                                                            <span className="text-xs text-gray-500">{t('main_competitors')}</span>
                                                            <p className="text-lg font-bold text-gray-800">3 {t('company')}</p>
                                                        </div>
                                                        <div className="absolute inset-0 bg-white/70 flex items-center justify-center">
                                                            <span className="text-sm font-medium text-gray-600">🔒 Pro</span>
                                                        </div>
                                                    </div>
                                                    <div className="relative bg-white border border-gray-200 rounded-lg p-4 overflow-hidden">
                                                        <div className="filter blur-sm pointer-events-none">
                                                            <span className="text-xs text-gray-500">{t('avg_price_deviation')}</span>
                                                            <p className="text-2xl font-bold text-gray-800">-12%</p>
                                                        </div>
                                                        <div className="absolute inset-0 bg-white/70 flex items-center justify-center">
                                                            <span className="text-sm font-medium text-gray-600">🔒 Pro</span>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Recent Contracts Table (Restored + Status Badges) */}
                                            <div>
                                                <h4 className="text-md font-semibold text-gray-700 mb-3">{t('recent_won_procurements')}</h4>
                                                <div className="border border-gray-200 rounded-lg overflow-hidden">
                                                    <table className="w-full">
                                                        <thead className="bg-gray-50 border-b border-gray-200">
                                                            <tr>
                                                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('authority')}</th>
                                                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('subject')}</th>
                                                                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('amount')}</th>
                                                                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('procurement_status')}</th>
                                                                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('deadline')}</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody className="divide-y divide-gray-200">
                                                            {company.procurements.slice(0, 10).map((proc: any, idx: number) => {
                                                                const status = getContractStatus(proc);
                                                                let dateClass = "text-gray-500";

                                                                if (proc.end_date) {
                                                                    const end = new Date(proc.end_date);
                                                                    const now = new Date();
                                                                    const sixMonths = new Date();
                                                                    sixMonths.setMonth(now.getMonth() + 6);

                                                                    if (end < now) {
                                                                        dateClass = "text-red-600 font-bold";
                                                                    } else if (end <= sixMonths) {
                                                                        dateClass = "text-yellow-600 font-bold";
                                                                    }
                                                                }

                                                                return (
                                                                    <tr key={idx} className="hover:bg-gray-50">
                                                                        <td className="px-4 py-3 text-sm text-gray-900">{proc.authority}</td>
                                                                        <td className="px-4 py-3 text-sm text-gray-600 max-w-xs truncate" title={proc.subject}>{proc.subject}</td>
                                                                        <td className="px-4 py-3 text-sm text-right font-semibold text-success">{formatCurrency(proc.amount)}</td>
                                                                        <td className="px-4 py-3 text-right">
                                                                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${status === 'EXPIRING' ? 'bg-orange-100 text-orange-800' :
                                                                                status === 'ACTIVE' ? 'bg-green-100 text-green-800' :
                                                                                    'bg-gray-100 text-gray-600'
                                                                                }`}>
                                                                                {status === 'EXPIRING' ? t('status.expiring') : status === 'ACTIVE' ? t('status.active') : t('status.closed')}
                                                                            </span>
                                                                        </td>
                                                                        <td className={`px-4 py-3 text-sm text-right whitespace-nowrap ${dateClass}`}>
                                                                            {proc.end_date || '-'}
                                                                        </td>
                                                                    </tr>
                                                                );
                                                            })}
                                                        </tbody>
                                                    </table>
                                                </div>
                                            </div>

                                            {/* CTA Button (Restored) */}
                                            <div className="bg-gradient-to-r from-primary to-accent rounded-lg p-6 text-center">
                                                <p className="text-white text-lg font-medium mb-3">
                                                    {t('cta_text', { name: company.name.split('"')[1] || company.name })}
                                                </p>
                                                <a
                                                    href={`https://www.iepirkumi.animas.lv/${company.regcode}`}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="inline-flex items-center gap-2 px-6 py-3 bg-white text-primary font-bold rounded-lg hover:bg-gray-100 transition-colors shadow-lg"
                                                >
                                                    <span>🚀</span>
                                                    {t('cta_button')}
                                                </a>
                                                <p className="text-white/80 text-sm mt-3">
                                                    {t('cta_subtext')}
                                                </p>
                                            </div>
                                        </>
                                    ) : (
                                        <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
                                            <span className="text-4xl">📋</span>
                                            <h3 className="mt-4 text-lg font-semibold text-gray-900">{t('no_procurement_data')}</h3>
                                            <p className="mt-2 text-sm text-gray-500 max-w-md mx-auto">
                                                {t('no_procurement_desc')}
                                            </p>
                                            <a
                                                href={`https://www.iepirkumi.animas.lv/${company.regcode}`}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="inline-flex items-center gap-2 mt-4 px-4 py-2 text-sm font-medium text-white bg-primary hover:bg-primary/90 rounded-lg transition-colors"
                                            >
                                                {t('check_platform')}
                                            </a>
                                        </div>
                                    )}
                                </div>
                            )}
                    </>
                )}
            </div>
        </div >
    );
}

