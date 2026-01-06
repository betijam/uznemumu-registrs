/**
 * Map utility functions for the Regions Dashboard
 */

export type MetricType = 'total_revenue' | 'total_profit' | 'total_employees' | 'avg_salary';

export interface RegionProperties {
    id: string;
    name: string;
    db_name?: string;
    location_type?: string;
    company_count: number;
    total_employees: number;
    total_revenue: number;
    total_profit: number;
    avg_salary: number;
}

// Color buckets for each metric (threshold-based to avoid Riga dominance)
const COLOR_BUCKETS: Record<MetricType, { thresholds: number[]; colors: string[]; label: string; format: (v: number) => string }> = {
    total_revenue: {
        thresholds: [10000000, 50000000, 100000000, 500000000, 1000000000], // 10M, 50M, 100M, 500M, 1B
        colors: ['#e3f2fd', '#90caf9', '#42a5f5', '#1e88e5', '#1565c0', '#0d47a1'],
        label: 'Apgrozījums',
        format: (v) => v >= 1000000000 ? `€${(v / 1000000000).toFixed(1)}B` : `€${(v / 1000000).toFixed(1)}M`
    },
    total_profit: {
        thresholds: [1000000, 5000000, 20000000, 50000000, 100000000], // 1M, 5M, 20M, 50M, 100M
        colors: ['#e8f5e9', '#a5d6a7', '#66bb6a', '#43a047', '#2e7d32', '#1b5e20'],
        label: 'Peļņa',
        format: (v) => v >= 1000000000 ? `€${(v / 1000000000).toFixed(1)}B` : `€${(v / 1000000).toFixed(1)}M`
    },
    avg_salary: {
        thresholds: [800, 1000, 1200, 1500, 2000], // Salary buckets
        colors: ['#f3e5f5', '#ce93d8', '#ab47bc', '#8e24aa', '#6a1b9a', '#4a148c'],
        label: 'Vid. alga',
        format: (v) => `€${Math.round(v)}`
    },
    total_employees: {
        thresholds: [500, 2000, 5000, 20000, 50000], // Employee buckets
        colors: ['#fff3e0', '#ffcc80', '#ffa726', '#fb8c00', '#f57c00', '#e65100'],
        label: 'Darbinieki',
        format: (v) => v >= 1000 ? `${(v / 1000).toFixed(1)}K` : v.toString()
    }
};

/**
 * Get color for a value using threshold buckets (logarithmic-like distribution)
 */
export function getColor(value: number, metric: MetricType): string {
    const bucket = COLOR_BUCKETS[metric];
    if (!bucket || value === 0 || value === null) {
        return '#f5f5f5'; // Gray for no data
    }

    // Find which bucket the value falls into
    for (let i = 0; i < bucket.thresholds.length; i++) {
        if (value < bucket.thresholds[i]) {
            return bucket.colors[i];
        }
    }

    // Value exceeds all thresholds - return darkest color
    return bucket.colors[bucket.colors.length - 1];
}

/**
 * Get the color scale configuration for a metric
 */
export function getColorScale(metric: MetricType) {
    return COLOR_BUCKETS[metric];
}

/**
 * Calculate min and max values for a metric from features
 */
export function calculateRange(features: any[], metric: MetricType): { min: number; max: number } {
    const values = features
        .map(f => f.properties[metric] || 0)
        .filter(v => v > 0);

    if (values.length === 0) {
        return { min: 0, max: 0 };
    }

    return {
        min: Math.min(...values),
        max: Math.max(...values)
    };
}

/**
 * Format a value for display based on metric type
 */
export function formatValue(value: number, metric: MetricType): string {
    return COLOR_BUCKETS[metric]?.format(value) || value.toString();
}

/**
 * Calculate centroid of a polygon for bubble overlays
 */
export function calculateCentroid(coordinates: number[][][]): [number, number] {
    let totalLat = 0;
    let totalLng = 0;
    let pointCount = 0;

    // Handle both Polygon and MultiPolygon
    const rings = Array.isArray(coordinates[0][0]) && typeof coordinates[0][0][0] === 'number'
        ? coordinates
        : coordinates.flat();

    for (const ring of rings) {
        for (const coord of ring) {
            if (Array.isArray(coord) && coord.length >= 2) {
                totalLng += coord[0];
                totalLat += coord[1];
                pointCount++;
            }
        }
    }

    if (pointCount === 0) return [56.9496, 24.1052]; // Default: Latvia center

    return [totalLat / pointCount, totalLng / pointCount];
}

/**
 * Latvia bounds for map initialization
 */
export const LATVIA_BOUNDS: [[number, number], [number, number]] = [
    [55.6, 20.9], // Southwest
    [58.1, 28.3]  // Northeast
];

export const LATVIA_CENTER: [number, number] = [56.9496, 24.1052];
