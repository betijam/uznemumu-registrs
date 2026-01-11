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
                                    <td className="py-2 text-gray-700">Apgrozījums / Turnover</td>
                                    <td className="py-2 text-right font-semibold text-gray-900">{formatCurrency(latest.turnover)}</td>
                                </tr>
                                <tr>
                                    <td className="py-2 text-gray-700">Neto peļņa / Net Profit</td>
                                    <td className={`py-2 text-right font-semibold ${(latest.profit || 0) >= 0 ? 'text-gray-900' : 'text-red-600'}`}>
                                        {formatCurrency(latest.profit)}
                                    </td>
                                </tr>
                                <tr>
                                    <td className="py-2 text-gray-700">Procentu izdevumi / Interest Expenses</td>
                                    <td className="py-2 text-right text-gray-900">{formatCurrency(latest.interest_expenses)}</td>
                                </tr>
                                <tr>
                                    <td className="py-2 text-gray-700">Nolietojums / Depreciation</td>
                                    <td className="py-2 text-right text-gray-900">{formatCurrency(latest.depreciation_expenses)}</td>
                                </tr>
                                <tr>
                                    <td className="py-2 text-gray-700">Ienākuma nodokļi / Income Tax Provision</td>
                                    <td className="py-2 text-right text-gray-900">{formatCurrency(latest.provision_for_income_taxes)}</td>
                                </tr>
                                <tr>
                                    <td className="py-2 text-gray-700">Darba samaksa / Labour Expenses</td>
                                    <td className="py-2 text-right text-gray-900">{formatCurrency(latest.by_nature_labour_expenses)}</td>
                                </tr>
                                <tr className="bg-blue-50">
                                    <td className="py-2 font-semibold text-gray-900">EBITDA</td>
                                    <td className="py-2 text-right font-bold text-gray-900">{formatCurrency(latest.ebitda)}</td>
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
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Assets */}
                            <div>
                                <h4 className="text-xs font-semibold text-gray-700 uppercase mb-3">Aktīvi / Assets</h4>
                                <table className="w-full text-sm">
                                    <tbody className="divide-y divide-gray-200">
                                        <tr>
                                            <td className="py-2 text-gray-700">Kopējie aktīvi / Total Assets</td>
                                            <td className="py-2 text-right font-semibold text-gray-900">{formatCurrency(latest.total_assets)}</td>
                                        </tr>
                                        <tr>
                                            <td className="py-2 text-gray-700">Apgrozāmie līdzekļi / Current Assets</td>
                                            <td className="py-2 text-right text-gray-900">{formatCurrency(latest.total_current_assets)}</td>
                                        </tr>
                                        <tr>
                                            <td className="py-2 text-gray-700 pl-4">↳ Nauda / Cash</td>
                                            <td className="py-2 text-right text-gray-900">{formatCurrency(latest.cash_balance)}</td>
                                        </tr>
                                        <tr>
                                            <td className="py-2 text-gray-700 pl-4">↳ Debitoru parādi / Accounts Receivable</td>
                                            <td className="py-2 text-right text-gray-900">{formatCurrency(latest.accounts_receivable)}</td>
                                        </tr>
                                        <tr>
                                            <td className="py-2 text-gray-700 pl-4">↳ Krājumi / Inventories</td>
                                            <td className="py-2 text-right text-gray-900">{formatCurrency(latest.inventories)}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>

                            {/* Liabilities & Equity */}
                            <div>
                                <h4 className="text-xs font-semibold text-gray-700 uppercase mb-3">Saistības un kapitāls / Liabilities & Equity</h4>
                                <table className="w-full text-sm">
                                    <tbody className="divide-y divide-gray-200">
                                        <tr>
                                            <td className="py-2 text-gray-700">Pašu kapitāls / Equity</td>
                                            <td className={`py-2 text-right font-semibold ${(latest.equity || 0) >= 0 ? 'text-gray-900' : 'text-red-600'}`}>
                                                {formatCurrency(latest.equity)}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td className="py-2 text-gray-700">Īstermiņa saistības / Current Liabilities</td>
                                            <td className="py-2 text-right text-gray-900">{formatCurrency(latest.current_liabilities)}</td>
                                        </tr>
                                        <tr>
                                            <td className="py-2 text-gray-700">Ilgtermiņa saistības / Non-Current Liabilities</td>
                                            <td className="py-2 text-right text-gray-900">{formatCurrency(latest.non_current_liabilities)}</td>
                                        </tr>
                                        <tr className="bg-blue-50">
                                            <td className="py-2 font-semibold text-gray-900">Kopējās saistības / Total Liabilities</td>
                                            <td className="py-2 text-right font-bold text-gray-900">
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
                        {latest.cfo_im_net_operating_cash_flow !== null ? (
                            <table className="w-full text-sm">
                                <tbody className="divide-y divide-gray-200">
                                    <tr className="bg-green-50">
                                        <td className="py-2 font-semibold text-gray-900">Operatīvā darbība / Operating Activities</td>
                                        <td className="py-2 text-right font-bold text-gray-900">
                                            {formatCurrency(latest.cfo_im_net_operating_cash_flow)}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td className="py-2 text-gray-700 pl-4">↳ Samaksātie ienākuma nodokļi / Income Taxes Paid</td>
                                        <td className="py-2 text-right text-gray-900">{formatCurrency(latest.cfo_im_income_taxes_paid)}</td>
                                    </tr>
                                    <tr className="bg-orange-50">
                                        <td className="py-2 font-semibold text-gray-900">Ieguldījumu darbība / Investing Activities</td>
                                        <td className="py-2 text-right font-bold text-gray-900">
                                            {formatCurrency(latest.cfi_acquisition_of_fixed_assets_intangible_assets)}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td className="py-2 text-gray-700 pl-4">↳ CapEx (pamatlīdzekļi) / Fixed Assets</td>
                                        <td className="py-2 text-right text-gray-900">{formatCurrency(latest.cfi_acquisition_of_fixed_assets_intangible_assets)}</td>
                                    </tr>
                                    <tr className="bg-purple-50">
                                        <td className="py-2 font-semibold text-gray-900">Finansēšanas darbība / Financing Activities</td>
                                        <td className="py-2 text-right font-bold text-gray-900">
                                            {formatCurrency(latest.cff_net_financing_cash_flow)}
                                        </td>
                                    </tr>
                                    <tr className="bg-blue-100">
                                        <td className="py-2 font-bold text-gray-900">Kopējā naudas izmaiņa / Net Change in Cash</td>
                                        <td className="py-2 text-right font-bold text-gray-900">
                                            {formatCurrency(
                                                (latest.cfo_im_net_operating_cash_flow || 0) +
                                                (latest.cfi_acquisition_of_fixed_assets_intangible_assets || 0) +
                                                (latest.cff_net_financing_cash_flow || 0)
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
