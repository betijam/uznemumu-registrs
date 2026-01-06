"use client";

import { MetricType, getColorScale } from "@/lib/mapUtils";

interface MapLegendProps {
    metric: MetricType;
    minValue: number;
    maxValue: number;
}

export default function MapLegend({ metric, minValue, maxValue }: MapLegendProps) {
    const scale = getColorScale(metric);

    if (!scale) return null;

    const formatLegendValue = (value: number): string => {
        if (metric === "total_revenue" || metric === "total_profit") {
            if (value >= 1000000000) return `€${(value / 1000000000).toFixed(1)}B`;
            if (value >= 1000000) return `€${(value / 1000000).toFixed(0)}M`;
            if (value >= 1000) return `€${(value / 1000).toFixed(0)}K`;
            return `€${value.toFixed(0)}`;
        }
        if (metric === "avg_salary") {
            return `€${Math.round(value)}`;
        }
        if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
        return value.toFixed(0);
    };

    return (
        <div className="absolute bottom-8 left-4 z-[1000] bg-white rounded-xl shadow-lg p-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">{scale.label}</h4>

            <div className="flex items-center gap-1">
                {scale.colors.map((color, i) => (
                    <div
                        key={i}
                        className="w-6 h-4 first:rounded-l last:rounded-r"
                        style={{ backgroundColor: color }}
                    />
                ))}
            </div>

            <div className="flex justify-between mt-1 text-xs text-gray-500">
                <span>{formatLegendValue(minValue)}</span>
                <span>{formatLegendValue(maxValue)}</span>
            </div>
        </div>
    );
}
