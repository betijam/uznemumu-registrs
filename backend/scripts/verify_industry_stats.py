
import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL is not set")
    exit(1)

engine = create_engine(DATABASE_URL)

def verify_stats():
    # Find ALL NACE codes where salary is missing or zero
    query = """
    SELECT nace_code, nace_name, data_year, avg_gross_salary 
    FROM industry_stats_materialized 
    WHERE avg_gross_salary IS NULL OR avg_gross_salary = 0
    ORDER BY nace_code;
    """
    
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)
        if df.empty:
            print("✅ No NACE codes found with missing salaries!")
        else:
            print(f"⚠️ Found {len(df)} NACE codes with missing salaries:")
            print(df.to_string())

if __name__ == "__main__":
    verify_stats()
