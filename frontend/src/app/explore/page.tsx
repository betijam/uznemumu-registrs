"use client";

import React, { useState, useEffect } from "react";
import Navbar from "@/components/Navbar"; // Assuming we have this
import FilterSidebar from "@/components/explore/FilterSidebar";
import CompanyListTable from "@/components/explore/CompanyListTable";
import { useSearchParams, useRouter } from "next/navigation";
import { Suspense } from 'react';

// Wrapped component for Suspense
function ExploreContent() {
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
        nace: searchParams.get('nace') || '',
        min_turnover: searchParams.get('min_turnover') || '',
        min_employees: searchParams.get('min_employees') || '',
        has_pvn: searchParams.get('has_pvn') === 'true',
        has_sanctions: searchParams.get('has_sanctions') === 'true'
    });

    const [data, setData] = useState<any[]>([]);
    const [meta, setMeta] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    // Sync state to URL
    useEffect(() => {
        const params = new URLSearchParams();
        Object.entries(filters).forEach(([key, value]) => {
            if (value !== '' && value !== null && value !== undefined && value !== false) {
                params.set(key, String(value));
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
                    if (value !== '' && value !== null && value !== undefined) {
                        params.set(key, String(value));
                    }
                });

                const res = await fetch(`/api/companies/list?${params.toString()}`);
                if (res.ok) {
                    const json = await res.json();
                    setData(json.data);
                    setMeta(json.meta);
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

    // Dynamic Columns based on sort/context
    const getColumns = () => {
        const baseColumns: any[] = [
            {
                key: 'name',
                label: 'Uzņēmums',
                render: (val: any, row: any) => (
                    <div className="max-w-[200px] md:max-w-[300px]">
                        <a href={`/company/${row.regcode}`} className="font-semibold text-gray-900 hover:text-purple-600 block truncate" title={val}>
                            {val}
                        </a>
                        <div className="text-gray-500 text-xs">Reg. nr. {row.regcode}</div>
                        {row.nace && <span className="inline-block bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded mt-1 truncate max-w-full">{row.nace}</span>}
                    </div>
                )
            }
        ];

        // Add Financials
        baseColumns.push(
            {
                key: 'turnover',
                label: 'Apgrozījums',
                align: 'right',
                sortable: true,
                render: (val: any) => val !== null ? <span className="font-medium text-gray-900">{(val / 1e6).toFixed(1)} M€</span> : <span className="text-gray-300">-</span>
            },
            {
                key: 'profit',
                label: 'Peļņa',
                align: 'right',
                sortable: true,
                render: (val: any, row: any) => (
                    <div className="flex flex-col items-end">
                        <span className={val > 0 ? "text-gray-900" : "text-red-500"}>
                            {val !== null ? `${(val / 1e6).toFixed(2)} M€` : '-'}
                        </span>
                        {row.profit_margin !== null && (
                            <span className="text-xs text-gray-400">{row.profit_margin.toFixed(1)}%</span>
                        )}
                    </div>
                )
            },
            {
                key: 'employees',
                label: 'Darbinieki',
                align: 'center',
                sortable: true,
                render: (val: any) => <span className="text-gray-900">{val || '-'}</span>
            }
        );

        // Conditional Columns
        if (filters.sort_by === 'salary') {
            baseColumns.push({
                key: 'salary',
                label: 'Vid. Alga (Bruto)',
                align: 'right',
                sortable: true,
                render: (val: any) => val ? <span className="font-bold text-green-700">{val.toFixed(0)} €</span> : <span className="text-gray-300">-</span>
            });
        }

        if (filters.sort_by === 'tax') {
            baseColumns.push({
                key: 'tax_paid',
                label: 'Nodokļi',
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
                <div className="flex justify-between items-center mb-6">
                    <h1 className="text-2xl font-bold text-gray-900">Uzņēmumu Saraksts</h1>
                    <div className="text-sm text-gray-500">
                        {meta ? `Atrasti ${meta.total.toLocaleString()} uzņēmumi (Gads: ${meta.financial_year})` : 'Meklē...'}
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
                        Iepriekšējā
                    </button>
                    <span className="px-4 py-2 text-gray-700">Lapa {filters.page}</span>
                    <button
                        disabled={!data.length || (data.length < filters.limit) || loading}
                        onClick={() => setFilters(p => ({ ...p, page: p.page + 1 }))}
                        className="px-4 py-2 border rounded hover:bg-gray-50 disabled:opacity-50"
                    >
                        Nākamā
                    </button>
                </div>
            </div>
        </div>
    );
}

export default function ExplorePage() {
    return (
        <div className="min-h-screen bg-gray-50">
            <Navbar />
            <div className="container mx-auto px-4 py-8">
                <Suspense fallback={<div className="text-center py-20">Lādē...</div>}>
                    <ExploreContent />
                </Suspense>
            </div>
        </div>
    );
}
