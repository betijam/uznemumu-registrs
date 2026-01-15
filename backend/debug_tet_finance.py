
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL is not set")
    exit(1)

engine = create_engine(DATABASE_URL)

def debug_tet_finance():
    with engine.connect() as conn:
        print("\n--- Checking 'Tet' Financial Data ---")
        # Regcode for Tet
        regcode = 40003052786 
        
        rows = conn.execute(text("""
            SELECT year, turnover, profit, source_type
            FROM financial_reports 
            WHERE company_regcode = :r
            ORDER BY year DESC, source_type
        """), {"r": regcode}).fetchall()
        
        for r in rows:
            print(f"Year: {r.year} | Type: {r.source_type} | Turnover: {r.turnover} | Profit: {r.profit}")

if __name__ == "__main__":
    debug_tet_finance()
