import React from 'react';

interface MarketPulseProps {
    data: {
        active_companies: number;
        new_this_week: number;
        liquidated_this_week: number;
        total_turnover: number;
    } | null;
    loading?: boolean;
}

export default function MarketPulse({ data, loading = false }: MarketPulseProps) {
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
            label: "AKTĪVI UZŅĒMUMI",
            value: data.active_companies.toLocaleString(),
            color: "text-gray-900"
        },
        {
            label: "REĢISTRĒTI ŠONEDĒĻ",
            value: `+${data.new_this_week}`,
            color: "text-green-600"
        },
        {
            label: "LIKVIDĒTI ŠONEDĒĻ",
            value: `-${data.liquidated_this_week}`,
            color: "text-red-500"
        },
        {
            label: "KOPĒJAIS APGROZĪJUMS",
            value: `${(data.total_turnover / 1e9).toFixed(1)} Md €`,
            sub: "▲ 6%", // Static trend or calculated if we have history
            color: "text-gray-900"
        }
    ];

    return (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 w-full max-w-7xl mx-auto mb-12">
            {stats.map((stat, idx) => (
                <div key={idx} className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col items-center justify-center text-center hover:shadow-md transition-shadow">
                    <div className={`text-2xl md:text-3xl font-bold mb-1 ${stat.color}`}>
                        {stat.value}
                        {stat.sub && <span className="text-xs text-green-500 ml-2 align-middle">{stat.sub}</span>}
                    </div>
                    <div className="text-xs font-semibold text-gray-500 tracking-wider uppercase">
                        {stat.label}
                    </div>
                </div>
            ))}
        </div>
    );
}
