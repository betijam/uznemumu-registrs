"""
Script to refresh the Dashboard Cache.
This should be run periodically (e.g., every night at 04:00).
It calculates heavy statistics (TOPs, Gazeles) and stores them in 'dashboard_cache'.
"""

import os
import json
import logging
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.error("DATABASE_URL is not set")
    exit(1)

engine = create_engine(DATABASE_URL)

def calculate_dashboard_stats():
    conn = engine.connect()
    
    try:
        logger.info("Starting Dashboard Refresh...")

        # 1. Determine LATEST FULL YEAR for financials
        # We look for the year that has substantial data (e.g. > 1000 reports)
        max_year_row = conn.execute(text("SELECT MAX(year) FROM financial_reports")).fetchone()
        latest_year = max_year_row[0] if max_year_row and max_year_row[0] else 2023
        
        # Ensure we have enough data for this year, otherwise fall back
        count_row = conn.execute(text("SELECT COUNT(*) FROM financial_reports WHERE year = :year"), {"year": latest_year}).fetchone()
        if count_row[0] < 1000:
            latest_year -= 1

        logger.info(f"Using Financial Year: {latest_year}")


        # 2. TOP TURNOVER (Apgrozījums)
        top_turnover = conn.execute(text("""
            SELECT 
                c.name, 
                c.name_in_quotes,
                c."type" as company_type,
                c.type_text,
                c.regcode, 
                f.turnover as value,
                c.nace_text as industry
            FROM financial_reports f
            JOIN companies c ON c.regcode = f.company_regcode
            WHERE f.year = :year 
              AND f.turnover IS NOT NULL
              AND f.turnover <> 'NaN'
            ORDER BY f.turnover DESC
            LIMIT 5
        """), {"year": latest_year}).fetchall()

        # 3. TOP PROFIT (Peļņa)
        top_profit = conn.execute(text("""
            SELECT 
                c.name, 
                c.name_in_quotes,
                c."type" as company_type,
                c.type_text,
                c.regcode, 
                f.profit as value,
                c.nace_text as industry
            FROM financial_reports f
            JOIN companies c ON c.regcode = f.company_regcode
            WHERE f.year = :year 
              AND f.profit IS NOT NULL
              AND f.profit <> 'NaN'
            ORDER BY f.profit DESC
            LIMIT 5
        """), {"year": latest_year}).fetchall()

        # 4. TOP SALARIES (Avg Salary > 10 employees)
        # Avg salary = (Total Social Tax / 0.2359) / (Total Employees * 12) approx?
        # Or if we have avg_gross_salary in materialized view?
        # Let's use tax_payments table: social_tax_vsaoi / avg_employees / 12 / 0.2359 (employer part) -> Gross?
        # Actually VSAOI includes employer part (23.59%) and employee part (10.5%).
        # Gross Wage = (VSAOI total) / (0.3409 rate) / employees / 12 months roughly.
        # Let's calculate: Total VSAOI / Avg Employees / 12 months / 0.3409
        
        # Only companies with > 10 employees to avoid 1-person holdings
        top_salaries = conn.execute(text("""
            WITH salary_calc AS (
                SELECT 
                    company_regcode,
                    (social_tax_vsaoi / NULLIF(avg_employees, 0) / 12 / 0.3409) as estimated_gross
                FROM tax_payments
                WHERE year = :year
                  AND avg_employees >= 10
                  AND social_tax_vsaoi > 0
            )
            SELECT 
                c.name, 
                c.name_in_quotes,
                c."type" as company_type,
                c.type_text,
                c.regcode, 
                s.estimated_gross as value,
                c.nace_text as industry
            FROM salary_calc s
            JOIN companies c ON c.regcode = s.company_regcode
            ORDER BY s.estimated_gross DESC
            LIMIT 5
        """), {"year": latest_year}).fetchall()

        # 5. GAZELES (Growth > 30%, Turnover > 1M)
        # Prev year turnover vs Current year turnover
        gazeles = conn.execute(text("""
            WITH cur AS (
                SELECT company_regcode, turnover 
                FROM financial_reports 
                WHERE year = :year 
                  AND turnover > 1000000 
                  AND turnover <> 'NaN'
            ),
            prev AS (
                SELECT company_regcode, turnover 
                FROM financial_reports 
                WHERE year = :prev_year 
                  AND turnover > 100000 
                  AND turnover <> 'NaN'
            )
            SELECT 
                c.name,
                c.name_in_quotes,
                c."type" as company_type,
                c.type_text,
                c.regcode,
                cur.turnover as current_turnover,
                ROUND(((cur.turnover - prev.turnover) / prev.turnover) * 100, 1) as growth_pct,
                c.nace_text as industry
            FROM cur
            JOIN prev ON cur.company_regcode = prev.company_regcode
            JOIN companies c ON c.regcode = cur.company_regcode
            WHERE ((cur.turnover - prev.turnover) / prev.turnover) > 0.30
            ORDER BY growth_pct DESC
            LIMIT 5
        """), {"year": latest_year, "prev_year": latest_year - 1}).fetchall()


        # Helper to clean float (handle NaN)
        def clean_float(val):
            import math
            if val is None:
                return 0
            try:
                f_val = float(val)
                if math.isnan(f_val) or math.isinf(f_val):
                    return 0
                return f_val
            except (ValueError, TypeError):
                return 0

        # Helper to dict
        def to_dict_list(rows, value_key="value"):
            return [
                {
                    "name": row.name, 
                    "name_in_quotes": row.name_in_quotes if hasattr(row, 'name_in_quotes') else None,
                    "type": row.company_type if hasattr(row, 'company_type') else None,
                    "type_text": row.type_text if hasattr(row, 'type_text') else None,
                    "regcode": row.regcode, 
                    value_key: clean_float(row.value),
                    "industry": row.industry
                } 
                for row in rows
            ]
        
        def gazeles_list(rows):
             return [
                {
                    "name": row.name, 
                    "name_in_quotes": row.name_in_quotes if hasattr(row, 'name_in_quotes') else None,
                    "type": row.company_type if hasattr(row, 'company_type') else None,
                    "type_text": row.type_text if hasattr(row, 'type_text') else None,
                    "regcode": row.regcode, 
                    "turnover": clean_float(row.current_turnover),
                    "growth": clean_float(row.growth_pct),
                    "industry": row.industry
                } 
                for row in rows
            ]

        # Construct payload
        dashboard_data = {
            "meta": {
                "year": latest_year, 
                "source": "Lursoft/VID"
            },
            "tops": {
                "turnover": to_dict_list(top_turnover),
                "profit": to_dict_list(top_profit),
                "salaries": to_dict_list(top_salaries, "value") 
            },
            "gazeles": gazeles_list(gazeles)
        }

        # Save to DB Cache
        conn.execute(text("""
            INSERT INTO dashboard_cache (key, data, updated_at)
            VALUES ('main_dashboard', :data, NOW())
            ON CONFLICT (key) DO UPDATE 
            SET data = :data, updated_at = NOW()
        """), {"data": json.dumps(dashboard_data)})
        
        conn.commit()
        logger.info("Dashboard Refresh Completed Successfully!")

    except Exception as e:
        logger.error(f"Dashboard Refresh Failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    calculate_dashboard_stats()
