-- 1. UZŅĒMUMI (Master tabula)
CREATE TABLE companies (
    regcode BIGINT PRIMARY KEY, 
    name TEXT NOT NULL,
    address TEXT,
    registration_date DATE,
    status TEXT, 
    sepa_identifier TEXT,
    company_size_badge TEXT,
    
    -- NACE Industry Classification (from VID tax data)
    nace_code VARCHAR(10),              -- Primary NACE code (e.g., "6201", "A", "4791")
    nace_text VARCHAR(500),             -- NACE description (e.g., "Datorprogrammēšana")
    nace_section VARCHAR(5),            -- Section code (e.g., "62", "A", "47") for grouping
    nace_section_text VARCHAR(200),     -- Section description (e.g., "IT pakalpojumi")
    employee_count INTEGER DEFAULT 0,   -- From VID tax data
    tax_data_year INTEGER,              -- Year of latest tax data
    
    last_updated TIMESTAMP DEFAULT NOW()
);
-- Indekss ātrai teksta meklēšanai
CREATE INDEX idx_company_name ON companies USING GIN (to_tsvector('simple', name));
-- NACE industry indexes for filtering
CREATE INDEX idx_companies_nace_code ON companies(nace_code);
CREATE INDEX idx_companies_nace_section ON companies(nace_section);
CREATE INDEX idx_companies_employee_count ON companies(employee_count);


-- 2. PERSONAS (Paplašināta ar visiem laukiem no CSV)
CREATE TABLE persons (
    id SERIAL PRIMARY KEY,
    company_regcode BIGINT REFERENCES companies(regcode),
    person_name TEXT NOT NULL, 
    person_code TEXT, -- 'latvian_identity_number_masked' vai dzimšanas datums
    role TEXT, -- 'officer', 'member', 'ubo'
    
    -- Officers (Amatpersonas)
    position TEXT,                    -- 'BOARD_MEMBER', 'CHAIR_OF_BOARD', etc.
    rights_of_representation TEXT,    -- 'INDIVIDUALLY', 'WITH_ALL', 'WITH_AT_LEAST'
    representation_with_at_least INT, -- Minimālais locekļu skaits
    
    -- Members (Dalībnieki)
    number_of_shares INTEGER,
    share_nominal_value DECIMAL(15,2),
    share_currency TEXT DEFAULT 'EUR',
    legal_entity_regcode BIGINT,      -- Ja dalībnieks ir uzņēmums
    
    -- UBOs
    nationality TEXT,                 -- ISO kods: 'LV', 'EE'
    residence TEXT,
    
    -- Kopīgie
    share_percent DECIMAL(5,2), 
    date_from DATE,
    date_to DATE,
    
    UNIQUE(company_regcode, person_name, role, person_code) 
);
CREATE INDEX idx_person_name ON persons(person_name);
CREATE INDEX idx_person_code ON persons(person_code);
CREATE INDEX idx_person_role ON persons(role);


-- 3. FINANSES (Paplašināta ar bilanci un rādītājiem)
CREATE TABLE financial_reports (
    id SERIAL PRIMARY KEY,
    company_regcode BIGINT REFERENCES companies(regcode),
    year INT NOT NULL,
    
    -- Income Statement (PZA)
    turnover DECIMAL(15,2), 
    profit DECIMAL(15,2), 
    employees INT, 
    taxes_paid DECIMAL(15,2),
    interest_expenses DECIMAL(15,2),
    depreciation_expenses DECIMAL(15,2),
    provision_for_income_taxes DECIMAL(15,2),
    
    -- Balance Sheet (Bilance)
    total_assets DECIMAL(15,2),
    total_current_assets DECIMAL(15,2),
    cash_balance DECIMAL(15,2),
    inventories DECIMAL(15,2),
    current_liabilities DECIMAL(15,2),
    non_current_liabilities DECIMAL(15,2),
    equity DECIMAL(15,2),
    
    -- Calculated Metrics
    ebitda DECIMAL(15,2),
    current_ratio DECIMAL(15,4),
    quick_ratio DECIMAL(15,4),
    cash_ratio DECIMAL(15,4),
    net_profit_margin DECIMAL(15,4),
    roe DECIMAL(15,4),
    roa DECIMAL(15,4),
    debt_to_equity DECIMAL(15,4),
    equity_ratio DECIMAL(15,4),
    
    UNIQUE(company_regcode, year)
);


-- 4. IEPIRKUMI - REZULTĀTI (Uzvarētāji)
CREATE TABLE procurements (
    id SERIAL PRIMARY KEY,
    winner_regcode BIGINT REFERENCES companies(regcode),
    contract_date DATE,
    authority_name TEXT,
    subject TEXT,
    amount DECIMAL(15,2),
    currency VARCHAR(3) DEFAULT 'EUR',
    -- Papildinājumi priekš ETL:
    year INT, -- Ērtai filtrēšanai pēc gada (2025, 2024 utt.)
    source_link TEXT -- Hipersaite uz EIS ziņojumu
);
CREATE INDEX idx_procurements_winner ON procurements(winner_regcode);


-- 5. IEPIRKUMI - PIEDĀVĀJUMI (Atvēršana / Pretendenti)
-- Šī tabula glabā informāciju par dalību, pat ja nav uzvarēts
CREATE TABLE procurement_bids (
    id SERIAL PRIMARY KEY,
    bidder_regcode BIGINT, -- Šeit neliekam REFERENCES, lai nebloķētu importu, ja uzņēmums vēl nav reģistra tabulā (vai ir ārvalstu)
    bidder_name TEXT,
    procurement_id TEXT, -- Iepirkuma identifikācijas numurs
    procurement_name TEXT,
    authority_name TEXT,
    opening_date DATE,
    source_year INT
);
CREATE INDEX idx_bids_bidder ON procurement_bids(bidder_regcode);


-- 6. RISKI (Paplašināta ar detalizētu kategoriju)
CREATE TABLE risks (
    id SERIAL PRIMARY KEY,
    company_regcode BIGINT REFERENCES companies(regcode),
    risk_type TEXT, -- 'sanction', 'liquidation', 'suspension', 'securing_measure'
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    start_date DATE,
    end_date DATE,
    
    -- Sanctions specific
    sanction_program TEXT, -- 'OFAC', 'EU', 'Latvia National'
    sanction_list_text TEXT,
    legal_base_url TEXT,
    
    -- Suspensions/Prohibitions specific
    suspension_code TEXT,
    suspension_grounds TEXT,
    
    -- Securing Measures specific
    measure_type TEXT, -- 'Līdzekļu arests', 'Aizliegums reģistrēt komercķīlas'
    institution_name TEXT, -- VID, Tiesu izpildītājs
    case_number TEXT,
    
    -- Liquidation specific
    liquidation_type TEXT, -- 'Likvidācija', 'Maksātnespējas process'
    liquidation_grounds TEXT,
    
    -- Risk scoring
    risk_score INT DEFAULT 0 -- Calculated: sanctions=100, liquidation=50, suspension=30, securing=10
);
CREATE INDEX idx_risks_company ON risks(company_regcode);
CREATE INDEX idx_risks_type ON risks(risk_type);
CREATE INDEX idx_risks_active ON risks(active);


-- 7. MONITORINGS (Lietotājiem)
CREATE TABLE user_subscriptions (
    id SERIAL PRIMARY KEY,
    user_email TEXT NOT NULL,
    target_regcode BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);


-- 8. VID SAMAKSĀTIE NODOKĻI
CREATE TABLE tax_payments (
    id SERIAL PRIMARY KEY,
    company_regcode BIGINT REFERENCES companies(regcode),
    year INT NOT NULL,
    total_tax_paid DECIMAL(15,2),      -- Kopējā nodokļu summa EUR
    labor_tax_iin DECIMAL(15,2),       -- Iedzīvotāju ienākuma nodoklis
    social_tax_vsaoi DECIMAL(15,2),    -- VSAOI
    avg_employees DECIMAL(10,2),       -- Vidējais darbinieku skaits
    nace_code VARCHAR(10),             -- Pamatdarbības NACE
    UNIQUE(company_regcode, year)
);
CREATE INDEX idx_tax_company ON tax_payments(company_regcode);


-- 9. VID REITINGS
CREATE TABLE company_ratings (
    id SERIAL PRIMARY KEY,
    company_regcode BIGINT REFERENCES companies(regcode),
    rating_grade VARCHAR(5),           -- 'A', 'B', 'C', 'N'
    rating_explanation TEXT,           -- Skaidrojums
    last_evaluated_on DATE,            -- Datums
    UNIQUE(company_regcode)
);
CREATE INDEX idx_rating_company ON company_ratings(company_regcode);