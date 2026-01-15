
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
        
        # We need to process the whole CSV to apply priority correctly
        use_cols = ['legal_entity_registration_number', 'year', 'source_type']
        
        # We'll load the whole CSV metdata into memory to do proper UGP prioritization
        # This is safe because it's only ~2M rows of strings/ints (few hundred MBs)
        df_csv = pd.read_csv(
            csv_path, 
            sep=';', 
            usecols=use_cols,
            dtype={'legal_entity_registration_number': str, 'year': 'Int32', 'source_type': str}
        )
        
        # Clean
        df_csv = df_csv.rename(columns={'legal_entity_registration_number': 'regcode'})
        
        # --- UGP PRIORITY LOGIC ---
        def get_priority(st):
            st_str = str(st).upper() if pd.notnull(st) else ""
            if st_str == 'UGP': return 2
            if st_str == 'UKGP': return 0
            return 1
            
        logger.info("⚖️ Applying UGP priority logic...")
        df_csv['priority'] = df_csv['source_type'].apply(get_priority)
        
        # Sort so highest priority is LAST
        df_csv = df_csv.sort_values(['regcode', 'year', 'priority'])
        
        # Deduplicate: only one label per company/year
        df_csv = df_csv.drop_duplicates(subset=['regcode', 'year'], keep='last')
        
        logger.info(f"✅ Prepared {len(df_csv)} unique labels for update.")
        
        # Prepare buffer for COPY
        s_buf = io.StringIO()
        df_csv[['regcode', 'year', 'source_type']].to_csv(s_buf, index=False, header=False, sep='\t')
        s_buf.seek(0)
        
        # Execute COPY
        cur.copy_from(s_buf, STAGING_TABLE, columns=('regcode', 'year', 'source_type'), null="")
        
        # 4. Index for speed
        logger.info("⚡ Indexing staging table...")
        cur.execute(f"CREATE INDEX idx_staging_update ON {STAGING_TABLE}(regcode, year);")
        
        # 5. Execute Bulk UPDATE in Batches
        logger.info("🔥 Executing Batch UPDATE on financial_reports using (regcode, year)...")
        
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
            raw_conn.commit()
            logger.info(f"   ✅ Batch {i+1}/{BATCHES} done. Updated {count} rows.")

        logger.info(f"✨ Total rows updated: {total_updated}")
        
        # Cleanup
        logger.info("🧹 Cleaning up staging table...")
        cur.execute(f"DROP TABLE IF EXISTS {STAGING_TABLE}")
        raw_conn.commit()

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
