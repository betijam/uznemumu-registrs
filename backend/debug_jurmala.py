
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

def debug_jurmala():
    print("--- DEBUGGING JURMALA DATA ---")
    
    with engine.connect() as conn:
        # 1. Check specific company 'SIA "GRUODIS"' (should be in Jūrmala)
        regcode = '40103685632' 
        print(f"\n1. Inspecting SIA 'GRUODIS' ({regcode})...")
        
        company = conn.execute(text("SELECT name, addressid, regcode, atvk, status FROM companies WHERE regcode = :reg"), {"reg": regcode}).fetchone()
        
        if not company:
            print("❌ Company NOT FOUND in 'companies' table!")
        else:
            print(f"✅ Found: {company.name}, AddressID: {company.addressid}, Status: '{company.status}'")
            
            # 2. Check Address Dimension
            if company.addressid:
                addr = conn.execute(text("SELECT * FROM address_dimension WHERE address_id = :aid"), {"aid": company.addressid}).fetchone()
                if addr:
                    print(f"   Address Info: City='{addr.city_name}', Municipality='{addr.municipality_name}', Parish='{addr.parish_name}'")
                    
                    # Check for invisible chars
                    if addr.city_name:
                        print(f"   City Name repr: {repr(addr.city_name)}")
                        if addr.city_name == 'Jūrmala':
                             print("   ✅ City matches 'Jūrmala' exactly.")
                        else:
                             print("   ❌ City DOES NOT match 'Jūrmala' exactly!")
                else:
                    print("   ❌ Address Dimension entry NOT FOUND!")
            else:
                print("   ❌ No Address ID!")

            # 3. Check Financial Reports
            print(f"\n2. Financial Reports for {regcode}:")
            reports = conn.execute(text("SELECT year, turnover, profit, employees FROM financial_reports WHERE company_regcode = :reg ORDER BY year DESC"), {"reg": regcode}).fetchall()
            for r in reports:
                print(f"   Year: {r.year}, Turnover: {r.turnover}, Profit: {r.profit}")

        # 4. Run the ACTUAL Query from locations.py
        print("\n3. Testing ACTUAL 'get_location_top_companies' Query for 'Jūrmala':")
        name = "Jūrmala"
        stable_year = 2024
        
        query = text("""
            SELECT 
                c.regcode,
                c.name,
                fr.turnover,
                fr.year as data_year
            FROM companies c
            JOIN address_dimension a ON c.addressid = a.address_id
            LEFT JOIN LATERAL (
                SELECT turnover, profit, employees, year
                FROM financial_reports
                WHERE company_regcode = c.regcode
                  AND turnover > 0
                  AND turnover != 'NaN'::float
                  AND year >= 2023
                  AND year <= :stable_year
                ORDER BY (year = :stable_year) DESC, year DESC
                LIMIT 1
            ) fr ON true
            WHERE a.city_name = :name
              AND (c.status IS NULL OR c.status = '' OR c.status IN ('active', 'A', 'AKTĪVS', 'reģistrēts'))
            ORDER BY fr.turnover DESC NULLS LAST
            LIMIT 10
        """)
        
        rows = conn.execute(query, {"name": name, "stable_year": stable_year}).fetchall()
        print(f"   Query returned {len(rows)} rows.")
        for i, r in enumerate(rows):
            print(f"   #{i+1}: {r.name} ({r.regcode}) - Turnover: {r.turnover} (Year: {r.data_year})")

if __name__ == "__main__":
    debug_jurmala()
