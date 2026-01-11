import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

def check_region_indexes():
    print("--- Checking Region Table Indexes ---")
    tables = ['territories', 'territory_year_aggregates', 'territory_industry_year_aggregates']
    
    with engine.connect() as conn:
        for table in tables:
            print(f"\nIndexes for table '{table}':")
            sql = f"""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename = '{table}'
            """
            result = conn.execute(text(sql)).fetchall()
            if not result:
                print("  ❌ No indexes found!")
            for row in result:
                print(f"  - {row.indexname}: {row.indexdef}")

if __name__ == "__main__":
    check_region_indexes()
