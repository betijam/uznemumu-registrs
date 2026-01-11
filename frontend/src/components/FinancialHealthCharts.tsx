"use client";

import React from 'react';
import { useTranslations } from 'next-intl';

interface GaugeProps {
    value: number;
    label: string;
    subLabel: string;
    min: number;
    max: number;
    inverse?: boolean; // if true, lower is better (e.g. debt)
    format?: (v: number) => string;
}

const Gauge = ({ value, label, subLabel, min, max, inverse = false, format }: GaugeProps) => {
    // Normalize value to 0-1 range
    const normalized = Math.min(Math.max((value - min) / (max - min), 0), 1);

    // Calculate angle: -90 to +90 degrees (semicircle) aka 180 to 0 in SVG arc terms?
    // Let's use stroke-dasharray approach for circle.
    // Half circle arc.

    // Determine color based on "health"
    // If inverse: low is green, high is red.
    // If normal: high is green, low is red.
    let color = "text-yellow-500";

    if (inverse) {
        // Bad if high
        if (normalized > 0.6) color = "text-red-500";
        else if (normalized > 0.3) color = "text-yellow-500";
        else color = "text-green-500";
    } else {
        // Good if high
        if (normalized > 0.6) color = "text-green-500";
        else if (normalized > 0.3) color = "text-yellow-500";
        else color = "text-red-500";
    }

    // Width of the stroke
    const strokeWidth = 10;
    const radius = 40;
    const center = 50;
    // Circumference of half circle = pi * r
    const circumference = Math.PI * radius;
    // Dash offset: 
    // Full dash = circumference.
    // We want to show 'normalized' portion.
    // Start from left (100% offset) to right (0% offset).
    // Actually, standard SVG circle starts at 3 o'clock. We rotate it.

    const dashArray = circumference;
    const dashOffset = circumference * (1 - normalized);

    const displayValue = format ? format(value) : value.toFixed(2);

    return (
        <div className="flex flex-col items-center bg-red-50 p-4 rounded-xl w-full">
            {/* Background is lightly tinted based on color? The image shows pinkish background for red gauges, greenish for green. */}
            {/* Let's make dynamic background */}
            <div className={`w-full h-full rounded-xl flex flex-col items-center justify-center py-4 ${color.includes('red') ? 'bg-red-50' : color.includes('green') ? 'bg-green-50' : 'bg-yellow-50'}`}>

                <div className="relative w-40 h-24 overflow-hidden mb-2">
                    {/* SVG Gauge */}
                    <svg viewBox="0 0 100 50" className="w-full h-full transform">
                        {/* Background Arc */}
                        <path
                            d="M 10 50 A 40 40 0 0 1 90 50"
                            fill="none"
                            stroke="#e5e7eb"
                            strokeWidth={strokeWidth}
                            strokeLinecap="round"
                        />

                        {/* Value Arc */}
                        <path
                            d="M 10 50 A 40 40 0 0 1 90 50"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth={strokeWidth}
                            strokeLinecap="round"
                            strokeDasharray={dashArray}
                            strokeDashoffset={dashOffset}
                            className={`transition-all duration-1000 ease-out ${color}`}
                        />
                    </svg>

                    {/* Value Text */}
                    <div className="absolute bottom-0 w-full text-center">
                        <span className={`text-2xl font-bold ${color.replace('text-', 'text-')}`}>{displayValue}</span>
                    </div>
                </div>

                <div className="text-center">
                    <div className="font-bold text-gray-800 text-sm">{label}</div>
                    <div className={`text-xs ${color} opacity-80`}>{subLabel}</div>
                </div>
            </div>
        </div>
    );
};

interface FinancialHealthChartsProps {
    latestFinancials: any;
}

export default function FinancialHealthCharts({ latestFinancials }: FinancialHealthChartsProps) {
    const t = useTranslations('FinancialAnalysis');

    if (!latestFinancials) return null;

    const { current_ratio, roe, debt_to_equity } = latestFinancials;

    return (
        <div className="mt-6 mb-8">
            <h3 className="text-lg font-bold text-gray-900 mb-4">{t('health_indicators')}</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

                {/* Liquidity (Current Ratio) - Higher is better. > 1 is good. */}
                <Gauge
                    value={current_ratio || 0}
                    min={0}
                    max={3}
                    label={t('liquidity')}
                    subLabel="Current Ratio"
                    format={(v) => v.toFixed(2)}
                />

                {/* ROE - Higher is better */}
                <Gauge
                    value={roe || 0}
                    min={-20}
                    max={50}
                    label="ROE"
                    subLabel={t('profitability')}
                    format={(v) => `${v.toFixed(1)}%`}
                />

                {/* Debt to Equity - Lower is better. > 2 is risky. */}
                <Gauge
                    value={debt_to_equity || 0}
                    min={0}
                    max={10}
                    inverse={true}
                    label="Parāda Slodze"
                    subLabel="Debt-to-Equity"
                    format={(v) => v.toFixed(2)}
                />
            </div>
        </div>
    );
}
