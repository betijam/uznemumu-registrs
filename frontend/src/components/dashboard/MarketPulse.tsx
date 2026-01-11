"use client";

import React from 'react';
import { useTranslations } from 'next-intl';

interface MarketPulseProps {
    data: {
        active_companies: number;
        total_employees: number;
        avg_salary: number;
        total_turnover: number;
        data_year?: number;
    } | null;
    loading?: boolean;
}

export default function MarketPulse({ data, loading = false }: MarketPulseProps) {
    const t = useTranslations('MarketPulse');

    if (loading || !data) {
        return (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 w-full max-w-7xl mx-auto mb-12">
                {[...Array(4)].map((_, i) => (
                    <div key={i} className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 animate-pulse h-24"></div>
                ))}
            </div>
        );
    }

    const stats = [
        {
            label: t('active_companies'),
            value: data.active_companies.toLocaleString(),
            color: "text-gray-900",
            indicator: "bg-indigo-500"
        },
        {
            label: t('total_employees'),
            value: data.total_employees.toLocaleString(),
            color: "text-gray-900",
            indicator: "bg-purple-500"
        },
        {
            label: t('avg_salary'),
            value: `${data.avg_salary.toLocaleString()} €`,
            color: "text-gray-900",
            indicator: "bg-green-500"
        },
        {
            label: t('total_turnover'),
            value: `${(data.total_turnover / 1e9).toFixed(1)} Md €`,
            sub: "6%", // Static trend or calculated if we have history
            color: "text-gray-900",
            indicator: "bg-orange-500"
        }
    ];

    return (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 w-full max-w-7xl mx-auto mb-12">
            {stats.map((stat, idx) => (
                <div key={idx} className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col items-center justify-center text-center hover:shadow-lg hover:-translate-y-1 transition-all duration-200 min-h-[96px] relative overflow-hidden group">
                    <div className={`text-2xl md:text-3xl font-bold mb-1 ${stat.color}`}>
                        {stat.value}
                        {stat.sub && <span className="text-xs text-green-500 ml-2 align-middle">↑ {stat.sub}</span>}
                    </div>
                    <div className="text-xs font-semibold text-gray-500 tracking-wider uppercase">
                        {stat.label}
                    </div>
                    {/* Colored indicator bar at bottom */}
                    <div className={`absolute bottom-0 left-0 right-0 h-1 ${stat.indicator}`}></div>
                </div>
            ))}
        </div>
    );
}
