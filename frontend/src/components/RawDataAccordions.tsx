"use client";

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { formatCurrency } from '@/utils/financialAnalysis';

interface RawDataAccordionsProps {
    financialHistory: any[];
}

export default function RawDataAccordions({ financialHistory }: RawDataAccordionsProps) {
    const t = useTranslations('FinancialAnalysis');
    const [expandedSection, setExpandedSection] = useState<string | null>(null);

    const latest = financialHistory[0] || {};

    const toggleSection = (section: string) => {
        setExpandedSection(expandedSection === section ? null : section);
    };

    return (
        <div className="border border-gray-200 rounded-lg bg-white overflow-hidden">
            <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">{t('rawData')}</h3>
                <p className="text-sm text-gray-600 mt-1">
                    {t('profitLoss')} · {t('balanceSheet')} · {t('cashFlowStatement')}
                </p>
            </div>

            {/* Profit & Loss Statement */}
            <div className="border-b border-gray-200">
                <button
                    onClick={() => toggleSection('pnl')}
                    className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                >
                    <div className="flex items-center gap-3">
                        <svg className={`w-5 h-5 text-gray-400 transition-transform ${expandedSection === 'pnl' ? 'rotate-90' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                        <span className="font-medium text-gray-900">{t('profitLoss')}</span>
                    </div>
                    <span className="text-sm text-gray-500">{latest.year || '-'}</span>
                </button>

                {expandedSection === 'pnl' && (
                    <div className="px-6 py-4 bg-gray-50">
                        <table className="w-full text-sm">
                            <tbody className="divide-y divide-gray-200">
                                <tr>
                                    <td className="py-2 text-gray-700">{t('turnover')} / Turnover</td>
                                    <td className="py-2 text-right font-semibold text-gray-900">{formatCurrency(latest.turnover)}</td>
                                </tr>
                                <tr>
                                    <td className="py-2 text-gray-700">{t('profit')} / Net Profit</td>
                                    <td className={`py-2 text-right font-semibold ${(latest.profit || 0) >= 0 ? 'text-gray-900' : 'text-red-600'}`}>
                                        {formatCurrency(latest.profit)}
                                    </td>
                                </tr>
                                <tr>
                                    <td className="py-2 text-gray-700">{t('interestExpenses')} / Interest Expenses</td>
                                    <td className="py-2 text-right text-gray-900">{formatCurrency(latest.interest_payment)}</td>
                                </tr>
                                <tr>
                                    <td className="py-2 text-gray-700">{t('depreciation')} / Depreciation</td>
                                    <td className="py-2 text-right text-gray-900">{formatCurrency(latest.depreciation)}</td>
                                </tr>
                                <tr>
                                    <td className="py-2 text-gray-700">{t('incomeTaxProvision')} / Income Tax Provision</td>
                                    <td className="py-2 text-right text-gray-900">{formatCurrency(latest.corporate_income_tax)}</td>
                                </tr>
                                <tr>
                                    <td className="py-2 text-gray-700">{t('labourExpenses')} / Labour Expenses</td>
                                    <td className="py-2 text-right text-gray-900">{formatCurrency(latest.labour_costs)}</td>
                                </tr>
                                <tr className="bg-blue-50/50">
                                    <td className="py-2 font-semibold text-gray-900">{t('ebitda')} / EBITDA</td>
                                    <td className="py-2 text-right font-bold text-gray-900">
                                        {formatCurrency(
                                            (latest.profit || 0) +
                                            (latest.interest_payment || 0) +
                                            (latest.corporate_income_tax || 0) +
                                            (latest.depreciation || 0)
                                        )}
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Balance Sheet */}
            <div className="border-b border-gray-200">
                <button
                    onClick={() => toggleSection('balance')}
                    className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                >
                    <div className="flex items-center gap-3">
                        <svg className={`w-5 h-5 text-gray-400 transition-transform ${expandedSection === 'balance' ? 'rotate-90' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                        <span className="font-medium text-gray-900">{t('balanceSheet')}</span>
                    </div>
                    <span className="text-sm text-gray-500">{latest.year || '-'}</span>
                </button>

                {expandedSection === 'balance' && (
                    <div className="px-6 py-4 bg-gray-50">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            {/* Assets */}
                            <div>
                                <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Aktīvi / Assets</h4>
                                <table className="w-full text-sm">
                                    <tbody className="divide-y divide-gray-200">
                                        <tr>
                                            <td className="py-2 text-gray-700 font-medium">{t('totalAssets')} / Total Assets</td>
                                            <td className="py-2 text-right font-semibold text-gray-900">{formatCurrency(latest.total_assets)}</td>
                                        </tr>
                                        <tr>
                                            <td className="py-2 text-gray-700">{t('currentAssets')} / Current Assets</td>
                                            <td className="py-2 text-right text-gray-900">{formatCurrency(latest.total_current_assets)}</td>
                                        </tr>
                                        <tr>
                                            <td className="py-2 text-gray-700 pl-4 text-xs">↳ {t('cash')} / Cash</td>
                                            <td className="py-2 text-right text-gray-900">{formatCurrency(latest.cash_balance)}</td>
                                        </tr>
                                        <tr>
                                            <td className="py-2 text-gray-700 pl-4 text-xs">↳ {t('accountsReceivable')} / Receivables</td>
                                            <td className="py-2 text-right text-gray-900">{formatCurrency(latest.accounts_receivable)}</td>
                                        </tr>
                                        <tr>
                                            <td className="py-2 text-gray-700 pl-4 text-xs">↳ {t('inventories')} / Inventories</td>
                                            <td className="py-2 text-right text-gray-900">{formatCurrency(latest.inventories)}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>

                            {/* Liabilities & Equity */}
                            <div>
                                <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Saistības un kapitāls / Liabilities & Equity</h4>
                                <table className="w-full text-sm">
                                    <tbody className="divide-y divide-gray-200">
                                        <tr>
                                            <td className="py-2 text-gray-700 font-medium">{t('equity')} / Equity</td>
                                            <td className={`py-2 text-right font-semibold ${(latest.equity || 0) >= 0 ? 'text-gray-900' : 'text-red-600'}`}>
                                                {formatCurrency(latest.equity)}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td className="py-2 text-gray-700">{t('currentLiabilities')} / Current Liabilities</td>
                                            <td className="py-2 text-right text-gray-900">{formatCurrency(latest.current_liabilities)}</td>
                                        </tr>
                                        <tr>
                                            <td className="py-2 text-gray-700">{t('nonCurrentLiabilities')} / Non-Current Liabilities</td>
                                            <td className="py-2 text-right text-gray-900">{formatCurrency(latest.non_current_liabilities)}</td>
                                        </tr>
                                        <tr className="bg-blue-50/50">
                                            <td className="py-3 font-semibold text-gray-900">{t('totalLiabilities')} / Total Liabilities</td>
                                            <td className="py-3 text-right font-bold text-gray-900">
                                                {formatCurrency((latest.current_liabilities || 0) + (latest.non_current_liabilities || 0))}
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Cash Flow Statement */}
            <div>
                <button
                    onClick={() => toggleSection('cashflow')}
                    className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                >
                    <div className="flex items-center gap-3">
                        <svg className={`w-5 h-5 text-gray-400 transition-transform ${expandedSection === 'cashflow' ? 'rotate-90' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                        <span className="font-medium text-gray-900">{t('cashFlowStatement')}</span>
                    </div>
                    <span className="text-sm text-gray-500">{latest.year || '-'}</span>
                </button>

                {expandedSection === 'cashflow' && (
                    <div className="px-6 py-4 bg-gray-50">
                        {latest.cfo !== null ? (
                            <table className="w-full text-sm">
                                <tbody className="divide-y divide-gray-200">
                                    <tr className="bg-green-50/50">
                                        <td className="py-2 font-semibold text-gray-900">{t('operatingCashFlow')} / Operating Activities</td>
                                        <td className="py-2 text-right font-bold text-gray-900">
                                            {formatCurrency(latest.cfo)}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td className="py-2 text-gray-700 pl-4 text-xs">↳ {t('taxesPaidCf')} / Taxes Paid (CF)</td>
                                        <td className="py-2 text-right text-gray-900">{formatCurrency(latest.taxes_paid_cf)}</td>
                                    </tr>
                                    <tr className="bg-orange-50/50">
                                        <td className="py-2 font-semibold text-gray-900">{t('investingCashFlow')} / Investing Activities</td>
                                        <td className="py-2 text-right font-bold text-gray-900">
                                            {formatCurrency(latest.cfi)}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td className="py-2 text-gray-700 pl-4 text-xs">↳ {t('capex')} / CapEx</td>
                                        <td className="py-2 text-right text-gray-900">{formatCurrency(latest.cfi)}</td>
                                    </tr>
                                    <tr className="bg-purple-50/50">
                                        <td className="py-2 font-semibold text-gray-900">{t('financingCashFlow')} / Financing Activities</td>
                                        <td className="py-2 text-right font-bold text-gray-900">
                                            {formatCurrency(latest.cff)}
                                        </td>
                                    </tr>
                                    <tr className="bg-blue-100/50">
                                        <td className="py-3 font-bold text-gray-900">{t('netCashChange')} / Net Change in Cash</td>
                                        <td className="py-3 text-right font-bold text-gray-900">
                                            {formatCurrency(
                                                (latest.cfo || 0) +
                                                (latest.cfi || 0) +
                                                (latest.cff || 0)
                                            )}
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        ) : (
                            <div className="text-center py-8 text-gray-500 text-sm italic">
                                {t('dataUnavailable')}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
