"""
Incremental ETL Update: Populate Extended Financial Fields
This script ONLY updates the new columns without re-importing all financial data.
Much faster than full ETL re-run.

Usage: python update_extended_fields.py
"""
import pandas as pd
import numpy as np
import logging
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get database URL
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set. Check your .env file.")

engine = create_engine(DATABASE_URL)

# Data source URLs (from config.py)
BALANCE_SHEETS_URL = "https://data.gov.lv/dati/dataset/8d31b878-536a-44aa-a013-8bc6b669d477/resource/50ef4f26-f410-4007-b296-22043ca3dc43/download/balance_sheets.csv"
INCOME_STATEMENTS_URL = "https://data.gov.lv/dati/dataset/8d31b878-536a-44aa-a013-8bc6b669d477/resource/d5fd17ef-d32e-40cb-8399-82b780095af0/download/income_statements.csv"
FINANCIAL_STATEMENTS_URL = "https://data.gov.lv/dati/dataset/8d31b878-536a-44aa-a013-8bc6b669d477/resource/27fcc5ec-c63b-4bfd-bb08-01f073a52d04/download/financial_statements.csv"

def update_extended_fields():
    """
    Incrementally update ONLY the new financial fields without touching existing data
    """
    logger.info("🔄 Starting Incremental Update for Extended Financial Fields...")
    
    CHUNK_SIZE = 50000
    
    # Step 1: Load statement ID mappings (small file)
    logger.info("📥 Loading financial statements headers...")
    df_stm = pd.read_csv(FINANCIAL_STATEMENTS_URL, sep=';', dtype=str)
    logger.info(f"Loaded {len(df_stm)} statements")
    
    df_stm = df_stm.rename(columns={
        'id': 'statement_id',
        'legal_entity_registration_number': 'company_regcode',
        'year': 'year'
    })
    
    for col in ['company_regcode', 'year']:
        df_stm[col] = pd.to_numeric(df_stm[col], errors='coerce')
    
    df_stm = df_stm[['statement_id', 'company_regcode', 'year']].dropna()
    
    # Step 2: Build Income Data Dictionary (for by_nature_labour_expenses)
    logger.info("📥 Loading income statements for labour expenses...")
    income_data = {}
    
    chunk_num = 0
    for inc_chunk in pd.read_csv(INCOME_STATEMENTS_URL, sep=';', dtype=str, chunksize=CHUNK_SIZE):
        chunk_num += 1
        
        for idx, row in inc_chunk.iterrows():
            if 'statement_id' not in row:
                continue
            
            stmt_id = row['statement_id']
            
            # Extract labour expenses
            labour_val = None
            if 'by_nature_labour_expenses' in row:
                labour_val = pd.to_numeric(row['by_nature_labour_expenses'], errors='coerce')
            elif 'darba_samaksa' in row:
                labour_val = pd.to_numeric(row['darba_samaksa'], errors='coerce')
            
            if labour_val is not None:
                income_data[stmt_id] = {'by_nature_labour_expenses': labour_val}
        
        if chunk_num % 10 == 0:
            logger.info(f"  Processed {chunk_num} income chunks...")
    
    logger.info(f"✅ Loaded labour expenses for {len(income_data)} statements")
    
    # Step 3: Process Balance Sheets and Update Database
    logger.info("📥 Processing balance sheets for accounts_receivable and cash flow...")
    
    chunk_num = 0
    total_updated = 0
    
    with engine.connect() as conn:
        for bal_chunk in pd.read_csv(BALANCE_SHEETS_URL, sep=';', dtype=str, chunksize=CHUNK_SIZE):
            chunk_num += 1
            logger.info(f"📊 Processing balance chunk {chunk_num}...")
            
            # Extract relevant fields
            fields_to_extract = {
                'statement_id': 'statement_id',
                'accounts_receivable': 'accounts_receivable',
                'debtori': 'accounts_receivable',
                'receivables': 'accounts_receivable',
                'cfo_im_net_operating_cash_flow': 'cfo_im_net_operating_cash_flow',
                'cfo_im_income_taxes_paid': 'cfo_im_income_taxes_paid',
                'cfi_acquisition_of_fixed_assets_intangible_assets': 'cfi_acquisition_of_fixed_assets_intangible_assets',
                'cff_net_financing_cash_flow': 'cff_net_financing_cash_flow'
            }
            
            # Build subset dataframe
            bal_cols = []
            rename_map = {}
            for csv_col, our_col in fields_to_extract.items():
                if csv_col in bal_chunk.columns:
                    bal_cols.append(csv_col)
                    rename_map[csv_col] = our_col
            
            if 'statement_id' not in bal_cols:
                continue
            
            df_subset = bal_chunk[bal_cols].copy()
            df_subset = df_subset.rename(columns=rename_map)
            
            # Convert to numeric
            for col in df_subset.columns:
                if col != 'statement_id':
                    df_subset[col] = pd.to_numeric(df_subset[col], errors='coerce')
            
            # Merge with statement metadata
            df_update = pd.merge(df_stm, df_subset, on='statement_id', how='inner')
            
            # Add labour expenses from income data
            df_update['by_nature_labour_expenses'] = df_update['statement_id'].map(
                lambda x: income_data.get(x, {}).get('by_nature_labour_expenses')
            )
            
            # Drop rows with no new data
            new_cols = ['accounts_receivable', 'by_nature_labour_expenses', 
                       'cfo_im_net_operating_cash_flow', 'cfo_im_income_taxes_paid',
                       'cfi_acquisition_of_fixed_assets_intangible_assets', 'cff_net_financing_cash_flow']
            
            df_update = df_update.dropna(subset=['company_regcode', 'year'])
            
            # Update database in batches using bulk operations
            if len(df_update) > 0:
                logger.info(f"  Preparing batch update for {len(df_update)} records...")
                
                # Use pandas to_sql with 'update' method for batch efficiency
                # Since to_sql doesn't support UPDATE, we'll use executemany() with batches
                
                batch_size = 5000
                updated_count = 0
                
                for batch_start in range(0, len(df_update), batch_size):
                    batch = df_update.iloc[batch_start:batch_start + batch_size]
                    
                    # Build batch update data
                    update_data = []
                    for _, row in batch.iterrows():
                        params = {
                            'regcode': int(row['company_regcode']),
                            'year': int(row['year'])
                        }
                        
                        # Add all extended fields to params
                        for col in new_cols:
                            if col in row and pd.notna(row[col]):
                                params[col] = float(row[col])
                            else:
                                params[col] = None
                        
                        update_data.append(params)
                    
                    # Execute batch update
                    if update_data:
                        update_sql = """
                            UPDATE financial_reports 
                            SET 
                                accounts_receivable = :accounts_receivable,
                                by_nature_labour_expenses = :by_nature_labour_expenses,
                                cfo_im_net_operating_cash_flow = :cfo_im_net_operating_cash_flow,
                                cfo_im_income_taxes_paid = :cfo_im_income_taxes_paid,
                                cfi_acquisition_of_fixed_assets_intangible_assets = :cfi_acquisition_of_fixed_assets_intangible_assets,
                                cff_net_financing_cash_flow = :cff_net_financing_cash_flow
                            WHERE company_regcode = :regcode AND year = :year
                        """
                        conn.execute(text(update_sql), update_data)
                        conn.commit()
                        updated_count += len(update_data)
                        logger.info(f"  ✅ Batch {batch_start//batch_size + 1}: Updated {len(update_data)} records (Total: {updated_count})")
                
                total_updated += updated_count
        
        conn.commit()
    
    logger.info(f"✅ Incremental update complete! Updated {total_updated} financial records.")
    
    # Verify
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(accounts_receivable) as has_ar,
                COUNT(by_nature_labour_expenses) as has_labour,
                COUNT(cfo_im_net_operating_cash_flow) as has_cfo
            FROM financial_reports
        """))
        stats = result.fetchone()
        logger.info(f"""
        📊 Update Statistics:
        - Total financial records: {stats[0]}
        - Records with accounts_receivable: {stats[1]}
        - Records with labour_expenses: {stats[2]}
        - Records with cash_flow: {stats[3]}
        """)

if __name__ == '__main__':
    update_extended_fields()
