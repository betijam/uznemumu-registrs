import os
import pandas as pd
from sqlalchemy import create_engine, text
from psycopg2.extras import execute_values
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env file if present
load_dotenv()

# Pārliecinies, ka .env failā ir pareizs URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/ur_db")

# Pievienojam pool_pre_ping=True, lai automātiski atjaunotu pārtrūkušus savienojumus
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def load_to_db(df: pd.DataFrame, table_name: str, unique_columns: list = None, truncate: bool = True):
    """
    Ielādē DataFrame PostgreSQL datubāzē.
    
    Args:
        df: Dati ko ielādēt
        table_name: Tabulas nosaukums
        unique_columns: Kolonas kas veido unique constraint (izmanto ON CONFLICT)
        truncate: Ja True - izdzēš esošos datus pirms ielādes. 
                  Ja False - tikai pievieno datus (APPEND režīms).
    """
    if df.empty:
        logger.warning(f"DataFrame for {table_name} is empty. Skipping load.")
        return

    try:
        with engine.connect() as conn:
            # TRUNCATE ārpus transakcijas (ātrāk)
            if truncate:
                logger.info(f"Truncating table {table_name}...")
                conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE;"))
                conn.commit()
            
            logger.info(f"Loading {len(df)} rows into {table_name}...")
            
            # Use ON CONFLICT for financial_reports with bulk insert (fast!)
            use_conflict_resolution = table_name == 'financial_reports' and not truncate
            
            if use_conflict_resolution:
                # Fast bulk insert with ON CONFLICT using execute_values
                logger.info(f"  Using ON CONFLICT DO UPDATE for {table_name}...")
                
                # Get raw connection for psycopg2
                raw_conn = conn.connection
                cursor = raw_conn.cursor()
                
                try:
                    # Prepare column names
                    cols = list(df.columns)
                    col_str = ', '.join(cols)
                    
                    # Prepare UPDATE clause (update all columns except the unique key)
                    update_cols = [c for c in cols if c not in ['company_regcode', 'year']]
                    update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_cols])
                    
                    # Convert dataframe to list of tuples
                    data = [tuple(row) for row in df.itertuples(index=False, name=None)]
                    
                    # Build SQL with ON CONFLICT
                    sql = f"""
                        INSERT INTO {table_name} ({col_str})
                        VALUES %s
                        ON CONFLICT (company_regcode, year)
                        DO UPDATE SET {update_set}
                    """
                    
                    # Execute in batches for stability
                    batch_size = 10000
                    for i in range(0, len(data), batch_size):
                        batch = data[i:i+batch_size]
                        execute_values(cursor, sql, batch, page_size=1000)
                        raw_conn.commit()
                        
                        if (i + batch_size) % 10000 == 0 or (i + batch_size) >= len(data):
                            logger.info(f"  Loaded {min(i + batch_size, len(data))}/{len(data)} rows...")
                    
                    logger.info(f"✅ {table_name}: All {len(data)} rows loaded successfully.")
                    
                finally:
                    cursor.close()
            else:
                # Standard pandas bulk insert for other tables
                # Optimized for Railway Hobby (8GB RAM)
                # Larger batches = fewer transactions = better performance
                batch_size = 10000
                total_rows = len(df)
                
                for i in range(0, total_rows, batch_size):
                    batch_df = df.iloc[i:i+batch_size]
                    
                    # Katram batch - jauna transakcija
                    trans = conn.begin()
                    try:
                        # Fast bulk insert - deduplication happens before calling this function
                        batch_df.to_sql(
                            table_name, 
                            conn, 
                            if_exists='append', 
                            index=False, 
                            method='multi'
                        )
                        trans.commit()
                        
                        if (i + batch_size) % 10000 == 0 or (i + batch_size) >= total_rows:
                            logger.info(f"  Loaded {min(i + batch_size, total_rows)}/{total_rows} rows...")
                            
                    except Exception as e:
                        trans.rollback()
                        logger.error(f"Batch {i}-{i+batch_size} failed: {e}")
                        raise e
                
                logger.info(f"✅ {table_name}: All {total_rows} rows loaded successfully.")
            
    except Exception as e:
        logger.error(f"Failed to load {table_name}: {e}")
        raise
