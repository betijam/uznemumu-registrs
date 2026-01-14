'use client';

import { ComposedChart, Area, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts';
import { useState } from 'react';

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
                {payload.map((entry: any, index: number) => {
                    // Custom formatting for Bar color in tooltip
                    const isProfit = entry.name === 'profit';
                    const color = isProfit
                        ? (entry.value >= 0 ? '#10B981' : '#EF4444')
                        : entry.color;

                    return (
                        <div key={index} className="flex items-center gap-2 mb-1 last:mb-0">
                            <div
                                className="w-3 h-3 rounded-full"
                                style={{ backgroundColor: color }}
                            />
                            <span className="text-sm text-gray-600 capitalize">
                                {isProfit ? 'Peļņa' : 'Apgrozījums'}:
                            </span>
                            <span className={`text-sm font-bold ${isProfit ? (entry.value >= 0 ? 'text-green-600' : 'text-red-600') : 'text-gray-900'}`}>
                                {formatCurrency(entry.value)}
                            </span>
                        </div>
                    );
                })}
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



    const [chartMode, setChartMode] = useState<'turnover' | 'profit'>('turnover');

    // Pre-process data
    const processedData = data.map(d => {
        const t = d.turnover !== null ? Number(d.turnover) : 0;
        const p = d.profit !== null ? Number(d.profit) : 0;
        return {
            ...d,
            turnover: t,
            profit: p,
            profitPos: p >= 0 ? p : 0,
            profitNeg: p < 0 ? p : 0
        };
    });

    // Calculate domain based on active mode
    const activeValues = processedData.map(d =>
        chartMode === 'turnover' ? d.turnover : d.profit
    );

    const minVal = Math.min(0, ...activeValues);
    const maxVal = Math.max(0, ...activeValues);

    let domainMin = minVal < 0 ? minVal * 1.2 : 0;
    // For turnover, usually 0 based, but maybe dynamic if needed. Current logic:
    // Profit often has negative, Turnover usually positive.
    let domainMax = maxVal > 0 ? maxVal * 1.1 : 0;

    if (domainMin === 0 && domainMax === 0) {
        domainMax = 1000;
    }

    const finalDomainMin = domainMin;
    const finalDomainMax = domainMax;

    return (
        <div className="bg-white p-6 rounded-xl shadow-md border border-gray-100 relative">
            <div className="flex items-center justify-between mb-6 pt-2">
                <div>
                    <h3 className="text-lg font-bold text-gray-900">Finanšu Dinamika</h3>
                    <p className="text-sm text-gray-500">Pēdējo 5 gadu tendences</p>
                </div>

                {/* Mode Toggle Buttons */}
                <div className="flex gap-2">
                    <button
                        onClick={() => setChartMode('turnover')}
                        className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${chartMode === 'turnover'
                            ? 'bg-blue-100 text-blue-700'
                            : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                            }`}
                    >
                        Apgrozījums
                    </button>
                    <button
                        onClick={() => setChartMode('profit')}
                        className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${chartMode === 'profit'
                            ? 'bg-green-100 text-green-700'
                            : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                            }`}
                    >
                        Peļņa
                    </button>
                </div>
            </div>

            {/* Legend - Dynamic based on mode */}
            <div className="flex items-center gap-4 text-xs font-medium mb-4 justify-end">
                {chartMode === 'turnover' && (
                    <div className="flex items-center gap-1.5">
                        <span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span>
                        <span className="text-gray-600">Apgrozījums</span>
                    </div>
                )}
                {chartMode === 'profit' && (
                    <>
                        <div className="flex items-center gap-1.5">
                            <span className="w-2.5 h-2.5 rounded-full bg-green-500"></span>
                            <span className="text-gray-600">Peļņa (+)</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <span className="w-2.5 h-2.5 rounded-full bg-red-500"></span>
                            <span className="text-gray-600">Zaudējumi (-)</span>
                        </div>
                    </>
                )}
            </div>

            <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart
                        data={processedData}
                        margin={{ top: 10, right: 0, left: 0, bottom: 0 }}
                    >
                        <defs>
                            <linearGradient id="colorTurnover" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.2} />
                                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
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
                            yAxisId="left"
                            type="number"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#6B7280', fontSize: 12 }}
                            domain={[finalDomainMin, finalDomainMax]}
                            allowDataOverflow={false}
                            tickFormatter={(value) => {
                                if (value === 0) return '0 €';
                                if (Math.abs(value) >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(1)}B`;
                                if (Math.abs(value) >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
                                if (Math.abs(value) >= 1_000) return `${(value / 1_000).toFixed(0)}k`;
                                return value;
                            }}
                        />
                        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'transparent' }} />
                        <ReferenceLine yAxisId="left" y={0} stroke="#4B5563" strokeDasharray="3 3" />

                        {chartMode === 'turnover' && (
                            <Area
                                yAxisId="left"
                                type="monotone"
                                dataKey="turnover"
                                name="turnover"
                                stroke="#3B82F6"
                                strokeWidth={2}
                                fillOpacity={1}
                                fill="url(#colorTurnover)"
                                animationDuration={500}
                            />
                        )}

                        {chartMode === 'profit' && (
                            <>
                                <Bar
                                    yAxisId="left"
                                    dataKey="profitPos"
                                    name="profit"
                                    barSize={32}
                                    fill="#10B981"
                                    stackId="profitStack"
                                    animationDuration={500}
                                />
                                <Bar
                                    yAxisId="left"
                                    dataKey="profitNeg"
                                    name="profit"
                                    barSize={32}
                                    fill="#EF4444"
                                    stackId="profitStack"
                                    animationDuration={500}
                                />
                            </>
                        )}
                    </ComposedChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
