from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def update_schema():
    print("Applying schema update...")
    with open('db/location_stats.sql', 'r', encoding='utf-8') as f:
        sql = f.read()
        
    with engine.connect() as conn:
        conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS public.location_statistics CASCADE;"))
        conn.execute(text(sql))
        conn.commit()
    print("✅ Schema updated successfully and view refreshed.")

if __name__ == "__main__":
    update_schema()
