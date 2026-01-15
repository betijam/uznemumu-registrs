
import pandas as pd
import requests
import os
import time
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Engine with connection pooling optimization
engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)

CSV_URL = "https://data.gov.lv/dati/dataset/8d31b878-536a-44aa-a013-8bc6b669d477/resource/27fcc5ec-c63b-4bfd-bb08-01f073a52d04/download/financial_statements.csv"
LOCAL_CSV = "financial_statements.csv"
BATCH_SIZE = 2000  # Number of rows to update in one SQL transaction
MAX_WORKERS = 5     # Number of parallel DB-writer threads

def download_csv():
    if os.path.exists(LOCAL_CSV):
        print(f"File {LOCAL_CSV} already exists, skipping download.")
        return
    
    print(f"Downloading {CSV_URL}...")
    start = time.time()
    response = requests.get(CSV_URL, stream=True)
    with open(LOCAL_CSV, 'wb') as f:
        for chunk in response.iter_content(chunk_size=32768):
            f.write(chunk)
    print(f"Download complete in {time.time() - start:.2f}s")

def process_batch(batch_data):
    """
    Executes a bulk update for a list of (regcode, year) tuples.
    """
    if not batch_data:
        return 0

    conn = engine.connect()
    try:
        # Create a VALUES string: ('4000...', 2023), ('4000...', 2024), ...
        values_list = ", ".join([
            f"('{r}', {y})" for r, y in batch_data
        ])

        # Optimized Bulk Update using UPDATE ... FROM (VALUES ...)
        query = text(f"""
            UPDATE financial_reports AS f
            SET 
                turnover = f.turnover * 1000,
                profit = f.profit * 1000,
                total_assets = f.total_assets * 1000,
                total_current_assets = f.total_current_assets * 1000,
                cash_balance = f.cash_balance * 1000,
                equity = f.equity * 1000,
                current_liabilities = f.current_liabilities * 1000,
                non_current_liabilities = f.non_current_liabilities * 1000,
                rounded_to_nearest = 'THOUSANDS'
            FROM (VALUES {values_list}) AS v(regcode, yr)
            WHERE f.company_regcode = v.regcode::bigint 
              AND f.year = v.yr::int
              AND (f.rounded_to_nearest IS NULL OR f.rounded_to_nearest != 'THOUSANDS');
        """)
        
        result = conn.execute(query)
        conn.commit()
        return result.rowcount
    except Exception as e:
        print(f"⚠️ Batch error: {e}")
        return 0
    finally:
        conn.close()

def fix_thousands_optimized():
    print(f"🚀 Starting OPTIMIZED fix (Workers: {MAX_WORKERS}, Batch: {BATCH_SIZE})...")
    start_time = time.time()
    
    total_records_processed = 0
    total_updated_db = 0
    
    # We will accumulate items here until we hit BATCH_SIZE
    current_batch = [] 
    
    futures = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Read CSV in large chunks
        for chunk in pd.read_csv(LOCAL_CSV, sep=';', dtype=str, chunksize=50000):
            if 'rounded_to_nearest' not in chunk.columns:
                print("❌ Error: 'rounded_to_nearest' column missing in CSV!")
                return

            # Filter efficiently in memory
            # We only care about rows where rounded_to_nearest IS 'THOUSANDS'
            target_rows = chunk[chunk['rounded_to_nearest'] == 'THOUSANDS']
            
            if target_rows.empty:
                continue

            for _, row in target_rows.iterrows():
                regcode = row.get('legal_entity_registration_number')
                year = row.get('year')
                
                if regcode and year:
                    current_batch.append((regcode, year))
                    
                    if len(current_batch) >= BATCH_SIZE:
                        # Submit batch to worker
                        futures.append(executor.submit(process_batch, list(current_batch)))
                        current_batch = [] # Reset
            
            total_records_processed += len(chunk)
            print(f"Scanning CSV... {total_records_processed} rows read.", end='\r')

        # Submit remaining items
        if current_batch:
            futures.append(executor.submit(process_batch, current_batch))

        print(f"\nCSV Scan complete. Waiting for DB updates to finish...")
        
        # Aggregate results
        for future in as_completed(futures):
            res = future.result()
            total_updated_db += res
            print(f"✅ Batch finished. Updated {res} rows. (Total: {total_updated_db})", end='\r')

    elapsed = time.time() - start_time
    print(f"\n\n🏁 DONE! script finished in {elapsed:.2f}s")
    print(f"   - Total records updated in DB: {total_updated_db}")

if __name__ == "__main__":
    download_csv()
    fix_thousands_optimized()
