export function formatCurrency(value: number | null | undefined): string {
    if (value === null || value === undefined || value === 0) return '-';
    const absValue = Math.abs(value);
    const sign = value < 0 ? '-' : '';
    if (absValue >= 1000000) {
        return `${sign}${(absValue / 1000000).toFixed(1)} M€`;
    } else if (absValue >= 1000) {
        return `${sign}${Math.round(absValue / 1000)} k€`;
    }
    return `${sign}${Math.round(absValue)} €`;
}
