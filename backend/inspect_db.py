from sqlalchemy import create_engine, text
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
import pandas as pd

engine = create_engine(DATABASE_URL)

def check_db():
    print("=== Checking Database Schema & Data ===\n")
    
    with engine.connect() as conn:
        # 1. Check financial_reports columns
        print("1. 'financial_reports' Columns:")
        result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'financial_reports'"))
        for row in result:
            print(f"   - {row[0]} ({row[1]})")
            
        print("\n2. Duplicate Cities in location_statistics:")
        result = conn.execute(text("""
            SELECT location_name, count(*) 
            FROM location_statistics 
            WHERE location_type='city' 
            GROUP BY location_name 
            HAVING count(*) > 1
        """))
        dupes = result.fetchall()
        if dupes:
            for d in dupes:
                print(f"   - {d[0]}: {d[1]} times")
        else:
            print("   None found")

        print("\n3. Inspecting 'Rīga' entries in address_dimension:")
        result = conn.execute(text("SELECT DISTINCT city_name, city_code FROM address_dimension WHERE city_name LIKE 'Rīga%'"))
        for row in result:
            print(f"   - {row[0]} (Code: {row[1]})")

if __name__ == "__main__":
    check_db()
