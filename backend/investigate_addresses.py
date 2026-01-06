import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/ur_db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

print("=== Investigating Unmatched Addresses ===\n")

with engine.connect() as conn:
    # Check sample of unmatched companies
    result = conn.execute(text("""
        SELECT c.addressid, COUNT(*) as company_count
        FROM companies c
        LEFT JOIN address_dimension a ON c.addressid = a.address_id
        WHERE c.addressid != '0' 
          AND c.addressid IS NOT NULL
          AND a.address_id IS NULL
        GROUP BY c.addressid
        ORDER BY company_count DESC
        LIMIT 20
    """))
    
    print("Top 20 unmatched addressid values:")
    unmatched_ids = []
    for row in result:
        print(f"  {row.addressid}: {row.company_count} companies")
        unmatched_ids.append(row.addressid)
    
    # Check if these exist in core.address_objects
    if unmatched_ids:
        print("\nChecking if these IDs exist in address_objects:")
        placeholders = ', '.join([f"'{id}'" for id in unmatched_ids[:5]])
        result = conn.execute(text(f"""
            SELECT kods, tips_cd, nosaukums, source
            FROM core.address_objects
            WHERE kods IN ({placeholders})
        """))
        
        found = list(result)
        if found:
            print("Found in address_objects:")
            for row in found:
                print(f"  {row.kods} (type {row.tips_cd}): {row.nosaukums} [{row.source}]")
        else:
            print("❌ None of these IDs exist in address_objects!")
            print("\nThese addressid values might be:")
            print("  - Invalid/outdated codes")
            print("  - From object types we're not loading (e.g., VIETA)")
            print("  - Require additional VARIS files")
    
    # Check distribution of object types in address_objects
    print("\n=== Object Type Distribution ===")
    result = conn.execute(text("""
        SELECT tips_cd, COUNT(*) as cnt, source
        FROM core.address_objects
        GROUP BY tips_cd, source
        ORDER BY cnt DESC
        LIMIT 20
    """))
    
    for row in result:
        print(f"  Type {row.tips_cd} ({row.source}): {row.cnt:,}")
    
    # Check addressid format in companies
    print("\n=== AddressID Patterns ===")
    result = conn.execute(text("""
        SELECT 
            CASE 
                WHEN addressid = '0' THEN 'Zero'
                WHEN addressid IS NULL THEN 'NULL'
                WHEN LENGTH(addressid) < 8 THEN 'Short (<8 chars)'
                WHEN LENGTH(addressid) = 9 THEN 'Standard (9 chars)'
                WHEN LENGTH(addressid) > 9 THEN 'Long (>9 chars)'
                ELSE 'Other'
            END as pattern,
            COUNT(*) as cnt
        FROM companies
        GROUP BY pattern
        ORDER BY cnt DESC
    """))
    
    for row in result:
        print(f"  {row.pattern}: {row.cnt:,}")
