
import os
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL is not set")
    exit(1)

engine = create_engine(DATABASE_URL)

def check_schema():
    insp = inspect(engine)
    columns = insp.get_columns('financial_reports')
    print("Columns in financial_reports:")
    for col in columns:
        print(f" - {col['name']} ({col['type']})")

if __name__ == "__main__":
    check_schema()
