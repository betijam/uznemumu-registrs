-- Optimised Cache Generation
-- Uses CTEs and JSONB aggregation to build the entire profile object in DB
-- Target speed: ~10k rows / second

WITH 
active_companies AS (
    SELECT * FROM companies WHERE status = 'active'
    -- You can remove the LIMIT or strict filter later to cache everything
    -- For now, let's cache ALL active companies
),

-- 1. Financial History & Growth
fin_data AS (
    SELECT 
        company_regcode,
        year,
        turnover,
        profit,
        employees,
        cash_balance,
        current_ratio, quick_ratio, cash_ratio,
        net_profit_margin, roe, roa, debt_to_equity, equity_ratio, ebitda,
        -- Calculate previous year for growth
        LAG(turnover) OVER (PARTITION BY company_regcode ORDER BY year) as prev_turnover,
        LAG(profit) OVER (PARTITION BY company_regcode ORDER BY year) as prev_profit
    FROM financial_reports
),
fin_calc AS (
    SELECT 
        *,
        CASE 
            WHEN prev_turnover IS NOT NULL AND prev_turnover != 0 
            THEN ROUND(((turnover - prev_turnover) / ABS(prev_turnover)) * 100, 1) 
            ELSE NULL 
        END as turnover_growth,
        CASE 
            WHEN prev_profit IS NOT NULL AND prev_profit != 0 
            THEN ROUND(((profit - prev_profit) / ABS(prev_profit)) * 100, 1) 
            ELSE NULL 
        END as profit_growth
    FROM fin_data
),
fin_agg AS (
    SELECT 
        company_regcode,
        jsonb_agg(
            jsonb_build_object(
                'year', year,
                'turnover', turnover,
                'profit', profit,
                'employees', employees,
                'cash_balance', cash_balance,
                'turnover_growth', turnover_growth,
                'profit_growth', profit_growth,
                'current_ratio', current_ratio,
                'quick_ratio', quick_ratio,
                'cash_ratio', cash_ratio,
                'net_profit_margin', net_profit_margin,
                'roe', roe,
                'roa', roa,
                'debt_to_equity', debt_to_equity,
                'equity_ratio', equity_ratio,
                'ebitda', ebitda
            ) ORDER BY year DESC
        ) as history,
        -- Get latest year data for summary
        (array_agg(
            jsonb_build_object(
                'year', year,
                'turnover', turnover,
                'profit', profit,
                'employees', employees,
                'turnover_growth', turnover_growth,
                'profit_growth', profit_growth
            ) ORDER BY year DESC
        ))[1] as latest_fin
    FROM fin_calc
    GROUP BY company_regcode
),

-- 2. Tax History
tax_data AS (
    SELECT 
        tp.company_regcode,
        tp.year,
        tp.total_tax_paid,
        tp.labor_tax_iin,
        tp.social_tax_vsaoi,
        tp.avg_employees,
        tp.nace_code,
        cm.avg_gross_salary,
        cm.avg_net_salary,
        -- Fallback calc if cm is missing
        CASE 
            WHEN cm.avg_gross_salary IS NULL AND tp.social_tax_vsaoi > 0 AND tp.avg_employees > 0
            THEN ROUND((tp.social_tax_vsaoi / 0.3409) / tp.avg_employees / 12, 2)
            ELSE NULL
        END as calc_gross
    FROM tax_payments tp
    LEFT JOIN company_computed_metrics cm ON tp.company_regcode = cm.company_regcode AND tp.year = cm.year
),
tax_agg AS (
    SELECT
        company_regcode,
        jsonb_agg(
            jsonb_build_object(
                'year', year,
                'total_tax_paid', total_tax_paid,
                'labor_tax_iin', labor_tax_iin,
                'social_tax_vsaoi', social_tax_vsaoi,
                'avg_employees', avg_employees,
                'nace_code', nace_code,
                'avg_gross_salary', COALESCE(avg_gross_salary, calc_gross),
                'avg_net_salary', CASE 
                    -- Simple net estimation if missing
                    WHEN avg_net_salary IS NULL AND (COALESCE(avg_gross_salary, calc_gross)) IS NOT NULL
                    THEN ROUND(
                        (COALESCE(avg_gross_salary, calc_gross) - (COALESCE(avg_gross_salary, calc_gross) * 0.105) - ((COALESCE(avg_gross_salary, calc_gross) - (COALESCE(avg_gross_salary, calc_gross) * 0.105)) * 0.20))
                    , 2)
                    ELSE avg_net_salary
                END
            ) ORDER BY year DESC
        ) as history
    FROM tax_data
    GROUP BY company_regcode
),

-- 3. Risks
risk_data AS (
    SELECT
        company_regcode,
        risk_type,
        risk_score,
        jsonb_build_object(
            'type', risk_type,
            'description', description,
            'date', start_date,
            'score', risk_score,
            'program', sanction_program,
            'list_text', sanction_list_text,
            'legal_base_url', legal_base_url,
            'liquidation_type', liquidation_type,
            'grounds', COALESCE(liquidation_grounds, suspension_grounds),
            'suspension_code', suspension_code,
            'measure_type', measure_type,
            'institution', institution_name,
            'case_number', case_number
        ) as risk_obj
    FROM risks
    WHERE active = TRUE
),
risk_agg AS (
    SELECT
        company_regcode,
        jsonb_build_object(
             'sanctions', COALESCE(jsonb_agg(risk_obj) FILTER (WHERE risk_type = 'sanction'), '[]'::jsonb),
             'liquidations', COALESCE(jsonb_agg(risk_obj) FILTER (WHERE risk_type = 'liquidation'), '[]'::jsonb),
             'suspensions', COALESCE(jsonb_agg(risk_obj) FILTER (WHERE risk_type = 'suspension'), '[]'::jsonb),
             'securing_measures', COALESCE(jsonb_agg(risk_obj) FILTER (WHERE risk_type = 'securing_measure'), '[]'::jsonb)
        ) as risks_by_type,
        SUM(risk_score) as total_score
    FROM risk_data
    GROUP BY company_regcode
),

-- 4. Persons
person_agg AS (
    SELECT
        company_regcode,
        COALESCE(jsonb_agg(
            jsonb_build_object(
                'name', person_name,
                'person_code', person_code,
                'nationality', nationality,
                'residence', residence,
                'registered_on', date_from,
                'birth_date', NULL -- Assuming not in DB or PII
            )
        ) FILTER (WHERE role = 'ubo'), '[]'::jsonb) as ubos,
        
        COALESCE(jsonb_agg(
            jsonb_build_object(
                'name', person_name,
                'person_code', person_code,
                'legal_entity_regcode', legal_entity_regcode,
                'number_of_shares', number_of_shares,
                'share_value', (COALESCE(number_of_shares,0) * COALESCE(share_nominal_value,0)),
                'share_currency', COALESCE(share_currency, 'EUR'),
                'percent', share_percent,
                'date_from', date_from
            )
        ) FILTER (WHERE role = 'member'), '[]'::jsonb) as members,
        
        COALESCE(jsonb_agg(
            jsonb_build_object(
                'name', person_name,
                'person_code', person_code,
                'position', position,
                'rights_of_representation', rights_of_representation,
                'representation_with_at_least', representation_with_at_least,
                'registered_on', date_from
            )
        ) FILTER (WHERE role = 'officer'), '[]'::jsonb) as officers,

        SUM(CASE WHEN role = 'member' THEN (COALESCE(number_of_shares,0) * COALESCE(share_nominal_value,0)) ELSE 0 END) as total_capital

    FROM persons
    GROUP BY company_regcode
),

-- 5. Procurements (Top 10)
proc_agg AS (
    SELECT
        winner_regcode as company_regcode,
        jsonb_agg(
            jsonb_build_object(
                'authority', authority_name,
                'subject', subject,
                'amount', amount,
                'date', contract_date
            ) ORDER BY contract_date DESC
        ) as list
    FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY winner_regcode ORDER BY contract_date DESC) as rn
        FROM procurements
    ) p
    WHERE rn <= 10
    GROUP BY winner_regcode
),

-- 6. Ratings
rating_agg AS (
    SELECT
        company_regcode,
        jsonb_build_object(
            'grade', rating_grade,
            'explanation', rating_explanation,
            'date', last_evaluated_on
        ) as rating_obj
    FROM company_ratings
)

INSERT INTO company_profile_cache (company_regcode, profile_data, updated_at)
SELECT
    c.regcode,
    jsonb_strip_nulls(jsonb_build_object(
        'regcode', c.regcode,
        'name', c.name,
        'name_in_quotes', c.name_in_quotes,
        'type', c.type,
        'type_text', c.type_text,
        'addressid', c.addressid,
        'address', c.address,
        'registration_date', c.registration_date,
        'status', c.status,
        'sepa_identifier', c.sepa_identifier,
        'pvn_number', c.pvn_number,
        'is_pvn_payer', c.is_pvn_payer,
        'company_size_badge', c.company_size_badge,
        'latest_size_year', NULL, -- Missing in table def provided
        'size_changed_recently', FALSE,
        'nace_code', c.nace_code,
        'nace_text', c.nace_text,
        'nace_section', c.nace_section,
        'nace_section_text', c.nace_section_text,
        'employee_count', c.employee_count,
        'tax_data_year', c.tax_data_year,
        
        -- Joined Data
        'financial_history', COALESCE(f.history, '[]'::jsonb),
        'finances', COALESCE(f.latest_fin, jsonb_build_object(
            'year', c.tax_data_year, 
            'employees', c.employee_count, 
            'turnover', NULL, 
            'profit', NULL
        )),
        
        'tax_history', COALESCE(t.history, '[]'::jsonb),
        'rating', rat.rating_obj,
        
        'risks', COALESCE(r.risks_by_type, '{"sanctions": [], "liquidations": [], "suspensions": [], "securing_measures": []}'::jsonb),
        'total_risk_score', COALESCE(r.total_score, 0),
        'risk_level', CASE 
            WHEN COALESCE(r.total_score, 0) >= 100 THEN 'CRITICAL'
            WHEN COALESCE(r.total_score, 0) >= 50 THEN 'HIGH'
            WHEN COALESCE(r.total_score, 0) >= 30 THEN 'MEDIUM'
            WHEN COALESCE(r.total_score, 0) > 0 THEN 'LOW'
            ELSE 'NONE'
        END,
        
        'ubos', COALESCE(p.ubos, '[]'::jsonb),
        'members', COALESCE(p.members, '[]'::jsonb),
        'officers', COALESCE(p.officers, '[]'::jsonb),
        'total_capital', COALESCE(p.total_capital, 0),
        
        'procurements', COALESCE(proc.list, '[]'::jsonb)
    )),
    NOW()
FROM active_companies c
LEFT JOIN fin_agg f ON c.regcode = f.company_regcode
LEFT JOIN tax_agg t ON c.regcode = t.company_regcode
LEFT JOIN risk_agg r ON c.regcode = r.company_regcode
LEFT JOIN person_agg p ON c.regcode = p.company_regcode
LEFT JOIN proc_agg proc ON c.regcode = proc.company_regcode
LEFT JOIN rating_agg rat ON c.regcode = rat.company_regcode

ON CONFLICT (company_regcode) 
DO UPDATE SET profile_data = EXCLUDED.profile_data, updated_at = NOW();
