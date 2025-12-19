import pandas as pd
import logging
from .loader import load_to_db

logger = logging.getLogger(__name__)

def process_companies(register_path: str, equity_path: str):
    logger.info("Processing Companies...")
    
    # 1. Load Register
    # Use generic types to avoid dtypes warning, clean later
    df_reg = pd.read_csv(register_path, sep=';', dtype=str)
    
    # Rename columns to match DB schema
    # Expected CSV columns: regcode, name, address, type_text, registered, terminated, ...
    # DB: regcode, name, address, registration_date, status, sepa_identifier, company_size_badge
    
    df_reg = df_reg.rename(columns={
        'regcode': 'regcode',
        'name': 'name',
        'address': 'address',
        'registered': 'registration_date',
        'type_text': 'company_size_badge', # Using type as badge placeholder for now, or calculate later
        'sepa': 'sepa_identifier'
    })

    # Status logic
    # If 'terminated' has a date, status = 'liquidated'. Else 'active'.
    df_reg['status'] = df_reg['terminated'].apply(lambda x: 'liquidated' if pd.notna(x) and x != '' else 'active')

    # Convert registration_date to clean date (YYYY-MM-DDT...)
    df_reg['registration_date'] = pd.to_datetime(df_reg['registration_date'], errors='coerce').dt.date

    # Ensure regcode is numeric
    df_reg['regcode'] = pd.to_numeric(df_reg['regcode'], errors='coerce')
    df_reg = df_reg.dropna(subset=['regcode']) # Drop invalid regcodes

    # Drop rows without name (constraint: keys must have names)
    df_reg['name'] = df_reg['name'].replace('', pd.NA)
    df_reg = df_reg.dropna(subset=['name'])

    # Select columns for DB
    cols_to_keep = ['regcode', 'name', 'address', 'registration_date', 'status', 'sepa_identifier']
    # Check if they exist
    for col in cols_to_keep:
        if col not in df_reg.columns:
            df_reg[col] = None
            
    df_final = df_reg[cols_to_keep].copy()
    
    # remove duplicates
    df_final = df_final.drop_duplicates(subset=['regcode'])

    # Load to DB
    # Note: 'equity_capitals' could be merged here to add more info, but current schema doesn't strictly require it 
    # unless we want to calculate company_size_badge based on capital.
    # For now, we load basic company info.
    
    load_to_db(df_final, 'companies')
