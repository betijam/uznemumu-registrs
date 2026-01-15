
-- Critical Indexes for Company Page Performance

-- 1. Financial Reports (Used everywhere)
CREATE INDEX IF NOT EXISTS idx_financial_reports_regcode ON financial_reports(company_regcode);
CREATE INDEX IF NOT EXISTS idx_financial_reports_regcode_year ON financial_reports(company_regcode, year DESC);

-- 2. Persons / Officers (Heavy join usually)
CREATE INDEX IF NOT EXISTS idx_persons_regcode ON persons(company_regcode);
CREATE INDEX IF NOT EXISTS idx_persons_regcode_role ON persons(company_regcode, role);

-- 3. Risks & Sanctions
CREATE INDEX IF NOT EXISTS idx_risks_regcode ON risks(company_regcode);
CREATE INDEX IF NOT EXISTS idx_risks_active_score ON risks(company_regcode, active DESC, risk_score DESC);

-- 4. Procurements (Can be large)
CREATE INDEX IF NOT EXISTS idx_procurements_winner_regcode ON procurements(winner_regcode);
CREATE INDEX IF NOT EXISTS idx_procurements_contract_date ON procurements(winner_regcode, contract_date DESC);

-- 5. Tax Payments
CREATE INDEX IF NOT EXISTS idx_tax_payments_regcode ON tax_payments(company_regcode);

-- 6. Company Ratings
CREATE INDEX IF NOT EXISTS idx_company_ratings_regcode ON company_ratings(company_regcode);

-- Analyze tables to update statistics for query planner
ANALYZE financial_reports;
ANALYZE persons;
ANALYZE risks;
ANALYZE procurements;
