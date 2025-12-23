import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("--- Financial Reports by Year ---")
    rows = conn.execute(text("SELECT year, COUNT(*), COUNT(turnover), SUM(turnover) FROM financial_reports GROUP BY year ORDER BY year DESC")).fetchall()
    for r in rows:
        print(f"Year: {r[0]}, Count: {r[1]}, With Turnover: {r[2]}, Total Turnover: {r[3]}")
    
    print("\n--- Companies Status ---")
    rows = conn.execute(text("SELECT status, COUNT(*) FROM companies GROUP BY status")).fetchall()
    for r in rows:
        print(f"Status: {r[0]}, Count: {r[1]}")
