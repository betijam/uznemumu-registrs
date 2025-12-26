"use client";

import { useState } from 'react';
import { Bar } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    ChartOptions
} from 'chart.js';

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
);

interface CompanyData {
    regNumber: string;
    name: string;
    workforce: {
        employees: number | null;
        avgSalary: number | null;
        revenuePerEmployee: number | null;
    };
    trend: {
        revenue: { year: number; value: number }[];
        employees: { year: number; value: number }[];
    };
}

interface WorkforceViewProps {
    companies: CompanyData[];
}

export default function WorkforceView({ companies }: WorkforceViewProps) {
    const [sortColumn, setSortColumn] = useState<string>('employees');
    const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

    const formatNumber = (val: number | null) => {
        if (val === null || val === undefined) return '-';
        return val.toLocaleString('lv-LV');
    };

    const formatCurrency = (val: number | null) => {
        if (val === null || val === undefined) return '-';
        return `€${val.toLocaleString('lv-LV', { maximumFractionDigits: 0 })}`;
    };

    // Sorting logic
    const sortedCompanies = [...companies].sort((a, b) => {
        let aVal: any, bVal: any;

        switch (sortColumn) {
            case 'employees':
                aVal = a.workforce.employees || 0;
                bVal = b.workforce.employees || 0;
                break;
            case 'avgSalary':
                aVal = a.workforce.avgSalary || 0;
                bVal = b.workforce.avgSalary || 0;
                break;
            case 'revenuePerEmployee':
                aVal = a.workforce.revenuePerEmployee || 0;
                bVal = b.workforce.revenuePerEmployee || 0;
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

    // Chart data - Employee count comparison
    const employeeChartData = {
        labels: companies.map(c => c.name.length > 30 ? c.name.substring(0, 30) + '...' : c.name),
        datasets: [
            {
                label: 'Darbinieku skaits',
                data: companies.map(c => c.workforce.employees || 0),
                backgroundColor: 'rgba(59, 130, 246, 0.8)',
                borderColor: 'rgb(59, 130, 246)',
                borderWidth: 1
            }
        ]
    };

    // Chart data - Salary comparison
    const salaryChartData = {
        labels: companies.map(c => c.name.length > 30 ? c.name.substring(0, 30) + '...' : c.name),
        datasets: [
            {
                label: 'Vidējā alga (EUR)',
                data: companies.map(c => c.workforce.avgSalary || 0),
                backgroundColor: 'rgba(16, 185, 129, 0.8)',
                borderColor: 'rgb(16, 185, 129)',
                borderWidth: 1
            }
        ]
    };

    const chartOptions: ChartOptions<'bar'> = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                callbacks: {
                    label: function (context: any) {
                        return context.dataset.label + ': ' + (context.parsed.y?.toLocaleString('lv-LV') || '0');
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                ticks: {
                    callback: function (value) {
                        return Number(value).toLocaleString('lv-LV');
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

    // Calculate growth rates
    const calculateGrowth = (trend: { year: number; value: number }[]) => {
        if (trend.length < 2) return null;
        const sorted = [...trend].sort((a, b) => a.year - b.year);
        const oldest = sorted[0].value;
        const newest = sorted[sorted.length - 1].value;
        if (oldest === 0) return null;
        return ((newest - oldest) / oldest) * 100;
    };

    return (
        <div className="space-y-6">
            {/* Comparison Table */}
            <div className="bg-white rounded-lg shadow-lg overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200">
                    <h2 className="text-lg font-bold text-gray-900">Darbaspēka rādītāju salīdzinājums</h2>
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
                                    onClick={() => handleSort('employees')}
                                >
                                    <div className="flex items-center justify-end gap-1">
                                        Darbinieki
                                        <SortIcon column="employees" />
                                    </div>
                                </th>
                                <th
                                    className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                    onClick={() => handleSort('avgSalary')}
                                >
                                    <div className="flex items-center justify-end gap-1">
                                        Vidējā alga
                                        <SortIcon column="avgSalary" />
                                    </div>
                                </th>
                                <th
                                    className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                    onClick={() => handleSort('revenuePerEmployee')}
                                >
                                    <div className="flex items-center justify-end gap-1">
                                        Apgrozījums / darbinieks
                                        <SortIcon column="revenuePerEmployee" />
                                    </div>
                                </th>
                                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Izmaiņa (5 gadi)
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {sortedCompanies.map((company, index) => {
                                const growth = calculateGrowth(company.trend.employees);

                                return (
                                    <tr key={company.regNumber} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                                        <td className="px-6 py-4 text-sm font-medium text-gray-900 sticky left-0 bg-inherit">
                                            <div className="max-w-xs truncate" title={company.name}>
                                                {company.name}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900 font-semibold">
                                            {formatNumber(company.workforce.employees)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900 font-semibold">
                                            {formatCurrency(company.workforce.avgSalary)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-700">
                                            {formatCurrency(company.workforce.revenuePerEmployee)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                                            {growth !== null ? (
                                                <span className={`inline-flex items-center gap-1 font-medium ${growth >= 0 ? 'text-green-600' : 'text-red-600'
                                                    }`}>
                                                    {growth >= 0 ? '↑' : '↓'}
                                                    {Math.abs(growth).toFixed(1)}%
                                                </span>
                                            ) : '-'}
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Employee Count Chart */}
                <div className="bg-white rounded-lg shadow-lg p-6">
                    <h3 className="text-lg font-bold text-gray-900 mb-4">Darbinieku skaits</h3>
                    <div className="h-80">
                        <Bar data={employeeChartData} options={chartOptions} />
                    </div>
                </div>

                {/* Salary Chart */}
                <div className="bg-white rounded-lg shadow-lg p-6">
                    <h3 className="text-lg font-bold text-gray-900 mb-4">Vidējā alga</h3>
                    <div className="h-80">
                        <Bar data={salaryChartData} options={chartOptions} />
                    </div>
                </div>
            </div>

            {/* Insights */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <div className="flex items-start gap-3">
                    <svg className="w-6 h-6 text-blue-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div>
                        <h4 className="font-semibold text-blue-900 mb-2">Analīzes ieskats</h4>
                        <ul className="text-sm text-blue-800 space-y-1">
                            <li>• Apgrozījums uz darbinieku rāda uzņēmuma efektivitāti</li>
                            <li>• Augstāka vidējā alga var norādīt uz kvalificētāku darbaspēku</li>
                            <li>• Darbinieku skaita izmaiņas atspoguļo uzņēmuma izaugsmi vai sarukšanu</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
}
