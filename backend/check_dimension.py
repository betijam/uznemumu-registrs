import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/ur_db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

print("=== Checking if ēka and iela are in dimension ===\n")

with engine.connect() as conn:
    # Check specific unmatched IDs
    test_ids = ['100301913', '101997600', '105402756', '105807560', '105859818']
    
    for aid in test_ids:
        result = conn.execute(text("""
            SELECT address_id, full_address, city_name, municipality_name
            FROM address_dimension
            WHERE address_id = :aid
        """), {"aid": aid})
        
        row = result.fetchone()
        if row:
            print(f"✅ {aid}: {row.full_address[:60] if row.full_address else 'N/A'}")
            print(f"   City: {row.city_name}, Municipality: {row.municipality_name}")
        else:
            print(f"❌ {aid}: NOT in dimension!")
            
            # Check in address_objects
            result2 = conn.execute(text("""
                SELECT kods, tips_cd, std, nosaukums
                FROM core.address_objects
                WHERE kods = :aid
            """), {"aid": aid})
            row2 = result2.fetchone()
            if row2:
                print(f"   Found in address_objects: type {row2.tips_cd}, {row2.nosaukums}")
    
    # Count by starting type
    print("\n=== Dimension entries by starting type ===")
    result = conn.execute(text("""
        SELECT 
            LEFT(a.address_id, 3) as prefix,
            o.tips_cd,
            COUNT(*) as cnt
        FROM address_dimension a
        JOIN core.address_objects o ON a.address_id = o.kods
        GROUP BY LEFT(a.address_id, 3), o.tips_cd
        ORDER BY cnt DESC
        LIMIT 10
    """))
    
    for row in result:
        print(f"  Type {row.tips_cd}: {row.cnt:,} entries")
