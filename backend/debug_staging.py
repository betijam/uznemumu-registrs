import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/ur_db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

print("=== Checking what's in stage.aw_dziv ===")
with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM stage.aw_dziv LIMIT 5"))
    for row in result:
        print(f"Kods: {row.objekta_kods}, Tips: {row.objekta_tips}, Adrese: {row.adrese}")

print("\n=== Checking column names ===")
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'stage' AND table_name = 'aw_dziv'
        ORDER BY ordinal_position
    """))
    columns = [row.column_name for row in result]
    print("Columns:", columns)

print("\n=== Re-checking the CSV ===")
df = pd.read_csv("temp_addresses/aw_dziv.csv", sep='\t', encoding='utf-8', dtype=str, low_memory=False, nrows=5)
print(f"CSV has {len(df.columns)} columns")
print("CSV columns:", list(df.columns))
print("\nFirst row:")
print(df.iloc[0].to_dict())
