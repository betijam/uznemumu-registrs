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
    logger.info("Processing Finance with Enhanced Ratios...")

    try:
        # --- 1. Load Financial Statements (Headers) ---
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
                
        df_final = df_stm[base_cols].copy()

        # --- 2. Load Income Statements (Enhanced) ---
        try:
            df_inc = pd.read_csv(income_path, sep=';', dtype=str)
            logger.info(f"Loaded income statements with {len(df_inc.columns)} columns")
            
            # Column mapping for income statement
            income_mapping = {
                # Turnover
                'net_turnover': 'turnover',
                'neto_apgrozijums': 'turnover',
                # Profit
                'net_income': 'profit',
                'net_profit': 'profit',
                'neto_pelna': 'profit',
                # Interest expenses
                'interest_expenses': 'interest_expenses',
                'procenti': 'interest_expenses',
                # Depreciation
                'by_nature_depreciation_expenses': 'depreciation_expenses',
                'amortizacija': 'depreciation_expenses',
                # Taxes
                'provision_for_income_taxes': 'provision_for_income_taxes',
                'nodokli': 'provision_for_income_taxes'
            }
            
            # Find and rename columns
            inc_cols = ['statement_id']
            rename_map = {}
            
            for csv_col, our_col in income_mapping.items():
                if csv_col in df_inc.columns:
                    inc_cols.append(csv_col)
                    rename_map[csv_col] = our_col
            
            if len(inc_cols) > 1:
                df_inc_subset = df_inc[inc_cols].copy()
                df_inc_subset = df_inc_subset.rename(columns=rename_map)
                
                # Convert to numeric
                for col in ['turnover', 'profit', 'interest_expenses', 'depreciation_expenses', 'provision_for_income_taxes']:
                    if col in df_inc_subset.columns:
                        df_inc_subset[col] = pd.to_numeric(df_inc_subset[col], errors='coerce')
                
                df_final = pd.merge(df_final, df_inc_subset, on='statement_id', how='left')
                logger.info(f"Merged income data - {df_final['turnover'].notna().sum()} records with turnover")
            else:
                logger.warning("No income statement columns found")
                for col in ['turnover', 'profit', 'interest_expenses', 'depreciation_expenses', 'provision_for_income_taxes']:
                    df_final[col] = None
                    
        except Exception as e:
            logger.warning(f"Could not process Income Statement: {e}")
            for col in ['turnover', 'profit', 'interest_expenses', 'depreciation_expenses', 'provision_for_income_taxes']:
                df_final[col] = None

        # --- 3. Load Balance Sheet (Enhanced) ---
        try:
            df_bal = pd.read_csv(balance_path, sep=';', dtype=str)
            logger.info(f"Loaded balance sheets with {len(df_bal.columns)} columns")
            
            # Column mapping for balance sheet - using EXACT CSV column names
            balance_mapping = {
                # Assets
                'total_assets': 'total_assets',
                'total_current_assets': 'total_current_assets',
                # Cash
                'cash': 'cash_balance',
                # Inventories
                'inventories': 'inventories',
                # Liabilities
                'current_liabilities': 'current_liabilities',
                'non_current_liabilities': 'non_current_liabilities',
                # Equity
                'equity': 'equity'
            }
            
            bal_cols = ['statement_id']
            rename_map = {}
            
            for csv_col, our_col in balance_mapping.items():
                if csv_col in df_bal.columns:
                    bal_cols.append(csv_col)
                    rename_map[csv_col] = our_col
            
            if len(bal_cols) > 1:
                df_bal_subset = df_bal[bal_cols].copy()
                df_bal_subset = df_bal_subset.rename(columns=rename_map)
                
                # Convert to numeric
                for col in ['total_assets', 'total_current_assets', 'cash_balance', 'inventories',
                           'current_liabilities', 'non_current_liabilities', 'equity']:
                    if col in df_bal_subset.columns:
                        df_bal_subset[col] = pd.to_numeric(df_bal_subset[col], errors='coerce')
                
                df_final = pd.merge(df_final, df_bal_subset, on='statement_id', how='left')
                logger.info(f"Merged balance data - {df_final['total_assets'].notna().sum()} records with assets")
            else:
                logger.warning("No balance sheet columns found")
                for col in ['total_assets', 'total_current_assets', 'cash_balance', 'inventories',
                           'current_liabilities', 'non_current_liabilities', 'equity']:
                    df_final[col] = None
                    
        except Exception as e:
            logger.warning(f"Could not process Balance Sheet: {e}")
            for col in ['total_assets', 'total_current_assets', 'cash_balance', 'inventories',
                       'current_liabilities', 'non_current_liabilities', 'equity']:
                df_final[col] = None

        # --- 4. Calculate Financial Ratios ---
        df_final = calculate_financial_ratios(df_final)

        # --- 5. Cleanup & Types ---
        numeric_cols = ['year', 'company_regcode', 'employees']
        for col in numeric_cols:
            if col in df_final.columns:
                df_final[col] = pd.to_numeric(df_final[col], errors='coerce')
        
        # taxes_paid is from VID data (separate)
        df_final['taxes_paid'] = None

        logger.info(f"Before dropna: {len(df_final)} records")
        df_final = df_final.dropna(subset=['company_regcode', 'year'])
        logger.info(f"After dropna: {len(df_final)} records")
        
        # Deduplication
        if 'statement_id' in df_final.columns:
            df_final = df_final.sort_values('statement_id')
            df_final = df_final.drop_duplicates(subset=['company_regcode', 'year'], keep='last')
            logger.info(f"After deduplication: {len(df_final)} records")

        # --- 6. Validate Foreign Keys ---
        logger.info("Validating financial records against existing companies...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT regcode FROM companies"))
            existing_regcodes = set(row[0] for row in result)
        
        initial_count = len(df_final)
        df_final = df_final[df_final['company_regcode'].isin(existing_regcodes)]
        filtered_count = initial_count - len(df_final)
        
        if filtered_count > 0:
            logger.warning(f"Filtered out {filtered_count} financial records with non-existent companies")
        
        logger.info(f"Proceeding with {len(df_final)} valid financial records")

        # --- 7. Final columns selection ---
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
        
        df_final = df_final[final_cols]
        
        logger.info(f"Final: {len(df_final)} records, {df_final['current_ratio'].notna().sum()} with ratios")
            
        load_to_db(df_final, 'financial_reports')

    except Exception as e:
        logger.error(f"Error processing finance: {e}")
        raise
