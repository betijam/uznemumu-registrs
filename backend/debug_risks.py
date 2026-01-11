from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import json

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
# Use the local connection string if env var not set correctly or accessible
if not DATABASE_URL or "railway" in DATABASE_URL:
    # Fallback/Manual URL - this assumes we're running in an environment where we can access the DB
    # If the user's psql failed, I'll try to rely on the environment variable first.
    pass

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Connected to DB")
        
        # Check specific companies
        regcodes = [40203360172, 40003806464]
        
        for regcode in regcodes:
            print(f"\n--- Checking {regcode} ---")
            
            # 1. Check if company exists
            comp = conn.execute(text("SELECT regcode, name FROM companies WHERE regcode = :r"), {"r": regcode}).fetchone()
            if comp:
                print(f"✅ Company found: {comp.name}")
            else:
                print(f"❌ Company NOT found in 'companies' table!")

            # 2. Check risks
            print(f"Scanning risks...")
            result = conn.execute(text("SELECT * FROM risks WHERE company_regcode = :r"), {"r": regcode}).fetchall()
            
            if not result:
                print("❌ No risk records found in DB.")
            else:
                print(f"✅ Found {len(result)} records:")
                for row in result:
                    d = dict(row._mapping)
                    print(json.dumps(d, indent=2, default=str))

except Exception as e:
    print(f"Error: {e}")
