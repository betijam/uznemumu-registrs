-- Migration: Add Extended Financial Fields for Advanced Analysis
-- Date: 2026-01-11
-- Purpose: Add Cash Flow, Accounts Receivable, and Labour Expenses fields

-- Add Balance Sheet field for DSO calculation
ALTER TABLE financial_reports ADD COLUMN IF NOT EXISTS accounts_receivable DECIMAL(15,2);

-- Add P&L field for average salary calculation
ALTER TABLE financial_reports ADD COLUMN IF NOT EXISTS by_nature_labour_expenses DECIMAL(15,2);

-- Add Cash Flow Statement fields
-- Operating Activities (CFO using Indirect Method)
ALTER TABLE financial_reports ADD COLUMN IF NOT EXISTS cfo_im_net_operating_cash_flow DECIMAL(15,2);
ALTER TABLE financial_reports ADD COLUMN IF NOT EXISTS cfo_im_income_taxes_paid DECIMAL(15,2);

-- Investing Activities (CFI)
ALTER TABLE financial_reports ADD COLUMN IF NOT EXISTS cfi_acquisition_of_fixed_assets_intangible_assets DECIMAL(15,2);

-- Financing Activities (CFF) - Optional for future use
ALTER TABLE financial_reports ADD COLUMN IF NOT EXISTS cff_net_financing_cash_flow DECIMAL(15,2);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_financial_reports_year ON financial_reports(year);
CREATE INDEX IF NOT EXISTS idx_financial_reports_company_year ON financial_reports(company_regcode, year);

-- Update comments
COMMENT ON COLUMN financial_reports.accounts_receivable IS 'Accounts receivable (debtors) for DSO calculation';
COMMENT ON COLUMN financial_reports.by_nature_labour_expenses IS 'Total labour expenses for average salary calculation';
COMMENT ON COLUMN financial_reports.cfo_im_net_operating_cash_flow IS 'Net operating cash flow (indirect method)';
COMMENT ON COLUMN financial_reports.cfo_im_income_taxes_paid IS 'Income taxes paid (cash flow)';
COMMENT ON COLUMN financial_reports.cfi_acquisition_of_fixed_assets_intangible_assets IS 'CapEx - acquisition of fixed/intangible assets (usually negative)';
COMMENT ON COLUMN financial_reports.cff_net_financing_cash_flow IS 'Net financing cash flow';
