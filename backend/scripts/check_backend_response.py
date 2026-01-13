"""
Check what backend returns for company 40002074377 (has FOREIGN_ENTITY member).
"""
import os
import sys
from sqlalchemy import text, create_engine
import json

DATABASE_URL = os.getenv("DATABASE_URL")
if len(sys.argv) > 1:
    DATABASE_URL = sys.argv[1]

if not DATABASE_URL:
    print("Usage: railway run python scripts/check_backend_response.py")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

# Simulate what get_persons returns
company_regcode = 40002074377

print("="*80)
print(f"CHECKING BACKEND RESPONSE FOR COMPANY {company_regcode}")
print("="*80)

with engine.connect() as conn:
    rows = conn.execute(text("""
        SELECT person_name, role, share_percent, date_from, person_code, birth_date,
               position, rights_of_representation, representation_with_at_least,
               number_of_shares, share_nominal_value, share_currency, legal_entity_regcode,
               nationality, residence, entity_type
        FROM persons WHERE company_regcode = :r AND role = 'member'
    """), {"r": company_regcode}).fetchall()
    
    print(f"\nFound {len(rows)} members")
    print("\nBackend will return:")
    print("-" * 80)
    
    for p in rows:
        member_dict = {
            "name": p.person_name,
            "person_code": p.person_code,
            "legal_entity_regcode": int(p.legal_entity_regcode) if p.legal_entity_regcode else None,
            "entity_type": p.entity_type if hasattr(p, 'entity_type') else None,
            "has_profile": p.entity_type != 'FOREIGN_ENTITY' if p.legal_entity_regcode else True,
            "number_of_shares": int(p.number_of_shares) if p.number_of_shares else None,
            "percent": 0  # simplified
        }
        
        print(json.dumps(member_dict, indent=2, ensure_ascii=False))
        print()

print("="*80)
