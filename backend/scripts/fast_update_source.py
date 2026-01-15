
import os
import time
import pandas as pd
from sqlalchemy import create_engine, text
import io
import psycopg2
import logging
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Config
DATABASE_URL = os.getenv("DATABASE_URL")
# Default path, specific to the user's environment or adjustable via args
CSV_PATH = "backend/data/financial_statements.csv" 
CHUNK_SIZE = 100000

if not DATABASE_URL:
    print("❌ DATABASE_URL env var is not set!")
    exit(1)

def fast_update_source_type(csv_path):
    """
    Updates financial_reports.source_type from CSV using high-performance COPY + UPDATE FROM strategy.
    """
    if not os.path.exists(csv_path):
        logger.error(f"❌ File not found: {csv_path}")
        return

    engine = create_engine(DATABASE_URL)
    
    logger.info("🚀 Starting fast update of source_type...")
    start_time = time.time()

    # 1. Create connection
    raw_conn = engine.raw_connection()
    try:
        cur = raw_conn.cursor()

        # 2. Create Staging Table (UNLOGGED for speed, but persistent across commits)
        STAGING_TABLE = "staging_source_updates"
        logger.info(f"🛠️ Creating staging table {STAGING_TABLE}...")
        cur.execute(f"DROP TABLE IF EXISTS {STAGING_TABLE}")
        cur.execute(f"""
            CREATE UNLOGGED TABLE {STAGING_TABLE} (
                regcode BIGINT,
                year INT,
                source_type TEXT
            );
        """)
        
        # 3. Read CSV and Stream to DB using COPY
        logger.info(f"📖 Reading CSV {csv_path} and streaming to DB...")
        
        total_rows = 0
        
        # Use Pandas to parse CSV efficiently, but only relevant columns
        # We assume headers: id;legal_entity_registration_number;year;...;source_type;...
        use_cols = ['legal_entity_registration_number', 'year', 'source_type']
        
        # Generator to process in chunks
        csv_iterator = pd.read_csv(
            csv_path, 
            sep=';', 
            usecols=lambda c: c in use_cols, # Robust selection
            dtype={'legal_entity_registration_number': str, 'year': 'Int32', 'source_type': str},
            chunksize=CHUNK_SIZE
        )
        
        for i, chunk in enumerate(csv_iterator):
            # Clean/Rename
            chunk = chunk.rename(columns={
                'legal_entity_registration_number': 'regcode',
                # source_type is already correct
            })
            
            # Filter: we only care if source_type is NOT NULL (or if we want to overwrite everything)
            # Actually, we should update everything to ensure correctness.
            # But let's convert NaN to None for SQL
            chunk = chunk.where(pd.notnull(chunk), None)
            
            # Prepare buffer for COPY
            s_buf = io.StringIO()
            chunk[['regcode', 'year', 'source_type']].to_csv(s_buf, index=False, header=False, sep='\t')
            s_buf.seek(0)
            
            # Execute COPY
            cur.copy_from(s_buf, STAGING_TABLE, columns=('regcode', 'year', 'source_type'), null="")
            
            total_rows += len(chunk)
            if (i + 1) % 5 == 0:
                logger.info(f"   ↳ Buffered {total_rows} rows...")
                
        logger.info(f"✅ Finished buffering {total_rows} rows to Staging Table.")
        
        # 4. Create Index on Staging Table (Critical for UPDATE performance)
        logger.info("⚡ Indexing staging table...")
        cur.execute(f"CREATE INDEX idx_staging_update ON {STAGING_TABLE}(regcode, year);")
        
        # 5. Execute Bulk UPDATE in Batches (Sharding)
        logger.info("🔥 Executing Batch UPDATE on financial_reports...")
        
        # Split into 10 chunks based on regcode modulo to keep transactions smaller
        BATCHES = 10
        total_updated = 0
        
        for i in range(BATCHES):
            logger.info(f"   ⏳ Batch {i+1}/{BATCHES} executing...")
            cur.execute(f"""
                UPDATE financial_reports f
                SET source_type = t.source_type
                FROM {STAGING_TABLE} t
                WHERE f.company_regcode = t.regcode 
                  AND f.year = t.year
                  AND f.company_regcode % {BATCHES} = {i}
                  AND f.source_type IS DISTINCT FROM t.source_type;
            """)
            count = cur.rowcount
            total_updated += count
            raw_conn.commit() # Commit each batch immediately
            logger.info(f"   ✅ Batch {i+1}/{BATCHES} done. Updated {count} rows.")

        logger.info(f"✨ Total rows updated: {total_updated}")
        
        # Cleanup
        logger.info("🧹 Cleaning up staging table...")
        cur.execute(f"DROP TABLE IF EXISTS {STAGING_TABLE}")
        raw_conn.commit()
        
    except Exception as e:
        logger.error(f"❌ Error during update: {e}")
        raw_conn.rollback()
    finally:
        cur.close()
        raw_conn.close()

    elapsed = time.time() - start_time
    logger.info(f"🎉 Done in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", help="Path to financial_statements.csv")
    args = parser.parse_args()
    
    fast_update_source_type(args.csv_path)
