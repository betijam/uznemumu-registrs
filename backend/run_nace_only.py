"""
Script to run NACE processing only
Updates company industry classifications
"""
import os
from etl.process_nace import process_nace
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # File paths
    VID_TAX_CSV = "data/VID_VSAOI.csv"
    NACE_CSV = "NACE.csv"
    
    # Check if files exist
    if not os.path.exists(VID_TAX_CSV):
        logger.error(f"VID tax file not found: {VID_TAX_CSV}")
        logger.info("Please ensure VID_VSAOI.csv is in the data/ folder")
        exit(1)
    
    if not os.path.exists(NACE_CSV):
        logger.error(f"NACE file not found: {NACE_CSV}")
        logger.info("Please ensure NACE.csv is in the root folder")
        exit(1)
    
    logger.info("Starting NACE processing...")
    logger.info(f"VID file: {VID_TAX_CSV}")
    logger.info(f"NACE file: {NACE_CSV}")
    
    try:
        process_nace(VID_TAX_CSV, NACE_CSV)
        logger.info("✅ NACE processing completed successfully!")
    except Exception as e:
        logger.error(f"❌ NACE processing failed: {e}")
        raise
