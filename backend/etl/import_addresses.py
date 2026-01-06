import os
import sys
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import logging

# Add parent directory to path so we can import from etl
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.config import ADDRESS_URLS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/ur_db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

TEMP_DIR = "temp_addresses"

def download_file(url, key):
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR, exist_ok=True)
    
    filename = f"{key}.csv"
    filepath = os.path.join(TEMP_DIR, filename)
    
    logger.info(f"Downloading {key} from {url}...")
    try:
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"Downloaded {key} to {filepath}")
        return key, filepath
    except Exception as e:
        logger.error(f"Failed to download {key}: {e}")
        return key, None

def load_csv_to_stage(key, filepath):
    if not filepath:
        return
    
    table_name = f"stage.{key}"
    logger.info(f"Loading {filepath} into {table_name}...")
    
    try:
        # Use pandas to load CSV and handle column mapping
        import pandas as pd
        
        # Read CSV with COMMA delimiter (not tab!)
        # Try UTF-8 first (most common), fallback to Windows-1257 if needed
        try:
            df = pd.read_csv(filepath, sep=',', encoding='utf-8', dtype=str, low_memory=False)
        except (UnicodeDecodeError, pd.errors.ParserError):
            try:
                df = pd.read_csv(filepath, sep=',', encoding='windows-1257', dtype=str, low_memory=False)
            except:
                df = pd.read_csv(filepath, sep=',', encoding='iso-8859-1', dtype=str, low_memory=False)
        
        # Actual CSV columns: KODS, TIPS_CD, STATUSS, APSTIPR, APST_PAK, VKUR_CD, VKUR_TIPS, NOSAUKUMS, SORT_NOS, ATRIB, DAT_SAK, DAT_MOD, DAT_BEIG, STD
        # We need to map these to our expected schema
        column_mapping = {
            'KODS': 'objekta_kods',
            'TIPS_CD': 'objekta_tips',
            'DAT_SAK': 'registrets',
            'DAT_MOD': 'aktualizets',
            'DAT_BEIG': 'beigu_datums',
            'STD': 'adrese',
            'NOSAUKUMS': 'nosaukums',
            'VKUR_CD': 'augst_objekta_kods',
            'VKUR_TIPS': 'augst_objekta_tips'
        }
        
        # Select only the columns we need
        df = df[[col for col in column_mapping.keys() if col in df.columns]].copy()
        df = df.rename(columns=column_mapping)
        
        # Load to database using SQLAlchemy
        with engine.connect() as conn:
            # Truncate first
            conn.execute(text(f"TRUNCATE TABLE {table_name}"))
            conn.commit()
            
            # Batch insert for large datasets
            batch_size = 10000
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]
                batch.to_sql(
                    table_name.split('.')[-1],  # table name without schema
                    conn,
                    schema='stage',
                    if_exists='append',
                    index=False,
                    method='multi'
                )
                if (i + batch_size) % 50000 == 0 or (i + batch_size) >= len(df):
                    logger.info(f"  Loaded {min(i + batch_size, len(df))}/{len(df)} rows...")
        
        logger.info(f"Loaded {table_name} ({len(df)} rows)")
    except Exception as e:
        logger.error(f"Failed to load {table_name}: {e}")
        raise

def main():
    start_time = time.time()
    
    # 0. Setup Database Schema
    logger.info("Applying database schema...")
    try:
        with engine.connect() as conn:
            # Read and execute the SQL file
            schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db", "addresses.sql")
            with open(schema_path, "r", encoding="utf-8") as f:
                sql_content = f.read()
                # Execute in a transaction
                conn.execute(text(sql_content))
                conn.commit()
        logger.info("Schema applied successfully")
    except Exception as e:
        logger.error(f"Schema application failed: {e}")
        return

    # 1. Download Files
    logger.info("Starting downloads...")
    files_map = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(download_file, url, key): key for key, url in ADDRESS_URLS.items()}
        for future in futures:
            key, filepath = future.result()
            if filepath:
                files_map[key] = filepath
    
    # 2. Load Staging Tables
    logger.info("Loading staging tables...")
    for key, filepath in files_map.items():
        load_csv_to_stage(key, filepath)
    
    # 3. Refresh Dimension
    logger.info("Refreshing address dimension (this might take a while)...")
    try:
        with engine.connect() as conn:
            conn.execute(text("CALL core.refresh_address_dimension();"))
            conn.commit()
        logger.info("Address dimension refreshed successfully.")
    except Exception as e:
        logger.error(f"Failed to refresh dimension: {e}")
    
    # 4. Cleanup (optional)
    # import shutil
    # shutil.rmtree(TEMP_DIR)
    
    logger.info(f"Address ETL completed in {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
