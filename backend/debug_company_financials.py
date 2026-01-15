
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

def debug_company(regcode):
    print(f"--- DEBUGGING COMPANY {regcode} ---")
    
    with engine.connect() as conn:
        # Get Company Info
        company = conn.execute(text("SELECT * FROM companies WHERE regcode = :regcode"), {"regcode": regcode}).fetchone()
        if not company:
            print("❌ Company not found!")
            return
        
        print(f"Name: {company.name}")
        print(f"Status: {company.status}")
        
        # Get Financials
        financials = conn.execute(text("""
            SELECT year, turnover, profit, employees
            FROM financial_reports
            WHERE company_regcode = :regcode
            ORDER BY year DESC
        """), {"regcode": regcode}).fetchall()
        
        print("\nFinancial Reports:")
        if not financials:
            print("❌ No financial reports found!")
        else:
            for r in financials:
                print(f"   Year: {r.year} | Turnover: {r.turnover} | Profit: {r.profit} | Employees: {r.employees}")

if __name__ == "__main__":
    debug_company("40003052786")
