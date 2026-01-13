"""
Fix entity_type for foreign entities based on companies.type
"""
import os
import sys
from pathlib import Path
from sqlalchemy import text, create_engine

# Get DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")
if len(sys.argv) > 1:
    DATABASE_URL = sys.argv[1]

if not DATABASE_URL:
    print("Usage: railway run python scripts/fix_foreign_entity_type.py")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

print("="*80)
print("FIXING FOREIGN ENTITY TYPE")
print("="*80)

with engine.connect() as conn:
    # Update foreign entities
    print("\n1. Updating entity_type for foreign entities...")
    result = conn.execute(text("""
        UPDATE persons p
        SET entity_type = 'FOREIGN_ENTITY'
        FROM companies c
        WHERE p.legal_entity_regcode = c.regcode
          AND p.role = 'member'
          AND (
            c.type ILIKE '%ārvalst%' OR
            c.type ILIKE '%filiale%' OR
            c.type ILIKE '%filiāle%'
          )
    """))
    conn.commit()
    
    updated_count = result.rowcount
    print(f"✅ Updated {updated_count} records to FOREIGN_ENTITY")
    
    # Verify
    print("\n2. Entity type distribution:")
    result = conn.execute(text("""
        SELECT 
            entity_type,
            COUNT(*) as count
        FROM persons
        WHERE role = 'member' AND legal_entity_regcode IS NOT NULL
        GROUP BY entity_type
        ORDER BY entity_type
    """))
    
    for row in result:
        print(f"  - {row[0]}: {row[1]:,}")
    
    # Show samples
    print("\n3. Sample foreign entities:")
    result = conn.execute(text("""
        SELECT 
            p.person_name,
            c.name as company_name,
            c.type as company_type
        FROM persons p
        JOIN companies c ON c.regcode = p.legal_entity_regcode
        WHERE p.entity_type = 'FOREIGN_ENTITY'
        LIMIT 10
    """))
    
    for row in result:
        print(f"  - {row[0][:50]:50} | {row[2]}")

print("\n" + "="*80)
print("✅ Migration completed!")
print("="*80)
