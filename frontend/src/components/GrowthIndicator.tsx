import React from 'react';

export const GrowthIndicator = ({ value }: { value: number | null }) => {
    if (value === null || value === undefined) return <span className="text-gray-300">-</span>;

    const isPositive = value >= 0;
    const colorClass = isPositive ? "text-green-600" : "text-red-600";
    const arrow = isPositive ? "↑" : "↓";

    return (
        <span className={`font-medium ${colorClass}`}>
            {arrow} {Math.abs(value).toFixed(1)}%
        </span>
    );
};
