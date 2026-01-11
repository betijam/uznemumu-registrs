/**
 * Financial Analysis Helper Functions
 * Calculations for Trust Score, Red Flags, Cash Flow metrics, etc.
 */

// ============================================================================
// TRUST SCORE CALCULATION
// ============================================================================

interface TrustScoreResult {
    score: number;
    riskLevel: 'low' | 'medium' | 'high';
    riskColor: string;
    liquidityScore: number;
    profitabilityScore: number;
    capitalScore: number;
}

/**
 * Calculate Trust Score (0-100) based on Liquidity, Profitability, and Capital
 * Formula: (Liquidity * 40%) + (Profitability * 30%) + (Capital * 30%)
 */
export function calculateTrustScore(financialData: any): TrustScoreResult | null {
    if (!financialData) return null;

    const { total_current_assets, current_liabilities, profit, turnover, equity, total_assets } = financialData;

    // Calculate sub-scores
    const liquidityScore = calculateLiquidityScore(total_current_assets, current_liabilities);
    const profitabilityScore = calculateProfitabilityScore(profit, turnover);
    const capitalScore = calculateCapitalScore(equity, total_assets);

    // If any sub-score is null, cannot calculate Trust Score
    if (liquidityScore === null || profitabilityScore === null || capitalScore === null) {
        return null;
    }

    // Weighted average
    const score = Math.round(
        (liquidityScore * 0.4) +
        (profitabilityScore * 0.3) +
        (capitalScore * 0.3)
    );

    // Determine risk level
    let riskLevel: 'low' | 'medium' | 'high';
    let riskColor: string;

    if (score >= 71) {
        riskLevel = 'low';
        riskColor = '#10b981'; // green
    } else if (score >= 41) {
        riskLevel = 'medium';
        riskColor = '#f59e0b'; // yellow/amber
    } else {
        riskLevel = 'high';
        riskColor = '#ef4444'; // red
    }

    return {
        score: Math.max(0, Math.min(100, score)), // Clamp to 0-100
        riskLevel,
        riskColor,
        liquidityScore,
        profitabilityScore,
        capitalScore
    };
}

/**
 * Liquidity Score: total_current_assets / current_liabilities
 * < 0.8 = 0pt; > 1.5 = 100pt; linear between
 */
function calculateLiquidityScore(currentAssets: number | null, currentLiabilities: number | null): number | null {
    if (!currentAssets || !currentLiabilities || currentLiabilities === 0) return null;

    const ratio = currentAssets / currentLiabilities;

    if (ratio <= 0.8) return 0;
    if (ratio >= 1.5) return 100;

    // Linear interpolation between 0.8 and 1.5
    return Math.round(((ratio - 0.8) / (1.5 - 0.8)) * 100);
}

/**
 * Profitability Score: profit / turnover
 * < 0% = 0pt; > 10% = 100pt; linear between
 */
function calculateProfitabilityScore(profit: number | null, turnover: number | null): number | null {
    if (profit === null || !turnover || turnover === 0) return null;

    const margin = (profit / turnover) * 100; // Convert to percentage

    if (margin <= 0) return 0;
    if (margin >= 10) return 100;

    // Linear interpolation between 0% and 10%
    return Math.round((margin / 10) * 100);
}

/**
 * Capital Score: equity / total_assets
 * < 10% = 0pt; > 50% = 100pt; linear between
 */
function calculateCapitalScore(equity: number | null, totalAssets: number | null): number | null {
    if (equity === null || !totalAssets || totalAssets === 0) return null;

    const ratio = (equity / totalAssets) * 100; // Convert to percentage

    if (ratio <= 10) return 0;
    if (ratio >= 50) return 100;

    // Linear interpolation between 10% and 50%
    return Math.round(((ratio - 10) / (50 - 10)) * 100);
}

// ============================================================================
// RED FLAGS DETECTION
// ============================================================================

export interface RedFlag {
    type: 'negative_ocf' | 'negative_equity' | 'high_dso' | 'low_cash_coverage';
    message: string;
    severity: 'high' | 'medium';
}

export function detectRedFlags(financialData: any): RedFlag[] {
    const flags: RedFlag[] = [];

    // 1. Negative Operating Cash Flow
    if (financialData.cfo_im_net_operating_cash_flow !== null &&
        financialData.cfo_im_net_operating_cash_flow < 0) {
        flags.push({
            type: 'negative_ocf',
            message: 'Negatīva operatīvā naudas plūsma',
            severity: 'high'
        });
    }

    // 2. Negative Equity
    if (financialData.equity !== null && financialData.equity < 0) {
        flags.push({
            type: 'negative_equity',
            message: 'Negatīvs pašu kapitāls',
            severity: 'high'
        });
    }

    // 3. High DSO (> 60 days)
    const dso = calculateDSO(financialData.accounts_receivable, financialData.turnover);
    if (dso !== null && dso > 60) {
        flags.push({
            type: 'high_dso',
            message: `Augsts debitoru apgrozījums (${Math.round(dso)} dienas)`,
            severity: 'medium'
        });
    }

    // 4. Low Cash Coverage (< 0.1)
    if (financialData.cash_balance !== null &&
        financialData.current_liabilities !== null &&
        financialData.current_liabilities > 0) {
        const cashCoverage = financialData.cash_balance / financialData.current_liabilities;
        if (cashCoverage < 0.1) {
            flags.push({
                type: 'low_cash_coverage',
                message: 'Zems naudas segums',
                severity: 'medium'
            });
        }
    }

    return flags;
}

// ============================================================================
// FINANCIAL METRICS CALCULATIONS
// ============================================================================

/**
 * Calculate Days Sales Outstanding (DSO)
 * Formula: (accounts_receivable / turnover) * 365
 */
export function calculateDSO(accountsReceivable: number | null, turnover: number | null): number | null {
    if (!accountsReceivable || !turnover || turnover === 0) return null;
    return (accountsReceivable / turnover) * 365;
}

/**
 * Calculate Free Cash Flow (FCF)
 * Formula: Operating Cash Flow + CapEx (CapEx is usually negative)
 */
export function calculateFCF(
    operatingCashFlow: number | null,
    capex: number | null
): number | null {
    if (operatingCashFlow === null) return null;
    return operatingCashFlow + (capex || 0);
}

/**
 * Calculate OCF to Net Income conversion rate
 */
export function calculateOCFConversion(
    operatingCashFlow: number | null,
    netIncome: number | null
): number | null {
    if (!operatingCashFlow || !netIncome || netIncome === 0) return null;
    return (operatingCashFlow / netIncome) * 100;
}

/**
 * Calculate Average Gross Salary
 * Formula: labour_expenses / employee_count / 12 months
 */
export function calculateAvgSalary(
    labourExpenses: number | null,
    employeeCount: number | null
): number | null {
    if (!labourExpenses || !employeeCount || employeeCount === 0) return null;
    return labourExpenses / employeeCount / 12;
}

/**
 * Calculate Year-over-Year growth percentage
 */
export function calculateYoYGrowth(current: number | null, previous: number | null): number | null {
    if (current === null || previous === null || previous === 0) return null;
    return ((current - previous) / Math.abs(previous)) * 100;
}

// ============================================================================
// FORMATTING HELPERS
// ============================================================================

export function formatCurrency(value: number | null): string {
    if (value === null || value === undefined) return '-';
    return new Intl.NumberFormat('lv-LV', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
}

export function formatPercent(value: number | null, decimals: number = 1): string {
    if (value === null || value === undefined) return '-';
    return `${value.toFixed(decimals)}%`;
}

export function formatRatio(value: number | null, decimals: number = 2): string {
    if (value === null || value === undefined) return '-';
    return value.toFixed(decimals);
}

export function formatNumber(value: number | null): string {
    if (value === null || value === undefined) return '-';
    return new Intl.NumberFormat('lv-LV').format(value);
}

// Safe division helper
export function safeDiv(numerator: number | null, denominator: number | null): number | null {
    if (numerator === null || denominator === null || denominator === 0) return null;
    return numerator / denominator;
}
