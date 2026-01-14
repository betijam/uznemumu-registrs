
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

def debug_jelgava():
    print("--- DEBUGGING JELGAVA DATA ---")
    
    with engine.connect() as conn:
        print("\n1. Testing ACTUAL 'get_location_top_companies' Query for 'Jelgava':")
        name = "Jelgava"
        stable_year = 2024
        
        # EXACT query from locations.py (V7.2)
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
            LIMIT 20
        """)
        
        rows = conn.execute(query, {"name": name, "stable_year": stable_year}).fetchall()
        print(f"   Query returned {len(rows)} rows.")
        for i, r in enumerate(rows):
            print(f"   #{i+1}: {r.name} ({r.regcode}) - Turnover: {r.turnover} (Year: {r.data_year})")

        print("\n2. Checking raw counts for Jelgava in address_dimension:")
        count = conn.execute(text("SELECT count(*) FROM address_dimension WHERE city_name = 'Jelgava'")).scalar()
        print(f"   Total addresses with city_name='Jelgava': {count}")
        
        print("\n3. Checking specific Jelgava companies (if any missing from top list):")
        # Let's find some active companies in Jelgava regardless of financial reports
        sample_query = text("""
            SELECT c.name, c.regcode, c.status
            FROM companies c 
            JOIN address_dimension a ON c.addressid = a.address_id
            WHERE a.city_name = 'Jelgava'
              AND (c.status IS NULL OR c.status = '' OR c.status IN ('active', 'A', 'AKTĪVS', 'reģistrēts'))
            LIMIT 5
        """)
        samples = conn.execute(sample_query).fetchall()
        for s in samples:
            print(f"   Found active company: {s.name} ({s.regcode}) Status: {s.status}")

if __name__ == "__main__":
    debug_jelgava()
