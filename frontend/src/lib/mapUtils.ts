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

// Color scales for each metric
const COLOR_SCALES: Record<MetricType, { colors: string[]; label: string; format: (v: number) => string }> = {
    total_revenue: {
        colors: ['#e3f2fd', '#90caf9', '#42a5f5', '#1e88e5', '#1565c0', '#0d47a1'],
        label: 'Apgrozījums',
        format: (v) => `€${(v / 1000000).toFixed(1)}M`
    },
    total_profit: {
        colors: ['#e8f5e9', '#a5d6a7', '#66bb6a', '#43a047', '#2e7d32', '#1b5e20'],
        label: 'Peļņa',
        format: (v) => `€${(v / 1000000).toFixed(1)}M`
    },
    avg_salary: {
        colors: ['#f3e5f5', '#ce93d8', '#ab47bc', '#8e24aa', '#6a1b9a', '#4a148c'],
        label: 'Vid. alga',
        format: (v) => `€${Math.round(v)}`
    },
    total_employees: {
        colors: ['#fff3e0', '#ffcc80', '#ffa726', '#fb8c00', '#f57c00', '#e65100'],
        label: 'Darbinieki',
        format: (v) => v.toLocaleString()
    }
};

/**
 * Get color for a value based on the metric and data range
 */
export function getColor(value: number, metric: MetricType, minValue: number, maxValue: number): string {
    const scale = COLOR_SCALES[metric];
    if (!scale || value === 0 || maxValue === minValue) {
        return '#f5f5f5'; // Gray for no data
    }

    const normalized = (value - minValue) / (maxValue - minValue);
    const index = Math.min(Math.floor(normalized * scale.colors.length), scale.colors.length - 1);

    return scale.colors[Math.max(0, index)];
}

/**
 * Get the color scale configuration for a metric
 */
export function getColorScale(metric: MetricType) {
    return COLOR_SCALES[metric];
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
    return COLOR_SCALES[metric]?.format(value) || value.toString();
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
