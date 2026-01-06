import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/ur_db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

print("=== Checking staging tables ===")
with engine.connect() as conn:
    for table in ['aw_dziv', 'aw_eka', 'aw_pilseta', 'aw_novads', 'aw_pagasts', 'aw_ciems', 'aw_iela']:
        result = conn.execute(text(f"SELECT COUNT(*) FROM stage.{table}"))
        count = result.scalar()
        print(f"stage.{table}: {count} rows")

print("\n=== Manually inserting to core.address_objects ===")
with engine.connect() as conn:
    # Try the insert manually
    conn.execute(text("TRUNCATE core.address_objects"))
    
    result = conn.execute(text("""
        INSERT INTO core.address_objects (kods, tips_cd, std, nosaukums, vkur_cd, vkur_tips, source)
        SELECT objekta_kods, objekta_tips, adrese, nosaukums, augst_objekta_kods, augst_objekta_tips, 'DZIV' 
        FROM stage.aw_dziv WHERE objekta_kods IS NOT NULL
        RETURNING kods
    """))
    count = len(list(result))
    conn.commit()
    print(f"Inserted {count} rows from aw_dziv")

print("\n=== Verifying core.address_objects ===")
with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM core.address_objects"))
    count = result.scalar()
    print(f"core.address_objects now has: {count} rows")
    
    result = conn.execute(text("SELECT tips_cd, COUNT(*) FROM core.address_objects GROUP BY tips_cd ORDER BY tips_cd"))
    for row in result:
        print(f"  Type {row.tips_cd}: {row[1]} rows")
