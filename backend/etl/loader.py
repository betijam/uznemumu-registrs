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
        unique_columns: (Netiek izmantots šobrīd)
        truncate: Ja True - izdzēš esošos datus pirms ielādes. 
                  Ja False - tikai pievieno datus (APPEND režīms).
    """
    if df.empty:
        logger.warning(f"DataFrame for {table_name} is empty. Skipping load.")
        return

    conn = None
    try:
        # Atveram savienojumu manuāli
        with engine.connect() as conn:
            # Sākam transakciju
            trans = conn.begin()
            
            try:
                # TRUNCATE tikai ja tas ir pieprasīts
                if truncate:
                    logger.info(f"Truncating table {table_name}...")
                    conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE;"))
                else:
                    logger.info(f"Appending to table {table_name} (no truncate)...")
                
                logger.info(f"Loading {len(df)} rows into {table_name}...")
                
                # Samazinām chunksize uz 2000 (drošāk method='multi' gadījumā)
                df.to_sql(
                    table_name, 
                    conn, 
                    if_exists='append', 
                    index=False, 
                    method='multi', 
                    chunksize=2000 
                )
                
                # Pārbaude PIRMS commit - vai dati tiešām ir iekšā transakcijā?
                result = conn.execute(text(f"SELECT count(*) FROM {table_name}"))
                count = result.scalar()
                logger.info(f"Pending commit: Table {table_name} has {count} rows inside transaction.")

                # MANUĀLS COMMIT
                trans.commit()
                
                logger.info(f"✅ COMMITTED successfully. {table_name} now holds data permanently.")
                
            except Exception as e:
                # Ja kaut kas noiet greizi iekšpusē, taisām rollback
                trans.rollback()
                logger.error(f"Transaction rolled back due to error: {e}")
                raise e

    except Exception as e:
        logger.error(f"Failed to establish connection or load {table_name}: {e}")
        raise
