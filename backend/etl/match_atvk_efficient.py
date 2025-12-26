"""
ETL Script: Efficient ATVK Matching using SQL Regex
Matches company addresses to territories using PostgreSQL regular expressions with word boundaries.
Prioritizes specific territories (Level 3) over broader ones (Level 2).
"""

import os
import re
import logging
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load env from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found")

def get_db_engine():
    return create_engine(DATABASE_URL)

def run_matching():
    engine = get_db_engine()
    start_time = datetime.now()
    
    with engine.connect() as conn:
        logger.info("📥 Loading territories...")
        
        # Load territories sorted by level (3 first) and length (longer first)
        # This ensures "Maltas pagasts" hits before "Malta" (if exists) and Level 3 before Level 2
        territories = conn.execute(text("""
            SELECT code, name, level, type
            FROM territories
            WHERE (valid_to IS NULL OR valid_to > NOW())
              AND level >= 2
            ORDER BY level DESC, LENGTH(name) DESC
        """)).fetchall()
        
        logger.info(f"✅ Loaded {len(territories)} territories")
        logger.info("🔄 Starting detailed matching (this may take a few minutes)...")
        
        total_updated = 0
        
        # Prepare regex-safe function
        def escape_regex(s):
            return re.escape(s).replace("'", "''")

        # Iterate and update
        # We use a transaction per batch of updates or one big one?
        # One big transaction might lock too much. Let's do autocommit or batch commits.
        
        count = 0
        for t in territories:
            name = t.name
            code = t.code
            
            # Variations to match
            patterns = [name]
            
            # Common suffix removal for broader matching
            name_lower = name.lower()
            if ' novads' in name_lower:
                patterns.append(name[:len(name)-7]) # Remove " novads"
            if ' pagasts' in name_lower:
                patterns.append(name[:len(name)-8]) # Remove " pagasts"
            if ' pilsēta' in name_lower:
                patterns.append(name[:len(name)-8]) # Remove " pilsēta"
                
            # Construct Regex Pattern
            # \m = start of word, \M = end of word. Case insensitive (~*)
            # Pattern: \m(Name|Name_Var)\M
            
            safe_patterns = [escape_regex(p) for p in patterns if len(p) > 2] # Skip very short names
            if not safe_patterns:
                continue
                
            regex_inner = "|".join(safe_patterns)
            regex = f"\\m({regex_inner})\\M"
            
            # Update query
            # Only update where ATVK is NULL to preserve previous specific matches
            query = text(f"""
                UPDATE companies
                SET atvk = :code
                WHERE atvk IS NULL 
                  AND address ~* :regex
            """)
            
            result = conn.execute(query, {"code": code, "regex": regex})
            
            if result.rowcount > 0:
                total_updated += result.rowcount
                # logger.info(f"   Mapped {result.rowcount} companies to {name}")
            
            count += 1
            if count % 50 == 0:
                conn.commit()
                logger.info(f"   Processed {count}/{len(territories)} territories... (Total updated: {total_updated})")

        conn.commit()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("=" * 60)
        logger.info(f"✅ Auto-matching complete")
        logger.info(f"   Total companies updated: {total_updated}")
        logger.info(f"   Time: {elapsed:.2f}s")
        logger.info("=" * 60)

if __name__ == "__main__":
    run_matching()
