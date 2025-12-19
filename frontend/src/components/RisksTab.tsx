"use client";

import RiskLevelBadge from './RiskLevelBadge';

interface RisksTabProps {
    company: any;
}

export default function RisksTab({ company }: RisksTabProps) {
    const risks = company.risks || {
        sanctions: [],
        liquidations: [],
        suspensions: [],
        securing_measures: []
    };

    const totalRiskScore = company.total_risk_score || 0;
    const riskLevel = company.risk_level || 'NONE';

    const formatDate = (dateStr: string | null) => {
        if (!dateStr) return '-';
        return new Date(dateStr).toLocaleDateString('lv-LV');
    };

    return (
        <div className="space-y-6">
            {/* Header with Risk Level */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">Riski un Tiesvedības</h2>
                    <p className="text-sm text-gray-600 mt-1">
                        Sankcijas, likvidācijas, aizliegumi un nodrošinājumi
                    </p>
                </div>
                <RiskLevelBadge level={riskLevel} score={totalRiskScore} size="lg" />
            </div>

            {/* SANCTIONS - CRITICAL */}
            {risks.sanctions && risks.sanctions.length > 0 ? (
                <div className="border-2 border-red-600 rounded-lg overflow-hidden bg-red-50">
                    <div className="bg-red-600 px-6 py-4">
                        <div className="flex items-center gap-3">
                            <span className="text-3xl">🔴</span>
                            <div>
                                <h3 className="text-xl font-bold text-white">
                                    UZMANĪBU: SUBJEKTS ATRODAS SANKCIJU SARAKSTOS
                                </h3>
                                <p className="text-red-100 text-sm mt-1">
                                    Ar šo uzņēmumu nedrīkst veikt darījumus
                                </p>
                            </div>
                        </div>
                    </div>
                    <div className="p-6 space-y-4">
                        {risks.sanctions.map((sanction: any, idx: number) => (
                            <div key={idx} className="bg-white border border-red-200 rounded-lg p-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <div className="text-xs text-gray-500 uppercase">Programma</div>
                                        <div className="text-sm font-semibold text-gray-900 mt-1">
                                            {sanction.program || 'Nav norādīts'}
                                        </div>
                                    </div>
                                    <div>
                                        <div className="text-xs text-gray-500 uppercase">Datums</div>
                                        <div className="text-sm font-semibold text-gray-900 mt-1">
                                            {formatDate(sanction.date)}
                                        </div>
                                    </div>
                                    <div className="col-span-2">
                                        <div className="text-xs text-gray-500 uppercase">Saraksts</div>
                                        <div className="text-sm text-gray-900 mt-1">
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
                                                📄 Skatīt oficiālo dokumentu →
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
                        <span className="text-2xl">✅</span>
                        <div>
                            <div className="font-semibold text-success">Sankcijas: Nav atrasts</div>
                            <div className="text-sm text-gray-600">Uzņēmums neatrodas sankciju sarakstos</div>
                        </div>
                    </div>
                </div>
            )}

            {/* LIQUIDATIONS */}
            {risks.liquidations && risks.liquidations.length > 0 ? (
                <div className="border-2 border-gray-800 rounded-lg overflow-hidden">
                    <div className="bg-gray-800 px-6 py-3">
                        <div className="flex items-center gap-3">
                            <span className="text-2xl">⚫</span>
                            <h3 className="text-lg font-bold text-white">
                                LIKVIDĀCIJAS PROCESS
                            </h3>
                        </div>
                    </div>
                    <div className="p-6 bg-gray-50 space-y-3">
                        {risks.liquidations.map((liq: any, idx: number) => (
                            <div key={idx} className="bg-white border border-gray-300 rounded-lg p-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <div className="text-xs text-gray-500 uppercase">Veids</div>
                                        <div className="text-sm font-semibold text-gray-900 mt-1">
                                            {liq.liquidation_type || 'Nav norādīts'}
                                        </div>
                                    </div>
                                    <div>
                                        <div className="text-xs text-gray-500 uppercase">Sākuma datums</div>
                                        <div className="text-sm font-semibold text-gray-900 mt-1">
                                            {formatDate(liq.date)}
                                        </div>
                                    </div>
                                    <div className="col-span-2">
                                        <div className="text-xs text-gray-500 uppercase">Pamatojums</div>
                                        <div className="text-sm text-gray-900 mt-1">
                                            {liq.grounds || '-'}
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
                            <span className="text-2xl">🟡</span>
                            <h3 className="text-lg font-bold text-white">
                                AKTĪVIE AIZLIEGUMI
                            </h3>
                        </div>
                    </div>
                    <div className="p-6 bg-yellow-50 space-y-3">
                        {risks.suspensions.map((susp: any, idx: number) => (
                            <div key={idx} className="bg-white border border-yellow-300 rounded-lg p-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <div className="text-xs text-gray-500 uppercase">Aizlieguma veids</div>
                                        <div className="text-sm font-semibold text-gray-900 mt-1">
                                            {susp.suspension_code || 'Nav norādīts'}
                                        </div>
                                    </div>
                                    <div>
                                        <div className="text-xs text-gray-500 uppercase">Reģistrēts</div>
                                        <div className="text-sm font-semibold text-gray-900 mt-1">
                                            {formatDate(susp.date)}
                                        </div>
                                    </div>
                                    <div className="col-span-2">
                                        <div className="text-xs text-gray-500 uppercase">Iemesls</div>
                                        <div className="text-sm text-gray-900 mt-1">
                                            {susp.grounds || '-'}
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
                                <span className="text-2xl">🟠</span>
                                <h3 className="text-lg font-bold text-gray-900">
                                    Nodrošinājuma Līdzekļi
                                </h3>
                            </div>
                            <div className="text-sm font-semibold text-orange-600">
                                Aktīvie: {risks.securing_measures.length}
                            </div>
                        </div>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-gray-50 border-b border-gray-200">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                        Datums
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                        Veids
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                        Iniciators (Iestāde)
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                        Lietas numurs
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
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            ) : null}

            {/* No Risks Message */}
            {totalRiskScore === 0 && (
                <div className="border border-success rounded-lg p-8 bg-success/5 text-center">
                    <div className="text-6xl mb-4">✅</div>
                    <h3 className="text-xl font-bold text-success mb-2">
                        Nav Identificētu Risku
                    </h3>
                    <p className="text-gray-600">
                        Uzņēmumam nav aktīvu sankciju, likvidācijas procesu, aizliegumu vai nodrošinājumu
                    </p>
                </div>
            )}

            {/* Info Box */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex gap-3">
                    <div className="text-blue-600 text-xl">ℹ️</div>
                    <div className="flex-1">
                        <h4 className="text-sm font-semibold text-blue-900 mb-1">
                            Par Riska Vērtējumu
                        </h4>
                        <p className="text-xs text-blue-800">
                            Riska līmenis tiek aprēķināts automātiski: Sankcijas (+100), Likvidācija (+50),
                            Aizliegumi (+30), Nodrošinājumi (+10). Kopējais rādītājs norāda uz uzņēmuma
                            tiesisko un finansiālo stabilitāti.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
