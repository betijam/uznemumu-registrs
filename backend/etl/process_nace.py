"""
NACE Industry Classification Processor

Processes VID tax data to extract NACE codes and employee counts,
merges with NACE reference dictionary for industry descriptions.
"""

import pandas as pd
import logging
import os
from .loader import load_to_db, engine
from sqlalchemy import text

logger = logging.getLogger(__name__)


def normalize_nace_code(nace_series: pd.Series) -> pd.Series:
    """
    Normalize NACE codes: remove dots/spaces, handle missing values.
    
    Input:  ["62.01", "47.91", None, "?", "", "A"]
    Output: ["6201", "4791", "0000", "0000", "0000", "A"]
    """
    # Convert to string and clean
    normalized = nace_series.astype(str).str.strip()
    
    # Remove dots and spaces
    normalized = normalized.str.replace('.', '', regex=False)
    normalized = normalized.str.replace(' ', '', regex=False)
    
    # Replace invalid values with "0000" (unknown industry)
    invalid_values = ['nan', 'None', '', '?', '0']
    normalized = normalized.replace(invalid_values, '0000')
    
    return normalized


def extract_section_code(nace_code: str) -> str:
    """
    Extract section code from NACE code for grouping.
    
    Examples:
        "6201" → "62"
        "A" → "A"
        "0111" → "01"
        "0000" → "00"
    """
    if not nace_code or nace_code == '0000':
        return '00'
    
    # If starts with letter, return just the letter
    if nace_code[0].isalpha():
        return nace_code[0]
    
    # Otherwise, return first 2 digits
    return nace_code[:2] if len(nace_code) >= 2 else nace_code


def load_nace_dictionary(nace_csv_path: str) -> dict:
    """
    Load NACE reference dictionary and create lookup tables.
    
    Returns: 
        dict with 'code_lookup' (code -> full description) and 
        'section_lookup' (section code -> section description)
    """
    logger.info(f"Loading NACE dictionary from {nace_csv_path}")
    
    try:
        # Load NACE CSV
        nace_df = pd.read_csv(nace_csv_path, dtype={'Kods': str})
        
        # Normalize NACE codes (remove dots)
        nace_df['Kods_normalized'] = normalize_nace_code(nace_df['Kods'])
        
        # Create code-to-description lookup
        code_lookup = dict(zip(nace_df['Kods_normalized'], nace_df['Nosaukums']))
        
        # Create section lookup (Limenis = 1 are sections like "A", "C", etc.)
        section_df = nace_df[nace_df['Limenis'] == 1].copy()
        section_lookup = dict(zip(section_df['Kods_normalized'], section_df['Nosaukums']))
        
        # Also add 2-digit divisions as sections
        division_df = nace_df[nace_df['Limenis'] == 2].copy()
        for _, row in division_df.iterrows():
            section_code = extract_section_code(row['Kods_normalized'])
            if section_code not in section_lookup and section_code != '00':
                section_lookup[section_code] = row['Nosaukums']
        
        logger.info(f"Loaded {len(code_lookup)} NACE codes and {len(section_lookup)} sections")
        
        return {
            'code_lookup': code_lookup,
            'section_lookup': section_lookup
        }
        
    except Exception as e:
        logger.error(f"Failed to load NACE dictionary: {e}")
        return {'code_lookup': {}, 'section_lookup': {}}


def process_nace(vid_csv_path: str, nace_csv_path: str):
    """
    Process VID tax data and merge with NACE descriptions.
    Updates companies table with industry classification.
    """
    logger.info("🏭 Processing NACE Industry Classification...")
    
    try:
        # Load NACE dictionary
        nace_dict = load_nace_dictionary(nace_csv_path)
        code_lookup = nace_dict['code_lookup']
        section_lookup = nace_dict['section_lookup']
        
        # Load VID tax data
        logger.info(f"Loading VID tax data from {vid_csv_path}")
        vid_df = pd.read_csv(
            vid_csv_path,
            sep=';',
            dtype={
                'Registracijas_kods': str,
                'Pamatdarbibas_NACE_kods': str,
                'Taksacijas_gads': str
            },
            encoding='utf-8'
        )
        
        logger.info(f"Loaded {len(vid_df)} VID tax records")
        
        # Filter valid registration codes (11 digits)
        vid_df = vid_df[
            (vid_df['Registracijas_kods'].notna()) &
            (vid_df['Registracijas_kods'].str.match(r'^\d{11}$'))
        ]
        
        logger.info(f"Filtered to {len(vid_df)} records with valid registration codes")
        
        # Normalize NACE codes
        vid_df['nace_normalized'] = normalize_nace_code(vid_df['Pamatdarbibas_NACE_kods'])
        
        # Convert tax year to integer
        vid_df['tax_year'] = pd.to_numeric(vid_df['Taksacijas_gads'], errors='coerce').fillna(0).astype(int)
        
        # Get employee count
        vid_df['employee_count'] = pd.to_numeric(
            vid_df['Videjais_nodarbinato_personu_skaits_cilv'],
            errors='coerce'
        ).fillna(0).astype(int)
        
        # Sort by company and year (latest first)
        vid_df = vid_df.sort_values(
            by=['Registracijas_kods', 'tax_year'],
            ascending=[True, False]
        )
        
        # Keep only latest entry per company
        latest_df = vid_df.drop_duplicates(subset=['Registracijas_kods'], keep='first')
        
        logger.info(f"Selected latest data for {len(latest_df)} companies")
        
        # Lookup NACE descriptions
        latest_df['nace_text'] = latest_df['nace_normalized'].map(code_lookup)
        
        # Extract section codes and descriptions
        latest_df['nace_section'] = latest_df['nace_normalized'].apply(extract_section_code)
        latest_df['nace_section_text'] = latest_df['nace_section'].map(section_lookup)
        
        # Handle missing descriptions
        latest_df['nace_text'] = latest_df['nace_text'].fillna('Nenoteikta nozare')
        latest_df['nace_section_text'] = latest_df['nace_section_text'].fillna('Cita nozare')
        
        # Prepare update data
        update_df = latest_df[[
            'Registracijas_kods',
            'nace_normalized',
            'nace_text',
            'nace_section',
            'nace_section_text',
            'employee_count',
            'tax_year'
        ]].rename(columns={
            'Registracijas_kods': 'regcode',
            'nace_normalized': 'nace_code',
            'tax_year': 'tax_data_year'
        })
        
        # Update companies table
        logger.info(f"Updating companies table with NACE data for {len(update_df)} companies...")
        
        with engine.connect() as conn:
            # Update in batches
            batch_size = 5000
            total_updated = 0
            
            for i in range(0, len(update_df), batch_size):
                batch = update_df.iloc[i:i+batch_size]
                
                # Build UPDATE query
                update_values = []
                for _, row in batch.iterrows():
                    update_values.append(f"""
                        ({row['regcode']}, 
                         '{row['nace_code']}', 
                         '{row['nace_text'].replace("'", "''")}',
                         '{row['nace_section']}',
                         '{row['nace_section_text'].replace("'", "''")}',
                         {row['employee_count']},
                         {row['tax_data_year']})
                    """)
                
                values_str = ','.join(update_values)
                
                update_sql = f"""
                    UPDATE companies AS c SET
                        nace_code = v.nace_code,
                        nace_text = v.nace_text,
                        nace_section = v.nace_section,
                        nace_section_text = v.nace_section_text,
                        employee_count = v.employee_count,
                        tax_data_year = v.tax_data_year
                    FROM (VALUES
                        {values_str}
                    ) AS v(regcode, nace_code, nace_text, nace_section, nace_section_text, employee_count, tax_data_year)
                    WHERE c.regcode = v.regcode
                """
                
                try:
                    result = conn.execute(text(update_sql))
                    conn.commit()
                    total_updated += result.rowcount or len(batch)
                    
                    if (i + batch_size) % 10000 == 0:
                        logger.info(f"  Updated {min(i + batch_size, len(update_df))}/{len(update_df)} companies...")
                        
                except Exception as e:
                    logger.error(f"Batch update failed at {i}: {e}")
                    conn.rollback()
            
            logger.info(f"✅ Updated {total_updated} companies with NACE classification")
            
            # Log statistics
            stats_sql = """
                SELECT 
                    nace_section,
                    nace_section_text,
                    COUNT(*) as company_count,
                    SUM(employee_count) as total_employees
                FROM companies
                WHERE nace_code IS NOT NULL AND nace_code != '0000'
                GROUP BY nace_section, nace_section_text
                ORDER BY company_count DESC
                LIMIT 10
            """
            
            result = conn.execute(text(stats_sql))
            logger.info("Top 10 industries by company count:")
            for row in result:
                logger.info(f"  {row[0]}: {row[1]} - {row[2]} companies, {row[3]:,} employees")
        
    except Exception as e:
        logger.error(f"Error processing NACE data: {e}")
        raise
