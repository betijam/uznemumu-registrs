import pandas as pd
import numpy as np
import logging
from .loader import load_to_db, engine
from sqlalchemy import text

logger = logging.getLogger(__name__)

def calculate_financial_ratios(df):
    """
    Calculate financial health ratios from balance sheet and income statement data.
    Handles division by zero and missing data gracefully.
    """
    logger.info("Calculating financial ratios...")
    
    # Liquidity Ratios
    df['current_ratio'] = np.where(
        (df['current_liabilities'].notna()) & (df['current_liabilities'] > 0),
        df['total_current_assets'] / df['current_liabilities'],
        None
    )
    
    df['quick_ratio'] = np.where(
        (df['current_liabilities'].notna()) & (df['current_liabilities'] > 0),
        (df['total_current_assets'] - df['inventories'].fillna(0)) / df['current_liabilities'],
        None
    )
    
    df['cash_ratio'] = np.where(
        (df['current_liabilities'].notna()) & (df['current_liabilities'] > 0),
        df['cash_balance'] / df['current_liabilities'],
        None
    )
    
    # Profitability Ratios
    df['net_profit_margin'] = np.where(
        (df['turnover'].notna()) & (df['turnover'] > 0),
        (df['profit'] / df['turnover']) * 100,
        None
    )
    
    df['roe'] = np.where(
        (df['equity'].notna()) & (df['equity'] > 0),
        (df['profit'] / df['equity']) * 100,
        None
    )
    
    df['roa'] = np.where(
        (df['total_assets'].notna()) & (df['total_assets'] > 0),
        (df['profit'] / df['total_assets']) * 100,
        None
    )
    
    # Solvency Ratios
    total_liabilities = (df['current_liabilities'].fillna(0) + 
                         df['non_current_liabilities'].fillna(0))
    
    df['debt_to_equity'] = np.where(
        (df['equity'].notna()) & (df['equity'] > 0),
        total_liabilities / df['equity'],
        None
    )
    
    df['equity_ratio'] = np.where(
        (df['total_assets'].notna()) & (df['total_assets'] > 0),
        (df['equity'] / df['total_assets']) * 100,
        None
    )
    
    # EBITDA Calculation
    # EBITDA = Net Income + Taxes + Interest + Depreciation
    df['ebitda'] = (
        df['profit'].fillna(0) + 
        df['provision_for_income_taxes'].fillna(0) + 
        df['interest_expenses'].fillna(0) + 
        df['depreciation_expenses'].fillna(0)
    )
    
    # Set EBITDA to None if profit is None (no data)
    df.loc[df['profit'].isna(), 'ebitda'] = None
    
    logger.info(f"Ratios calculated: {df['current_ratio'].notna().sum()} records with current_ratio")
    
    return df


def process_finance(statements_path: str, balance_path: str, income_path: str):
    """
    Process financial data with CHUNKED LOADING to prevent memory issues.
    
    This function loads large CSV files (1.8M+ rows) in chunks to avoid OOM errors.
    """
    logger.info("🔄 Processing Finance with Chunked Loading (Memory-Optimized)...")

    try:
        CHUNK_SIZE = 50000  # Process 50k rows at a time
        
        # --- 1. Load Financial Statements (Headers) - Small file, load fully ---
        logger.info("Loading financial statements headers...")
        df_stm = pd.read_csv(statements_path, sep=';', dtype=str)
        logger.info(f"Loaded {len(df_stm)} financial statements")
        
        df_stm = df_stm.rename(columns={
            'id': 'statement_id',
            'legal_entity_registration_number': 'company_regcode', 
            'year': 'year',
            'employees': 'employees'
        })
        
        base_cols = ['statement_id', 'company_regcode', 'year', 'employees']
        for c in base_cols:
            if c not in df_stm.columns:
                df_stm[c] = None
                
        df_stm = df_stm[base_cols].copy()
        
        # Convert to numeric
        for col in ['year', 'company_regcode', 'employees']:
            if col in df_stm.columns:
                df_stm[col] = pd.to_numeric(df_stm[col], errors='coerce')

        # --- 2. Build Income Data Dictionary (Chunked) ---
        logger.info(f"Loading income statements in chunks of {CHUNK_SIZE}...")
        income_data = {}  # statement_id -> {turnover, profit, ...}
        
        try:
            chunk_num = 0
            for inc_chunk in pd.read_csv(income_path, sep=';', dtype=str, chunksize=CHUNK_SIZE):
                chunk_num += 1
                
                # Column mapping for income statement
                income_mapping = {
                    'net_turnover': 'turnover',
                    'neto_apgrozijums': 'turnover',
                    'net_income': 'profit',
                    'net_profit': 'profit',
                    'neto_pelna': 'profit',
                    'interest_expenses': 'interest_expenses',
                    'procenti': 'interest_expenses',
                    'by_nature_depreciation_expenses': 'depreciation_expenses',
                    'amortizacija': 'depreciation_expenses',
                    'provision_for_income_taxes': 'provision_for_income_taxes',
                    'nodokli': 'provision_for_income_taxes'
                }
                
                # Extract relevant columns
                for idx, row in inc_chunk.iterrows():
                    if 'statement_id' not in row:
                        continue
                    
                    stmt_id = row['statement_id']
                    income_data[stmt_id] = {}
                    
                    for csv_col, our_col in income_mapping.items():
                        if csv_col in row:
                            income_data[stmt_id][our_col] = pd.to_numeric(row[csv_col], errors='coerce')
                
                if chunk_num % 10 == 0:
                    logger.info(f"  Processed income chunk {chunk_num} ({len(income_data)} statements so far)")
            
            logger.info(f"✅ Loaded income data for {len(income_data)} statements")
                    
        except Exception as e:
            logger.warning(f"Could not process Income Statement: {e}")
            income_data = {}

        # --- 3. Process Balance Sheets in Chunks and Merge/Load Incrementally ---
        logger.info(f"Processing balance sheets in chunks of {CHUNK_SIZE}...")
        
        # Get existing company regcodes for validation
        with engine.connect() as conn:
            result = conn.execute(text("SELECT regcode FROM companies"))
            existing_regcodes = set(row[0] for row in result)
        
        logger.info(f"Found {len(existing_regcodes)} existing companies for validation")
        
        is_first_chunk = True
        chunk_num = 0
        total_loaded = 0
        
        try:
            for bal_chunk in pd.read_csv(balance_path, sep=';', dtype=str, chunksize=CHUNK_SIZE):
                chunk_num += 1
                logger.info(f"📊 Processing balance sheet chunk {chunk_num} ({len(bal_chunk)} rows)...")
                
                # Column mapping for balance sheet
                balance_mapping = {
                    'total_assets': 'total_assets',
                    'total_current_assets': 'total_current_assets',
                    'cash': 'cash_balance',
                    'inventories': 'inventories',
                    'current_liabilities': 'current_liabilities',
                    'non_current_liabilities': 'non_current_liabilities',
                    'equity': 'equity'
                }
                
                bal_cols = ['statement_id']
                rename_map = {}
                
                for csv_col, our_col in balance_mapping.items():
                    if csv_col in bal_chunk.columns:
                        bal_cols.append(csv_col)
                        rename_map[csv_col] = our_col
                
                if len(bal_cols) > 1:
                    df_bal_subset = bal_chunk[bal_cols].copy()
                    df_bal_subset = df_bal_subset.rename(columns=rename_map)
                    
                    # Convert to numeric
                    for col in ['total_assets', 'total_current_assets', 'cash_balance', 'inventories',
                               'current_liabilities', 'non_current_liabilities', 'equity']:
                        if col in df_bal_subset.columns:
                            df_bal_subset[col] = pd.to_numeric(df_bal_subset[col], errors='coerce')
                else:
                    df_bal_subset = bal_chunk[['statement_id']].copy()
                    for col in ['total_assets', 'total_current_assets', 'cash_balance', 'inventories',
                               'current_liabilities', 'non_current_liabilities', 'equity']:
                        df_bal_subset[col] = None
                
                # Merge with statements
                df_merged = pd.merge(df_stm, df_bal_subset, on='statement_id', how='inner')
                
                # Add income data
                for col in ['turnover', 'profit', 'interest_expenses', 'depreciation_expenses', 'provision_for_income_taxes']:
                    df_merged[col] = df_merged['statement_id'].map(
                        lambda x: income_data.get(x, {}).get(col)
                    )
                
                # Calculate financial ratios
                df_merged = calculate_financial_ratios(df_merged)
                
                # Add taxes_paid placeholder (populated by VID data separately)
                df_merged['taxes_paid'] = None
                
                # Cleanup
                df_merged = df_merged.dropna(subset=['company_regcode', 'year'])
                
                # Deduplication within chunk
                if 'statement_id' in df_merged.columns:
                    df_merged = df_merged.sort_values('statement_id')
                    df_merged = df_merged.drop_duplicates(subset=['company_regcode', 'year'], keep='last')
                
                # Validate foreign keys (only keep records for existing companies)
                df_merged = df_merged[df_merged['company_regcode'].isin(existing_regcodes)]
                
                # Final columns selection
                final_cols = [
                    'company_regcode', 'year', 'employees', 'taxes_paid',
                    # Income Statement
                    'turnover', 'profit', 'interest_expenses', 'depreciation_expenses', 'provision_for_income_taxes',
                    # Balance Sheet
                    'total_assets', 'total_current_assets', 'cash_balance', 'inventories',
                    'current_liabilities', 'non_current_liabilities', 'equity',
                    # Calculated Ratios
                    'ebitda', 'current_ratio', 'quick_ratio', 'cash_ratio',
                    'net_profit_margin', 'roe', 'roa', 'debt_to_equity', 'equity_ratio'
                ]
                
                df_merged = df_merged[final_cols]
                
                if len(df_merged) > 0:
                    # Load to DB (truncate only on first chunk, append for rest)
                    load_to_db(df_merged, 'financial_reports', truncate=is_first_chunk)
                    is_first_chunk = False
                    total_loaded += len(df_merged)
                    logger.info(f"  ✅ Chunk {chunk_num}: Loaded {len(df_merged)} records (Total: {total_loaded})")
                else:
                    logger.info(f"  ⚠️  Chunk {chunk_num}: No valid records to load")
        
        except Exception as e:
            logger.error(f"Error processing balance sheet chunks: {e}")
            raise
        
        logger.info(f"✅ Financial data processing complete: {total_loaded} total records loaded")
            
    except Exception as e:
        logger.error(f"Error processing finance: {e}")
        raise

