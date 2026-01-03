import sys
import os

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Force localhost for local execution (overrides default 'db' host)
os.environ["DATABASE_URL"] = "postgresql://postgres:password@localhost:5432/ur_db"

from sqlalchemy import text
from etl.loader import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    sql = """
    -- Add contract end date and termination date columns
    ALTER TABLE procurements ADD COLUMN IF NOT EXISTS contract_end_date DATE;
    ALTER TABLE procurements ADD COLUMN IF NOT EXISTS termination_date DATE;

    -- Create index for performance on date filtering
    CREATE INDEX IF NOT EXISTS idx_procurements_end_date ON procurements(contract_end_date);
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
