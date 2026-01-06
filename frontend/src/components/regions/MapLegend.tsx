"use client";

import { MetricType, getColorScale } from "@/lib/mapUtils";

interface MapLegendProps {
    metric: MetricType;
}

export default function MapLegend({ metric }: MapLegendProps) {
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

    // Create legend labels from thresholds
    const thresholds = scale.thresholds || [];
    const legendLabels = [
        "< " + formatLegendValue(thresholds[0] || 0),
        ...thresholds.slice(0, -1).map((t, i) =>
            formatLegendValue(t) + " - " + formatLegendValue(thresholds[i + 1])
        ),
        "> " + formatLegendValue(thresholds[thresholds.length - 1] || 0)
    ];

    return (
        <div className="absolute bottom-8 left-4 z-[1000] bg-white rounded-xl shadow-lg p-4 max-w-[200px]">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">{scale.label}</h4>

            <div className="space-y-1">
                {scale.colors.map((color, i) => (
                    <div key={i} className="flex items-center gap-2">
                        <div
                            className="w-5 h-4 rounded"
                            style={{ backgroundColor: color }}
                        />
                        <span className="text-xs text-gray-600">
                            {legendLabels[i] || ""}
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
}
