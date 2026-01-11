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

    // Limit to 3 latest years
    const yearsToShow = financialHistory.slice(0, 3);

    // Check if we have any cash flow data at all
    const hasAnyCashFlow = yearsToShow.some(y =>
        y.cfo !== null || y.cfi !== null || y.cff !== null || y.taxes_paid_cf !== null
    );

    const toggleSection = (section: string) => {
        setExpandedSection(expandedSection === section ? null : section);
    };

    const renderHeader = () => (
        <thead className="bg-gray-100 border-b border-gray-200">
            <tr>
                <th className="px-6 py-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{t('indicator')}</th>
                {yearsToShow.map(y => (
                    <th key={y.year} className="px-6 py-2 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        {y.year}
                    </th>
                ))}
                {yearsToShow.length === 0 && (
                    <th className="px-6 py-2 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">-</th>
                )}
            </tr>
        </thead>
    );

    return (
        <div className="border border-gray-200 rounded-lg bg-white overflow-hidden shadow-sm">
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
                    <span className="text-sm text-gray-500">
                        {yearsToShow.length > 0 ? `${yearsToShow[yearsToShow.length - 1].year} - ${yearsToShow[0].year}` : '-'}
                    </span>
                </button>

                {expandedSection === 'pnl' && (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            {renderHeader()}
                            <tbody className="divide-y divide-gray-200">
                                <tr>
                                    <td className="px-6 py-3 text-gray-700">{t('turnover')} / Turnover</td>
                                    {yearsToShow.map(y => (
                                        <td key={y.year} className="px-6 py-3 text-right font-semibold text-gray-900">{formatCurrency(y.turnover)}</td>
                                    ))}
                                </tr>
                                <tr>
                                    <td className="px-6 py-3 text-gray-700">{t('profit')} / Net Profit</td>
                                    {yearsToShow.map(y => (
                                        <td key={y.year} className={`px-6 py-3 text-right font-semibold ${(y.profit || 0) >= 0 ? 'text-gray-900' : 'text-red-600'}`}>
                                            {formatCurrency(y.profit)}
                                        </td>
                                    ))}
                                </tr>
                                <tr>
                                    <td className="px-6 py-3 text-gray-700">{t('interestExpenses')} / Interest</td>
                                    {yearsToShow.map(y => (
                                        <td key={y.year} className="px-6 py-3 text-right text-gray-900">{formatCurrency(y.interest_payment)}</td>
                                    ))}
                                </tr>
                                <tr>
                                    <td className="px-6 py-3 text-gray-700">{t('depreciation')} / Deprec.</td>
                                    {yearsToShow.map(y => (
                                        <td key={y.year} className="px-6 py-3 text-right text-gray-900">{formatCurrency(y.depreciation)}</td>
                                    ))}
                                </tr>
                                <tr>
                                    <td className="px-6 py-3 text-gray-700">{t('incomeTaxProvision')} / Tax Prov.</td>
                                    {yearsToShow.map(y => (
                                        <td key={y.year} className="px-6 py-3 text-right text-gray-900">{formatCurrency(y.corporate_income_tax)}</td>
                                    ))}
                                </tr>
                                <tr>
                                    <td className="px-6 py-3 text-gray-700">{t('labourExpenses')} / Labour</td>
                                    {yearsToShow.map(y => (
                                        <td key={y.year} className="px-6 py-3 text-right text-gray-900">{formatCurrency(y.labour_costs)}</td>
                                    ))}
                                </tr>
                                <tr className="bg-blue-50/50">
                                    <td className="px-6 py-3 font-semibold text-gray-900">
                                        {t('ebitda')} / EBITDA
                                        <div className="text-xs font-normal text-gray-500 mt-1">
                                            = Peļņa + Nodokļi + Procenti + Nolietojums
                                        </div>
                                    </td>
                                    {yearsToShow.map(y => (
                                        <td key={y.year} className="px-6 py-3 text-right font-bold text-gray-900">
                                            {formatCurrency(y.ebitda)}
                                        </td>
                                    ))}
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
                    <span className="text-sm text-gray-500">
                        {yearsToShow.length > 0 ? `${yearsToShow[yearsToShow.length - 1].year} - ${yearsToShow[0].year}` : '-'}
                    </span>
                </button>

                {expandedSection === 'balance' && (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            {renderHeader()}
                            <tbody className="divide-y divide-gray-200">
                                <tr className="bg-gray-50/50 font-bold">
                                    <td colSpan={1 + yearsToShow.length} className="px-6 py-2 text-gray-500 text-[10px] uppercase tracking-wider">Aktīvi / Assets</td>
                                </tr>
                                <tr>
                                    <td className="px-6 py-3 text-gray-700 font-medium">{t('totalAssets')}</td>
                                    {yearsToShow.map(y => (
                                        <td key={y.year} className="px-6 py-3 text-right font-semibold text-gray-900">{formatCurrency(y.total_assets)}</td>
                                    ))}
                                </tr>
                                <tr>
                                    <td className="px-6 py-3 text-gray-700">{t('currentAssets')}</td>
                                    {yearsToShow.map(y => (
                                        <td key={y.year} className="px-6 py-3 text-right text-gray-900">{formatCurrency(y.total_current_assets)}</td>
                                    ))}
                                </tr>
                                <tr className="text-gray-500">
                                    <td className="px-10 py-2 text-xs italic">↳ {t('cash')}</td>
                                    {yearsToShow.map(y => (
                                        <td key={y.year} className="px-6 py-2 text-right">{formatCurrency(y.cash_balance)}</td>
                                    ))}
                                </tr>
                                <tr className="text-gray-500">
                                    <td className="px-10 py-2 text-xs italic">↳ {t('accountsReceivable')}</td>
                                    {yearsToShow.map(y => (
                                        <td key={y.year} className="px-6 py-2 text-right">{formatCurrency(y.accounts_receivable)}</td>
                                    ))}
                                </tr>
                                <tr className="text-gray-500">
                                    <td className="px-10 py-2 text-xs italic">↳ {t('inventories')}</td>
                                    {yearsToShow.map(y => (
                                        <td key={y.year} className="px-6 py-2 text-right">{formatCurrency(y.inventories)}</td>
                                    ))}
                                </tr>

                                <tr className="bg-gray-50/50 font-bold border-t border-gray-200">
                                    <td colSpan={1 + yearsToShow.length} className="px-6 py-2 text-gray-500 text-[10px] uppercase tracking-wider">Saistības & Kapitāls / Liabilities & Equity</td>
                                </tr>
                                <tr>
                                    <td className="px-6 py-3 text-gray-700 font-medium">{t('equity')}</td>
                                    {yearsToShow.map(y => (
                                        <td key={y.year} className={`px-6 py-3 text-right font-semibold ${(y.equity || 0) >= 0 ? 'text-gray-900' : 'text-red-600'}`}>
                                            {formatCurrency(y.equity)}
                                        </td>
                                    ))}
                                </tr>
                                <tr>
                                    <td className="px-6 py-3 text-gray-700">{t('currentLiabilities')}</td>
                                    {yearsToShow.map(y => (
                                        <td key={y.year} className="px-6 py-3 text-right text-gray-900">{formatCurrency(y.current_liabilities)}</td>
                                    ))}
                                </tr>
                                <tr>
                                    <td className="px-6 py-3 text-gray-700">{t('nonCurrentLiabilities')}</td>
                                    {yearsToShow.map(y => (
                                        <td key={y.year} className="px-6 py-3 text-right text-gray-900">{formatCurrency(y.non_current_liabilities)}</td>
                                    ))}
                                </tr>
                                <tr className="bg-blue-50/50">
                                    <td className="px-6 py-3 font-semibold text-gray-900">{t('totalLiabilities')}</td>
                                    {yearsToShow.map(y => (
                                        <td key={y.year} className="px-6 py-3 text-right font-bold text-gray-900">
                                            {formatCurrency((y.current_liabilities || 0) + (y.non_current_liabilities || 0))}
                                        </td>
                                    ))}
                                </tr>
                            </tbody>
                        </table>
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
                    <span className="text-sm text-gray-500">
                        {yearsToShow.length > 0 ? `${yearsToShow[yearsToShow.length - 1].year} - ${yearsToShow[0].year}` : '-'}
                    </span>
                </button>

                {expandedSection === 'cashflow' && (
                    <div className="overflow-x-auto">
                        {hasAnyCashFlow ? (
                            <table className="w-full text-sm">
                                {renderHeader()}
                                <tbody className="divide-y divide-gray-200">
                                    <tr className="bg-green-50/50">
                                        <td className="px-6 py-3 font-semibold text-gray-900">{t('operatingCashFlow')}</td>
                                        {yearsToShow.map(y => (
                                            <td key={y.year} className="px-6 py-3 text-right font-bold text-gray-900">{formatCurrency(y.cfo)}</td>
                                        ))}
                                    </tr>
                                    <tr className="text-gray-500">
                                        <td className="px-10 py-2 text-xs italic">↳ {t('taxesPaidCf')}</td>
                                        {yearsToShow.map(y => (
                                            <td key={y.year} className="px-6 py-2 text-right">{formatCurrency(y.taxes_paid_cf)}</td>
                                        ))}
                                    </tr>
                                    <tr className="bg-orange-50/50">
                                        <td className="px-6 py-3 font-semibold text-gray-900">{t('investingCashFlow')}</td>
                                        {yearsToShow.map(y => (
                                            <td key={y.year} className="px-6 py-3 text-right font-bold text-gray-900">{formatCurrency(y.cfi)}</td>
                                        ))}
                                    </tr>
                                    <tr className="bg-purple-50/50">
                                        <td className="px-6 py-3 font-semibold text-gray-900">{t('financingCashFlow')}</td>
                                        {yearsToShow.map(y => (
                                            <td key={y.year} className="px-6 py-3 text-right font-bold text-gray-900">{formatCurrency(y.cff)}</td>
                                        ))}
                                    </tr>
                                    <tr className="bg-blue-100/50 border-t-2 border-blue-200">
                                        <td className="px-6 py-4 font-bold text-gray-900">{t('netCashChange')}</td>
                                        {yearsToShow.map(y => (
                                            <td key={y.year} className="px-6 py-4 text-right font-bold text-gray-900">
                                                {formatCurrency((y.cfo || 0) + (y.cfi || 0) + (y.cff || 0))}
                                            </td>
                                        ))}
                                    </tr>
                                </tbody>
                            </table>
                        ) : (
                            <div className="text-center py-12 text-gray-500 text-sm italic">
                                {t('dataUnavailable')}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
