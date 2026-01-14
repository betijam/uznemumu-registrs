
import os
from sqlalchemy import text, create_engine
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def force_recreate_views():
    sql_file = os.path.join(os.path.dirname(__file__), "db", "location_stats.sql")
    if not os.path.exists(sql_file):
        print(f"Error: {sql_file} not found")
        return

    with open(sql_file, "r", encoding="utf-8") as f:
        sql = f.read()

    with engine.connect() as conn:
        print("Dropping old view...")
        conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS public.location_statistics CASCADE;"))
        conn.commit()
        
        print("Creating new views from location_stats.sql...")
        # Split by semicolon to execute one by one if needed, but usually text() handles blocks
        conn.execute(text(sql))
        conn.commit()
        print("✅ Success! Views recreated with 2024 priority.")

if __name__ == "__main__":
    force_recreate_views()
