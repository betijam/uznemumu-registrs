import os
import sys
from sqlalchemy import create_engine, text
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if len(sys.argv) < 2:
    print("Usage: python run_any_migration.py <path_to_sql_file>")
    sys.exit(1)

migration_file = sys.argv[1]

if not os.path.exists(migration_file):
    print(f"Error: File '{migration_file}' not found.")
    sys.exit(1)

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set")

engine = create_engine(DATABASE_URL)

try:
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    with engine.connect() as conn:
        # Split by semicolon to handle multiple statements
        statements = [s.strip() for s in sql.split(';') if s.strip()]
        for stmt in statements:
            conn.execute(text(stmt))
            conn.commit()
            
    logger.info(f"✅ Successfully executed {migration_file}")

except Exception as e:
    logger.error(f"❌ Failed to execute migration: {e}")
    sys.exit(1)
