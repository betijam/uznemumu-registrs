"use client";

import { useState } from 'react';
import { Line } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    ChartOptions
} from 'chart.js';

// Register ChartJS components
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

interface CompanyData {
    regNumber: string;
    name: string;
    financials: {
        revenue: number | null;
        profit: number | null;
        profitMargin: number | null;
        ebitda: number | null;
        assetsTotal: number | null;
        equityTotal: number | null;
        roe: number | null;
        roa: number | null;
    };
    trend: {
        revenue: { year: number; value: number }[];
        employees: { year: number; value: number }[];
    };
}

interface FinancialViewProps {
    companies: CompanyData[];
}

type ChartMetric = 'revenue' | 'profit';

export default function FinancialView({ companies }: FinancialViewProps) {
    const [sortColumn, setSortColumn] = useState<string>('revenue');
    const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
    const [chartMetric, setChartMetric] = useState<ChartMetric>('revenue');

    const formatCurrency = (val: number | null) => {
        if (val === null || val === undefined) return '-';
        return `€${val.toLocaleString('lv-LV', { maximumFractionDigits: 0 })}`;
    };

    const formatPercent = (val: number | null) => {
        if (val === null || val === undefined) return '-';
        return `${val.toFixed(2)}%`;
    };

    // Sorting logic
    const sortedCompanies = [...companies].sort((a, b) => {
        let aVal: any, bVal: any;

        switch (sortColumn) {
            case 'revenue':
                aVal = a.financials.revenue || 0;
                bVal = b.financials.revenue || 0;
                break;
            case 'profit':
                aVal = a.financials.profit || 0;
                bVal = b.financials.profit || 0;
                break;
            case 'profitMargin':
                aVal = a.financials.profitMargin || 0;
                bVal = b.financials.profitMargin || 0;
                break;
            case 'ebitda':
                aVal = a.financials.ebitda || 0;
                bVal = b.financials.ebitda || 0;
                break;
            case 'roe':
                aVal = a.financials.roe || 0;
                bVal = b.financials.roe || 0;
                break;
            case 'roa':
                aVal = a.financials.roa || 0;
                bVal = b.financials.roa || 0;
                break;
            default:
                return 0;
        }

        return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
    });

    const handleSort = (column: string) => {
        if (sortColumn === column) {
            setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
        } else {
            setSortColumn(column);
            setSortDirection('desc');
        }
    };

    // Chart data preparation
    const prepareChartData = () => {
        const allYears = new Set<number>();
        companies.forEach(company => {
            company.trend.revenue.forEach(point => allYears.add(point.year));
        });
        const years = Array.from(allYears).sort();

        const datasets = companies.map((company, index) => {
            const colors = [
                'rgb(59, 130, 246)', // blue
                'rgb(16, 185, 129)', // green
                'rgb(249, 115, 22)', // orange
                'rgb(139, 92, 246)', // purple
                'rgb(236, 72, 153)'  // pink
            ];

            const color = colors[index % colors.length];

            const data = years.map(year => {
                const point = company.trend.revenue.find(p => p.year === year);
                return point ? point.value : null;
            });

            return {
                label: company.name,
                data: data,
                borderColor: color,
                backgroundColor: color,
                tension: 0.3,
                spanGaps: true
            };
        });

        return {
            labels: years,
            datasets: datasets
        };
    };

    const chartOptions: ChartOptions<'line'> = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top' as const,
            },
            title: {
                display: true,
                text: chartMetric === 'revenue' ? 'Apgrozījuma dinamika' : 'Peļņas dinamika',
                font: {
                    size: 16,
                    weight: 'bold'
                }
            },
            tooltip: {
                callbacks: {
                    label: function (context) {
                        let label = context.dataset.label || '';
                        if (label) {
                            label += ': ';
                        }
                        if (context.parsed.y !== null) {
                            label += '€' + context.parsed.y.toLocaleString('lv-LV');
                        }
                        return label;
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                ticks: {
                    callback: function (value) {
                        return '€' + Number(value).toLocaleString('lv-LV');
                    }
                }
            }
        }
    };

    const SortIcon = ({ column }: { column: string }) => {
        if (sortColumn !== column) {
            return (
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                </svg>
            );
        }
        return sortDirection === 'asc' ? (
            <svg className="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
            </svg>
        ) : (
            <svg className="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
        );
    };

    return (
        <div className="space-y-6">
            {/* Comparison Table */}
            <div className="bg-white rounded-lg shadow-lg overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200">
                    <h2 className="text-lg font-bold text-gray-900">Finanšu rādītāju salīdzinājums</h2>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sticky left-0 bg-gray-50">
                                    Uzņēmums
                                </th>
                                <th
                                    className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                    onClick={() => handleSort('revenue')}
                                >
                                    <div className="flex items-center justify-end gap-1">
                                        Apgrozījums
                                        <SortIcon column="revenue" />
                                    </div>
                                </th>
                                <th
                                    className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                    onClick={() => handleSort('profit')}
                                >
                                    <div className="flex items-center justify-end gap-1">
                                        Peļņa
                                        <SortIcon column="profit" />
                                    </div>
                                </th>
                                <th
                                    className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                    onClick={() => handleSort('profitMargin')}
                                >
                                    <div className="flex items-center justify-end gap-1">
                                        Peļņas marža
                                        <SortIcon column="profitMargin" />
                                    </div>
                                </th>
                                <th
                                    className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                    onClick={() => handleSort('ebitda')}
                                >
                                    <div className="flex items-center justify-end gap-1">
                                        EBITDA
                                        <SortIcon column="ebitda" />
                                    </div>
                                </th>
                                <th
                                    className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                    onClick={() => handleSort('roe')}
                                >
                                    <div className="flex items-center justify-end gap-1">
                                        ROE
                                        <SortIcon column="roe" />
                                    </div>
                                </th>
                                <th
                                    className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                    onClick={() => handleSort('roa')}
                                >
                                    <div className="flex items-center justify-end gap-1">
                                        ROA
                                        <SortIcon column="roa" />
                                    </div>
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {sortedCompanies.map((company, index) => (
                                <tr key={company.regNumber} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 sticky left-0 bg-inherit">
                                        {company.name}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900 font-semibold">
                                        {formatCurrency(company.financials.revenue)}
                                    </td>
                                    <td className={`px-6 py-4 whitespace-nowrap text-sm text-right font-semibold ${(company.financials.profit || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                                        }`}>
                                        {formatCurrency(company.financials.profit)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-700">
                                        {formatPercent(company.financials.profitMargin)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-700">
                                        {formatCurrency(company.financials.ebitda)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-700">
                                        {formatPercent(company.financials.roe)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-700">
                                        {formatPercent(company.financials.roa)}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Trend Chart */}
            <div className="bg-white rounded-lg shadow-lg p-6">
                <div className="mb-4 flex items-center justify-between">
                    <h2 className="text-lg font-bold text-gray-900">Dinamika (pēdējie 5 gadi)</h2>
                    <div className="flex gap-2">
                        <button
                            onClick={() => setChartMetric('revenue')}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${chartMetric === 'revenue'
                                    ? 'bg-primary text-white'
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                }`}
                        >
                            Apgrozījums
                        </button>
                        <button
                            onClick={() => setChartMetric('profit')}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${chartMetric === 'profit'
                                    ? 'bg-primary text-white'
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                }`}
                            disabled
                        >
                            Peļņa (drīzumā)
                        </button>
                    </div>
                </div>
                <div className="h-96">
                    <Line data={prepareChartData()} options={chartOptions} />
                </div>
            </div>
        </div>
    );
}
