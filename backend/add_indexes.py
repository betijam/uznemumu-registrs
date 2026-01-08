from app.core.database import engine
from sqlalchemy import text
import time

def add_indexes():
    print("Adding indexes... This might take a while.")
    start = time.time()
    
    # 1. Extensions
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent;"))
            conn.commit()
    except Exception as e:
        print(f"Error creating extensions: {e}")

    # 2. Immutable Unaccent Wrapper
    # We need this because standard unaccent is STABLE, not IMMUTABLE, so it can't be used in functional indexes without a wrapper or hack.
    print("Creating immutable_unaccent function...")
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE OR REPLACE FUNCTION immutable_unaccent(text)
                  RETURNS text AS
                $func$
                  SELECT public.unaccent('public.unaccent', $1)
                $func$  LANGUAGE sql IMMUTABLE;
            """))
            conn.commit()
    except Exception as e:
        print(f"Error creating immutable_unaccent (attempting fallback): {e}")

    # 3. Indexes (Separate transactions to prevent aborts)

    # Regcode
    print("Creating index on regcode...")
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_companies_regcode ON companies (regcode);"))
            conn.commit()
    except Exception as e:
        print(f"Error idx_companies_regcode: {e}")

    # Name (Trigram)
    print("Creating trigram index on name...")
    try:
        with engine.connect() as conn:
            # Try using the wrapper first
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_companies_name_trgm 
                ON companies 
                USING gin (immutable_unaccent(lower(name)) gin_trgm_ops);
            """))
            conn.commit()
            print("Success: Created index using immutable_unaccent")
    except Exception as e:
        print(f"Error with immutable_unaccent index: {e}")
        # Fallback: Just lower(name) if wrapper failed
        try:
            with engine.connect() as conn:
                print("Fallback: Creating index on lower(name)...")
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_companies_name_lower_trgm 
                    ON companies 
                    USING gin (lower(name) gin_trgm_ops);
                """))
                conn.commit()
        except Exception as e2:
             print(f"Error with fallback index: {e2}")

    # Status
    print("Creating index on status...")
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_companies_status ON companies (status);"))
            conn.commit()
    except Exception as e:
        print(f"Error idx_companies_status: {e}")

    # Optimize List Page (NACE, Turnover, etc)
    print("Creating indexes for list page filtering...")
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_companies_nace ON companies (nace_section);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_companies_type ON companies (type);"))
            
            # Address index for Region filter
            print("Creating trigram index on address...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_companies_address_trgm 
                ON companies 
                USING gin (upper(address) gin_trgm_ops);
            """))
            
            conn.commit()
    except Exception as e:
        print(f"Error extra indexes: {e}")

    print(f"Indexes added in {time.time() - start:.2f}s")

if __name__ == "__main__":
    add_indexes()
