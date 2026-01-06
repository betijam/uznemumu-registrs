from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def debug_salary():
    with engine.connect() as conn:
        # Test the calculation for one city
        print("=== Testing Jaunjelgava salary calculation ===\n")
        
        result = conn.execute(text("""
            SELECT 
                c.regcode,
                c.name,
                t.social_tax_vsaoi,
                t.avg_employees,
                -- Individual company salary
                (t.social_tax_vsaoi / 0.3409) / t.avg_employees / 12 as company_avg_salary
            FROM companies c
            JOIN address_dimension a ON c.addressid = a.address_id
            LEFT JOIN (
                SELECT DISTINCT ON (company_regcode)
                    company_regcode, social_tax_vsaoi, avg_employees, year
                FROM tax_payments
                WHERE year >= 2020
                ORDER BY company_regcode, year DESC
            ) t ON c.regcode = t.company_regcode
            WHERE a.city_name = 'Jaunjelgava'
              AND c.status = 'active'
              AND t.social_tax_vsaoi > 0
              AND t.avg_employees > 0
            ORDER BY company_avg_salary DESC NULLS LAST
            LIMIT 20
        """))
        
        rows = result.fetchall()
        for row in rows:
            print(f"{row.name[:40]:40} | VSAOI: €{row.social_tax_vsaoi:>10,.0f} | Emp: {row.avg_employees:>5} | Calc: €{row.company_avg_salary:>10,.0f}")
        
        # Check what the aggregate is
        print("\n=== Aggregate for Jaunjelgava ===")
        result2 = conn.execute(text("""
            SELECT 
                COUNT(DISTINCT c.regcode) as companies,
                AVG((t.social_tax_vsaoi / 0.3409) / t.avg_employees / 12) as avg_method1,
                SUM(t.social_tax_vsaoi) / NULLIF(SUM(t.avg_employees), 0) / 12 / 0.3409 as avg_method2
            FROM companies c
            JOIN address_dimension a ON c.addressid = a.address_id
            LEFT JOIN (
                SELECT DISTINCT ON (company_regcode)
                    company_regcode, social_tax_vsaoi, avg_employees, year
                FROM tax_payments
                WHERE year >= 2020
                ORDER BY company_regcode, year DESC
            ) t ON c.regcode = t.company_regcode
            WHERE a.city_name = 'Jaunjelgava'
              AND c.status = 'active'
              AND t.social_tax_vsaoi > 0
              AND t.avg_employees > 0
        """))
        
        agg = result2.fetchone()
        print(f"Companies: {agg.companies}")
        print(f"Method 1 (AVG of company avgs): €{agg.avg_method1:,.2f}")
        print(f"Method 2 (SUM/SUM weighted): €{agg.avg_method2:,.2f}")

if __name__ == "__main__":
    debug_salary()
