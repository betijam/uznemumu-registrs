"use client";

interface CompanyData {
    regNumber: string;
    name: string;
    industryCode: string;
    industryName: string;
    financials: {
        revenue: number | null;
        profitMargin: number | null;
    };
    workforce: {
        avgSalary: number | null;
        revenuePerEmployee: number | null;
    };
    industryBenchmark: {
        avgRevenue: number | null;
        avgProfitMargin: number | null;
        avgSalary: number | null;
        avgRevenuePerEmployee: number | null;
        positionByRevenue: {
            rank: number;
            total: number;
            percentile: number;
        } | null;
    } | null;
}

interface IndustryViewProps {
    companies: CompanyData[];
}

export default function IndustryView({ companies }: IndustryViewProps) {
    const formatCurrency = (val: number | null) => {
        if (val === null || val === undefined) return '-';
        return `€${val.toLocaleString('lv-LV', { maximumFractionDigits: 0 })}`;
    };

    const formatPercent = (val: number | null) => {
        if (val === null || val === undefined) return '-';
        return `${val.toFixed(2)}%`;
    };

    const getPercentileBadge = (percentile: number | null) => {
        if (percentile === null) return null;

        let color = '';
        let label = '';

        if (percentile >= 90) {
            color = 'bg-green-100 text-green-800 border-green-200';
            label = 'Top 10%';
        } else if (percentile >= 75) {
            color = 'bg-blue-100 text-blue-800 border-blue-200';
            label = 'Top 25%';
        } else if (percentile >= 50) {
            color = 'bg-yellow-100 text-yellow-800 border-yellow-200';
            label = 'Top 50%';
        } else {
            color = 'bg-gray-100 text-gray-800 border-gray-200';
            label = 'Apakšējā puse';
        }

        return (
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${color}`}>
                {label}
            </span>
        );
    };

    const calculateDifference = (actual: number | null, average: number | null): string => {
        if (actual === null || average === null || average === 0) return '-';
        const diff = ((actual - average) / average) * 100;
        const sign = diff >= 0 ? '+' : '';
        return `${sign}${diff.toFixed(1)}%`;
    };

    const getDifferenceColor = (actual: number | null, average: number | null): string => {
        if (actual === null || average === null) return 'text-gray-500';
        return actual >= average ? 'text-green-600' : 'text-red-600';
    };

    return (
        <div className="space-y-6">
            {companies.map((company) => (
                <div key={company.regNumber} className="bg-white rounded-lg shadow-lg p-6">
                    {/* Company Header */}
                    <div className="mb-6 pb-4 border-b border-gray-200">
                        <div className="flex items-start justify-between">
                            <div>
                                <h3 className="text-xl font-bold text-gray-900">{company.name}</h3>
                                <p className="text-sm text-gray-600 mt-1">{company.industryName}</p>
                            </div>
                            {company.industryBenchmark?.positionByRevenue && (
                                <div>
                                    {getPercentileBadge(company.industryBenchmark.positionByRevenue.percentile)}
                                </div>
                            )}
                        </div>
                    </div>

                    {company.industryBenchmark ? (
                        <>
                            {/* Ranking Info */}
                            {company.industryBenchmark.positionByRevenue && (
                                <div className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
                                    <div className="flex items-center gap-2 mb-2">
                                        <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                                        </svg>
                                        <h4 className="font-semibold text-blue-900">Pozīcija nozarē</h4>
                                    </div>
                                    <div className="grid grid-cols-3 gap-4">
                                        <div>
                                            <p className="text-xs text-blue-600 mb-1">Vieta</p>
                                            <p className="text-2xl font-bold text-blue-900">
                                                #{company.industryBenchmark.positionByRevenue.rank}
                                            </p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-blue-600 mb-1">No kopējā</p>
                                            <p className="text-2xl font-bold text-blue-900">
                                                {company.industryBenchmark.positionByRevenue.total}
                                            </p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-blue-600 mb-1">Percentile</p>
                                            <p className="text-2xl font-bold text-blue-900">
                                                {company.industryBenchmark.positionByRevenue.percentile.toFixed(1)}%
                                            </p>
                                        </div>
                                    </div>
                                    <p className="text-sm text-blue-700 mt-3">
                                        Šis uzņēmums atrodas <strong>top {(100 - company.industryBenchmark.positionByRevenue.percentile).toFixed(0)}%</strong> savā nozarē pēc apgrozījuma
                                    </p>
                                </div>
                            )}

                            {/* Comparison Table */}
                            <div className="overflow-hidden border border-gray-200 rounded-lg">
                                <table className="w-full">
                                    <thead className="bg-gray-50">
                                        <tr>
                                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                                Rādītājs
                                            </th>
                                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                                                Uzņēmums
                                            </th>
                                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                                                Nozares vidējais
                                            </th>
                                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                                                Atšķirība
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody className="bg-white divide-y divide-gray-200">
                                        {/* Revenue */}
                                        <tr>
                                            <td className="px-4 py-3 text-sm font-medium text-gray-900">
                                                Apgrozījums
                                            </td>
                                            <td className="px-4 py-3 text-sm text-right font-semibold text-gray-900">
                                                {formatCurrency(company.financials.revenue)}
                                            </td>
                                            <td className="px-4 py-3 text-sm text-right text-gray-600">
                                                {formatCurrency(company.industryBenchmark.avgRevenue)}
                                            </td>
                                            <td className={`px-4 py-3 text-sm text-right font-semibold ${getDifferenceColor(company.financials.revenue, company.industryBenchmark.avgRevenue)
                                                }`}>
                                                {calculateDifference(company.financials.revenue, company.industryBenchmark.avgRevenue)}
                                            </td>
                                        </tr>

                                        {/* Profit Margin */}
                                        <tr className="bg-gray-50">
                                            <td className="px-4 py-3 text-sm font-medium text-gray-900">
                                                Peļņas marža
                                            </td>
                                            <td className="px-4 py-3 text-sm text-right font-semibold text-gray-900">
                                                {formatPercent(company.financials.profitMargin)}
                                            </td>
                                            <td className="px-4 py-3 text-sm text-right text-gray-600">
                                                {formatPercent(company.industryBenchmark.avgProfitMargin)}
                                            </td>
                                            <td className={`px-4 py-3 text-sm text-right font-semibold ${getDifferenceColor(company.financials.profitMargin, company.industryBenchmark.avgProfitMargin)
                                                }`}>
                                                {calculateDifference(company.financials.profitMargin, company.industryBenchmark.avgProfitMargin)}
                                            </td>
                                        </tr>

                                        {/* Average Salary */}
                                        <tr>
                                            <td className="px-4 py-3 text-sm font-medium text-gray-900">
                                                Vidējā alga
                                            </td>
                                            <td className="px-4 py-3 text-sm text-right font-semibold text-gray-900">
                                                {formatCurrency(company.workforce.avgSalary)}
                                            </td>
                                            <td className="px-4 py-3 text-sm text-right text-gray-600">
                                                {formatCurrency(company.industryBenchmark.avgSalary)}
                                            </td>
                                            <td className={`px-4 py-3 text-sm text-right font-semibold ${getDifferenceColor(company.workforce.avgSalary, company.industryBenchmark.avgSalary)
                                                }`}>
                                                {calculateDifference(company.workforce.avgSalary, company.industryBenchmark.avgSalary)}
                                            </td>
                                        </tr>

                                        {/* Revenue per Employee */}
                                        <tr className="bg-gray-50">
                                            <td className="px-4 py-3 text-sm font-medium text-gray-900">
                                                Apgrozījums / darbinieks
                                            </td>
                                            <td className="px-4 py-3 text-sm text-right font-semibold text-gray-900">
                                                {formatCurrency(company.workforce.revenuePerEmployee)}
                                            </td>
                                            <td className="px-4 py-3 text-sm text-right text-gray-600">
                                                {formatCurrency(company.industryBenchmark.avgRevenuePerEmployee)}
                                            </td>
                                            <td className={`px-4 py-3 text-sm text-right font-semibold ${getDifferenceColor(company.workforce.revenuePerEmployee, company.industryBenchmark.avgRevenuePerEmployee)
                                                }`}>
                                                {calculateDifference(company.workforce.revenuePerEmployee, company.industryBenchmark.avgRevenuePerEmployee)}
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </>
                    ) : (
                        <div className="text-center py-8 text-gray-500">
                            <svg className="w-12 h-12 mx-auto mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            <p>Nav pieejami nozares salīdzinājuma dati šim uzņēmumam</p>
                        </div>
                    )}
                </div>
            ))}

            {/* Legend */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
                <h4 className="font-semibold text-gray-900 mb-3">Kā lasīt šos datus</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-700">
                    <div>
                        <p className="font-medium text-gray-900 mb-1">Percentile</p>
                        <p>Rāda, cik % no nozares uzņēmumiem ir ar zemāku apgrozījumu. Augstāks = labāk.</p>
                    </div>
                    <div>
                        <p className="font-medium text-gray-900 mb-1">Atšķirība</p>
                        <p>Zaļš = virs nozares vidējā. Sarkans = zem nozares vidējā.</p>
                    </div>
                    <div>
                        <p className="font-medium text-gray-900 mb-1">Top 10%</p>
                        <p>Uzņēmums ir starp 10% lielākajiem nozarē pēc apgrozījuma.</p>
                    </div>
                    <div>
                        <p className="font-medium text-gray-900 mb-1">Nozares vidējais</p>
                        <p>Aprēķināts no visiem aktīvajiem uzņēmumiem šajā nozarē.</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
