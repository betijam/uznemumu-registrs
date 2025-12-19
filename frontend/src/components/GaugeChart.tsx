"use client";

interface GaugeChartProps {
    value: number | null;
    min?: number;
    max?: number;
    thresholds: {
        good: number;
        warning: number;
    };
    label: string;
    subtitle?: string;
    format?: (val: number) => string;
    invertColors?: boolean; // For metrics where lower is better (like debt ratio)
}

export default function GaugeChart({
    value,
    min = 0,
    max = 3,
    thresholds,
    label,
    subtitle,
    format = (v) => v.toFixed(2),
    invertColors = false
}: GaugeChartProps) {
    if (value === null || value === undefined) {
        return (
            <div className="flex flex-col items-center justify-center p-6 bg-gray-50 rounded-lg border border-gray-200">
                <div className="text-gray-400 text-sm">{label}</div>
                <div className="text-2xl font-bold text-gray-300 mt-2">N/A</div>
                {subtitle && <div className="text-xs text-gray-400 mt-1">{subtitle}</div>}
            </div>
        );
    }

    // Determine color based on thresholds
    const getColor = () => {
        if (invertColors) {
            // For metrics where lower is better (debt ratios)
            if (value <= thresholds.warning) return { bg: 'bg-success/10', text: 'text-success', stroke: '#10b981' };
            if (value <= thresholds.good) return { bg: 'bg-yellow-50', text: 'text-yellow-600', stroke: '#f59e0b' };
            return { bg: 'bg-danger/10', text: 'text-danger', stroke: '#ef4444' };
        } else {
            // For metrics where higher is better (liquidity, ROE)
            if (value >= thresholds.good) return { bg: 'bg-success/10', text: 'text-success', stroke: '#10b981' };
            if (value >= thresholds.warning) return { bg: 'bg-yellow-50', text: 'text-yellow-600', stroke: '#f59e0b' };
            return { bg: 'bg-danger/10', text: 'text-danger', stroke: '#ef4444' };
        }
    };

    const colors = getColor();

    // Calculate percentage for arc (clamped between 0 and 1)
    const clampedValue = Math.min(Math.max(value, min), max);
    const percentage = (clampedValue - min) / (max - min);

    // SVG semi-circle gauge using stroke-dasharray
    const radius = 40;
    const strokeWidth = 8;
    const centerX = 50;
    const centerY = 50;

    // Semi-circle path (from left to right, curved at top)
    const circumference = Math.PI * radius; // Half circle circumference
    const dashLength = percentage * circumference;
    const gapLength = circumference - dashLength;

    // Semi-circle arc path (starts at left, goes to right through top)
    const arcPath = `M ${centerX - radius} ${centerY} A ${radius} ${radius} 0 0 1 ${centerX + radius} ${centerY}`;

    return (
        <div className={`flex flex-col items-center justify-center p-6 rounded-lg border ${colors.bg} border-gray-200`}>
            {/* Gauge SVG */}
            <svg viewBox="0 0 100 60" className="w-32 h-20">
                {/* Background arc (gray) */}
                <path
                    d={arcPath}
                    fill="none"
                    stroke="#e5e7eb"
                    strokeWidth={strokeWidth}
                    strokeLinecap="round"
                />
                {/* Value arc (colored) */}
                <path
                    d={arcPath}
                    fill="none"
                    stroke={colors.stroke}
                    strokeWidth={strokeWidth}
                    strokeLinecap="round"
                    strokeDasharray={`${dashLength} ${gapLength}`}
                />
            </svg>

            {/* Value below gauge */}
            <div className={`text-2xl font-bold ${colors.text} -mt-2`}>
                {format(value)}
            </div>

            {/* Label */}
            <div className="text-sm font-semibold text-gray-700 mt-1">{label}</div>
            {subtitle && <div className="text-xs text-gray-500 mt-0.5">{subtitle}</div>}
        </div>
    );
}
