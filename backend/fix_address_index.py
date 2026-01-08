from app.core.database import engine
from sqlalchemy import text
import time

def fix_address_index():
    print("Fixing address index for ILIKE support...")
    start = time.time()
    with engine.connect() as conn:
        try:
            print("Dropping old index...")
            conn.execute(text("DROP INDEX IF EXISTS idx_companies_address_trgm;"))
            conn.commit()
            
            print("Creating standard GIN index on address (supports ILIKE)...")
            conn.execute(text("""
                CREATE INDEX idx_companies_address_trgm 
                ON companies 
                USING gin (address gin_trgm_ops);
            """))
            conn.commit()
            print("Success!")
        except Exception as e:
            print(f"Error: {e}")

    print(f"Fixed in {time.time() - start:.2f}s")

if __name__ == "__main__":
    fix_address_index()
