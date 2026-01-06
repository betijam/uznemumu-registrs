import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/ur_db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

print("=== Debugging Empty Dimension ===\n")

with engine.connect() as conn:
    # Check if core.address_objects still has data
    result = conn.execute(text("SELECT COUNT(*) FROM core.address_objects"))
    count = result.scalar()
    print(f"core.address_objects: {count:,} rows")
    
    # Check staging tables
    result = conn.execute(text("SELECT COUNT(*) FROM stage.aw_dziv"))
    count = result.scalar()
    print(f"stage.aw_dziv: {count:,} rows")
    
    # Check dimension
    result = conn.execute(text("SELECT COUNT(*) FROM address_dimension"))
    count = result.scalar()
    print(f"address_dimension: {count:,} rows")
    
    # Check if procedure exists
    result = conn.execute(text("""
        SELECT proname, pg_get_functiondef(oid) as definition
        FROM pg_proc
        WHERE proname = 'refresh_address_dimension'
    """))
    
    proc = result.fetchone()
    if proc:
        print(f"\n✅ Procedure exists: {proc.proname}")
        # Check if it has the new logic
        if "'109', '108', '104'" in proc.definition:
            print("✅ Procedure has updated logic")
        else:
            print("❌ Procedure has OLD logic - needs update")
    else:
        print("\n❌ Procedure does NOT exist!")
