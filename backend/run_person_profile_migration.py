import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Try loading from multiple locations
locations = ['.env', '../.env', 'backend/.env']
loaded = False
for loc in locations:
    if os.path.exists(loc):
        load_dotenv(loc)
        print(f"✓ Loaded .env from {loc}")
        loaded = True
        break

if not loaded:
    print("⚠️  Warning: No .env file found in common locations.")

url = os.getenv("DATABASE_URL")
if not url:
    print("❌ Error: DATABASE_URL not found in environment!")
    sys.exit(1)

print(f"🔗 Connecting to database...")

try:
    engine = create_engine(url)
    conn = engine.connect()
    
    # Read SQL migration file
    migration_file = 'db/migrations/add_person_profile_indexes.sql'
    if not os.path.exists(migration_file):
        # Try referencing from backend root if run from project root
        migration_file = 'backend/db/migrations/add_person_profile_indexes.sql'
    
    if not os.path.exists(migration_file):
        print(f"❌ Error: Migration file not found at {migration_file}")
        sys.exit(1)
    
    print(f"📄 Reading migration file: {migration_file}")
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    print(f"🚀 Applying person profile indexes migration...")
    
    # Execute migration
    conn.execute(text(sql))
    conn.commit()
    
    print(f"✅ Migration Success!")
    print(f"")
    print(f"Created indexes:")
    print(f"  - idx_persons_person_code_active (partial index for active persons)")
    print(f"  - idx_persons_name_trgm (GIN index for person name search)")
    print(f"  - idx_persons_company_role (composite index for joins)")
    print(f"  - idx_persons_birth_date (for person matching)")
    print(f"")
    print(f"Person profile pages are now ready to use! 🎉")
    
except Exception as e:
    print(f"❌ Migration Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'conn' in locals():
        conn.close()
        print(f"🔌 Database connection closed.")
