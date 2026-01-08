"""
Script to fix NACE descriptions for existing codes in database
Re-maps existing nace_code to proper nace_text using updated NACE.csv
"""
import pandas as pd
from sqlalchemy import text
from etl.loader import engine
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def normalize_nace_code(code_str):
    """Remove dots and spaces from NACE code"""
    if not code_str:
        return None
    return str(code_str).replace('.', '').replace(' ', '').strip()

def load_nace_mapping():
    """Load NACE code -> description mapping"""
    logger.info("Loading NACE.csv...")
    nace_df = pd.read_csv('../NACE.csv', dtype={'Kods': str}, encoding='utf-8')
    
    # Normalize codes
    nace_df['Kods_normalized'] = nace_df['Kods'].apply(normalize_nace_code)
    
    # Create lookup
    mapping = dict(zip(nace_df['Kods_normalized'], nace_df['Nosaukums']))
    
    # Add 4-digit variants (5310 for 531)
    for code, name in list(mapping.items()):
        if len(code) == 3 and code.isdigit():
            mapping[code + '0'] = name
    
    logger.info(f"Loaded {len(mapping)} NACE code mappings")
    return mapping

def fix_nace_descriptions():
    """Update nace_text for all companies based on their nace_code"""
    
    # Load mapping
    nace_mapping = load_nace_mapping()
    
    with engine.connect() as conn:
        # Get all companies with NACE codes
        result = conn.execute(text("""
            SELECT regcode, nace_code 
            FROM companies 
            WHERE nace_code IS NOT NULL 
              AND nace_code != '0000'
              AND nace_code != ''
        """))
        
        companies = result.fetchall()
        logger.info(f"Found {len(companies)} companies with NACE codes")
        
        # Prepare updates
        updates = []
        fixed_count = 0
        
        for regcode, nace_code in companies:
            new_text = nace_mapping.get(nace_code)
            if new_text and new_text != 'Nenoteikta nozare':
                updates.append((regcode, new_text))
                fixed_count += 1
        
        logger.info(f"Will update {fixed_count} companies with proper NACE descriptions")
        
        # Update in batches
        batch_size = 5000
        total_updated = 0
        
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i+batch_size]
            
            # Build VALUES clause
            values = ','.join([
                f"({regcode}, '{text.replace(chr(39), chr(39)+chr(39))}')"  # Escape single quotes
                for regcode, text in batch
            ])
            
            update_sql = f"""
                UPDATE companies AS c
                SET nace_text = v.new_text
                FROM (VALUES {values}) AS v(regcode, new_text)
                WHERE c.regcode = v.regcode
            """
            
            conn.execute(text(update_sql))
            conn.commit()
            total_updated += len(batch)
            
            logger.info(f"Updated {total_updated}/{len(updates)} companies...")
        
        logger.info(f"✅ Successfully updated {total_updated} companies!")
        
        # Show statistics
        stats = conn.execute(text("""
            SELECT 
                CASE 
                    WHEN nace_text = 'Nenoteikta nozare' THEN 'Nenoteikta'
                    ELSE 'Noteikta'
                END as category,
                COUNT(*) as count
            FROM companies
            WHERE nace_code IS NOT NULL AND nace_code != '0000'
            GROUP BY category
        """)).fetchall()
        
        logger.info("Final statistics:")
        for category, count in stats:
            logger.info(f"  {category}: {count:,} companies")

if __name__ == "__main__":
    try:
        fix_nace_descriptions()
    except Exception as e:
        logger.error(f"ERROR: {e}")
        raise
