"""
ETL Script: Import ATVK Territories from Official CSV

Downloads and imports Latvia's Administrative Territorial Classification (ATVK)
from the official government data portal.

Source: https://data.gov.lv/dati/lv/dataset/f4c3be02-cca3-4fd1-b3ea-c3050a155852

ATVK Code Structure (7 characters):
- Positions 1-2: Region level
- Positions 3-4: Administrative territory (01-19: cities, 20-99: municipalities)
- Positions 5-6: Territorial unit (01-19: city, 20-39: town, 40-99: parish)
- Position 7: Modification count
"""

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

ATVK_CSV_URL = "https://data.gov.lv/dati/lv/dataset/f4c3be02-cca3-4fd1-b3ea-c3050a155852/resource/7e2b3c8b-32d1-4bec-be3a-5e621ac37005/download/atvk2021_30062024.csv"


def determine_level_and_type(code: str):
    """
    Determine territory level and type from ATVK code
    
    Returns: (level, type_name)
    """
    pos_3_4 = int(code[2:4])
    pos_5_6 = int(code[4:6])
    
    if pos_5_6 == 0:  # Municipality level
        level = 2
        if 1 <= pos_3_4 <= 19:
            type_name = "VALSTSPILSĒTU_PAŠVALDĪBA"
        else:
            type_name = "NOVADS"
    else:  # City/parish level
        level = 3
        if 1 <= pos_5_6 <= 19:
            type_name = "VALSTSPILSĒTA"
        elif 20 <= pos_5_6 <= 39:
            type_name = "PILSĒTA"
        else:
            type_name = "PAGASTS"
    
    return level, type_name


def determine_parent_code(code: str, level: int):
    """
    Determine parent territory code based on ATVK hierarchy
    
    Level 2 (municipality) -> parent is region (positions 1-2)
    Level 3 (city/parish) -> parent is municipality (positions 1-4)
    """
    if level == 2:
        # Parent is region (positions 1-2) - 7 chars total
        return code[:2] + "00000"
    elif level == 3:
        # Parent is municipality (positions 1-4) - 7 chars total
        return code[:4] + "000"
    return None


def create_regions(conn):
    """
    Create region-level territories (level 1) from unique position 1-2 codes
    """
    logger.info("Creating region-level territories...")
    
    # Get unique region codes from existing municipalities
    result = conn.execute(text("""
        SELECT DISTINCT SUBSTRING(code, 1, 2) AS region_code
        FROM territories
        WHERE level = 2
    """)).fetchall()
    
    region_names = {
        "01": "Rīgas reģions",
        "02": "Vidzemes reģions",
        "03": "Kurzemes reģions",
        "04": "Zemgales reģions",
        "05": "Latgales reģions"
    }
    
    regions_created = 0
    for row in result:
        region_code = row.region_code + "00000"  # 2 + 5 = 7 characters
        region_name = region_names.get(row.region_code, f"Reģions {row.region_code}")
        
        conn.execute(text("""
            INSERT INTO territories (code, name, level, type, parent_code)
            VALUES (:code, :name, 1, 'REĢIONS', NULL)
            ON CONFLICT (code) DO UPDATE SET
                name = EXCLUDED.name,
                level = EXCLUDED.level,
                type = EXCLUDED.type
        """), {
            "code": region_code,
            "name": region_name
        })
        regions_created += 1
    
    logger.info(f"✅ Created {regions_created} regions")
    return regions_created


def import_atvk():
    """
    Main import function
    """
    engine = create_engine(DATABASE_URL)
    
    logger.info("=" * 60)
    logger.info("ATVK TERRITORIES IMPORT STARTED")
    logger.info("=" * 60)
    start_time = datetime.now()
    
    try:
        # Download CSV
        logger.info(f"📥 Downloading ATVK CSV from: {ATVK_CSV_URL}")
        df = pd.read_csv(ATVK_CSV_URL, sep=',', encoding='utf-8')
        logger.info(f"✅ Downloaded {len(df)} records")
        
        territories = []
        
        # Process each row
        for _, row in df.iterrows():
            code = str(row['Code']).strip()
            name = str(row['Name']).strip()
            valid_from = row.get('ValidFrom')
            valid_to = row.get('ValidTo')
            
            # Skip if code is invalid
            if len(code) != 7:
                logger.warning(f"⚠️  Skipping invalid code: {code}")
                continue
            
            level, type_name = determine_level_and_type(code)
            parent_code = determine_parent_code(code, level)
            
            # Parse dates from DD.MM.YYYY format
            valid_from_parsed = None
            valid_to_parsed = None
            if pd.notna(valid_from) and valid_from:
                try:
                    valid_from_parsed = pd.to_datetime(valid_from, format='%d.%m.%Y').date()
                except:
                    pass
            if pd.notna(valid_to) and valid_to:
                try:
                    valid_to_parsed = pd.to_datetime(valid_to, format='%d.%m.%Y').date()
                except:
                    pass
            
            territories.append({
                'code': code,
                'name': name,
                'level': level,
                'type': type_name,
                'parent_code': parent_code,
                'valid_from': valid_from_parsed,
                'valid_to': valid_to_parsed
            })
        
        # Insert into database using batch operation
        logger.info(f"💾 Inserting {len(territories)} territories into database...")
        
        with engine.connect() as conn:
            # Use executemany for batch insert (much faster than individual inserts)
            from sqlalchemy.dialects.postgresql import insert
            
            stmt = text("""
                INSERT INTO territories (code, name, level, type, parent_code, valid_from, valid_to)
                VALUES (:code, :name, :level, :type, :parent_code, :valid_from, :valid_to)
                ON CONFLICT (code) DO UPDATE SET
                    name = EXCLUDED.name,
                    level = EXCLUDED.level,
                    type = EXCLUDED.type,
                    parent_code = EXCLUDED.parent_code,
                    valid_from = EXCLUDED.valid_from,
                    valid_to = EXCLUDED.valid_to
            """)
            
            # Batch insert all territories at once
            conn.execute(stmt, territories)
            inserted = len(territories)
            
            # Create region-level territories
            regions_created = create_regions(conn)
            
            conn.commit()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ ATVK TERRITORIES IMPORT COMPLETED")
        logger.info(f"   Territories imported: {inserted}")
        logger.info(f"   Regions created: {regions_created}")
        logger.info(f"   Time elapsed: {elapsed:.2f} seconds")
        logger.info("=" * 60)
        
        # Show summary by type
        with engine.connect() as conn:
            summary = conn.execute(text("""
                SELECT type, COUNT(*) as count
                FROM territories
                GROUP BY type
                ORDER BY count DESC
            """)).fetchall()
            
            logger.info("\n📊 Territory Summary:")
            for row in summary:
                logger.info(f"   {row.type}: {row.count}")
        
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        raise


if __name__ == "__main__":
    import_atvk()
