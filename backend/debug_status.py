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

url = os.getenv("DATABASE_URL")
if not url:
    print("Error: DATABASE_URL not found!")
    sys.exit(1)

try:
    engine = create_engine(url)
    with engine.connect() as conn:
        print("\n--- DISTINCT STATUS VALUES ---")
        result = conn.execute(text("SELECT DISTINCT status, COUNT(*) as cnt FROM companies GROUP BY status ORDER BY cnt DESC LIMIT 20"))
        for row in result:
            print(f"'{row.status}' (Count: {row.cnt})")
        
        print("\n--- SAMPLE ACTIVE CHECK ---")
        # Test the clause I was using
        clause = "(status IS NULL OR status = '' OR status = 'A' OR status ILIKE 'aktīvs')"
        cnt = conn.execute(text(f"SELECT COUNT(*) FROM companies WHERE {clause}")).scalar()
        print(f"Rows matching 'Active' clause: {cnt}")

except Exception as e:
    print(f"Error: {e}")
