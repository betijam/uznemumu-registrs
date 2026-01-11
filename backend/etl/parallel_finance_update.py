"""
PARALLEL ETL - Uses all CPU cores for maximum speed
"""
import pandas as pd
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
from csv_cache import CSVCache
from multiprocessing import Pool, cpu_count
from functools import partial
from io import StringIO
import psycopg2

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# CSV URLs
BALANCE_SHEETS_URL = "https://data.gov.lv/dati/dataset/8d31b878-536a-44aa-a013-8bc6b669d477/resource/50ef4f26-f410-4007-b296-22043ca3dc43/download/balance_sheets.csv"
FINANCIAL_STATEMENTS_URL = "https://data.gov.lv/dati/dataset/8d31b878-536a-44aa-a013-8bc6b669d477/resource/27fcc5ec-c63b-4bfd-bb08-01f073a52d04/download/financial_statements.csv"

BATCH_SIZE = 1000  # Larger batches for parallel processing
NUM_WORKERS = max(1, cpu_count() - 1)  # Leave 1 core free

def process_balance_chunk(args):
    """Process a single balance sheet chunk - runs in parallel"""
    chunk_data, stmt_lookup_df = args
    
    try:
        # Extract accounts_receivable column
        ar_col = None
        for col in ['accounts_receivable', 'debtori', 'receivables']:
            if col in chunk_data.columns:
                ar_col = col
                break
        
        if not ar_col or 'statement_id' not in chunk_data.columns:
            return []
        
        # Filter to only statement_ids we care about
        chunk_data = chunk_data[chunk_data['statement_id'].isin(stmt_lookup_df['statement_id'])]
        
        if len(chunk_data) == 0:
            return []
        
        # Merge with statement lookup
        chunk_data = chunk_data.merge(
            stmt_lookup_df[['statement_id', 'regcode', 'year']], 
            on='statement_id', 
            how='inner'  # Only keep matches
        )
        
        # Convert accounts_receivable to numeric
        chunk_data['accounts_receivable'] = pd.to_numeric(chunk_data[ar_col], errors='coerce')
        
        # Drop rows with missing data
        chunk_data = chunk_data.dropna(subset=['regcode', 'year', 'accounts_receivable'])
        
        if len(chunk_data) == 0:
            return []
        
        # Return as list of dicts for database update
        return chunk_data[['regcode', 'year', 'accounts_receivable']].to_dict('records')
    
    except Exception as e:
        logger.error(f"Error processing chunk: {e}")
        return []

class ParallelFinanceETL:
    """Ultra-fast parallel ETL"""
    
    def __init__(self, full_load=False):
        self.engine = engine
        self.cache = CSVCache()
        self.full_load = full_load
        self.job_name = 'extended_financial_fields'
        
    def get_last_run_date(self):
        """Get timestamp of last successful run"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT last_success_at FROM etl_state 
                WHERE job_name = :job
            """), {"job": self.job_name}).fetchone()
            
            if result and result[0] and not self.full_load:
                return result[0]
            return None
    
    def update_state(self, status, records_processed=0, error=None):
        """Update ETL state table"""
        with self.engine.connect() as conn:
            if status == 'SUCCESS':
                conn.execute(text("""
                    UPDATE etl_state 
                    SET status = :status,
                        last_run_at = NOW(),
                        last_success_at = NOW(),
                        records_processed = :records,
                        error_message = NULL,
                        updated_at = NOW()
                    WHERE job_name = :job
                """), {"status": status, "records": records_processed, "job": self.job_name})
            else:
                conn.execute(text("""
                    UPDATE etl_state 
                    SET status = :status,
                        last_run_at = NOW(),
                        error_message = :error,
                        updated_at = NOW()
                    WHERE job_name = :job
                """), {"status": status, "error": str(error)[:500], "job": self.job_name})
            conn.commit()
    
    def get_regcodes_to_update(self):
        """Get list of company regcodes that need updating"""
        last_run = self.get_last_run_date()
        
        with self.engine.connect() as conn:
            if last_run:
                logger.info(f"📊 Incremental mode: Finding records changed since {last_run}")
                result = conn.execute(text("""
                    SELECT DISTINCT company_regcode 
                    FROM financial_reports 
                    WHERE created_at > :last_run OR updated_at > :last_run
                """), {"last_run": last_run}).fetchall()
            else:
                logger.info("📊 Full load mode: Processing all records")
                result = conn.execute(text("""
                    SELECT DISTINCT company_regcode 
                    FROM financial_reports
                """)).fetchall()
                
            regcodes = set(row[0] for row in result)
            logger.info(f"✅ Found {len(regcodes)} companies to update")
            return regcodes
    
    def run(self):
        """Execute parallel ETL"""
        try:
            self.update_state('RUNNING')
            logger.info(f"🚀 Starting PARALLEL ETL with {NUM_WORKERS} workers...")
            
            # Get regcodes that need updating
            regcodes_to_update = self.get_regcodes_to_update()
            
            if len(regcodes_to_update) == 0:
                logger.info("✅ No records to update!")
                self.update_state('SUCCESS', 0)
                return
            
            # Get cached CSV paths
            logger.info("📥 Preparing CSV files...")
            statements_path = self.cache.get_cached_path(FINANCIAL_STATEMENTS_URL)
            balance_path = self.cache.get_cached_path(BALANCE_SHEETS_URL)
            
            # Step 1: Build statement mapping (VECTORIZED)
            logger.info(f"📥 Loading statement mappings...")
            stmt_map = {}
            
            for stmt_chunk in pd.read_csv(statements_path, sep=';', dtype=str, chunksize=100000):
                stmt_chunk['regcode'] = pd.to_numeric(stmt_chunk['legal_entity_registration_number'], errors='coerce')
                stmt_chunk['year_int'] = pd.to_numeric(stmt_chunk['year'], errors='coerce')
                
                relevant = stmt_chunk[stmt_chunk['regcode'].isin(regcodes_to_update)].copy()
                
                if len(relevant) > 0:
                    new_mappings = relevant.set_index('id')[['regcode', 'year_int']].to_dict('index')
                    for stmt_id, data in new_mappings.items():
                        stmt_map[stmt_id] = {'regcode': int(data['regcode']), 'year': int(data['year_int'])}
            
            logger.info(f"✅ Loaded {len(stmt_map)} statement mappings")
            
            if len(stmt_map) == 0:
                logger.info("✅ No statements found")
                self.update_state('SUCCESS', 0)
                return
            
            # Convert to DataFrame for parallel workers
            stmt_lookup_df = pd.DataFrame.from_dict(stmt_map, orient='index')
            stmt_lookup_df.index.name = 'statement_id'
            stmt_lookup_df = stmt_lookup_df.reset_index()
            
            # Step 2: Read balance sheets in chunks and prepare for parallel processing
            logger.info(f"📊 Reading balance sheets for parallel processing...")
            
            chunks_to_process = []
            for bal_chunk in pd.read_csv(balance_path, sep=';', dtype=str, chunksize=50000):
                chunks_to_process.append((bal_chunk, stmt_lookup_df))
            
            logger.info(f"✅ Prepared {len(chunks_to_process)} chunks for {NUM_WORKERS} workers")
            
            # Step 3: Process chunks in parallel
            logger.info(f"🚀 Processing in parallel...")
            all_updates = []
            
            with Pool(processes=NUM_WORKERS) as pool:
                results = pool.map(process_balance_chunk, chunks_to_process)
                
                # Flatten results
                for chunk_result in results:
                    all_updates.extend(chunk_result)
                    if len(all_updates) % 10000 == 0:
                        logger.info(f"  Processed {len(all_updates)} records so far...")
            
            logger.info(f"✅ Parallel processing complete! {len(all_updates)} updates ready")
            
            # Step 4: Batch update database
            if all_updates:
                self._batch_update(all_updates)
            
            logger.info(f"✅ ETL complete! Updated {len(all_updates)} records")
            self.update_state('SUCCESS', len(all_updates))
            
        except Exception as e:
            logger.error(f"❌ ETL failed: {e}")
            self.update_state('FAILED', 0, str(e))
            raise
    
    def _batch_update(self, all_updates):
        """ULTRA-FAST batch update using temp table"""
        if not all_updates:
            return
        
        total = len(all_updates)
        logger.info(f"💾 Bulk updating {total} records using temp table...")
        
        # Convert to DataFrame for bulk operations
        df = pd.DataFrame(all_updates)
        
        try:
            # Get raw connection from SQLAlchemy
            raw_conn = self.engine.raw_connection()
            cursor = raw_conn.cursor()
            
            # Create temp table
            cursor.execute("""
                CREATE TEMP TABLE temp_updates (
                    regcode BIGINT,
                    year INT,
                    accounts_receivable NUMERIC
                ) ON COMMIT DROP
            """)
            
            # Prepare CSV data in memory
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False, header=False)
            csv_buffer.seek(0)
            
            # COPY data to temp table (SUPER FAST!)
            logger.info(f"  📥 Loading {total} records into temp table...")
            cursor.copy_from(csv_buffer, 'temp_updates', sep=',', columns=('regcode', 'year', 'accounts_receivable'))
            
            # Single UPDATE FROM (updates all rows in one query!)
            logger.info(f"  🚀 Executing bulk UPDATE...")
            cursor.execute("""
                UPDATE financial_reports fr
                SET accounts_receivable = tu.accounts_receivable,
                    updated_at = NOW()
                FROM temp_updates tu
                WHERE fr.company_regcode = tu.regcode 
                  AND fr.year = tu.year
            """)
            
            rows_updated = cursor.rowcount
            raw_conn.commit()
            cursor.close()
            raw_conn.close()
            
            logger.info(f"  ✅ Updated {rows_updated} records in single operation!")
            
        except Exception as e:
            logger.error(f"Bulk update failed: {e}")
            raise

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--full', action='store_true', help='Run full load')
    args = parser.parse_args()
    
    etl = ParallelFinanceETL(full_load=args.full)
    etl.run()
