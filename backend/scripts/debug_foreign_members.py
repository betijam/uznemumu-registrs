"""
Debug script to check what data backend returns for a company with foreign members.
"""
import os
import sys
from sqlalchemy import text, create_engine

DATABASE_URL = os.getenv("DATABASE_URL")
if len(sys.argv) > 1:
    DATABASE_URL = sys.argv[1]

if not DATABASE_URL:
    print("Usage: railway run python scripts/debug_foreign_members.py")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

# Find a company with foreign members
print("="*80)
print("DEBUGGING FOREIGN MEMBER DATA")
print("="*80)

with engine.connect() as conn:
    # Find company with FOREIGN_ENTITY members
    result = conn.execute(text("""
        SELECT DISTINCT company_regcode
        FROM persons
        WHERE role = 'member' AND entity_type = 'FOREIGN_ENTITY'
        LIMIT 1
    """))
    
    company_regcode = result.scalar()
    
    if not company_regcode:
        print("No companies with FOREIGN_ENTITY members found!")
        sys.exit(1)
    
    print(f"\nCompany regcode: {company_regcode}")
    
    # Get all members for this company
    result = conn.execute(text("""
        SELECT 
            person_name,
            person_code,
            legal_entity_regcode,
            entity_type,
            role,
            number_of_shares,
            share_percent
        FROM persons
        WHERE company_regcode = :regcode AND role = 'member'
        ORDER BY entity_type
    """), {"regcode": company_regcode})
    
    print("\nMembers:")
    print("-" * 80)
    for row in result:
        print(f"Name: {row[0][:60]:60}")
        print(f"  person_code: {row[1]}")
        print(f"  legal_entity_regcode: {row[2]}")
        print(f"  entity_type: {row[3]}")
        print(f"  shares: {row[5]}")
        print()

print("="*80)
