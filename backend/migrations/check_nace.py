import os
import sys
from sqlalchemy import create_engine, text

try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
    load_dotenv(env_path)
    DATABASE_URL = os.getenv("DATABASE_URL")
except ImportError:
    DATABASE_URL = None

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found")
    sys.exit(1)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("\n--- SAMPLE NACE_SECTION ---")
    rows = conn.execute(text("SELECT nace_section, COUNT(*) as cnt FROM companies GROUP BY nace_section ORDER BY cnt DESC LIMIT 20")).fetchall()
    for r in rows:
        print(r)

    print("\n--- SAMPLE NACE_CODE ---")
    rows = conn.execute(text("SELECT left(nace_code, 2) as prefix, COUNT(*) as cnt FROM companies WHERE nace_code IS NOT NULL GROUP BY left(nace_code, 2) ORDER BY cnt DESC LIMIT 20")).fetchall()
    for r in rows:
        print(r)
