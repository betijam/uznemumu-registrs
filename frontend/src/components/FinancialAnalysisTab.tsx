"use client";

import { useTranslations } from 'next-intl';
import RawDataAccordions from './RawDataAccordions';
import {
    calculateTrustScore,
    detectRedFlags,
    calculateDSO,
    calculateFCF,
    calculateOCFConversion,
    calculateYoYGrowth,
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
    const latest = financialHistory[0] || {};

    // Calculate Trust Score
    const trustScoreData = calculateTrustScore(latest);

    // Detect Red Flags
    const redFlags = detectRedFlags(latest);

    return (
        <div className="space-y-6">
            {/* Trust Score Section */}
            {trustScoreData && (
                <div className="border border-gray-200 rounded-lg p-6 bg-white">
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <h3 className="text-lg font-semibold text-gray-900">{t('trustScore')}</h3>
                            <p className="text-sm text-gray-600 mt-1">
                                {t('liquidityScore')} · {t('profitabilityScore')} · {t('capitalScore')}
                            </p>
                        </div>
                        <div className="text-right">
                            <div
                                className="text-5xl font-bold mb-2"
                                style={{ color: trustScoreData.riskColor }}
                            >
                                {trustScoreData.score}
                            </div>
                            <div
                                className="inline-block px-3 py-1 rounded-full text-sm font-medium text-white"
                                style={{ backgroundColor: trustScoreData.riskColor }}
                            >
                                {t(`risk${trustScoreData.riskLevel.charAt(0).toUpperCase()}${trustScoreData.riskLevel.slice(1)}`)}
                            </div>
                        </div>
                    </div>

                    {/* Sub-scores */}
                    <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-gray-200">
                        <div className="text-center">
                            <div className="text-2xl font-bold text-primary">{trustScoreData.liquidityScore}</div>
                            <div className="text-xs text-gray-600 mt-1">{t('liquidityScore')}</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-accent">{trustScoreData.profitabilityScore}</div>
                            <div className="text-xs text-gray-600 mt-1">{t('profitabilityScore')}</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-secondary">{trustScoreData.capitalScore}</div>
                            <div className="text-xs text-gray-600 mt-1">{t('capitalScore')}</div>
                        </div>
                    </div>
                </div>
            )}

            {/* Red Flags Section */}
            {redFlags.length > 0 && (
                <div className="border border-red-200 rounded-lg p-4 bg-red-50">
                    <div className="flex items-start gap-3">
                        <svg className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                        <div className="flex-1">
                            <h4 className="font-semibold text-red-900 mb-2">{t('redFlagsTitle')}</h4>
                            <ul className="space-y-1">
                                {redFlags.map((flag, idx) => (
                                    <li key={idx} className="text-sm text-red-800">
                                        • {flag.message}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </div>
                </div>
            )}

            {/* Cash Flow Analysis */}
            {latest.cfo_im_net_operating_cash_flow !== null && (
                <div className="border border-gray-200 rounded-lg p-6 bg-white">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('cashFlowTitle')}</h3>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {/* Net Profit */}
                        <div className="border border-gray-200 rounded-lg p-4">
                            <div className="text-sm text-gray-600 mb-2">{t('netProfit')}</div>
                            <div className="text-2xl font-bold text-gray-900">{formatCurrency(latest.profit)}</div>
                            {financialHistory[1]?.profit && (
                                <div className={`text-sm mt-2 ${(latest.profit - financialHistory[1].profit) >= 0 ? 'text-green-600' : 'text-red-600'
                                    }`}>
                                    {formatPercent(calculateYoYGrowth(latest.profit, financialHistory[1].profit))} {t('yoyChange')}
                                </div>
                            )}
                        </div>

                        {/* Operating Cash Flow */}
                        <div className="border border-gray-200 rounded-lg p-4">
                            <div className="text-sm text-gray-600 mb-2">{t('operatingCashFlow')}</div>
                            <div className="text-2xl font-bold text-gray-900">
                                {formatCurrency(latest.cfo_im_net_operating_cash_flow)}
                            </div>
                            {latest.profit && (
                                <div className="mt-3">
                                    <div className="flex justify-between text-xs text-gray-600 mb-1">
                                        <span>{t('conversionRate')}</span>
                                        <span>{formatPercent(calculateOCFConversion(latest.cfo_im_net_operating_cash_flow, latest.profit))}</span>
                                    </div>
                                    <div className="w-full bg-gray-200 rounded-full h-2">
                                        <div
                                            className={`h-2 rounded-full ${(calculateOCFConversion(latest.cfo_im_net_operating_cash_flow, latest.profit) || 0) < 80
                                                ? 'bg-redred-500'
                                                : 'bg-green-500'
                                                }`}
                                            style={{ width: `${Math.min(100, calculateOCFConversion(latest.cfo_im_net_operating_cash_flow, latest.profit) || 0)}%` }}
                                        />
                                    </div>
                                    {(calculateOCFConversion(latest.cfo_im_net_operating_cash_flow, latest.profit) || 0) < 80 && (
                                        <div className="text-xs text-red-600 mt-1">{t('lowConversion')}</div>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Free Cash Flow */}
                        <div className="border border-gray-200 rounded-lg p-4">
                            <div className="text-sm text-gray-600 mb-2">{t('freeCashFlow')}</div>
                            <div className="text-2xl font-bold text-gray-900">
                                {formatCurrency(calculateFCF(
                                    latest.cfo_im_net_operating_cash_flow,
                                    latest.cfi_acquisition_of_fixed_assets_intangible_assets
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Financial Health Indicators */}
            <div className="border border-gray-200 rounded-lg p-6 bg-white">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('healthIndicators')}</h3>

                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-gray-200">
                                <th className="text-left py-3 text-sm font-medium text-gray-700">{t('metric')}</th>
                                <th className="text-right py-3 text-sm font-medium text-gray-700">{t('value')}</th>
                                <th className="text-center py-3 text-sm font-medium text-gray-700">{t('trend')}</th>
                                <th className="text-right py-3 text-sm font-medium text-gray-700">{t('benchmark')}</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {/* Current Ratio */}
                            <tr>
                                <td className="py-3 text-sm text-gray-900">{t('currentRatio')}</td>
                                <td className="py-3 text-sm text-right font-semibold text-gray-900">
                                    {formatRatio(latest.current_ratio)}
                                </td>
                                <td className="py-3 text-center">
                                    {financialHistory.length >= 3 && (
                                        <div className="inline-flex items-center gap-1">
                                            {(() => {
                                                const recent = financialHistory.slice(0, 3).map(f => f.current_ratio).filter(v => v !== null);
                                                if (recent.length < 2) return <span className="text-gray-400">-</span>;
                                                const trend = recent[0] > recent[recent.length - 1] ? '↗' : recent[0] < recent[recent.length - 1] ? '↘' : '→';
                                                const color = recent[0] > recent[recent.length - 1] ? 'text-green-600' : recent[0] < recent[recent.length - 1] ? 'text-red-600' : 'text-gray-600';
                                                return <span className={`text-lg ${color}`}>{trend}</span>;
                                            })()}
                                        </div>
                                    )}
                                </td>
                                <td className="py-3 text-sm text-right text-gray-600">&gt; 1.2</td>
                            </tr>

                            {/* Cash Ratio */}
                            <tr>
                                <td className="py-3 text-sm text-gray-900">{t('cashRatio')}</td>
                                <td className="py-3 text-sm text-right font-semibold text-gray-900">
                                    {formatRatio(latest.cash_ratio)}
                                </td>
                                <td className="py-3 text-center">
                                    {financialHistory.length >= 3 && (
                                        <div className="inline-flex items-center gap-1">
                                            {(() => {
                                                const recent = financialHistory.slice(0, 3).map(f => f.cash_ratio).filter(v => v !== null);
                                                if (recent.length < 2) return <span className="text-gray-400">-</span>;
                                                const trend = recent[0] > recent[recent.length - 1] ? '↗' : recent[0] < recent[recent.length - 1] ? '↘' : '→';
                                                const color = recent[0] > recent[recent.length - 1] ? 'text-green-600' : recent[0] < recent[recent.length - 1] ? 'text-red-600' : 'text-gray-600';
                                                return <span className={`text-lg ${color}`}>{trend}</span>;
                                            })()}
                                        </div>
                                    )}
                                </td>
                                <td className="py-3 text-sm text-right text-gray-600">&gt; 0.2</td>
                            </tr>

                            {/* DSO */}
                            <tr>
                                <td className="py-3 text-sm text-gray-900">{t('dso')}</td>
                                <td className="py-3 text-sm text-right font-semibold text-gray-900">
                                    {latest.accounts_receivable && latest.turnover
                                        ? formatRatio(calculateDSO(latest.accounts_receivable, latest.turnover))
                                        : '-'}
                                </td>
                                <td className="py-3 text-center">-</td>
                                <td className="py-3 text-sm text-right text-gray-600">&lt; 45</td>
                            </tr>

                            {/* Net Profit Margin */}
                            <tr>
                                <td className="py-3 text-sm text-gray-900">{t('netProfitMargin')}</td>
                                <td className="py-3 text-sm text-right font-semibold text-gray-900">
                                    {formatPercent(latest.net_profit_margin)}
                                </td>
                                <td className="py-3 text-center">
                                    {financialHistory.length >= 3 && (
                                        <div className="inline-flex items-center gap-1">
                                            {(() => {
                                                const recent = financialHistory.slice(0, 3).map(f => f.net_profit_margin).filter(v => v !== null);
                                                if (recent.length < 2) return <span className="text-gray-400">-</span>;
                                                const trend = recent[0] > recent[recent.length - 1] ? '↗' : recent[0] < recent[recent.length - 1] ? '↘' : '→';
                                                const color = recent[0] > recent[recent.length - 1] ? 'text-green-600' : recent[0] < recent[recent.length - 1] ? 'text-red-600' : 'text-gray-600';
                                                return <span className={`text-lg ${color}`}>{trend}</span>;
                                            })()}
                                        </div>
                                    )}
                                </td>
                                <td className="py-3 text-sm text-right text-gray-600">&gt; 3%</td>
                            </tr>

                            {/* Debt to Equity */}
                            <tr>
                                <td className="py-3 text-sm text-gray-900">{t('debtToEquity')}</td>
                                <td className="py-3 text-sm text-right font-semibold text-gray-900">
                                    {formatRatio(latest.debt_to_equity)}
                                </td>
                                <td className="py-3 text-center">
                                    {financialHistory.length >= 3 && (
                                        <div className="inline-flex items-center gap-1">
                                            {(() => {
                                                const recent = financialHistory.slice(0, 3).map(f => f.debt_to_equity).filter(v => v !== null);
                                                if (recent.length < 2) return <span className="text-gray-400">-</span>;
                                                const trend = recent[0] > recent[recent.length - 1] ? '↗' : recent[0] < recent[recent.length - 1] ? '↘' : '→';
                                                const color = recent[0] < recent[recent.length - 1] ? 'text-green-600' : recent[0] > recent[recent.length - 1] ? 'text-red-600' : 'text-gray-600';
                                                return <span className={`text-lg ${color}`}>{trend}</span>;
                                            })()}
                                        </div>
                                    )}
                                </td>
                                <td className="py-3 text-sm text-right text-gray-600">&lt; 1.5</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Fiscal Discipline & Historical Dynamics */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Fiscal Discipline */}
                <div className="border border-gray-200 rounded-lg p-6 bg-white">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('fiscalDiscipline')}</h3>

                    {company.tax_history && company.tax_history[0] ? (
                        <div className="space-y-4">
                            <div className="flex justify-between items-center pb-3 border-b border-gray-100">
                                <span className="text-sm text-gray-600">{t('totalTaxes')}</span>
                                <span className="text-lg font-bold text-gray-900">
                                    {formatCurrency(company.tax_history[0].total_tax_paid)}
                                </span>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <div className="text-xs text-gray-500 mb-1">{t('iin')}</div>
                                    <div className="text-base font-semibold text-gray-900">
                                        {formatCurrency(company.tax_history[0].labor_tax_iin)}
                                    </div>
                                </div>
                                <div>
                                    <div className="text-xs text-gray-500 mb-1">{t('vsaoi')}</div>
                                    <div className="text-base font-semibold text-gray-900">
                                        {formatCurrency(company.tax_history[0].social_tax_vsaoi)}
                                    </div>
                                </div>
                            </div>

                            <div className="pt-3 border-t border-gray-100">
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-gray-600">{t('employeeCount')}</span>
                                    <span className="text-base font-semibold text-gray-900">
                                        {company.tax_history[0].avg_employees || '-'}
                                    </span>
                                </div>

                                {company.tax_history[0].avg_gross_salary && (
                                    <div className="flex justify-between items-center mt-2">
                                        <span className="text-sm text-gray-600">{t('avgSalary')}</span>
                                        <span className="text-base font-semibold text-gray-900">
                                            {formatCurrency(company.tax_history[0].avg_gross_salary)} <span className="text-xs text-gray-500">{t('perMonth')}</span>
                                        </span>
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="text-center py-8 text-gray-500 text-sm">{t('dataUnavailable')}</div>
                    )}
                </div>

                {/* Historical Dynamics */}
                <div className="border border-gray-200 rounded-lg p-6 bg-white">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('historicalDynamics')}</h3>

                    {financialHistory.length > 0 ? (
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-gray-200">
                                        <th className="text-left py-2 text-xs font-medium text-gray-600">{t('year')}</th>
                                        <th className="text-right py-2 text-xs font-medium text-gray-600">{t('turnover')}</th>
                                        <th className="text-right py-2 text-xs font-medium text-gray-600">{t('profit')}</th>
                                        <th className="text-right py-2 text-xs font-medium text-gray-600">{t('margin')}</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-50">
                                    {financialHistory.slice(0, 5).map((year: any) => (
                                        <tr key={year.year} className="hover:bg-gray-50">
                                            <td className="py-2 font-medium text-gray-900">{year.year}</td>
                                            <td className="py-2 text-right text-gray-700">
                                                {formatCurrency(year.turnover)}
                                                {year.turnover_growth !== null && year.turnover_growth !== undefined && (
                                                    <span className={`ml-2 text-xs ${year.turnover_growth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                                        {year.turnover_growth >= 0 ? '▲' : '▼'}{Math.abs(year.turnover_growth).toFixed(0)}%
                                                    </span>
                                                )}
                                            </td>
                                            <td className={`py-2 text-right ${(year.profit || 0) >= 0 ? 'text-gray-700' : 'text-red-600'}`}>
                                                {formatCurrency(year.profit)}
                                            </td>
                                            <td className="py-2 text-right text-gray-600">
                                                {formatPercent(year.net_profit_margin)}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ) : (
                        <div className="text-center py-8 text-gray-500 text-sm">{t('dataUnavailable')}</div>
                    )}
                </div>
            </div>

            {/* Raw Data Accordions */}
            <RawDataAccordions financialHistory={financialHistory} />
        </div>
    );
}
