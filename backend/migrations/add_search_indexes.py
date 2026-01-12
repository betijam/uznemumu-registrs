"""
Migration: Add pg_trgm extension and GIN indexes for fast search
This enables trigram-based similarity search with proper ranking.
"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in environment")

engine = create_engine(DATABASE_URL)

def run_migration():
    """Add pg_trgm extension and create GIN indexes for search optimization"""
    
    with engine.connect() as conn:
        logger.info("🔧 Adding pg_trgm extension...")
        
        # 1. Enable extensions
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent;"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
        
        # 2. Create immutable_unaccent function (if not exists)
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION immutable_unaccent(text)
              RETURNS text AS
            $func$
            SELECT public.unaccent('public.unaccent', $1)
            $func$ LANGUAGE sql IMMUTABLE;
        """))
        
        logger.info("📊 Creating GIN indexes for trigram search...")
        
        # 3. Create GIN index on company name (normalized)
        # This makes LIKE %word% and SIMILARITY() queries blazing fast
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_companies_name_trgm 
            ON companies 
            USING gin (immutable_unaccent(lower(name)) gin_trgm_ops);
        """))
        
        # 4. Create GIN index on regcode (for numeric searches)
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_companies_regcode_trgm 
            ON companies 
            USING gin (CAST(regcode AS TEXT) gin_trgm_ops);
        """))
        
        # 5. Optional: Index on name_in_quotes for better ranking
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_companies_name_quotes_trgm 
            ON companies 
            USING gin (immutable_unaccent(lower(name_in_quotes)) gin_trgm_ops);
        """))
        
        conn.commit()
        logger.info("✅ Search optimization indexes created successfully!")
        
        # Verify indexes
        result = conn.execute(text("""
            SELECT indexname FROM pg_indexes 
            WHERE tablename = 'companies' 
            AND indexname LIKE '%trgm%';
        """))
        
        indexes = [row[0] for row in result]
        logger.info(f"📋 Trigram indexes on companies table: {indexes}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_migration()
