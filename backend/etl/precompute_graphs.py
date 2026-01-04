
import logging
from sqlalchemy import text
from app.services.graph_service import calculate_company_graph
from .loader import engine
import json
from psycopg2.extras import execute_values
import time

logger = logging.getLogger(__name__)

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
        
        # We process companies that have at least one member connection (either as owner or subsidiary)
        # to avoid wasting time on completely isolated companies
        query = text("""
            SELECT DISTINCT c.regcode 
            FROM companies c
            JOIN persons p ON p.company_regcode = c.regcode OR p.legal_entity_regcode = c.regcode
            WHERE p.role = 'member'
        """)
        
        companies = conn.execute(query).fetchall()
        total_count = len(companies)
        logger.info(f"Found {total_count} companies with connections to process.")
        
        batch_size = 100
        batch_data = []
        
        
        # Parallel processing setup
        max_workers = 10
        logger.info(f"Starting parallel processing with {max_workers} workers...")
        
        batch_size = 100
        batch_data = [] # Buffer for main thread
        total_processed = 0
        
        start_time = time.time()
        
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def process_one_company(regcode):
            """Worker function to process a single company"""
            # Create NEW connection per thread to avoid race conditions
            with engine.connect() as thread_conn:
                try:
                    return regcode, calculate_company_graph(thread_conn, regcode, year=2024)
                except Exception as e:
                    return regcode, None

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_regcode = {executor.submit(process_one_company, row.regcode): row.regcode for row in companies}
            
            for future in as_completed(future_to_regcode):
                regcode, graph = future.result()
                
                if graph:
                    batch_data.append((regcode, json.dumps(graph)))
                
                # Batch upsert in main thread
                if len(batch_data) >= batch_size:
                    _upsert_batch(conn, batch_data)
                    total_processed += len(batch_data)
                    batch_data = []
                    
                    elapsed = time.time() - start_time
                    rate = total_processed / elapsed
                    remaining = (total_count - total_processed) / rate if rate > 0 else 0
                    logger.info(f"Processed {total_processed}/{total_count} ({rate:.1f} comp/sec). ETA: {remaining/60:.1f} min")
        
        # Flush remaining
        if batch_data:
            _upsert_batch(conn, batch_data)
            
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
