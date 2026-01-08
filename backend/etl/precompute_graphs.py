
import logging
from sqlalchemy import text
from app.services.graph_service import calculate_company_graphs_batch
from sqlalchemy import create_engine
import os
import json
from psycopg2.extras import execute_values
import time
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env file
load_dotenv()

# Create dedicated engine with high pool size for this specific ETL job
# Standard engine from loader.py has default pool size (5), which bottlenecks 50 threads.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/ur_db")
engine = create_engine(DATABASE_URL, pool_size=50, max_overflow=10, pool_pre_ping=True)

def precompute_graphs():
    """
    Iterates over all companies (optimized: active only first),
    calculates their relationship graph, and batch upserts into company_graph_cache.
    """
    logger.info("Starting company graph pre-computation...")
    
    with engine.connect() as conn:
        # Ensure table exists
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS company_graph_cache (
                company_regcode BIGINT PRIMARY KEY,
                graph_data JSONB,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()

        # Get all companies to process
        # Prioritize companies with many members (likely to be slow)
        logger.info("Fetching target companies...")
        
        query = text("""
            SELECT DISTINCT c.regcode 
            FROM companies c
            JOIN persons p ON p.company_regcode = c.regcode OR p.legal_entity_regcode = c.regcode
            WHERE p.role IN ('member', 'officer', 'ubo')
        """)
        
        companies = conn.execute(query).fetchall()
        total_count = len(companies)
        all_regcodes = [r.regcode for r in companies]
        logger.info(f"Found {total_count} companies with connections to process.")
        
        # Parallel processing setup
        max_workers = 50
        logger.info(f"Starting parallel processing with {max_workers} workers...")
        
        # Chunk regcodes into larger batches for the workers
        # Each worker will handle a batch of 100
        chunk_size = 100
        chunks = [all_regcodes[i:i + chunk_size] for i in range(0, len(all_regcodes), chunk_size)]
        
        total_processed = 0
        start_time = time.time()
        
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def process_batch(regcodes_chunk):
            """Worker function to process a batch of companies"""
            with engine.connect() as thread_conn:
                try:
                    return calculate_company_graphs_batch(thread_conn, regcodes_chunk, year=2024)
                except Exception as e:
                    logger.error(f"Error processing batch: {e}")
                    return {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit chunk tasks
            futures = [executor.submit(process_batch, chunk) for chunk in chunks]
            
            batch_accumulated = []
            
            for future in as_completed(futures):
                results = future.result() # Dict of {regcode: graph}
                
                # Convert results to list tuples
                for regcode, graph in results.items():
                    if graph:
                         batch_accumulated.append((regcode, json.dumps(graph)))
                
                # Upsert to DB if accumulated enough
                if len(batch_accumulated) >= 200:
                    _upsert_batch(conn, batch_accumulated)
                    total_processed += len(batch_accumulated)
                    batch_accumulated = []
                    
                    elapsed = time.time() - start_time
                    rate = total_processed / elapsed
                    remaining = (total_count - total_processed) / rate if rate > 0 else 0
                    logger.info(f"Processed {total_processed}/{total_count} ({rate:.1f} comp/sec). ETA: {remaining/60:.1f} min")
        
        # Flush remaining
        if batch_accumulated:
            _upsert_batch(conn, batch_accumulated)
            
    logger.info("✅ Graph pre-computation completed.")

def _upsert_batch(conn, data):
    """Upsert batch using execute_values for speed"""
    try:
        raw_conn = conn.connection
        cursor = raw_conn.cursor()
        
        execute_values(cursor, """
            INSERT INTO company_graph_cache (company_regcode, graph_data)
            VALUES %s
            ON CONFLICT (company_regcode) 
            DO UPDATE SET graph_data = EXCLUDED.graph_data, updated_at = NOW()
        """, data)
        
        raw_conn.commit()
    except Exception as e:
        logger.error(f"Batch upsert failed: {e}")
        conn.rollback()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    precompute_graphs()
