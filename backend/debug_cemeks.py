from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

# Use the direct DATABASE_URL from environment or the user provided one
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not found, cannot debug")
    exit(1)

engine = create_engine(DATABASE_URL)

REGCODE = 40003806464 # Cemeks SIA

def check_risks():
    print(f"\n--- Checking Risks for {REGCODE} ---")
    with engine.connect() as conn:
        # Check total risks
        all_risks = conn.execute(text("SELECT * FROM risks WHERE company_regcode = :r"), {"r": REGCODE}).fetchall()
        print(f"Total risks found in DB: {len(all_risks)}")
        
        # Check active risks
        active_risks = conn.execute(text("SELECT * FROM risks WHERE company_regcode = :r AND active = TRUE"), {"r": REGCODE}).fetchall()
        print(f"Active risks found in DB: {len(active_risks)}")
        
        for r in all_risks:
            print(f"  - Type: {r.risk_type}, Active: {r.active}, Score: {r.risk_score}, Start: {r.start_date}")

def check_competitors_logic():
    print(f"\n--- Checking Competitors Logic for {REGCODE} ---")
    with engine.connect() as conn:
        company = conn.execute(
            text("SELECT nace_code, nace_text, employee_count FROM companies WHERE regcode = :r"),
            {"r": REGCODE}
        ).fetchone()
        
        if not company:
            print("Company not found in companies table")
            return
            
        print(f"Company Found: NACE={company.nace_code}, Emp={company.employee_count}")
        
        if not company.nace_code or len(company.nace_code) < 3:
            print("NACE code too short or missing, returning []")
            return
        
        nace_prefix = company.nace_code[:3]
        employee_count = company.employee_count or 0
        min_emp = int(employee_count * 0.7) if employee_count > 0 else 0
        max_emp = int(employee_count * 1.3) if employee_count > 0 else 999999
        
        print(f"Params: prefix={nace_prefix}%, min={min_emp}, max={max_emp}")
        
        try:
            competitors = conn.execute(text("""
                SELECT 
                    c.regcode,
                    c.name,
                    c.employee_count,
                    c.nace_text,
                    fr.turnover,
                    fr.profit,
                    fr.year
                FROM companies c
                LEFT JOIN financial_reports fr ON fr.company_regcode = c.regcode
                    AND fr.year = (SELECT MAX(year) FROM financial_reports WHERE company_regcode = c.regcode)
                WHERE c.nace_code LIKE :nace_prefix
                    AND c.regcode != :regcode
                    AND (:min_emp = 0 OR c.employee_count BETWEEN :min_emp AND :max_emp)
                ORDER BY fr.turnover DESC NULLS LAST, c.employee_count DESC
                LIMIT 5
            """), {
                "nace_prefix": f"{nace_prefix}%",
                "regcode": REGCODE,
                "min_emp": min_emp,
                "max_emp": max_emp
            }).fetchall()
            print(f"Competitors query success. Found: {len(competitors)}")
            for c in competitors:
                print(f"  - {c.name} ({c.regcode}) T={c.turnover}")
        except Exception as e:
            print(f"Competitors query FAILED: {e}")

if __name__ == "__main__":
    check_risks()
    check_competitors_logic()
