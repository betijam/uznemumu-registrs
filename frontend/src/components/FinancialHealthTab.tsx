"use client";

import GaugeChart from './GaugeChart';

interface FinancialHealthTabProps {
    company: any;
}

export default function FinancialHealthTab({ company }: FinancialHealthTabProps) {
    const financialHistory = company.financial_history || [];
    const latest = financialHistory[0] || {};

    // Get latest ratios
    const currentRatio = latest.current_ratio;
    const roe = latest.roe;
    const debtToEquity = latest.debt_to_equity;
    const quickRatio = latest.quick_ratio;
    const roa = latest.roa;
    const netProfitMargin = latest.net_profit_margin;
    const ebitda = latest.ebitda;

    const formatCurrency = (val: number | null) => {
        if (val === null || val === undefined) return '-';
        return new Intl.NumberFormat('lv-LV', {
            style: 'currency',
            currency: 'EUR',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(val);
    };

    const formatPercent = (val: number | null) => {
        if (val === null || val === undefined) return '-';
        return `${val.toFixed(2)}%`;
    };

    const formatRatio = (val: number | null) => {
        if (val === null || val === undefined) return '-';
        return val.toFixed(2);
    };

    // Sparkline component
    const Sparkline = ({ data }: { data: number[] }) => {
        if (!data || data.length === 0) return <span className="text-gray-400">-</span>;

        const max = Math.max(...data);
        const min = Math.min(...data);
        const range = max - min || 1;

        const points = data.map((val, idx) => {
            const x = (idx / (data.length - 1)) * 60;
            const y = 20 - ((val - min) / range) * 15;
            return `${x},${y}`;
        }).join(' ');

        return (
            <svg viewBox="0 0 60 20" className="w-16 h-6 inline-block">
                <polyline
                    points={points}
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    className="text-primary"
                />
            </svg>
        );
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h2 className="text-2xl font-bold text-gray-900">Finanšu Veselība</h2>
                <p className="text-sm text-gray-600 mt-1">
                    Profesionāli finanšu rādītāji un tendences
                </p>
            </div>

            {/* Top Gauges - Key Indicators */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <GaugeChart
                    value={currentRatio}
                    min={0}
                    max={3}
                    thresholds={{ good: 1.2, warning: 1.0 }}
                    label="Likviditāte"
                    subtitle="Current Ratio"
                    format={(v) => v.toFixed(2)}
                />

                <GaugeChart
                    value={roe}
                    min={-20}
                    max={30}
                    thresholds={{ good: 10, warning: 5 }}
                    label="ROE"
                    subtitle="Pašu kapitāla atdeve"
                    format={(v) => `${v.toFixed(1)}%`}
                />

                <GaugeChart
                    value={debtToEquity}
                    min={0}
                    max={3}
                    thresholds={{ good: 1.5, warning: 2.5 }}
                    label="Parāda Slodze"
                    subtitle="Debt-to-Equity"
                    format={(v) => v.toFixed(2)}
                />
            </div>

            {/* Trend Chart - Turnover & Profit */}
            <div className="border border-gray-200 rounded-lg p-6 bg-white">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Apgrozījums & Peļņa (Tendence)
                </h3>

                {financialHistory.length > 0 ? (
                    <div className="flex items-end justify-between h-64 gap-4">
                        {financialHistory.slice(0, 7).reverse().map((f: any) => {
                            const maxTurnover = Math.max(...financialHistory.map((x: any) => x.turnover || 0));
                            const maxProfit = Math.max(...financialHistory.map((x: any) => Math.abs(x.profit || 0)));

                            const CHART_HEIGHT = 256;
                            const turnoverHeight = f.turnover ? (f.turnover / maxTurnover) * CHART_HEIGHT * 0.8 : 0;
                            const profitHeight = f.profit ? (Math.abs(f.profit) / maxProfit) * (CHART_HEIGHT * 0.3) : 0;
                            const isProfitNegative = (f.profit || 0) < 0;

                            return (
                                <div key={f.year} className="flex-1 flex flex-col items-center gap-2">
                                    <div className="w-full flex flex-col gap-1 items-center justify-end" style={{ height: `${CHART_HEIGHT}px` }}>
                                        {/* Turnover Bar */}
                                        <div
                                            className="w-full bg-primary rounded-t transition-all hover:opacity-80 relative group"
                                            style={{ height: `${Math.max(turnoverHeight, 4)}px` }}
                                        >
                                            <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-primary text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                                                {formatCurrency(f.turnover)}
                                            </div>
                                        </div>
                                        {/* Profit Bar */}
                                        <div
                                            className={`w-full rounded-t transition-all hover:opacity-80 relative group ${isProfitNegative ? 'bg-danger' : 'bg-accent'}`}
                                            style={{ height: `${Math.max(profitHeight, 4)}px` }}
                                        >
                                            <div className={`absolute -top-8 left-1/2 -translate-x-1/2 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10 ${isProfitNegative ? 'bg-danger' : 'bg-accent'}`}>
                                                {formatCurrency(f.profit)}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="text-center">
                                        <span className="text-xs text-gray-600 font-medium">{f.year}</span>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                ) : (
                    <div className="h-64 flex items-center justify-center text-gray-500">
                        Nav pieejami vēsturiskie dati
                    </div>
                )}
            </div>

            {/* Detailed Metrics Table */}
            <div className="border border-gray-200 rounded-lg overflow-hidden bg-white">
                <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-900">
                        Detalizēti Finanšu Rādītāji
                    </h3>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-gray-50 border-b border-gray-200">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Rādītājs
                                </th>
                                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Vērtība
                                </th>
                                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Tendence (5 gadi)
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Norma
                                </th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {/* Liquidity Ratios */}
                            <tr className="bg-blue-50/30">
                                <td colSpan={4} className="px-6 py-2 text-sm font-semibold text-gray-700">
                                    Likviditātes Rādītāji
                                </td>
                            </tr>
                            <tr>
                                <td className="px-6 py-4 text-sm text-gray-900">Current Ratio</td>
                                <td className="px-6 py-4 text-sm text-right font-semibold text-gray-900">
                                    {formatRatio(currentRatio)}
                                </td>
                                <td className="px-6 py-4 text-center">
                                    <Sparkline data={financialHistory.slice(0, 5).reverse().map((f: any) => f.current_ratio).filter((v: any) => v !== null)} />
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-600">&gt; 1.2</td>
                            </tr>
                            <tr>
                                <td className="px-6 py-4 text-sm text-gray-900">Quick Ratio</td>
                                <td className="px-6 py-4 text-sm text-right font-semibold text-gray-900">
                                    {formatRatio(quickRatio)}
                                </td>
                                <td className="px-6 py-4 text-center">
                                    <Sparkline data={financialHistory.slice(0, 5).reverse().map((f: any) => f.quick_ratio).filter((v: any) => v !== null)} />
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-600">&gt; 0.8</td>
                            </tr>

                            {/* Profitability Ratios */}
                            <tr className="bg-green-50/30">
                                <td colSpan={4} className="px-6 py-2 text-sm font-semibold text-gray-700">
                                    Rentabilitātes Rādītāji
                                </td>
                            </tr>
                            <tr>
                                <td className="px-6 py-4 text-sm text-gray-900">Net Profit Margin</td>
                                <td className="px-6 py-4 text-sm text-right font-semibold text-gray-900">
                                    {formatPercent(netProfitMargin)}
                                </td>
                                <td className="px-6 py-4 text-center">
                                    <Sparkline data={financialHistory.slice(0, 5).reverse().map((f: any) => f.net_profit_margin).filter((v: any) => v !== null)} />
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-600">Atkarīgs no nozares</td>
                            </tr>
                            <tr>
                                <td className="px-6 py-4 text-sm text-gray-900">ROE (Return on Equity)</td>
                                <td className="px-6 py-4 text-sm text-right font-semibold text-gray-900">
                                    {formatPercent(roe)}
                                </td>
                                <td className="px-6 py-4 text-center">
                                    <Sparkline data={financialHistory.slice(0, 5).reverse().map((f: any) => f.roe).filter((v: any) => v !== null)} />
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-600">&gt; 10%</td>
                            </tr>
                            <tr>
                                <td className="px-6 py-4 text-sm text-gray-900">ROA (Return on Assets)</td>
                                <td className="px-6 py-4 text-sm text-right font-semibold text-gray-900">
                                    {formatPercent(roa)}
                                </td>
                                <td className="px-6 py-4 text-center">
                                    <Sparkline data={financialHistory.slice(0, 5).reverse().map((f: any) => f.roa).filter((v: any) => v !== null)} />
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-600">&gt; 5%</td>
                            </tr>

                            {/* Solvency Ratios */}
                            <tr className="bg-orange-50/30">
                                <td colSpan={4} className="px-6 py-2 text-sm font-semibold text-gray-700">
                                    Maksātspējas Rādītāji
                                </td>
                            </tr>
                            <tr>
                                <td className="px-6 py-4 text-sm text-gray-900">Debt-to-Equity</td>
                                <td className="px-6 py-4 text-sm text-right font-semibold text-gray-900">
                                    {formatRatio(debtToEquity)}
                                </td>
                                <td className="px-6 py-4 text-center">
                                    <Sparkline data={financialHistory.slice(0, 5).reverse().map((f: any) => f.debt_to_equity).filter((v: any) => v !== null)} />
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-600">&lt; 1.5</td>
                            </tr>

                            {/* EBITDA */}
                            <tr className="bg-purple-50/30">
                                <td colSpan={4} className="px-6 py-2 text-sm font-semibold text-gray-700">
                                    Naudas Plūsma
                                </td>
                            </tr>
                            <tr>
                                <td className="px-6 py-4 text-sm text-gray-900">EBITDA</td>
                                <td className="px-6 py-4 text-sm text-right font-semibold text-gray-900">
                                    {formatCurrency(ebitda)}
                                </td>
                                <td className="px-6 py-4 text-center">
                                    <Sparkline data={financialHistory.slice(0, 5).reverse().map((f: any) => f.ebitda).filter((v: any) => v !== null)} />
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-600">Pozitīvs</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Info Box */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex gap-3">

                    <div className="flex-1">
                        <h4 className="text-sm font-semibold text-blue-900 mb-1">
                            Par Finanšu Rādītājiem
                        </h4>
                        <p className="text-xs text-blue-800">
                            Šie rādītāji tiek automātiski aprēķināti no uzņēmuma bilances un peļņas/zaudējumu aprēķina.
                            Tendences parāda pēdējo 5 gadu dinamiku. Normas ir vispārīgas un var atšķirties atkarībā no nozares.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
