#!/usr/bin/env python3
"""
NACE Columns Migration Script

Automatically adds NACE-related columns to companies table if they don't exist.
Safe to run multiple times (uses IF NOT EXISTS).
"""

import logging
from sqlalchemy import text
from etl.loader import engine

logger = logging.getLogger(__name__)

def migrate_nace_columns():
    """Add NACE columns to companies table if they don't exist"""
    
    logger.info("=" * 60)
    logger.info("NACE DATABASE MIGRATION")
    logger.info("=" * 60)
    
    migration_sql = """
    -- Add NACE columns to companies table
    ALTER TABLE companies ADD COLUMN IF NOT EXISTS nace_code VARCHAR(10);
    ALTER TABLE companies ADD COLUMN IF NOT EXISTS nace_text VARCHAR(500);
    ALTER TABLE companies ADD COLUMN IF NOT EXISTS nace_section VARCHAR(5);
    ALTER TABLE companies ADD COLUMN IF NOT EXISTS nace_section_text VARCHAR(200);
    ALTER TABLE companies ADD COLUMN IF NOT EXISTS employee_count INTEGER DEFAULT 0;
    ALTER TABLE companies ADD COLUMN IF NOT EXISTS tax_data_year INTEGER;
    
    -- Create indexes for efficient filtering
    CREATE INDEX IF NOT EXISTS idx_companies_nace_code ON companies(nace_code);
    CREATE INDEX IF NOT EXISTS idx_companies_nace_section ON companies(nace_section);
    CREATE INDEX IF NOT EXISTS idx_companies_employee_count ON companies(employee_count);
    """
    
    try:
        with engine.connect() as conn:
            logger.info("Checking and creating NACE columns...")
            
            # Execute migration
            conn.execute(text(migration_sql))
            conn.commit()
            
            logger.info("✅ NACE columns migration completed successfully")
            
            # Verify columns exist
            verify_sql = """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'companies' 
              AND column_name IN ('nace_code', 'nace_text', 'nace_section', 
                                  'nace_section_text', 'employee_count', 'tax_data_year')
            ORDER BY column_name;
            """
            
            result = conn.execute(text(verify_sql))
            columns = result.fetchall()
            
            logger.info(f"Verified {len(columns)} NACE columns exist:")
            for col in columns:
                logger.info(f"  ✓ {col[0]} ({col[1]})")
            
            return True
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    success = migrate_nace_columns()
    exit(0 if success else 1)
