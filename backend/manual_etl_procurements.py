import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add backend to sys.path so imports work
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

try:
    from etl.process_procurements import process_procurements_etl
    
    logger.info("🚀 Starting Manual Procurement ETL Load...")
    process_procurements_etl()
    logger.info("✅ Procurement ETL Load Completed Successfully!")
    
except Exception as e:
    logger.error(f"❌ ETL Failed: {e}")
    raise
