/**
 * Format company name for display
 * If name_in_quotes and type are available, returns "NAME, TYPE" (e.g., "ANIMAS, SIA")
 * Otherwise returns the full legal name as fallback
 */
export function formatCompanyName(company: {
    name: string;
    name_in_quotes?: string | null;
    type?: string | null;
}): string {
    if (company.name_in_quotes && company.type) {
        return `${company.name_in_quotes}, ${company.type}`;
    }
    return company.name;
}
