"use client";

import React, { useState, useEffect } from "react";
import Navbar from "@/components/Navbar"; // Assuming we have this
import FilterSidebar from "@/components/explore/FilterSidebar";
import CompanyListTable from "@/components/explore/CompanyListTable";
import { useSearchParams, useRouter } from "next/navigation";
import { Suspense } from 'react';
import { useComparison } from "@/contexts/ComparisonContext";
import { formatCompanyName } from "@/utils/formatCompanyName";
import { useTranslations } from 'next-intl';

// Wrapped component for Suspense
function ExploreContent() {
    const t = useTranslations('Analytics');
    const tStats = useTranslations('Analytics.stats');
    const tTable = useTranslations('Analytics.table');
    const tPagination = useTranslations('Analytics.pagination');

    const searchParams = useSearchParams();
    const router = useRouter();

    // Init state from URL
    const [filters, setFilters] = useState({
        page: Number(searchParams.get('page')) || 1,
        limit: 50,
        sort_by: searchParams.get('sort_by') || 'turnover',
        order: searchParams.get('order') || 'desc',
        status: searchParams.get('status') || 'active',
        region: searchParams.get('region') || '',
        nace: searchParams.getAll('nace'), // Get all nace values as array
        min_turnover: searchParams.get('min_turnover') || '',
        min_employees: searchParams.get('min_employees') || '',
        has_pvn: searchParams.get('has_pvn') === 'true',
        has_sanctions: searchParams.get('has_sanctions') === 'true'
    });

    const [data, setData] = useState<any[]>([]);
    const [meta, setMeta] = useState<any>(null);
    const [stats, setStats] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    // Comparison functionality
    const { selectedCompanies, addCompany, removeCompany, isSelected, canAddMore } = useComparison();

    // Sync state to URL
    useEffect(() => {
        const params = new URLSearchParams();
        Object.entries(filters).forEach(([key, value]) => {
            if (value !== '' && value !== null && value !== undefined && value !== false) {
                if (key === 'nace' && Array.isArray(value)) {
                    if (value.length > 0) {
                        value.forEach(v => params.append(key, String(v)));
                    }
                } else {
                    params.set(key, String(value));
                }
            }
        });
        router.push(`/explore?${params.toString()}`, { scroll: false });
    }, [filters, router]);

    // Fetch Data
    useEffect(() => {
        async function fetchData() {
            setLoading(true);
            try {
                // Build query string
                const params = new URLSearchParams();
                Object.entries(filters).forEach(([key, value]) => {
                    if (value !== '' && value !== null && value !== undefined && value !== false) {
                        if (key === 'nace' && Array.isArray(value)) {
                            value.forEach(v => params.append(key, String(v)));
                        } else {
                            params.set(key, String(value));
                        }
                    }
                });

                const res = await fetch(`/api/companies/list?${params.toString()}`);
                if (res.ok) {
                    const json = await res.json();
                    setData(json.data);
                    setMeta(json.meta);
                    setStats(json.stats);
                }
            } catch (error) {
                console.error("Explore fetch error:", error);
            } finally {
                setLoading(false);
            }
        }

        const timer = setTimeout(() => {
            fetchData();
        }, 300); // 300ms debounce

        return () => clearTimeout(timer);
    }, [filters]);

    const handleFilterChange = (newFilters: any) => {
        setFilters(prev => ({ ...prev, ...newFilters, page: 1 }));
    };

    const handleSort = (key: string) => {
        setFilters(prev => ({
            ...prev,
            sort_by: key,
            order: prev.sort_by === key && prev.order === 'desc' ? 'asc' : 'desc',
            page: 1
        }));
    };

    // Helper for formatting money
    const formatMoney = (val: number | null) => {
        if (val === null || val === undefined) return <span className="text-gray-300">-</span>;

        // Check for 0 value explicitly
        if (val === 0) return <span className="text-gray-500">0 €</span>;

        const absVal = Math.abs(val);

        let formatted = '';
        if (absVal >= 1e6) {
            formatted = `${(val / 1e6).toFixed(2)} M€`;
        } else if (absVal >= 1e3) {
            formatted = `${(val / 1e3).toFixed(1)} K€`;
        } else {
            formatted = `${val.toFixed(0)} €`;
        }

        return <span className="font-medium text-gray-900">{formatted}</span>;
    };

    // Helper for formatting profit
    const formatProfit = (val: number | null, margin: number | null) => {
        if (val === null || val === undefined) return <span className="text-gray-300">-</span>;

        const isPositive = val >= 0;
        const colorClass = isPositive ? "text-gray-900" : "text-red-600";

        // Format similar to money but with color
        const absVal = Math.abs(val);
        let formatted = '';
        if (absVal >= 1e6) {
            formatted = `${(val / 1e6).toFixed(2)} M€`;
        } else if (absVal >= 1e3) {
            formatted = `${(val / 1e3).toFixed(1)} K€`;
        } else {
            formatted = `${val.toFixed(0)} €`;
        }

        return (
            <div className="flex flex-col items-end">
                <span className={colorClass}>{formatted}</span>
                {margin !== null && (
                    <span className={`text-xs ${margin < 0 ? 'text-red-400' : 'text-green-600'}`}>
                        {margin.toFixed(1)}%
                    </span>
                )}
            </div>
        );
    }

    // Dynamic Columns based on sort/context
    const getColumns = () => {
        const baseColumns: any[] = [
            // Checkbox column for comparison
            {
                key: 'checkbox',
                label: '',
                width: '40px',
                render: (val: any, row: any) => {
                    const selected = isSelected(row.regcode.toString());
                    const disabled = !selected && !canAddMore;

                    return (
                        <input
                            type="checkbox"
                            checked={selected}
                            disabled={disabled}
                            onChange={(e) => {
                                if (e.target.checked) {
                                    addCompany({
                                        regcode: row.regcode.toString(),
                                        name: row.name
                                    });
                                } else {
                                    removeCompany(row.regcode.toString());
                                }
                            }}
                            className="w-4 h-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
                            title={disabled ? tTable('max_compare') : tTable('add_compare')}
                        />
                    );
                }
            },
            {
                key: 'name',
                label: tTable('company'),
                render: (val: any, row: any) => (
                    <div className="max-w-[150px] md:max-w-[240px]">
                        <a href={`/company/${row.regcode}`} className="font-semibold text-gray-900 hover:text-purple-600 block truncate" title={row.name}>
                            {formatCompanyName(row)}
                        </a>
                        <div className="text-gray-500 text-xs">Reg. nr. {row.regcode}</div>
                        {row.nace && <span className="inline-block bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded mt-1 truncate max-w-full" title={row.nace}>{row.nace}</span>}
                    </div>
                )
            }
        ];

        // Add Financials
        baseColumns.push(
            {
                key: 'turnover',
                label: tTable('turnover'),
                align: 'right',
                sortable: true,
                render: (val: any) => formatMoney(val)
            },
            {
                key: 'profit',
                label: tTable('profit'),
                align: 'right',
                sortable: true,
                render: (val: any, row: any) => formatProfit(val, row.profit_margin)
            },
            {
                key: 'employees',
                label: tTable('employees'),
                align: 'center',
                sortable: true,
                render: (val: any) => <span className="text-gray-900">{val ?? '-'}</span>
            },
            {
                key: 'salary',
                label: tTable('avg_salary'),
                align: 'right',
                sortable: true,
                render: (val: any) => val ? <span className="font-bold text-green-700">{val.toFixed(0)} €</span> : <span className="text-gray-300">-</span>
            },
            {
                key: 'turnover_growth',
                label: tTable('growth'),
                align: 'right',
                sortable: true,
                render: (val: any) => val ? <span className="font-bold text-green-600">+{val}%</span> : <span className="text-gray-300">-</span>
            }
        );

        // Conditional Columns
        if (filters.sort_by === 'tax') {
            baseColumns.push({
                key: 'tax_paid',
                label: tTable('tax_paid'),
                align: 'right',
                sortable: true,
                render: (val: any) => val ? <span className="text-gray-900">{(val / 1e3).toFixed(1)} K€</span> : <span className="text-gray-300">-</span>
            });
        }

        return baseColumns;
    };

    return (
        <div className="flex flex-col md:flex-row gap-6 min-h-[500px]">
            {/* Sidebar */}
            <div className="w-full md:w-64 flex-shrink-0">
                <FilterSidebar filters={filters} onFilterChange={handleFilterChange} />
            </div>

            {/* Main Content */}
            <div className="flex-1 min-w-0">
                {/* Stats Cards (KPIs) */}
                {stats && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
                            <div className="text-xs text-gray-500 uppercase font-semibold">{tStats('companies')}</div>
                            <div className="text-xl font-bold text-gray-900">{stats.count.toLocaleString()}</div>
                        </div>
                        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
                            <div className="text-xs text-gray-500 uppercase font-semibold">{tStats('total_turnover')}</div>
                            <div className="text-xl font-bold text-blue-600">
                                {(stats.total_turnover / 1e6).toFixed(1)} M€
                            </div>
                        </div>
                        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
                            <div className="text-xs text-gray-500 uppercase font-semibold">{tStats('total_profit')}</div>
                            <div className={`text-xl font-bold ${stats.total_profit >= 0 ? "text-green-600" : "text-red-600"}`}>
                                {(stats.total_profit / 1e6).toFixed(1)} M€
                            </div>
                        </div>
                        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
                            <div className="text-xs text-gray-500 uppercase font-semibold">{tStats('employees')}</div>
                            <div className="text-xl font-bold text-purple-600">
                                {stats.total_employees?.toLocaleString() || '-'}
                            </div>
                        </div>
                    </div>
                )}

                <div className="flex justify-between items-center mb-6">
                    <h1 className="text-2xl font-bold text-gray-900 hidden md:block">{t('title')}</h1>
                    <div className="text-sm text-gray-500 ml-auto">
                        {meta ? t('data_year', { year: meta.financial_year }) : t('loading')}
                    </div>
                </div>

                <CompanyListTable
                    data={data}
                    loading={loading}
                    columns={getColumns()}
                    sortConfig={{ key: filters.sort_by, direction: filters.order as 'asc' | 'desc' }}
                    onSort={handleSort}
                />

                {/* Simple Pagination */}
                <div className="mt-6 flex justify-center gap-2">
                    <button
                        disabled={filters.page === 1 || loading}
                        onClick={() => setFilters(p => ({ ...p, page: p.page - 1 }))}
                        className="px-4 py-2 border rounded hover:bg-gray-50 disabled:opacity-50"
                    >
                        {tPagination('prev')}
                    </button>
                    <span className="px-4 py-2 text-gray-700 flex items-center">{tPagination('page', { page: filters.page })}</span>
                    <button
                        disabled={!data.length || (data.length < filters.limit) || loading}
                        onClick={() => setFilters(p => ({ ...p, page: p.page + 1 }))}
                        className="px-4 py-2 border rounded hover:bg-gray-50 disabled:opacity-50"
                    >
                        {tPagination('next')}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default function ExplorePage() {
    const t = useTranslations('Common');
    return (
        <div className="min-h-screen bg-gray-50">
            <Navbar />
            <div className="container mx-auto px-4 py-8">
                <Suspense fallback={<div className="text-center py-20">{t('loading')}</div>}>
                    <ExploreContent />
                </Suspense>
            </div>
        </div>
    );
}
