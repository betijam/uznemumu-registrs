"""
ULTRA FAST entity_type update using TEMP table and single UPDATE.
Much faster than row-by-row updates.
"""
import os
import sys
import pandas as pd
import logging
import requests
from sqlalchemy import text, create_engine
from io import StringIO
from concurrent.futures import ThreadPoolExecutor
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("Error: DATABASE_URL not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL, pool_size=10)

# CSV URLs
MEMBERS_CSV_URL = "https://data.gov.lv/dati/dataset/e1162626-e02a-4545-9236-37553609a988/resource/837b451a-4833-4fd1-bfdd-b45b35a994fd/download/members.csv"
OFFICERS_CSV_URL = "https://data.gov.lv/dati/dataset/096c7a47-33cd-4dc9-a876-2c86e86230fd/resource/e665114a-73c2-4375-9470-55874b4cfa6b/download/officers.csv"


def download_csv(url, name):
    """Download CSV file."""
    logger.info(f"Downloading {name}...")
    response = requests.get(url, timeout=300)
    response.raise_for_status()
    logger.info(f"✅ {name}: {len(response.content):,} bytes")
    return response.text


def update_using_temp_table(df, role, csv_name):
    """Ultra-fast update using temporary table."""
    logger.info(f"\nProcessing {csv_name} for role={role}...")
    
    # Filter and prepare
    df_with_type = df[df['entity_type'].notna()].copy()
    logger.info(f"  Rows with entity_type: {len(df_with_type):,}")
    
    # Show distribution
    print(f"\n  {csv_name} distribution:")
    for et, count in df_with_type['entity_type'].value_counts().items():
        print(f"    {et}: {count:,}")
    
    # Rename and clean
    df_with_type = df_with_type.rename(columns={
        'at_legal_entity_registration_number': 'company_regcode',
        'name': 'person_name'
    })
    
    df_with_type['company_regcode'] = pd.to_numeric(df_with_type['company_regcode'], errors='coerce')
    df_with_type['person_name'] = df_with_type['person_name'].str.strip()
    df_with_type = df_with_type.dropna(subset=['company_regcode', 'person_name', 'entity_type'])
    
    logger.info(f"  Valid records: {len(df_with_type):,}")
    
    if len(df_with_type) == 0:
        return 0
    
    # Prepare final dataframe
    df_final = df_with_type[['company_regcode', 'person_name', 'entity_type']].copy()
    df_final['company_regcode'] = df_final['company_regcode'].astype('int64')
    
    start_time = time.time()
    
    with engine.connect() as conn:
        # Create temp table
        logger.info("  Creating temp table...")
        conn.execute(text("""
            CREATE TEMP TABLE temp_entity_updates (
                company_regcode BIGINT,
                person_name TEXT,
                entity_type VARCHAR(50)
            ) ON COMMIT DROP
        """))
        
        # Bulk insert into temp table
        logger.info(f"  Bulk inserting {len(df_final):,} records...")
        df_final.to_sql(
            'temp_entity_updates',
            conn,
            if_exists='append',
            index=False,
            method='multi',
            chunksize=10000
        )
        
        # Single UPDATE query
        logger.info("  Executing bulk UPDATE...")
        result = conn.execute(text("""
            UPDATE persons p
            SET entity_type = t.entity_type
            FROM temp_entity_updates t
            WHERE p.company_regcode = t.company_regcode
              AND p.person_name = t.person_name
              AND p.role = :role
        """), {"role": role})
        
        conn.commit()
        updated = result.rowcount
    
    elapsed = time.time() - start_time
    logger.info(f"  ✅ Updated {updated:,} records in {elapsed:.2f}s ({updated/elapsed:.0f} rec/sec)")
    
    return updated


def main():
    """Main function."""
    print("="*80)
    print("ULTRA FAST ENTITY_TYPE UPDATE (TEMP TABLE METHOD)")
    print("="*80)
    
    total_start = time.time()
    
    # Download CSVs in parallel
    logger.info("Downloading CSVs...")
    with ThreadPoolExecutor(max_workers=2) as executor:
        members_future = executor.submit(download_csv, MEMBERS_CSV_URL, "members.csv")
        officers_future = executor.submit(download_csv, OFFICERS_CSV_URL, "officers.csv")
        
        members_text = members_future.result()
        officers_text = officers_future.result()
    
    # Parse CSVs
    logger.info("\nParsing CSVs...")
    df_members = pd.read_csv(StringIO(members_text), sep=';', dtype=str)
    logger.info(f"  members.csv: {len(df_members):,} rows")
    
    df_officers = pd.read_csv(StringIO(officers_text), sep=';', dtype=str)
    logger.info(f"  officers.csv: {len(df_officers):,} rows")
    
    # Update from both
    total_updated = 0
    total_updated += update_using_temp_table(df_members, 'member', "members.csv")
    total_updated += update_using_temp_table(df_officers, 'officer', "officers.csv")
    
    # Verify
    print("\n" + "="*80)
    print("VERIFICATION")
    print("="*80)
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT role, entity_type, COUNT(*) as count
            FROM persons
            WHERE entity_type IS NOT NULL
            GROUP BY role, entity_type
            ORDER BY role, entity_type
        """))
        
        print("\nEntity type distribution:")
        for row in result:
            print(f"  {row[0]:10} | {row[1]:20} | {row[2]:,}")
        
        # FOREIGN_ENTITY count
        result = conn.execute(text("""
            SELECT COUNT(*) FROM persons WHERE entity_type = 'FOREIGN_ENTITY'
        """))
        print(f"\n🌍 FOREIGN_ENTITY total: {result.scalar():,}")
    
    total_elapsed = time.time() - total_start
    print("\n" + "="*80)
    print(f"✅ Completed in {total_elapsed:.2f}s")
    print(f"Total updated: {total_updated:,}")
    print("="*80)


if __name__ == "__main__":
    main()
