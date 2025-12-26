"""
ETL Script: Populate Company ATVK Codes from Addresses (FAST VERSION)

This script uses a single SQL UPDATE to populate ATVK codes,
which is 100x faster than individual updates.
"""

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")


def populate_company_atvk_fast():
    """
    Populate companies.atvk using a single SQL UPDATE (much faster!)
    """
    engine = create_engine(DATABASE_URL)
    
    logger.info("=" * 60)
    logger.info("COMPANY ATVK POPULATION (FAST) STARTED")
    logger.info("=" * 60)
    start_time = datetime.now()
    
    with engine.connect() as conn:
        # Step 1: Get territories sorted by specificity
        logger.info("📥 Loading territories...")
        territories = conn.execute(text("""
            SELECT code, name, level, type
            FROM territories
            WHERE (valid_to IS NULL OR valid_to > NOW())
              AND level >= 2
            ORDER BY level DESC, LENGTH(name) DESC
        """)).fetchall()
        
        logger.info(f"✅ Loaded {len(territories)} territories")
        
        # Step 2: Build CASE WHEN SQL for matching
        # Most specific matches first (level 3 parishes/cities, then level 2 municipalities)
        logger.info("🔧 Building match query...")
        
        case_clauses = []
        for t in territories:
            name = t.name.replace("'", "''")  # Escape single quotes
            code = t.code
            
            # Add primary match
            case_clauses.append(f"WHEN LOWER(address) LIKE '%{name.lower()}%' THEN '{code}'")
            
            # Add variations without common suffixes
            name_lower = name.lower()
            if ' novads' in name_lower:
                base = name_lower.replace(' novads', '').replace("'", "''")
                case_clauses.append(f"WHEN LOWER(address) LIKE '%, {base},%' THEN '{code}'")
            if ' pagasts' in name_lower:
                base = name_lower.replace(' pagasts', '').replace("'", "''")
                case_clauses.append(f"WHEN LOWER(address) LIKE '%, {base} pag%' THEN '{code}'")
        
        case_sql = "\n            ".join(case_clauses[:500])  # Limit to avoid query too long
        
        # Step 3: Run bulk UPDATE
        logger.info("🔄 Running bulk update...")
        
        sql = f"""
        UPDATE companies
        SET atvk = CASE
            {case_sql}
            ELSE NULL
        END
        WHERE status = 'active'
          AND address IS NOT NULL
        """
        
        result = conn.execute(text(sql))
        updated = result.rowcount
        
        conn.commit()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # Get statistics
        stats = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(atvk) as with_atvk,
                COUNT(*) - COUNT(atvk) as without_atvk
            FROM companies
            WHERE status = 'active'
        """)).fetchone()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ COMPANY ATVK POPULATION COMPLETED")
        logger.info(f"   Total rows processed: {updated}")
        logger.info(f"   Companies with ATVK: {stats.with_atvk}")
        logger.info(f"   Companies without ATVK: {stats.without_atvk}")
        logger.info(f"   Coverage: {stats.with_atvk / stats.total * 100:.1f}%")
        logger.info(f"   Time elapsed: {elapsed:.2f} seconds")
        logger.info("=" * 60)
        
        # Show top territories
        top_territories = conn.execute(text("""
            SELECT t.name, t.type, COUNT(c.regcode) as company_count
            FROM companies c
            JOIN territories t ON t.code = c.atvk
            WHERE c.status = 'active'
            GROUP BY t.name, t.type
            ORDER BY company_count DESC
            LIMIT 10
        """)).fetchall()
        
        logger.info("\n📊 Top 10 Territories by Company Count:")
        for t in top_territories:
            logger.info(f"   {t.name} ({t.type}): {t.company_count} companies")


if __name__ == "__main__":
    populate_company_atvk_fast()
