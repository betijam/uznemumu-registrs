"""
ETL Script: Import Old ATVK Codes and Normalize Company ATVK

This script:
1. Imports old ATVK data (2017) for companies registered before 30.06.2021
2. Normalizes company ATVK codes by padding with leading zeroes to 7 characters
3. Creates mapping between old and new ATVK codes

ATVK Code Change: At 30.06.2021, Latvia switched to new territorial codes
- Companies registered before 30.06.2021 use old ATVK codes
- Companies registered after use new ATVK codes
- Matching: company ATVK "3000" should match territory "0003000" (pad with zeroes)
"""

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

OLD_ATVK_URL = "https://data.gov.lv/dati/lv/dataset/f4c3be02-cca3-4fd1-b3ea-c3050a155852/resource/087ced25-97f2-48f2-9093-ee9f361e5e2e/download/atvk_2017.csv"
ATVK_CHANGE_DATE = "2021-06-30"


def normalize_atvk(code) -> str:
    """Normalize ATVK code to 7 characters with leading zeroes"""
    if not code:
        return None
    # Remove any non-numeric characters
    code_str = str(code).strip()
    code_str = ''.join(c for c in code_str if c.isdigit())
    if not code_str:
        return None
    # Pad with leading zeroes to 7 characters
    return code_str.zfill(7)


def import_old_atvk_codes():
    """
    Import old ATVK codes (2017) into territories table with valid_to date
    """
    engine = create_engine(DATABASE_URL)
    
    logger.info("📥 Downloading old ATVK data (2017)...")
    
    try:
        df = pd.read_csv(OLD_ATVK_URL, sep=',', encoding='utf-8')
        logger.info(f"✅ Downloaded {len(df)} old territory records")
    except Exception as e:
        logger.error(f"❌ Failed to download old ATVK: {e}")
        return 0
    
    with engine.connect() as conn:
        territories = []
        
        for _, row in df.iterrows():
            code_raw = str(row['Code']).strip()
            code = normalize_atvk(code_raw)
            name = str(row['Name']).strip() if pd.notna(row.get('Name')) else None
            
            if not code or not name:
                continue
            
            # Determine level and type from code
            pos_3_4 = int(code[2:4]) if len(code) >= 4 else 0
            pos_5_6 = int(code[4:6]) if len(code) >= 6 else 0
            
            if pos_5_6 == 0:
                level = 2
                if 1 <= pos_3_4 <= 19:
                    type_name = "VALSTSPILSĒTU_PAŠVALDĪBA"
                else:
                    type_name = "NOVADS"
            else:
                level = 3
                if 1 <= pos_5_6 <= 19:
                    type_name = "VALSTSPILSĒTA"
                elif 20 <= pos_5_6 <= 39:
                    type_name = "PILSĒTA"
                else:
                    type_name = "PAGASTS"
            
            parent_code = code[:2] + "00000" if level == 2 else code[:4] + "000"
            
            territories.append({
                "code": code,
                "name": name,
                "level": level,
                "type": type_name,
                "parent_code": parent_code,
                "valid_to": ATVK_CHANGE_DATE
            })
        
        # Batch insert all at once
        if territories:
            conn.execute(text("""
                INSERT INTO territories (code, name, level, type, parent_code, valid_to)
                VALUES (:code, :name, :level, :type, :parent_code, :valid_to)
                ON CONFLICT (code) DO NOTHING
            """), territories)
            conn.commit()
        
        logger.info(f"✅ Imported {len(territories)} old territory codes")
        return len(territories)


def normalize_company_atvk():
    """
    Normalize company ATVK codes to 7 characters with leading zeroes
    """
    engine = create_engine(DATABASE_URL)
    
    logger.info("🔄 Normalizing company ATVK codes...")
    
    with engine.connect() as conn:
        # First, check what ATVK data we have in companies
        sample = conn.execute(text("""
            SELECT atvk, COUNT(*) as cnt 
            FROM companies 
            WHERE atvk IS NOT NULL AND atvk != ''
            GROUP BY atvk 
            ORDER BY cnt DESC 
            LIMIT 10
        """)).fetchall()
        
        if sample:
            logger.info("📊 Sample ATVK codes in companies:")
            for s in sample:
                logger.info(f"   {s.atvk}: {s.cnt} companies")
        
        # Normalize: pad with leading zeroes to 7 characters
        result = conn.execute(text("""
            UPDATE companies
            SET atvk = LPAD(atvk, 7, '0')
            WHERE atvk IS NOT NULL 
              AND atvk != ''
              AND LENGTH(atvk) < 7
        """))
        padded = result.rowcount
        
        conn.commit()
        
        logger.info(f"✅ Normalized {padded} company ATVK codes")
        
        # Get statistics
        stats = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN atvk IS NOT NULL AND atvk != '' THEN 1 END) as with_atvk,
                COUNT(CASE WHEN atvk IS NULL OR atvk = '' THEN 1 END) as without_atvk
            FROM companies
            WHERE status = 'active'
        """)).fetchone()
        
        logger.info(f"   Companies with ATVK: {stats.with_atvk}")
        logger.info(f"   Companies without ATVK: {stats.without_atvk}")
        
        # Check how many match territories
        matches = conn.execute(text("""
            SELECT COUNT(*) as matched
            FROM companies c
            JOIN territories t ON t.code = c.atvk
            WHERE c.status = 'active' AND c.atvk IS NOT NULL
        """)).fetchone()
        
        logger.info(f"   Companies matching territories: {matches.matched}")
        
        return padded


def run_atvk_setup():
    """Main function to set up ATVK matching"""
    logger.info("=" * 60)
    logger.info("ATVK SETUP STARTED")
    logger.info("=" * 60)
    start_time = datetime.now()
    
    # Step 1: Import old ATVK codes
    old_count = import_old_atvk_codes()
    
    # Step 2: Normalize company ATVK codes
    normalized = normalize_company_atvk()
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ ATVK SETUP COMPLETED")
    logger.info(f"   Old territories imported: {old_count}")
    logger.info(f"   Company codes normalized: {normalized}")
    logger.info(f"   Time elapsed: {elapsed:.2f} seconds")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_atvk_setup()
