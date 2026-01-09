import sys
import os
import logging

# Setup logging FIRST
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("python-dotenv not installed, assuming environment variables are set")

# Check if DATABASE_URL is set
if "DATABASE_URL" not in os.environ:
    logger.warning("DATABASE_URL not found in environment. Defaulting to localhost.")
    os.environ["DATABASE_URL"] = "postgresql://postgres:password@localhost:5432/ur_db"
else:
    # Mask password for logging
    db_url = os.environ["DATABASE_URL"]
    masked_url = db_url.split('@')[-1] if '@' in db_url else '***'
    logger.info(f"Using DATABASE_URL connecting to: {masked_url}")

from sqlalchemy import text
from etl.loader import engine

def run_migration():
    sql = """
    -- Add contract end date and termination date columns
    ALTER TABLE procurements ADD COLUMN IF NOT EXISTS contract_end_date DATE;
    ALTER TABLE procurements ADD COLUMN IF NOT EXISTS termination_date DATE;

    -- Add deduplication columns
    ALTER TABLE procurements ADD COLUMN IF NOT EXISTS procurement_id TEXT;
    ALTER TABLE procurements ADD COLUMN IF NOT EXISTS part_number TEXT;

    -- Create index for performance on date filtering
    CREATE INDEX IF NOT EXISTS idx_procurements_end_date ON procurements(contract_end_date);
    CREATE INDEX IF NOT EXISTS idx_procurements_id ON procurements(procurement_id);
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
        logger.info("Migration executed successfully.")
    except Exception as e:
        logger.error(f"Migration failed: {e}")

if __name__ == "__main__":
    run_migration()
