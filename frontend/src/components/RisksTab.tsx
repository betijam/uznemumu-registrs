"use client";

import { useTranslations } from 'next-intl';
import { useState, useEffect } from 'react';
import RiskLevelBadge from './RiskLevelBadge';

interface RisksTabProps {
    company: any;
}

export default function RisksTab({ company }: RisksTabProps) {
    const t = useTranslations('RisksTab');

    // State for lazy-loaded risk data
    const [riskData, setRiskData] = useState<any>(company.risks ? {
        risks: company.risks,
        total_risk_score: company.total_risk_score,
        risk_level: company.risk_level
    } : null);

    const [isLoading, setIsLoading] = useState(!company.risks);

    // Sync state with prop if it arrives later (from CompanyTabs lazy load)
    useEffect(() => {
        if (company.risks && !riskData) {
            setRiskData({
                risks: company.risks,
                total_risk_score: company.total_risk_score,
                risk_level: company.risk_level
            });
            setIsLoading(false);
        }
    }, [company.risks, company.total_risk_score, company.risk_level]);

    useEffect(() => {
        // Fetch only if we don't have data in prop AND we haven't fetched it yet
        if (!riskData && !company.risks) {
            const fetchRisks = async () => {
                try {
                    setIsLoading(true);
                    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
                    const res = await fetch(`${API_BASE_URL}/companies/${company.regcode}/risks`);
                    if (res.ok) {
                        const data = await res.json();
                        setRiskData(data);
                    }
                } catch (e) {
                    console.error("Failed to fetch risks", e);
                } finally {
                    setIsLoading(false);
                }
            };
            fetchRisks();
        } else {
            setIsLoading(false);
        }
    }, [company.regcode, riskData]);

    const risks = riskData?.risks || {
        sanctions: [],
        liquidations: [],
        suspensions: [],
        securing_measures: []
    };

    // Use fetched values -> then fallback to summary from 'quick' -> then company root props -> then defaults
    const totalRiskScore = riskData?.total_risk_score ?? company.risk_summary?.total_score ?? company.total_risk_score ?? 0;
    const riskLevel = riskData?.risk_level ?? company.risk_summary?.level ?? company.risk_level ?? 'NONE';

    const formatDate = (dateStr: string | null) => {
        if (!dateStr) return '-';
        return new Date(dateStr).toLocaleDateString('lv-LV');
    };

    const hasRisks =
        (risks.sanctions && risks.sanctions.length > 0) ||
        (risks.liquidations && risks.liquidations.length > 0) ||
        (risks.suspensions && risks.suspensions.length > 0) ||
        (risks.securing_measures && risks.securing_measures.length > 0);

    return (
        <div className="space-y-6">
            {/* Header with Risk Level */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">{t('title')}</h2>
                    <p className="text-sm text-gray-600 mt-1">
                        {t('subtitle')}
                    </p>
                </div>
                <RiskLevelBadge level={riskLevel} score={totalRiskScore} size="lg" />
            </div>

            {/* Loading State */}
            {isLoading && (
                <div className="flex justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
            )}

            {!isLoading && (
                <>
                    {/* SANCTIONS - CRITICAL */}
                    {risks.sanctions && risks.sanctions.length > 0 ? (
                        <div className="border-2 border-red-600 rounded-lg overflow-hidden bg-red-50">
                            <div className="bg-red-600 px-6 py-4">
                                <div className="flex items-center gap-3">

                                    <div>
                                        <h3 className="text-xl font-bold text-white">
                                            {t('sanctions_alert_title')}
                                        </h3>
                                        <p className="text-red-100 text-sm mt-1">
                                            {t('sanctions_alert_desc')}
                                        </p>
                                    </div>
                                </div>
                            </div>
                            <div className="p-6 space-y-4">
                                {risks.sanctions.map((sanction: any, idx: number) => (
                                    <div key={idx} className="bg-white border border-red-200 rounded-lg p-4">
                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <div className="text-xs text-gray-500 uppercase">{t('program')}</div>
                                                <div className="text-sm font-semibold text-gray-900 mt-1">
                                                    {sanction.program || t('not_specified')}
                                                </div>
                                            </div>
                                            <div>
                                                <div className="text-xs text-gray-500 uppercase">{t('date')}</div>
                                                <div className="text-sm font-semibold text-gray-900 mt-1">
                                                    {formatDate(sanction.date)}
                                                </div>
                                            </div>
                                            <div className="col-span-1">
                                                <div className="text-xs text-gray-500 uppercase">Score</div>
                                                <div className="text-sm font-bold text-red-600 mt-1">
                                                    +{sanction.score || 100}
                                                </div>
                                            </div>
                                            <div className="col-span-1">
                                                <div className="text-xs text-gray-500 uppercase">{t('list')}</div>
                                                <div className="text-sm text-gray-900 mt-1 line-clamp-1">
                                                    {sanction.list_text || '-'}
                                                </div>
                                            </div>
                                            {sanction.legal_base_url && (
                                                <div className="col-span-2">
                                                    <a
                                                        href={sanction.legal_base_url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="text-sm text-blue-600 hover:underline"
                                                    >
                                                        📄 {t('view_official_doc')}
                                                    </a>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="border border-success rounded-lg p-4 bg-success/5">
                            <div className="flex items-center gap-3">

                                <div>
                                    <div className="font-semibold text-success">{t('sanctions_none_title')}</div>
                                    <div className="text-sm text-gray-600">{t('sanctions_none_desc')}</div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* LIQUIDATIONS */}
                    {risks.liquidations && risks.liquidations.length > 0 ? (
                        <div className="border-2 border-gray-800 rounded-lg overflow-hidden">
                            <div className="bg-gray-800 px-6 py-3">
                                <div className="flex items-center gap-3">

                                    <h3 className="text-lg font-bold text-white">
                                        {t('liquidation_title')}
                                    </h3>
                                </div>
                            </div>
                            <div className="p-6 bg-gray-50 space-y-3">
                                {risks.liquidations.map((liq: any, idx: number) => (
                                    <div key={idx} className="bg-white border border-gray-300 rounded-lg p-4">
                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <div className="text-xs text-gray-500 uppercase">{t('type')}</div>
                                                <div className="text-sm font-semibold text-gray-900 mt-1">
                                                    {liq.liquidation_type || t('not_specified')}
                                                </div>
                                            </div>
                                            <div>
                                                <div className="text-xs text-gray-500 uppercase">{t('start_date')}</div>
                                                <div className="text-sm font-semibold text-gray-900 mt-1">
                                                    {formatDate(liq.date)}
                                                </div>
                                            </div>
                                            <div className="col-span-1">
                                                <div className="text-xs text-gray-500 uppercase">{t('grounds')}</div>
                                                <div className="text-sm text-gray-900 mt-1">
                                                    {liq.grounds || '-'}
                                                </div>
                                            </div>
                                            <div className="col-span-1">
                                                <div className="text-xs text-gray-500 uppercase">Score</div>
                                                <div className="text-sm font-bold text-gray-900 mt-1">
                                                    +{liq.score || 50}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : null}

                    {/* SUSPENSIONS & PROHIBITIONS */}
                    {risks.suspensions && risks.suspensions.length > 0 ? (
                        <div className="border border-yellow-500 rounded-lg overflow-hidden">
                            <div className="bg-yellow-500 px-6 py-3">
                                <div className="flex items-center gap-3">

                                    <h3 className="text-lg font-bold text-white">
                                        {t('prohibitions_title')}
                                    </h3>
                                </div>
                            </div>
                            <div className="p-6 bg-yellow-50 space-y-3">
                                {risks.suspensions.map((susp: any, idx: number) => (
                                    <div key={idx} className="bg-white border border-yellow-300 rounded-lg p-4">
                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <div className="text-xs text-gray-500 uppercase">{t('prohibition_type')}</div>
                                                <div className="text-sm font-semibold text-gray-900 mt-1">
                                                    {susp.suspension_code || t('not_specified')}
                                                </div>
                                            </div>
                                            <div>
                                                <div className="text-xs text-gray-500 uppercase">{t('registered')}</div>
                                                <div className="text-sm font-semibold text-gray-900 mt-1">
                                                    {formatDate(susp.date)}
                                                </div>
                                            </div>
                                            <div className="col-span-1">
                                                <div className="text-xs text-gray-500 uppercase">{t('reason')}</div>
                                                <div className="text-sm text-gray-900 mt-1">
                                                    {susp.grounds || '-'}
                                                </div>
                                            </div>
                                            <div className="col-span-1">
                                                <div className="text-xs text-gray-500 uppercase">Score</div>
                                                <div className="text-sm font-bold text-gray-900 mt-1">
                                                    +{susp.score || 30}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : null}

                    {/* SECURING MEASURES */}
                    {risks.securing_measures && risks.securing_measures.length > 0 ? (
                        <div className="border border-orange-400 rounded-lg overflow-hidden bg-white">
                            <div className="px-6 py-4 bg-orange-50 border-b border-orange-200">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">

                                        <h3 className="text-lg font-bold text-gray-900">
                                            {t('security_measures_title')}
                                        </h3>
                                    </div>
                                    <div className="text-sm font-semibold text-orange-600">
                                        {t('active_count', { count: risks.securing_measures.length })}
                                    </div>
                                </div>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full">
                                    <thead className="bg-gray-50 border-b border-gray-200">
                                        <tr>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                                {t('date')}
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                                {t('type')}
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                                {t('initiator')}
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                                {t('case_number')}
                                            </th>
                                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                                                Score
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-200">
                                        {risks.securing_measures.map((measure: any, idx: number) => (
                                            <tr key={idx} className="hover:bg-gray-50">
                                                <td className="px-6 py-4 text-sm text-gray-900">
                                                    {formatDate(measure.date)}
                                                </td>
                                                <td className="px-6 py-4 text-sm text-gray-900">
                                                    {measure.measure_type || '-'}
                                                </td>
                                                <td className="px-6 py-4 text-sm text-gray-900">
                                                    {measure.institution || '-'}
                                                </td>
                                                <td className="px-6 py-4 text-sm text-gray-600 font-mono">
                                                    {measure.case_number || '-'}
                                                </td>
                                                <td className="px-6 py-4 text-sm text-right font-bold text-gray-900">
                                                    +{measure.score || 10}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    ) : null}

                    {/* No Risks Message */}
                    {!hasRisks && (
                        <div className="border border-success rounded-lg p-8 bg-success/5 text-center">

                            <h3 className="text-xl font-bold text-success mb-2">
                                {t('no_risks_title')}
                            </h3>
                            <p className="text-gray-600">
                                {t('no_risks_desc')}
                            </p>
                        </div>
                    )}
                </>
            )}

            {/* Info Box */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex gap-3">

                    <div className="flex-1">
                        <h4 className="text-sm font-semibold text-blue-900 mb-1">
                            {t('risk_assessment_title')}
                        </h4>
                        <p className="text-xs text-blue-800">
                            {t('risk_assessment_desc')}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
