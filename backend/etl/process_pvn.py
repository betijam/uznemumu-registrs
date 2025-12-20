#!/usr/bin/env python3
"""
Process PVN (VAT) taxpayer registry from data.gov.lv

Downloads and processes official PVN registry to determine:
- Which companies are active VAT payers
- PVN registration numbers (LV prefix format)
- Updates companies table with accurate PVN status

Data source: https://data.gov.lv/dati/dataset/9a5eae1c-2438-48cf-854b-6a2c170f918f
"""

import sys
import os
# Add parent directory to path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import logging
from sqlalchemy import text
from etl.loader import engine
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PVN_CSV_URL = "https://data.gov.lv/dati/dataset/9a5eae1c-2438-48cf-854b-6a2c170f918f/resource/610910e9-e086-4c5b-a7ea-0a896a697672/download/pdb_pvnmaksataji_odata.csv"

def migrate_pvn_columns():
    """Auto-create PVN columns and indexes if they don't exist"""
    logger.info("Checking/creating PVN database columns...")
    
    with engine.connect() as conn:
        try:
            # Add columns
            conn.execute(text("""
                ALTER TABLE companies 
                ADD COLUMN IF NOT EXISTS pvn_number VARCHAR(20),
                ADD COLUMN IF NOT EXISTS is_pvn_payer BOOLEAN DEFAULT FALSE
            """))
            
            # Add indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_companies_pvn ON companies(pvn_number)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_companies_is_pvn_payer ON companies(is_pvn_payer)
            """))
            
            conn.commit()
            logger.info("✅ PVN columns and indexes ready")
            
        except Exception as e:
            logger.warning(f"Migration warning (may be safe to ignore): {e}")


def download_pvn_data():
    """Download latest PVN registry CSV"""
    logger.info(f"Downloading PVN registry from data.gov.lv...")
    
    try:
        response = requests.get(PVN_CSV_URL, timeout=60)
        response.raise_for_status()
        
        # Save to temp file
        temp_path = "/tmp/pvn_registry.csv"
        with open(temp_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"✅ Downloaded PVN registry to {temp_path}")
        return temp_path
    
    except Exception as e:
        logger.error(f"Failed to download PVN data: {e}")
        return None

def process_pvn_registry():
    """Process PVN registry and update companies table"""
    
    # Auto-migrate database schema
    migrate_pvn_columns()
    
    # Download data
    csv_path = download_pvn_data()
    if not csv_path:
        logger.error("Cannot proceed without PVN data")
        return
    
    # Load CSV
    logger.info("Loading PVN registry CSV...")
    df = pd.read_csv(csv_path, dtype={'Numurs': str})
    
    logger.info(f"Loaded {len(df)} PVN records")
    logger.info(f"Columns: {df.columns.tolist()}")
    
    # Extract regcode from PVN number (remove "LV" prefix)
    df['regcode'] = df['Numurs'].str.replace('LV', '', regex=False)
    df['regcode'] = pd.to_numeric(df['regcode'], errors='coerce')
    
    # Filter valid regcodes
    df = df[df['regcode'].notna()].copy()
    df['regcode'] = df['regcode'].astype(int)
    
    # Determine active PVN status
    # "Aktivs" column: if "nav" -> not active VAT payer
    df['is_pvn_active'] = df['Aktivs'].str.lower() != 'nav'
    
    logger.info(f"Processed {len(df)} valid PVN records")
    logger.info(f"Active PVN payers: {df['is_pvn_active'].sum()}")
    logger.info(f"Inactive: {(~df['is_pvn_active']).sum()}")
    
    # Update database using FAST batch method
    with engine.connect() as conn:
        logger.info("Updating companies table with PVN data (batch mode)...")
        
        # Step 1: Reset all PVN fields (fast single query)
        conn.execute(text("""
            UPDATE companies 
            SET pvn_number = NULL, 
                is_pvn_payer = FALSE
        """))
        conn.commit()
        logger.info("✅ Reset PVN fields")
        
        # Step 2: Prepare active PVN payers data
        active_pvn = df[df['is_pvn_active']][['regcode', 'Numurs']].copy()
        logger.info(f"Preparing {len(active_pvn)} active PVN records for batch update...")
        
        # Step 3: Create temporary table and bulk insert
        logger.info("Creating temporary table...")
        conn.execute(text("""
            CREATE TEMP TABLE pvn_temp (
                regcode BIGINT,
                pvn_number VARCHAR(20)
            )
        """))
        logger.info("✅ Temporary table created")
        
        # Batch insert in chunks of 5000
        chunk_size = 5000
        total_inserted = 0
        logger.info(f"Starting bulk insert in chunks of {chunk_size}...")
        
        for i in range(0, len(active_pvn), chunk_size):
            chunk = active_pvn.iloc[i:i+chunk_size]
            # Convert to list of dicts FAST (no iterrows!)
            values = [
                {"regcode": int(row['regcode']), "pvn": row['Numurs']} 
                for row in chunk.to_dict('records')
            ]
            
            logger.info(f"  Inserting chunk {i//chunk_size + 1}/{(len(active_pvn)-1)//chunk_size + 1} ({len(values)} records)...")
            conn.execute(
                text("INSERT INTO pvn_temp (regcode, pvn_number) VALUES (:regcode, :pvn)"),
                values
            )
            total_inserted += len(values)
            logger.info(f"  ✅ Inserted {total_inserted}/{len(active_pvn)} records total")
        
        conn.commit()
        logger.info(f"✅ All {total_inserted} records inserted into temp table")
        
        # Step 4: Single UPDATE query using JOIN (SUPER FAST!)
        result = conn.execute(text("""
            UPDATE companies c
            SET 
                pvn_number = t.pvn_number,
                is_pvn_payer = TRUE
            FROM pvn_temp t
            WHERE c.regcode = t.regcode
        """))
        conn.commit()
        
        updated_count = result.rowcount
        logger.info(f"✅ Updated {updated_count} companies with active PVN status")
        
        # Cleanup
        conn.execute(text("DROP TABLE pvn_temp"))
        conn.commit()
        
        # Statistics
        stats = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_pvn_payer THEN 1 ELSE 0 END) as pvn_payers,
                SUM(CASE WHEN NOT is_pvn_payer THEN 1 ELSE 0 END) as non_payers
            FROM companies
        """)).fetchone()
        
        logger.info(f"\n📊 PVN Statistics:")
        logger.info(f"  Total companies: {stats.total:,}")
        logger.info(f"  PVN payers: {stats.pvn_payers:,} ({stats.pvn_payers/stats.total*100:.1f}%)")
        logger.info(f"  Non-PVN: {stats.non_payers:,} ({stats.non_payers/stats.total*100:.1f}%)")
    
    # Cleanup
    if os.path.exists(csv_path):
        os.remove(csv_path)
        logger.info("Cleaned up temporary files")

if __name__ == "__main__":
    process_pvn_registry()
