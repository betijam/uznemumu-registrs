import time
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

def debug_search():
    print("--- Debugging Search Performance ---")
    
    with engine.connect() as conn:
        # 1. Check indexes again
        print("\nChecking ALl indexes for 'companies':")
        indexes = conn.execute(text("""
            SELECT indexname, indexdef FROM pg_indexes 
            WHERE tablename = 'companies'
        """)).fetchall()
        for row in indexes:
            print(f"  - {row.indexname}: {row.indexdef}")
            
        # 2. Check "ANIMAS" data
        print("\nChecking data for 'ANIMAS':")
        res = conn.execute(text("""
            SELECT name, immutable_unaccent(lower(name)) as processed_name 
            FROM companies 
            WHERE name ILIKE '%ANIMAS%'
            LIMIT 5
        """)).fetchall()
        for row in res:
            print(f"  - Actual: '{row.name}' | Processed: '{row.processed_name}'")

        # 3. Test Prefix Match speed separately
        print("\nTesting Prefix Match speed (Rank 0 candidate):")
        start = time.time()
        res = conn.execute(text("""
            EXPLAIN ANALYZE
            SELECT name FROM companies 
            WHERE immutable_unaccent(lower(name)) LIKE 'animas%'
            LIMIT 5
        """)).fetchall()
        print(f"Prefix Match Duration: {time.time() - start:.4f}s")
        for row in res:
            print(f"  {row[0]}")

        # 4. Test Fuzzy Match speed separately
        print("\nTesting Fuzzy Match speed (Rank 1 candidate):")
        start = time.time()
        res = conn.execute(text("""
            EXPLAIN ANALYZE
            SELECT name FROM companies 
            WHERE immutable_unaccent(lower(name)) % 'animas'
            LIMIT 5
        """)).fetchall()
        print(f"Fuzzy Match Duration: {time.time() - start:.4f}s")
        # for row in res:
        #    print(f"  {row[0]}")

if __name__ == "__main__":
    debug_search()
