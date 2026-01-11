import os
import sqlalchemy
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
engine = sqlalchemy.create_engine(DATABASE_URL)

def check_columns():
    with engine.connect() as conn:
        print("--- Checking financial_reports columns ---")
        sql = """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'financial_reports'
            ORDER BY column_name;
        """
        result = conn.execute(text(sql)).fetchall()
        for row in result:
            print(f"{row.column_name}: {row.data_type}")

if __name__ == "__main__":
    check_columns()
