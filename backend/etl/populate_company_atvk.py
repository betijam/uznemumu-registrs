"""
ETL Script: Populate Company ATVK Codes from Addresses

This script extracts ATVK territorial codes from company addresses
by matching address text to territory names.

Strategy:
1. Load all territories (municipalities, cities, parishes)
2. For each company, search its address for territory names
3. Match the most specific territory found (parish > city > municipality)
4. Update company.atvk with the matched territory code
"""

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")


def normalize_text(text: str) -> str:
    """Normalize text for matching (lowercase, remove extra spaces)"""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.lower().strip())


def populate_company_atvk():
    """
    Populate companies.atvk by matching addresses to territory names
    """
    engine = create_engine(DATABASE_URL)
    
    logger.info("=" * 60)
    logger.info("COMPANY ATVK POPULATION STARTED")
    logger.info("=" * 60)
    start_time = datetime.now()
    
    with engine.connect() as conn:
        # Step 1: Load all territories
        logger.info("📥 Loading territories...")
        territories = conn.execute(text("""
            SELECT code, name, level, type
            FROM territories
            WHERE valid_to IS NULL OR valid_to > NOW()
            ORDER BY level DESC, name
        """)).fetchall()
        
        logger.info(f"✅ Loaded {len(territories)} territories")
        
        # Create lookup structures
        # Priority: level 3 (parish/city) > level 2 (municipality)
        territory_patterns = []
        for t in territories:
            name = t.name
            code = t.code
            level = t.level
            
            # Clean up name for matching
            # Remove common suffixes for better matching
            search_names = [name]
            
            # Add variations
            if " novads" in name.lower():
                search_names.append(name.lower().replace(" novads", ""))
            if " pagasts" in name.lower():
                search_names.append(name.lower().replace(" pagasts", ""))
            if " pilsēta" in name.lower():
                search_names.append(name.lower().replace(" pilsēta", ""))
                
            for search_name in search_names:
                territory_patterns.append({
                    'code': code,
                    'name': name,
                    'search_name': normalize_text(search_name),
                    'level': level
                })
        
        # Sort by level (more specific first) and name length (longer names first for better matching)
        territory_patterns.sort(key=lambda x: (-x['level'], -len(x['search_name'])))
        
        logger.info(f"📋 Created {len(territory_patterns)} search patterns")
        
        # Step 2: Process companies in batches
        logger.info("🔄 Processing companies...")
        
        batch_size = 1000
        total_updated = 0
        offset = 0
        
        while True:
            # Get batch of companies without ATVK
            companies = conn.execute(text("""
                SELECT regcode, address
                FROM companies
                WHERE address IS NOT NULL
                  AND (atvk IS NULL OR atvk = '')
                ORDER BY regcode
                LIMIT :batch_size OFFSET :offset
            """), {"batch_size": batch_size, "offset": offset}).fetchall()
            
            if not companies:
                break
            
            updates = []
            for company in companies:
                regcode = company.regcode
                address = normalize_text(company.address)
                
                if not address:
                    continue
                
                # Find best matching territory
                matched_code = None
                matched_level = 0
                
                for pattern in territory_patterns:
                    if pattern['search_name'] in address:
                        # Prefer more specific matches (higher level)
                        if pattern['level'] > matched_level:
                            matched_code = pattern['code']
                            matched_level = pattern['level']
                            # If we found a level 3 match, stop searching
                            if matched_level == 3:
                                break
                
                if matched_code:
                    updates.append({
                        'regcode': regcode,
                        'atvk': matched_code
                    })
            
            # Batch update
            if updates:
                for update in updates:
                    conn.execute(text("""
                        UPDATE companies SET atvk = :atvk WHERE regcode = :regcode
                    """), update)
                
                total_updated += len(updates)
                logger.info(f"   Updated {total_updated} companies...")
            
            offset += batch_size
            
            # Safety limit
            if offset > 500000:
                logger.warning("⚠️  Reached safety limit, stopping")
                break
        
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
        logger.info(f"   Total companies updated: {total_updated}")
        logger.info(f"   Companies with ATVK: {stats.with_atvk}")
        logger.info(f"   Companies without ATVK: {stats.without_atvk}")
        logger.info(f"   Coverage: {stats.with_atvk / stats.total * 100:.1f}%")
        logger.info(f"   Time elapsed: {elapsed:.2f} seconds")
        logger.info("=" * 60)
        
        # Show top territories by company count
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
    populate_company_atvk()
