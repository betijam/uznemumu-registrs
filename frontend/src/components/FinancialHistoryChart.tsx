'use client';

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface FinancialHistoryProps {
    data: {
        year: number;
        turnover: number | null;
        profit: number | null;
    }[];
}

const formatCurrency = (value: number) => {
    if (value >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(1)}B €`;
    if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M €`;
    if (value >= 1_000) return `${(value / 1_000_000).toFixed(0)}k €`;
    return `${value} €`;
};

const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-white p-4 border border-gray-100 shadow-xl rounded-xl">
                <p className="font-bold text-gray-900 mb-2">{label}. gads</p>
                {payload.map((entry: any, index: number) => (
                    <div key={index} className="flex items-center gap-2 mb-1 last:mb-0">
                        <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: entry.color }}
                        />
                        <span className="text-sm text-gray-600 capitalize">
                            {entry.name === 'turnover' ? 'Apgrozījums' : 'Peļņa'}:
                        </span>
                        <span className="text-sm font-bold text-gray-900">
                            {formatCurrency(entry.value)}
                        </span>
                    </div>
                ))}
            </div>
        );
    }
    return null;
};

export default function FinancialHistoryChart({ data }: FinancialHistoryProps) {
    if (!data || data.length === 0) {
        return (
            <div className="h-64 flex items-center justify-center bg-gray-50 rounded-xl border border-dashed border-gray-300">
                <p className="text-gray-400">Nav vēsturisko datu</p>
            </div>
        );
    }

    return (
        <div className="bg-white p-6 rounded-xl shadow-md border border-gray-100">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h3 className="text-lg font-bold text-gray-900">Finanšu Dinamika</h3>
                    <p className="text-sm text-gray-500">Pēdējo 5 gadu tendences</p>
                </div>
            </div>

            <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                        data={data}
                        margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
                    >
                        <defs>
                            <linearGradient id="colorTurnover" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="colorProfit" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                        <XAxis
                            dataKey="year"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#6B7280', fontSize: 12 }}
                            dy={10}
                        />
                        <YAxis
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#6B7280', fontSize: 12 }}
                            tickFormatter={(value) => {
                                if (value >= 1000000000) return `${(value / 1000000000).toFixed(0)}B`;
                                if (value >= 1000000) return `${(value / 1000000).toFixed(0)}M`;
                                return value;
                            }}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <Area
                            type="monotone"
                            dataKey="turnover"
                            name="turnover"
                            stroke="#3B82F6"
                            strokeWidth={3}
                            fillOpacity={1}
                            fill="url(#colorTurnover)"
                        />
                        <Area
                            type="monotone"
                            dataKey="profit"
                            name="profit"
                            stroke="#10B981"
                            strokeWidth={3}
                            fillOpacity={1}
                            fill="url(#colorProfit)"
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
