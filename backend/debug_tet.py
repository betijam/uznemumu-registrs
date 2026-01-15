
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL is not set")
    exit(1)

engine = create_engine(DATABASE_URL)

def debug_tet():
    with engine.connect() as conn:
        print("\n--- Checking 'Tet' Data ---")
        # Find Tet by regcode or broad name search
        rows = conn.execute(text("""
            SELECT regcode, name, name_in_quotes, status, latest_turnover, type 
            FROM companies 
            WHERE name ILIKE '%Tet%' 
            ORDER BY latest_turnover DESC NULLS LAST
            LIMIT 10
        """)).fetchall()
        
        for r in rows:
            print(f"Regcode: {r.regcode}")
            print(f"Name: {r.name}")
            print(f"Quotes: {r.name_in_quotes}")
            print(f"Status: {r.status}")
            print(f"Turnover: {r.latest_turnover}")
            print("-" * 30)

        print("\n--- Testing Search Logic for query 'Tet' ---")
        # Replicating dashboard.py logic exactly
        q_raw = "Tet"
        params = {"q_raw": q_raw, "word0": "%Tet%"}
        
        sql = """
            SELECT name, name_in_quotes, latest_turnover, 
                CASE WHEN status = 'active' THEN 0 ELSE 1 END as rank_status,
                CASE 
                    WHEN immutable_unaccent(lower(name_in_quotes)) = immutable_unaccent(lower(:q_raw)) THEN 0 
                    WHEN immutable_unaccent(lower(name_in_quotes)) LIKE immutable_unaccent(lower(:q_raw)) || '%' THEN 1
                    ELSE 2 
                END as rank_name
            FROM companies 
            WHERE immutable_unaccent(lower(name)) LIKE immutable_unaccent(lower(:word0))
            ORDER BY 
                rank_status,
                rank_name,
                latest_turnover DESC NULLS LAST
            LIMIT 7
        """
        results = conn.execute(text(sql), params).fetchall()
        print(f"Found {len(results)} results for 'Tet':")
        for res in results:
             print(f"{res.name} | RankN: {res.rank_name} | Turnover: {res.latest_turnover}")

if __name__ == "__main__":
    debug_tet()
