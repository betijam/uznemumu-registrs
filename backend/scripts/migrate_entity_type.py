"""
Fast migration script to add and populate entity_type column in persons table.
Uses parallel processing and batching for optimal performance.

Usage:
    python migrate_entity_type.py
    python migrate_entity_type.py postgresql://user:pass@host/db
"""
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, create_engine
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from typing import List, Tuple
import time

# Try to load .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        logging.info(f"Loaded .env from {env_path}")
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get database URL from command line, environment, or prompt
DATABASE_URL = None
if len(sys.argv) > 1:
    DATABASE_URL = sys.argv[1]
    logger.info("Using DATABASE_URL from command line argument")
else:
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL:
        logger.info("Using DATABASE_URL from environment variable")

if not DATABASE_URL:
    logger.error("DATABASE_URL not found!")
    logger.error("Please provide it via:")
    logger.error("  1. Command line: python migrate_entity_type.py 'postgresql://...'")
    logger.error("  2. Environment variable: export DATABASE_URL='postgresql://...'")
    logger.error("  3. .env file in backend directory")
    sys.exit(1)

engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=40)

BATCH_SIZE = 10000  # Process 10k records per batch
MAX_WORKERS = 8     # Parallel workers


def run_migration():
    """Step 1: Add entity_type column if not exists"""
    logger.info("🔧 Step 1: Adding entity_type column...")
    
    with engine.connect() as conn:
        # Add column
        conn.execute(text("""
            ALTER TABLE persons 
            ADD COLUMN IF NOT EXISTS entity_type VARCHAR(50)
        """))
        
        # Add index
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_persons_entity_type 
            ON persons(entity_type)
        """))
        
        conn.commit()
    
    logger.info("✅ Column and index created successfully")


def get_total_counts():
    """Get counts for progress tracking"""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                COUNT(*) FILTER (WHERE role = 'member' AND legal_entity_regcode IS NOT NULL) as legal_entities,
                COUNT(*) FILTER (WHERE role IN ('member', 'officer', 'ubo') AND legal_entity_regcode IS NULL) as physical_persons
            FROM persons
            WHERE entity_type IS NULL
        """)).fetchone()
        
        return {
            'legal_entities': result[0],
            'physical_persons': result[1]
        }


def get_company_regcodes_batch() -> List[int]:
    """Get all company regcodes in one query for fast lookup"""
    logger.info("📋 Loading all company regcodes into memory...")
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT regcode FROM companies"))
        regcodes = {row[0] for row in result}
    
    logger.info(f"✅ Loaded {len(regcodes):,} company regcodes")
    return regcodes


def get_legal_entity_batches(batch_size: int) -> List[Tuple[int, int]]:
    """Get ID ranges for batching legal entities"""
    with engine.connect() as conn:
        # Get min and max IDs
        result = conn.execute(text("""
            SELECT MIN(id), MAX(id)
            FROM persons
            WHERE role = 'member' AND legal_entity_regcode IS NOT NULL
        """)).fetchone()
        
        if not result[0]:
            return []
        
        min_id, max_id = result[0], result[1]
        
        # Create batches
        batches = []
        current = min_id
        while current <= max_id:
            batches.append((current, min(current + batch_size - 1, max_id)))
            current += batch_size
        
        return batches


def process_legal_entity_batch(batch_range: Tuple[int, int], company_regcodes: set) -> int:
    """Process a batch of legal entities - determine FOREIGN vs LEGAL"""
    start_id, end_id = batch_range
    
    # Create new connection for this thread
    thread_engine = create_engine(DATABASE_URL, pool_size=1)
    
    try:
        with thread_engine.connect() as conn:
            # Fetch batch
            rows = conn.execute(text("""
                SELECT id, legal_entity_regcode
                FROM persons
                WHERE id BETWEEN :start_id AND :end_id
                  AND role = 'member'
                  AND legal_entity_regcode IS NOT NULL
                  AND entity_type IS NULL
            """), {"start_id": start_id, "end_id": end_id}).fetchall()
            
            if not rows:
                return 0
            
            # Classify in memory
            foreign_ids = []
            legal_ids = []
            
            for row in rows:
                person_id, regcode = row[0], row[1]
                if regcode in company_regcodes:
                    legal_ids.append(person_id)
                else:
                    foreign_ids.append(person_id)
            
            # Batch update FOREIGN_ENTITY
            if foreign_ids:
                conn.execute(text("""
                    UPDATE persons
                    SET entity_type = 'FOREIGN_ENTITY'
                    WHERE id = ANY(:ids)
                """), {"ids": foreign_ids})
            
            # Batch update LEGAL_ENTITY
            if legal_ids:
                conn.execute(text("""
                    UPDATE persons
                    SET entity_type = 'LEGAL_ENTITY'
                    WHERE id = ANY(:ids)
                """), {"ids": legal_ids})
            
            conn.commit()
            
            return len(rows)
    
    finally:
        thread_engine.dispose()


def populate_legal_entities_parallel(company_regcodes: set):
    """Step 2a: Populate FOREIGN_ENTITY and LEGAL_ENTITY in parallel"""
    logger.info("🚀 Step 2a: Classifying legal entities (FOREIGN vs LEGAL)...")
    
    batches = get_legal_entity_batches(BATCH_SIZE)
    
    if not batches:
        logger.info("No legal entities to process")
        return
    
    logger.info(f"Processing {len(batches)} batches with {MAX_WORKERS} workers...")
    
    processed = 0
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(process_legal_entity_batch, batch, company_regcodes): batch 
            for batch in batches
        }
        
        for future in as_completed(futures):
            batch = futures[future]
            try:
                count = future.result()
                processed += count
                
                if processed % (BATCH_SIZE * 5) == 0:
                    elapsed = time.time() - start_time
                    rate = processed / elapsed if elapsed > 0 else 0
                    logger.info(f"Processed {processed:,} records ({rate:.0f} records/sec)")
            
            except Exception as e:
                logger.error(f"Error processing batch {batch}: {e}")
    
    elapsed = time.time() - start_time
    logger.info(f"✅ Classified {processed:,} legal entities in {elapsed:.2f}s ({processed/elapsed:.0f} records/sec)")


def populate_physical_persons():
    """Step 2b: Populate PHYSICAL_PERSON (simple, fast)"""
    logger.info("👤 Step 2b: Marking physical persons...")
    
    start_time = time.time()
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            UPDATE persons
            SET entity_type = 'PHYSICAL_PERSON'
            WHERE role IN ('member', 'officer', 'ubo')
              AND legal_entity_regcode IS NULL
              AND entity_type IS NULL
        """))
        
        conn.commit()
        count = result.rowcount
    
    elapsed = time.time() - start_time
    logger.info(f"✅ Marked {count:,} physical persons in {elapsed:.2f}s")


def verify_results():
    """Step 3: Verify and show statistics"""
    logger.info("📊 Step 3: Verifying results...")
    
    with engine.connect() as conn:
        # Get counts by entity_type
        result = conn.execute(text("""
            SELECT 
                entity_type,
                role,
                COUNT(*) as count
            FROM persons
            GROUP BY entity_type, role
            ORDER BY entity_type, role
        """)).fetchall()
        
        logger.info("\n" + "="*60)
        logger.info("ENTITY TYPE DISTRIBUTION:")
        logger.info("="*60)
        
        for row in result:
            entity_type = row[0] or 'NULL'
            role = row[1]
            count = row[2]
            logger.info(f"{entity_type:20} | {role:10} | {count:,}")
        
        # Check for NULLs
        null_count = conn.execute(text("""
            SELECT COUNT(*) FROM persons WHERE entity_type IS NULL
        """)).scalar()
        
        logger.info("="*60)
        if null_count > 0:
            logger.warning(f"⚠️  {null_count:,} records still have NULL entity_type")
        else:
            logger.info("✅ All records have entity_type populated!")


def main():
    """Run the complete migration"""
    logger.info("="*60)
    logger.info("ENTITY TYPE MIGRATION - FAST PARALLEL VERSION")
    logger.info("="*60)
    
    total_start = time.time()
    
    try:
        # Step 1: Add column
        run_migration()
        
        # Get counts
        counts = get_total_counts()
        logger.info(f"\nRecords to process:")
        logger.info(f"  Legal entities: {counts['legal_entities']:,}")
        logger.info(f"  Physical persons: {counts['physical_persons']:,}")
        logger.info("")
        
        # Step 2a: Load company regcodes and classify legal entities
        company_regcodes = get_company_regcodes_batch()
        populate_legal_entities_parallel(company_regcodes)
        
        # Step 2b: Mark physical persons
        populate_physical_persons()
        
        # Step 3: Verify
        verify_results()
        
        total_elapsed = time.time() - total_start
        logger.info(f"\n🎉 Migration completed in {total_elapsed:.2f}s")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
