import Link from "next/link";
import React from "react";
import { useTranslations } from 'next-intl';

interface Column {
    key: string;
    label: string;
    render?: (value: any, row: any) => React.ReactNode;
    sortable?: boolean;
    align?: 'left' | 'right' | 'center';
}

interface CompanyListTableProps {
    data: any[];
    loading: boolean;
    columns: Column[];
    sortConfig: { key: string; direction: 'asc' | 'desc' };
    onSort: (key: string) => void;
}

export default function CompanyListTable({ data, loading, columns, sortConfig, onSort }: CompanyListTableProps) {
    const t = useTranslations('Analytics');
    if (loading) {
        return (
            <div className="bg-white rounded-lg shadow border border-gray-100 p-8 space-y-4">
                {[...Array(5)].map((_, i) => (
                    <div key={i} className="h-12 bg-gray-50 rounded animate-pulse"></div>
                ))}
            </div>
        );
    }

    if (!data.length) {
        return (
            <div className="bg-white rounded-lg shadow border border-gray-100 p-12 text-center text-gray-500">
                {t('no_results')}
            </div>
        );
    }

    return (
        <div className="bg-white rounded-lg shadow border border-gray-100 overflow-hidden">
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            {columns.map((col) => (
                                <th
                                    key={col.key}
                                    scope="col"
                                    className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100
                                                ${col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'}`}
                                    onClick={() => col.sortable && onSort(col.key)}
                                >
                                    <div className={`flex items-center gap-1 ${col.align === 'right' ? 'justify-end' : col.align === 'center' ? 'justify-center' : 'justify-start'}`}>
                                        {col.label}
                                        {sortConfig.key === col.key && (
                                            <span>{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                                        )}
                                    </div>
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {data.map((row) => (
                            <tr key={row.regcode} className="hover:bg-gray-50 transition-colors">
                                {columns.map((col) => (
                                    <td key={col.key} className={`px-6 py-4 whitespace-nowrap text-sm text-gray-900 
                                                                 ${col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'}`}>
                                        {col.render ? col.render(row[col.key], row) : row[col.key]}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
