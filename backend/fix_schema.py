"""
Quick fix for benchmark schema - increase profit margin precision
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

def fix_schema():
    engine = create_engine(DATABASE_URL)
    
    print("🔧 Fixing profit margin column precision...")
    
    with engine.connect() as conn:
        # Step 1: Drop dependent views
        print("  📌 Dropping views...")
        conn.execute(text("DROP VIEW IF EXISTS v_industry_latest_stats CASCADE"))
        conn.execute(text("DROP VIEW IF EXISTS v_company_benchmark_data CASCADE"))
        
        # Step 2: Alter column precision
        print("  📌 Altering column type...")
        conn.execute(text("""
            ALTER TABLE industry_year_aggregates 
            ALTER COLUMN avg_profit_margin TYPE NUMERIC(10,2)
        """))
        
        # Step 3: Recreate views
        print("  📌 Recreating views...")
        
        # View 1: Latest industry stats
        conn.execute(text("""
            CREATE VIEW v_industry_latest_stats AS
            SELECT 
                industry_code,
                year,
                avg_revenue,
                avg_profit_margin,
                avg_employees,
                avg_salary,
                total_companies
            FROM industry_year_aggregates iya
            WHERE year = (
                SELECT MAX(year) 
                FROM industry_year_aggregates 
                WHERE industry_code = iya.industry_code
            )
        """))
        
        # View 2: Company benchmark data
        conn.execute(text("""
            CREATE VIEW v_company_benchmark_data AS
            SELECT 
                c.regcode,
                c.name,
                c.nace_code,
                fr.year,
                fr.turnover,
                fr.profit,
                fr.employees,
                cir.revenue_rank,
                cir.revenue_percentile,
                iya.avg_revenue,
                iya.avg_profit_margin
            FROM companies c
            LEFT JOIN financial_reports fr ON c.regcode = fr.company_regcode
            LEFT JOIN company_industry_rankings cir 
                ON c.regcode = cir.company_regcode 
                AND c.nace_code = cir.industry_code 
                AND fr.year = cir.year
            LEFT JOIN industry_year_aggregates iya 
                ON c.nace_code = iya.industry_code 
                AND fr.year = iya.year
            WHERE c.status = 'active'
        """))
        
        conn.commit()
    
    print("✅ Schema fixed! Profit margin can now handle larger values.")
    print("\n🎯 Now run the ETL again:")
    print("   python backend/etl/calculate_benchmark_data.py")

if __name__ == "__main__":
    fix_schema()
