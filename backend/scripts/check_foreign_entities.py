"""
Quick script to check how foreign entities are identified in the database.
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
    print("Usage: python check_foreign_entities.py [DATABASE_URL]")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

print("="*80)
print("CHECKING FOREIGN ENTITY IDENTIFICATION")
print("="*80)

with engine.connect() as conn:
    # Check persons table structure
    print("\n1. Persons table columns:")
    result = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'persons'
        ORDER BY ordinal_position
    """))
    for row in result:
        print(f"  - {row[0]}: {row[1]}")
    
    # Check sample of members with legal_entity_regcode
    print("\n2. Sample members with legal_entity_regcode:")
    result = conn.execute(text("""
        SELECT 
            person_name,
            legal_entity_regcode,
            entity_type
        FROM persons
        WHERE role = 'member' 
          AND legal_entity_regcode IS NOT NULL
        LIMIT 10
    """))
    for row in result:
        print(f"  - {row[0][:50]:50} | regcode: {row[1]} | type: {row[2]}")
    
    # Check if any members have specific patterns indicating foreign
    print("\n3. Checking for foreign indicators in person_name:")
    result = conn.execute(text("""
        SELECT 
            person_name,
            legal_entity_regcode,
            COUNT(*) as count
        FROM persons
        WHERE role = 'member' 
          AND legal_entity_regcode IS NOT NULL
          AND (
            person_name ILIKE '%gmbh%' OR
            person_name ILIKE '%uab%' OR
            person_name ILIKE '%osaühing%' OR
            person_name ILIKE '%ltd%' OR
            person_name ILIKE '%ab%'
          )
        GROUP BY person_name, legal_entity_regcode
        LIMIT 20
    """))
    
    foreign_count = 0
    for row in result:
        print(f"  - {row[0][:60]:60} | regcode: {row[1]}")
        foreign_count += row[2]
    
    print(f"\nTotal foreign-looking entities: {foreign_count}")
    
    # Check companies table for these regcodes
    print("\n4. Checking if foreign regcodes exist in companies table:")
    result = conn.execute(text("""
        SELECT 
            p.person_name,
            p.legal_entity_regcode,
            c.name as company_name,
            c.type as company_type
        FROM persons p
        LEFT JOIN companies c ON c.regcode = p.legal_entity_regcode
        WHERE p.role = 'member' 
          AND p.legal_entity_regcode IS NOT NULL
          AND (
            p.person_name ILIKE '%gmbh%' OR
            p.person_name ILIKE '%uab%' OR
            p.person_name ILIKE '%osaühing%'
          )
        LIMIT 10
    """))
    
    for row in result:
        exists = "EXISTS" if row[2] else "NOT FOUND"
        print(f"  - {row[0][:40]:40} | {row[1]} | {exists}")
        if row[2]:
            print(f"    Company: {row[2][:50]} | Type: {row[3]}")

print("\n" + "="*80)
