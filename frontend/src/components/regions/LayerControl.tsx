"use client";

import { MetricType, getColorScale, formatValue } from "@/lib/mapUtils";

interface LayerControlProps {
    selectedMetric: MetricType;
    onMetricChange: (metric: MetricType) => void;
    showBubbles: boolean;
    onBubblesChange: (show: boolean) => void;
    showTopPerformers: boolean;
    onTopPerformersChange: (show: boolean) => void;
}

const METRICS: { value: MetricType; label: string; icon: string }[] = [
    { value: "total_revenue", label: "Apgrozījums", icon: "💰" },
    { value: "total_profit", label: "Peļņa", icon: "📈" },
    { value: "avg_salary", label: "Vid. alga", icon: "💵" },
    { value: "total_employees", label: "Darbinieki", icon: "👥" },
];

export default function LayerControl({
    selectedMetric,
    onMetricChange,
    showBubbles,
    onBubblesChange,
    showTopPerformers,
    onTopPerformersChange,
}: LayerControlProps) {
    return (
        <div className="absolute top-4 right-4 z-[1000] bg-white rounded-xl shadow-lg p-4 min-w-[200px]">
            {/* Base Metric Selection */}
            <div className="mb-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">
                    Iekrāsot pēc...
                </h3>
                <div className="space-y-1">
                    {METRICS.map((metric) => (
                        <label
                            key={metric.value}
                            className={`flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors ${selectedMetric === metric.value
                                    ? "bg-primary/10 text-primary"
                                    : "hover:bg-gray-50"
                                }`}
                        >
                            <input
                                type="radio"
                                name="metric"
                                value={metric.value}
                                checked={selectedMetric === metric.value}
                                onChange={() => onMetricChange(metric.value)}
                                className="sr-only"
                            />
                            <span className="text-lg">{metric.icon}</span>
                            <span className="text-sm font-medium">{metric.label}</span>
                            {selectedMetric === metric.value && (
                                <span className="ml-auto text-primary">✓</span>
                            )}
                        </label>
                    ))}
                </div>
            </div>

            {/* Overlay Toggles */}
            <div className="border-t pt-3">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">
                    Papildus slāņi
                </h3>
                <div className="space-y-2">
                    <label className="flex items-center gap-2 cursor-pointer">
                        <input
                            type="checkbox"
                            checked={showBubbles}
                            onChange={(e) => onBubblesChange(e.target.checked)}
                            className="w-4 h-4 text-primary rounded border-gray-300 focus:ring-primary"
                        />
                        <span className="text-sm">Blīvuma burbuļi</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                        <input
                            type="checkbox"
                            checked={showTopPerformers}
                            onChange={(e) => onTopPerformersChange(e.target.checked)}
                            className="w-4 h-4 text-primary rounded border-gray-300 focus:ring-primary"
                        />
                        <span className="text-sm">Top 10 uzņēmumi</span>
                    </label>
                </div>
            </div>
        </div>
    );
}
