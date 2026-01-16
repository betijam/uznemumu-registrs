
import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def check_missing_data():
    query = """
    WITH sample_nace AS (
        SELECT UNNEST(ARRAY['01', '02', '10', '13']) as code
    )
    SELECT 
        sn.code,
        f.year as finance_year,
        t.year as tax_year,
        COUNT(DISTINCT f.company_regcode) as finance_companies,
        COUNT(DISTINCT t.company_regcode) as tax_companies,
        SUM(t.avg_employees) as total_tax_employees,
        SUM(t.social_tax_vsaoi) as total_vsaoi
    FROM sample_nace sn
    JOIN companies c ON LEFT(c.nace_code, 2) = sn.code
    LEFT JOIN financial_reports f ON f.company_regcode = c.regcode
    LEFT JOIN tax_payments t ON t.company_regcode = c.regcode AND t.year = f.year
    WHERE f.year >= 2023
    GROUP BY sn.code, f.year, t.year
    ORDER BY sn.code, f.year;
    """
    
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)
        print(df.to_string())

if __name__ == "__main__":
    check_missing_data()
