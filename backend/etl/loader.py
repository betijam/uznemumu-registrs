import os
import pandas as pd
from sqlalchemy import create_engine, text
import logging

logger = logging.getLogger(__name__)

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
                  Ja False - tikai pie vieno datus (APPEND režīms).
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
            
            # Sadalam mazākos batch (500 rows) ar commit starp katru
            # Lai izvairītos no Railway timeout (60s)
            batch_size = 500
            total_rows = len(df)
            
            # Determine if we should use ON CONFLICT for this table
            use_upsert = table_name == 'financial_reports' and not truncate
            
            for i in range(0, total_rows, batch_size):
                batch_df = df.iloc[i:i+batch_size]
                
                # Katram batch - jauna transakcija
                trans = conn.begin()
                try:
                    if use_upsert:
                        # Use raw SQL with ON CONFLICT for financial_reports
                        # This handles duplicates across chunks
                        cols = list(batch_df.columns)
                        col_str = ', '.join(cols)
                        placeholders = ', '.join([f':{col}' for col in cols])
                        
                        update_set = ','.join([f"{col} = EXCLUDED.{col}" for col in cols if col not in ['company_regcode', 'year']])
                        
                        sql = text(f"""
                            INSERT INTO {table_name} ({col_str})
                            VALUES ({placeholders})
                            ON CONFLICT (company_regcode, year)
                            DO UPDATE SET {update_set}
                        """)
                        
                        # Execute for each row in batch
                        for _, row in batch_df.iterrows():
                            conn.execute(sql, row.to_dict())
                    else:
                        # Standard pandas to_sql for other tables
                        batch_df.to_sql(
                            table_name, 
                            conn, 
                            if_exists='append', 
                            index=False, 
                            method='multi'
                        )
                    trans.commit()
                    
                    if (i + batch_size) % 5000 == 0 or (i + batch_size) >= total_rows:
                        logger.info(f"  Loaded {min(i + batch_size, total_rows)}/{total_rows} rows...")
                        
                except Exception as e:
                    trans.rollback()
                    logger.error(f"Batch {i}-{i+batch_size} failed: {e}")
                    raise e
            
            logger.info(f"✅ {table_name}: All {total_rows} rows loaded successfully.")
            
    except Exception as e:
        logger.error(f"Failed to load {table_name}: {e}")
        raise
