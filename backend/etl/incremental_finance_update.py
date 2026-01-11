"""
OPTIMIZED Incremental ETL using dictionary lookups instead of slow pandas merges
Based on the fast approach from process_finance_extended.py
"""
import pandas as pd
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
from csv_cache import CSVCache

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

# CSV URLs
BALANCE_SHEETS_URL = "https://data.gov.lv/dati/dataset/8d31b878-536a-44aa-a013-8bc6b669d477/resource/50ef4f26-f410-4007-b296-22043ca3dc43/download/balance_sheets.csv"
FINANCIAL_STATEMENTS_URL = "https://data.gov.lv/dati/dataset/8d31b878-536a-44aa-a013-8bc6b669d477/resource/27fcc5ec-c63b-4bfd-bb08-01f073a52d04/download/financial_statements.csv"

BATCH_SIZE = 50  # Very small batches for visibility over slow network

class OptimizedFinanceETL:
    """Fast ETL using dictionary lookups instead of pandas merge"""
    
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
        """Execute optimized ETL using dictionary lookups"""
        try:
            self.update_state('RUNNING')
            logger.info(f"🚀 Starting {'FULL' if self.full_load else 'INCREMENTAL'} ETL run...")
            
            # Get regcodes that need updating
            regcodes_to_update = self.get_regcodes_to_update()
            
            if len(regcodes_to_update) == 0:
                logger.info("✅ No records to update! All up to date.")
                self.update_state('SUCCESS', 0)
                return
            
            # Get cached CSV paths
            logger.info("📥 Preparing CSV files...")
            statements_path = self.cache.get_cached_path(FINANCIAL_STATEMENTS_URL)
            balance_path = self.cache.get_cached_path(BALANCE_SHEETS_URL)
            
            # Step 1: Build statement mapping dictionary (statement_id -> (regcode, year))
            logger.info(f"📥 Loading statement mappings...")
            stmt_map = {}  # statement_id -> {'regcode': X, 'year': Y}
            
            chunk_num = 0
            for stmt_chunk in pd.read_csv(statements_path, sep=';', dtype=str, chunksize=50000):
                chunk_num += 1
                for _, row in stmt_chunk.iterrows():
                    try:
                        regcode = int(row['legal_entity_registration_number'])
                        if regcode in regcodes_to_update:
                            stmt_map[row['id']] = {
                                'regcode': regcode,
                                'year': int(row['year'])
                            }
                    except:
                        continue
                
                if chunk_num % 5 == 0:
                    logger.info(f"  Processed {chunk_num} statement chunks, {len(stmt_map)} relevant statements")
            
            logger.info(f"✅ Loaded {len(stmt_map)} relevant statement mappings")
            
            if len(stmt_map) == 0:
                logger.info("✅ No statements found for these companies")
                self.update_state('SUCCESS', 0)
                return
            
            # Step 2: Process balance sheets using VECTORIZED operations (much faster)
            logger.info(f"📊 Processing balance sheets...")
            
            updates = []  # List of (regcode, year, accounts_receivable)
            chunk_num = 0
            total_rows_processed = 0
            
            for bal_chunk in pd.read_csv(balance_path, sep=';', dtype=str, chunksize=1000): # Smaller read chunk
                chunk_num += 1
                chunk_start = pd.Timestamp.now()
                # logger.info(f"📊 Processing balance chunk {chunk_num} ({len(bal_chunk)} rows)...") # Too noisy
                
                # Extract accounts_receivable column
                ar_col = None
                for col in ['accounts_receivable', 'debtori', 'receivables']:
                    if col in bal_chunk.columns:
                        ar_col = col
                        break
                
                if not ar_col or 'statement_id' not in bal_chunk.columns:
                    continue
                
                # OPTIMIZATION: Filter to only statement_ids we care about FIRST
                bal_chunk = bal_chunk[bal_chunk['statement_id'].isin(stmt_map.keys())]
                
                if len(bal_chunk) == 0:
                    continue
                
                # VECTORIZED: Add regcode and year from statement map
                bal_chunk['regcode'] = bal_chunk['statement_id'].map(lambda x: stmt_map.get(x, {}).get('regcode'))
                bal_chunk['year'] = bal_chunk['statement_id'].map(lambda x: stmt_map.get(x, {}).get('year'))
                
                # Convert accounts_receivable to numeric
                bal_chunk['accounts_receivable'] = pd.to_numeric(bal_chunk[ar_col], errors='coerce')
                
                # Drop rows with missing data
                bal_chunk = bal_chunk.dropna(subset=['regcode', 'year', 'accounts_receivable'])
                
                if len(bal_chunk) == 0:
                    continue
                
                # Buffer updates
                chunk_updates = bal_chunk[['regcode', 'year', 'accounts_receivable']].to_dict('records')
                updates.extend(chunk_updates)
                total_rows_processed += len(bal_chunk)
                
                # Process buffer if it gets large enough, OR if we have any updates to prevent memory growth
                if len(updates) >= BATCH_SIZE:
                    self._batch_update(updates)
                    updates = [] # Clear buffer
                
                # Show progress every 10 chunks to avoid spam
                if chunk_num % 10 == 0:
                    logger.info(f"  ⏱️  Processed {chunk_num} CSV chunks (Total updated: {total_rows_processed})")
            
            # Final batch
            if updates:
                self._batch_update(updates)
            
            logger.info(f"✅ Update complete! Updated {total_rows_processed} total rows")
            self.update_state('SUCCESS', total_rows_processed)
            
        except Exception as e:
            logger.error(f"❌ ETL failed: {e}")
            self.update_state('FAILED', 0, str(e))
            raise
    
    def _batch_update(self, all_updates):
        """Batch update database in small slices to avoid timeouts"""
        if not all_updates:
            return
        
        # Slicing the updates list into smaller pieces
        total = len(all_updates)
        
        # Process in slices of BATCH_SIZE (e.g. 50)
        for i in range(0, total, BATCH_SIZE):
            slice_end = min(i + BATCH_SIZE, total)
            batch = all_updates[i:slice_end]
            
            try:
                with self.engine.connect() as conn:
                    conn.execute(
                        text("""
                            UPDATE financial_reports 
                            SET accounts_receivable = :accounts_receivable,
                                updated_at = NOW()
                            WHERE company_regcode = :regcode AND year = :year
                        """),
                        batch
                    )
                    conn.commit()
                # logger.info(f"    💾 Updated records {i+1}-{slice_end}") 
                print(f".", end="", flush=True) # Visual progress dot
            except Exception as e:
                logger.error(f"Failed to update batch {i}-{slice_end}: {e}")
        
        print("") # Newline after dots

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--full', action='store_true', help='Run full load instead of incremental')
    args = parser.parse_args()
    
    etl = OptimizedFinanceETL(full_load=args.full)
    etl.run()
