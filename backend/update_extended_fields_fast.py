"""
Optimized Incremental ETL Update - Smaller Batches
Much faster with 500-record batches instead of 5000
"""
import pandas as pd
import numpy as np
import logging
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set. Check your .env file.")

engine = create_engine(DATABASE_URL)

# Smaller, local CSVs or skip download if too slow
BALANCE_SHEETS_URL = "https://data.gov.lv/dati/dataset/8d31b878-536a-44aa-a013-8bc6b669d477/resource/50ef4f26-f410-4007-b296-22043ca3dc43/download/balance_sheets.csv"
INCOME_STATEMENTS_URL = "https://data.gov.lv/dati/dataset/8d31b878-536a-44aa-a013-8bc6b669d477/resource/d5fd17ef-d32e-40cb-8399-82b780095af0/download/income_statements.csv"
FINANCIAL_STATEMENTS_URL = "https://data.gov.lv/dati/dataset/8d31b878-536a-44aa-a013-8bc6b669d477/resource/27fcc5ec-c63b-4bfd-bb08-01f073a52d04/download/financial_statements.csv"

def update_extended_fields_fast():
    """
    FAST incremental update with smaller batches (500 instead of 5000)
    """
    logger.info("🔄 Starting FAST Incremental Update...")
    
    try:
        CHUNK_SIZE = 10000  # Read 10k at a time
        BATCH_SIZE = 500    # Update 500 at a time (10x smaller!)
        
        # Step 1: Load minimal statement mappings
        logger.info("📥 Loading financial statements (this may take a few minutes)...")
        df_stm = pd.read_csv(FINANCIAL_STATEMENTS_URL, sep=';', dtype=str, usecols=['id', 'legal_entity_registration_number', 'year'])
        
        df_stm = df_stm.rename(columns={
            'id': 'statement_id',
            'legal_entity_registration_number': 'company_regcode',
            'year': 'year'
        })
        
        for col in ['company_regcode', 'year']:
            df_stm[col] = pd.to_numeric(df_stm[col], errors='coerce')
        
        df_stm = df_stm.dropna(subset=['statement_id', 'company_regcode', 'year'])
        logger.info(f"✅ Loaded {len(df_stm)} statement mappings")
        
        # Step 2: Process balance sheets in chunks
        logger.info("📥 Processing balance sheets...")
        
        total_updated = 0
        chunk_num = 0
        
        with engine.connect() as conn:
            for bal_chunk in pd.read_csv(BALANCE_SHEETS_URL, sep=';', dtype=str, chunksize=CHUNK_SIZE):
                chunk_num += 1
                logger.info(f"📊 Processing balance chunk {chunk_num}...")
                
                # Extract only needed columns
                needed_cols = ['statement_id', 'accounts_receivable', 'debtori', 'receivables']
                available_cols = [c for c in needed_cols if c in bal_chunk.columns]
                
                if 'statement_id' not in available_cols:
                    continue
                
                df_bal = bal_chunk[available_cols].copy()
                
                # Merge accounts_receivable columns
                if 'accounts_receivable' not in df_bal.columns:
                    if 'debtori' in df_bal.columns:
                        df_bal['accounts_receivable'] = df_bal['debtori']
                    elif 'receivables' in df_bal.columns:
                        df_bal['accounts_receivable'] = df_bal['receivables']
                
                df_bal['accounts_receivable'] = pd.to_numeric(df_bal.get('accounts_receivable'), errors='coerce')
                
                # Merge with statements
                df_update = pd.merge(df_stm, df_bal[['statement_id', 'accounts_receivable']], on='statement_id', how='inner')
                df_update = df_update.dropna(subset=['accounts_receivable'])
                
                if len(df_update) == 0:
                    continue
                
                # Update in SMALL batches
                for batch_start in range(0, len(df_update), BATCH_SIZE):
                    batch = df_update.iloc[batch_start:batch_start + BATCH_SIZE]
                    
                    update_data = [
                        {
                            'regcode': int(row['company_regcode']),
                            'year': int(row['year']),
                            'accounts_receivable': float(row['accounts_receivable']) if pd.notna(row['accounts_receivable']) else None
                        }
                        for _, row in batch.iterrows()
                    ]
                    
                    if update_data:
                        conn.execute(
                            text("""
                                UPDATE financial_reports 
                                SET accounts_receivable = :accounts_receivable
                                WHERE company_regcode = :regcode AND year = :year
                            """),
                            update_data
                        )
                        conn.commit()
                        total_updated += len(update_data)
                        
                        if total_updated % 5000 == 0:
                            logger.info(f"  ✅ Updated {total_updated} records so far...")
        
        logger.info(f"✅ Update complete! Updated {total_updated} records with accounts_receivable.")
        
        # Verify
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(accounts_receivable) as has_ar
                FROM financial_reports
            """))
            stats = result.fetchone()
            logger.info(f"""
            📊 Final Statistics:
            - Total financial records: {stats[0]}
            - Records with accounts_receivable: {stats[1]} ({100*stats[1]/stats[0]:.1f}%)
            """)
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise

if __name__ == '__main__':
    update_extended_fields_fast()
