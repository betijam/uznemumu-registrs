import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add backend to sys.path so imports work
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Force localhost connection for manual execution if not set
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "postgresql://postgres:password@localhost:5432/ur_db"

try:
    from etl.process_procurements import process_procurements_etl
    
    logger.info("🚀 Starting Manual Procurement ETL Load...")
    process_procurements_etl()
    logger.info("✅ Procurement ETL Load Completed Successfully!")
    
except Exception as e:
    logger.error(f"❌ ETL Failed: {e}")
    raise
