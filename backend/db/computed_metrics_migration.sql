-- Migration: Create company_computed_metrics table for performance optimization
-- This table stores pre-calculated metrics to avoid computing them on every request

CREATE TABLE IF NOT EXISTS company_computed_metrics (
    id SERIAL PRIMARY KEY,
    company_regcode BIGINT REFERENCES companies(regcode) ON DELETE CASCADE,
    year INT NOT NULL,
    
    -- Salary metrics (calculated from tax_payments.social_tax_vsaoi)
    avg_gross_salary NUMERIC(10,2),
    avg_net_salary NUMERIC(10,2),
    
    -- Financial ratios (calculated from financial_reports)
    profit_margin NUMERIC(10,2),
    revenue_per_employee NUMERIC(15,2),
    
    -- Risk aggregates (from risks table)
    total_risk_score INT DEFAULT 0,
    has_active_risks BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    computed_at TIMESTAMP DEFAULT NOW(),
    data_version INT DEFAULT 1,
    
    UNIQUE(company_regcode, year)
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_computed_metrics_company ON company_computed_metrics(company_regcode);
CREATE INDEX IF NOT EXISTS idx_computed_metrics_year ON company_computed_metrics(year);
CREATE INDEX IF NOT EXISTS idx_computed_metrics_company_year ON company_computed_metrics(company_regcode, year);

-- Function to auto-update computed_at timestamp
CREATE OR REPLACE FUNCTION update_computed_at_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.computed_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update timestamp on updates
DROP TRIGGER IF EXISTS trigger_update_computed_at ON company_computed_metrics;
CREATE TRIGGER trigger_update_computed_at
    BEFORE UPDATE ON company_computed_metrics
    FOR EACH ROW
    EXECUTE FUNCTION update_computed_at_timestamp();

-- Comments for documentation
COMMENT ON TABLE company_computed_metrics IS 'Pre-computed metrics for company profiles to improve page load performance';
COMMENT ON COLUMN company_computed_metrics.avg_gross_salary IS 'Monthly average gross salary calculated from VSAOI (social tax)';
COMMENT ON COLUMN company_computed_metrics.avg_net_salary IS 'Monthly average net salary after deductions';
COMMENT ON COLUMN company_computed_metrics.profit_margin IS 'Profit margin percentage: (profit / revenue) * 100';
COMMENT ON COLUMN company_computed_metrics.revenue_per_employee IS 'Revenue divided by number of employees';
COMMENT ON COLUMN company_computed_metrics.total_risk_score IS 'Sum of all active risk scores for the company';
COMMENT ON COLUMN company_computed_metrics.has_active_risks IS 'Boolean flag indicating if company has any active risks';
