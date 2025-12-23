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
        print(f"Loaded .env from {loc}")
        loaded = True
        break

if not loaded:
    print("Warning: No .env file found in common locations.")

url = os.getenv("DATABASE_URL")
if not url:
    print("Error: DATABASE_URL not found in environment!")
    sys.exit(1)

try:
    engine = create_engine(url)
    conn = engine.connect()
    
    # Read SQL
    migration_file = 'db/explorer_migration.sql'
    if not os.path.exists(migration_file):
        migration_file = 'backend/db/explorer_migration.sql'
    
    if not os.path.exists(migration_file):
         print(f"Error: Migration file not found at {migration_file}")
         sys.exit(1)

    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
        conn.execute(text(sql))
        conn.commit()
    
    print("Explorer Migration Success!")
except Exception as e:
    print(f"Migration Failed: {e}")
    sys.exit(1)
finally:
    if 'conn' in locals():
        conn.close()
