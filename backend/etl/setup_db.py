import logging
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

def setup_db():
    """Create necessary extensions, functions, and indexes for performance"""
    logger.info("🔧 Starting database optimization setup...")
    
    with engine.connect() as conn:
        try:
            # 1. Extensions
            logger.info("  - Enabling extensions (pg_trgm, unaccent)...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent"))
            conn.commit()
        except Exception as e:
            logger.warning(f"  ⚠️ Extension setup failed (might need superuser): {e}")

        try:
            # 2. Immutable unaccent wrapper
            # This is required because 'unaccent' is not immutable by default in some PG versions
            # and indexes on expressions must use immutable functions.
            logger.info("  - Creating immutable unaccent wrapper...")
            conn.execute(text("""
                CREATE OR REPLACE FUNCTION public.immutable_unaccent(text)
                RETURNS text AS
                $func$
                SELECT public.unaccent('public.unaccent', $1)
                $func$ LANGUAGE sql IMMUTABLE;
            """))
            conn.commit()
        except Exception as e:
            logger.warning(f"  ⚠️ Function creation failed: {e}")

        try:
            # 3. Search Indexes
            logger.info("  - Creating search indexes (GIN Trigram)...")
            
            # Index for company names (using the immutable wrapper)
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_companies_name_trgm 
                ON companies USING gin (immutable_unaccent(lower(name)) gin_trgm_ops)
            """))
            
            # Index for person names
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_persons_name_trgm 
                ON persons USING gin (immutable_unaccent(lower(person_name)) gin_trgm_ops)
            """))
            
            # Alternative: Standard index for exact/prefix matches (MUCH faster than GIN for large datasets)
            logger.info("  - Creating prefix indexes (B-tree)...")
            
            # Using v2 to avoid conflicts with existing bad definitions
            conn.execute(text("DROP INDEX IF EXISTS idx_companies_name_prefix"))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_companies_name_prefix_v2
                ON companies (immutable_unaccent(lower(name)) text_pattern_ops)
            """))
            
            conn.execute(text("DROP INDEX IF EXISTS idx_persons_name_prefix"))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_persons_name_prefix_v2
                ON persons (immutable_unaccent(lower(person_name)) text_pattern_ops)
            """))
            
            conn.commit()
        except Exception as e:
            logger.error(f"  ❌ Search index creation failed: {e}")

        try:
            # 4. Region Optimization
            logger.info("  - Creating region/finance indexes...")
            
            # For fast filtering by region and status
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_companies_atvk_status 
                ON companies (atvk, status)
            """))
            
            # For fast top-companies lookup in regions
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_fin_reports_regcode_year_turnover
                ON financial_reports (company_regcode, year, turnover)
            """))
            
            conn.commit()
            logger.info("✅ Database setup complete!")
        except Exception as e:
            logger.error(f"  ❌ Region index creation failed: {e}")

if __name__ == "__main__":
    setup_db()
