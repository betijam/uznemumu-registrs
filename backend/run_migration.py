"""
Run Database Migration for Extended Financial Fields
Usage: python run_migration.py
"""
import os
from sqlalchemy import create_engine, text
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set. Check your .env file.")

logger.info(f"Connecting to database...")
engine = create_engine(DATABASE_URL)

# Read migration SQL
migration_file = os.path.join(
    os.path.dirname(__file__), 
    'db', 
    'migrations', 
    'add_extended_financial_fields.sql'
)

logger.info(f"Reading migration file: {migration_file}")
with open(migration_file, 'r', encoding='utf-8') as f:
    migration_sql = f.read()

# Execute migration
try:
    with engine.connect() as conn:
        logger.info("Executing migration...")
        
        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        for i, stmt in enumerate(statements, 1):
            logger.info(f"Executing statement {i}/{len(statements)}...")
            conn.execute(text(stmt))
            conn.commit()
        
        logger.info("✅ Migration completed successfully!")
        
        # Verify new columns exist
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'financial_reports' 
            AND column_name IN (
                'accounts_receivable', 
                'by_nature_labour_expenses',
                'cfo_im_net_operating_cash_flow',
                'cfo_im_income_taxes_paid',
                'cfi_acquisition_of_fixed_assets_intangible_assets',
                'cff_net_financing_cash_flow'
            )
            ORDER BY column_name
        """))
        
        new_columns = [row[0] for row in result]
        logger.info(f"✅ Verified new columns: {', '.join(new_columns)}")
        
except Exception as e:
    logger.error(f"❌ Migration failed: {e}")
    raise

logger.info("Migration complete. You can now run the incremental ETL update.")
