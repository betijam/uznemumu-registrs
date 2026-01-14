"use client";

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import RawDataAccordions from './RawDataAccordions';
import FinancialHealthCharts from './FinancialHealthCharts';
import {
    formatCurrency,
    formatPercent,
    formatRatio
} from '@/utils/financialAnalysis';

interface FinancialAnalysisTabProps {
    company: any;
}

export default function FinancialAnalysisTab({ company }: FinancialAnalysisTabProps) {
    const t = useTranslations('FinancialAnalysis');
    const financialHistory = company.financial_history || [];
    const taxHistory = company.tax_history || [];
    const [showAllHistory, setShowAllHistory] = useState(false);

    // Filter/Sort
    const sortedHistory = [...financialHistory].sort((a: any, b: any) => b.year - a.year);
    const visibleHistory = showAllHistory ? sortedHistory : sortedHistory.slice(0, 5);
    const latest = sortedHistory[0] || {};

    return (
        <div className="space-y-8">

            {/* 1. VID Reitings / Tax Rating */}
            {company.rating && (
                <div className={`p-4 rounded-lg border ${company.rating.grade === 'A' ? 'bg-green-50 border-green-200' :
                    company.rating.grade === 'B' ? 'bg-yellow-50 border-yellow-200' :
                        'bg-gray-50 border-gray-200'
                    }`}>
                    <div className="flex items-center gap-3">
                        <div className={`text-2xl font-bold ${company.rating.grade === 'A' ? 'text-green-700' :
                            company.rating.grade === 'B' ? 'text-yellow-700' :
                                'text-gray-700'
                            }`}>
                            {company.rating.grade} {t('grade')}
                        </div>
                        <div className="text-sm text-gray-600">
                            {t('taxRatingDescription')}
                        </div>
                    </div>
                    {company.rating.last_updated && (
                        <div className="text-xs text-gray-400 mt-1">
                            {t('updated')}: {company.rating.last_updated}
                        </div>
                    )}
                </div>
            )}

            {/* 2. Visual Graphs (NEW) */}
            <FinancialHealthCharts latestFinancials={latest} />

            {/* 3. Detalizēti Finanšu Rādītāji (Moved Up) */}
            <div className="border border-gray-200 rounded-lg bg-white overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                    <h3 className="font-semibold text-gray-900">{t('detailedFinancials')}</h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="text-xs text-gray-500 uppercase bg-gray-50 border-b border-gray-100">
                            <tr>
                                <th className="px-6 py-3">{t('indicator')}</th>
                                <th className="px-6 py-3 text-right">{t('value')}</th>
                                <th className="px-6 py-3 text-center">{t('trend')}</th>
                                <th className="px-6 py-3 text-right">{t('norm')}</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {/* Likviditāte Header */}
                            <tr className="bg-gray-50/50">
                                <td colSpan={4} className="px-6 py-2 text-xs font-semibold text-gray-500 uppercase">💧 {t('liquidity')}</td>
                            </tr>
                            <tr>
                                <td className="px-6 py-3 text-gray-900 pl-8">Current Ratio</td>
                                <td className="px-6 py-3 text-right font-medium">{formatRatio(latest.current_ratio)}</td>
                                <td className="px-6 py-3 text-center text-xs">
                                    {sortedHistory.length >= 2 ? (
                                        (sortedHistory[0].current_ratio > sortedHistory[1].current_ratio) ?
                                            <span className="text-green-600 text-lg">↗</span> : <span className="text-red-600 text-lg">↘</span>
                                    ) : '-'}
                                </td>
                                <td className="px-6 py-3 text-right text-gray-500 text-xs">&gt; 1.2</td>
                            </tr>
                            <tr>
                                <td className="px-6 py-3 text-gray-900 pl-8">Quick Ratio</td>
                                <td className="px-6 py-3 text-right font-medium">{formatRatio(latest.quick_ratio)}</td>
                                <td className="px-6 py-3 text-center text-xs">
                                    {sortedHistory.length >= 2 ? (
                                        (sortedHistory[0].quick_ratio > sortedHistory[1].quick_ratio) ?
                                            <span className="text-green-600 text-lg">↗</span> : <span className="text-red-600 text-lg">↘</span>
                                    ) : '-'}
                                </td>
                                <td className="px-6 py-3 text-right text-gray-500 text-xs">&gt; 0.8</td>
                            </tr>

                            {/* Rentabilitāte Header */}
                            <tr className="bg-gray-50/50">
                                <td colSpan={4} className="px-6 py-2 text-xs font-semibold text-gray-500 uppercase">💰 {t('profitability')}</td>
                            </tr>
                            <tr>
                                <td className="px-6 py-3 text-gray-900 pl-8">Net Profit Margin</td>
                                <td className="px-6 py-3 text-right font-medium">{formatPercent(latest.net_profit_margin)}</td>
                                <td className="px-6 py-3 text-center text-xs">
                                    {sortedHistory.length >= 2 ? (
                                        (sortedHistory[0].net_profit_margin > sortedHistory[1].net_profit_margin) ?
                                            <span className="text-green-600 text-lg">↗</span> : <span className="text-red-600 text-lg">↘</span>
                                    ) : '-'}
                                </td>
                                <td className="px-6 py-3 text-right text-gray-500 text-xs">{t('dependsOnIndustry')}</td>
                            </tr>
                            <tr>
                                <td className="px-6 py-3 text-gray-900 pl-8">ROE</td>
                                <td className="px-6 py-3 text-right font-medium">{formatPercent(latest.roe)}</td>
                                <td className="px-6 py-3 text-center text-xs">
                                    {sortedHistory.length >= 2 ? (
                                        (sortedHistory[0].roe > sortedHistory[1].roe) ?
                                            <span className="text-green-600 text-lg">↗</span> : <span className="text-red-600 text-lg">↘</span>
                                    ) : '-'}
                                </td>
                                <td className="px-6 py-3 text-right text-gray-500 text-xs">&gt; 10%</td>
                            </tr>
                            <tr>
                                <td className="px-6 py-3 text-gray-900 pl-8">ROA</td>
                                <td className="px-6 py-3 text-right font-medium">{formatPercent(latest.roa)}</td>
                                <td className="px-6 py-3 text-center text-xs">
                                    {sortedHistory.length >= 2 ? (
                                        (sortedHistory[0].roa > sortedHistory[1].roa) ?
                                            <span className="text-green-600 text-lg">↗</span> : <span className="text-red-600 text-lg">↘</span>
                                    ) : '-'}
                                </td>
                                <td className="px-6 py-3 text-right text-gray-500 text-xs">&gt; 5%</td>
                            </tr>

                            {/* Maksātspēja Header */}
                            <tr className="bg-gray-50/50">
                                <td colSpan={4} className="px-6 py-2 text-xs font-semibold text-gray-500 uppercase">📉 {t('solvency')}</td>
                            </tr>
                            <tr>
                                <td className="px-6 py-3 text-gray-900 pl-8">Debt-to-Equity</td>
                                <td className="px-6 py-3 text-right font-medium">{formatRatio(latest.debt_to_equity)}</td>
                                <td className="px-6 py-3 text-center text-xs">
                                    {sortedHistory.length >= 2 ? (
                                        (sortedHistory[0].debt_to_equity < sortedHistory[1].debt_to_equity) ?
                                            <span className="text-green-600 text-lg">↘</span> : <span className="text-red-600 text-lg">↗</span>
                                    ) : '-'}
                                </td>
                                <td className="px-6 py-3 text-right text-gray-500 text-xs">&lt; 1.5</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            {/* 4. Fiskālā Disciplīna (Table) */}
            <div className="border border-gray-200 rounded-lg bg-white overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                    <h3 className="font-semibold text-gray-900">{t('fiscalDiscipline')}</h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="text-xs text-gray-500 uppercase bg-gray-50 border-b border-gray-100">
                            <tr>
                                <th className="px-6 py-3">{t('year')}</th>
                                <th className="px-6 py-3 text-right">{t('totalTax')}</th>
                                <th className="px-6 py-3 text-right">{t('vsaoi')}</th>
                                <th className="px-6 py-3 text-right">{t('iin')}</th>
                                <th className="px-6 py-3 text-right">{t('employees')}</th>
                                <th className="px-6 py-3 text-right">{t('avgSalary')}</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {taxHistory.length > 0 ? taxHistory.map((row: any, idx: number) => (
                                <tr key={idx} className="hover:bg-gray-50">
                                    <td className="px-6 py-3 font-medium text-gray-900">{row.year}</td>
                                    <td className="px-6 py-3 text-right font-medium">{formatCurrency(row.total_tax_paid)}</td>
                                    <td className="px-6 py-3 text-right text-gray-600">{formatCurrency(row.social_tax_vsaoi)}</td>
                                    <td className="px-6 py-3 text-right text-gray-600">{formatCurrency(row.labor_tax_iin)}</td>
                                    <td className="px-6 py-3 text-right text-gray-900">{row.avg_employees}</td>
                                    <td className="px-6 py-3 text-right font-medium text-green-700">
                                        {formatCurrency(row.avg_gross_salary)}
                                    </td>
                                </tr>
                            )) : (
                                <tr>
                                    <td colSpan={6} className="px-6 py-4 text-center text-gray-500">{t('noData')}</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* 5. Finanšu Vēsture (Table with See More) */}
            <div className="border border-gray-200 rounded-lg bg-white overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                    <h3 className="font-semibold text-gray-900">{t('financialHistory')}</h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="text-xs text-gray-500 uppercase bg-gray-50 border-b border-gray-100">
                            <tr>
                                <th className="px-6 py-3">{t('year')}</th>
                                <th className="px-6 py-3 text-right">{t('turnover')}</th>
                                <th className="px-6 py-3 text-right">{t('profit')}</th>
                                <th className="px-6 py-3 text-right">{t('employees')}</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {visibleHistory.length > 0 ? visibleHistory.map((row: any, idx: number) => (
                                <tr key={idx} className="hover:bg-gray-50">
                                    <td className="px-6 py-3 font-medium text-gray-900">{row.year}</td>
                                    <td className="px-6 py-3 text-right">
                                        {formatCurrency(row.turnover)}
                                    </td>
                                    <td className={`px-6 py-3 text-right font-medium ${row.profit >= 0 ? 'text-gray-900' : 'text-red-600'}`}>
                                        {formatCurrency(row.profit)}
                                    </td>
                                    <td className="px-6 py-3 text-right text-gray-600">
                                        {row.employees || '-'}
                                    </td>
                                </tr>
                            )) : (
                                <tr>
                                    <td colSpan={4} className="px-6 py-4 text-center text-gray-500">{t('noData')}</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
                {sortedHistory.length > 5 && (
                    <div className="p-3 border-t border-gray-100 text-center">
                        <button
                            onClick={() => setShowAllHistory(!showAllHistory)}
                            className="text-sm font-medium text-blue-600 hover:text-blue-700"
                        >
                            {showAllHistory ? t('showLess') : t('showMore')}
                        </button>
                    </div>
                )}
            </div>

            {/* 6. Raw Data Accordions */}
            <RawDataAccordions financialHistory={sortedHistory} />

        </div>
    );
}
