
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("Error: DATABASE_URL not found!")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

def safe_float(val):
    if val is None: return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0

def debug_industry_overview():
    print("--- DEBUGGING INDUSTRY OVERVIEW CARD DATA ---")
    
    with engine.connect() as conn:
        print("\n1. Checking 'industry_stats_materialized' content summary:")
        summary = conn.execute(text("""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(total_turnover) as rows_with_turnover,
                MIN(data_year) as min_year,
                MAX(data_year) as max_year
            FROM industry_stats_materialized
        """)).fetchone()
        print(f"   Total Rows: {summary.total_rows}")
        print(f"   Rows with Turnover: {summary.rows_with_turnover}")
        print(f"   Year Range: {summary.min_year} - {summary.max_year}")
        
        if summary.total_rows == 0:
            print("❌ TABLE IS EMPTY! API will return None.")
            return

        print("\n2. Executing MACRO query (exactly as in industries.py):")
        # Copy-pasted query from industries.py
        macro_query = text("""
            SELECT 
                SUM(total_turnover) as total_turnover,
                SUM(total_profit) as total_profit,
                SUM(employee_count) as total_employees,
                AVG(avg_gross_salary) as avg_salary,
                MAX(data_year) as data_year
            FROM industry_stats_materialized
            WHERE nace_level = 1 
            AND nace_code != '00'
            AND nace_name NOT ILIKE '%Cita nozare%'
        """)
        
        macro = conn.execute(macro_query).fetchone()
        
        print("\n--- MACRO QUERY RESULT (Raw DB) ---")
        print(f"   total_turnover: {macro.total_turnover} (Type: {type(macro.total_turnover)})")
        print(f"   total_profit: {macro.total_profit}")
        print(f"   total_employees: {macro.total_employees}")
        print(f"   avg_salary: {macro.avg_salary}")
        print(f"   data_year: {macro.data_year}")
        
        if macro.total_turnover is None:
            print("❌ MACRO TURNOVER IS NULL! This is why cards are empty.")
            
            print("\n3. Investigating WHY turnover is NULL. Checking individual rows:")
            # Let's see if any row has NaN or something weird causing SUM to fail (though we fixed NaN)
            rows = conn.execute(text("""
                SELECT nace_code, total_turnover, data_year 
                FROM industry_stats_materialized 
                WHERE nace_level = 1 AND (total_turnover IS NULL)
                LIMIT 5
            """)).fetchall()
            if rows:
                print("   Found rows with NULL turnover:")
                for r in rows:
                    print(f"   - NACE {r.nace_code}: {r.total_turnover}")
            else:
                print("   No rows strictly NULL found. Checking for valid values...")
                valid_rows = conn.execute(text("""
                    SELECT nace_code, total_turnover 
                    FROM industry_stats_materialized 
                    WHERE nace_level = 1 LIMIT 5
                """)).fetchall()
                for r in valid_rows:
                    print(f"   - {r.nace_code}: {r.total_turnover}")

        print("\n4. Simulating Response Object Construction:")
        processed_turnover = safe_float(macro.total_turnover if macro else 0)
        print(f"   safe_float(turnover): {processed_turnover}")
        
        if processed_turnover > 0:
            print("✅ Backend seems correct. If you see '-' in frontend, check frontend code.")
        else:
            print("❌ Backend result is 0 or None.")

if __name__ == "__main__":
    debug_industry_overview()
