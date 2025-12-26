import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load env from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("ERROR: DATABASE_URL not found in environment")
    sys.exit(1)

print(f"Connecting to: {db_url.split('@')[1] if '@' in db_url else '...'}...")
engine = create_engine(db_url)

with engine.connect() as conn:
    total = conn.execute(text("SELECT COUNT(*) FROM companies")).scalar()
    with_atvk = conn.execute(text("SELECT COUNT(*) FROM companies WHERE atvk IS NOT NULL")).scalar()
    
    print(f"Total companies: {total}")
    print(f"Companies with ATVK: {with_atvk}")
    
    if total > 0:
        print(f"Coverage: {(with_atvk/total)*100:.2f}%")
