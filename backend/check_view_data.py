from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def check_view_data():
    with engine.connect() as conn:
        print("=== Checking actual materialized view data ===\n")
        
        result = conn.execute(text("""
            SELECT 
                location_name,
                company_count,
                total_employees,
                avg_salary,
                avg_revenue_per_company
            FROM location_statistics
            WHERE location_name IN ('Jaunjelgava', 'Rīga', 'Mārupe')
            ORDER BY location_name
        """))
        
        for row in result:
            print(f"{row.location_name:20} | Companies: {row.company_count:>5} | Avg Salary: €{row.avg_salary:>12,.2f}")

if __name__ == "__main__":
    check_view_data()
