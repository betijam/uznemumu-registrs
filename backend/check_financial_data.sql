-- Check if financial data exists for company 40003520643
-- Run this query in your Neon database console

SELECT 
    year,
    turnover,
    profit,
    by_nature_labour_expenses as labour_costs,
    interest_expenses,
    depreciation_expenses,
    provision_for_income_taxes,
    inventories,
    non_current_liabilities,
    cfo_im_net_operating_cash_flow as cfo,
    cfo_im_income_taxes_paid as taxes_paid_cf,
    cfi_acquisition_of_fixed_assets_intangible_assets as cfi,
    cff_net_financing_cash_flow as cff
FROM financial_reports
WHERE company_regcode = '40003520643'
ORDER BY year DESC
LIMIT 3;
