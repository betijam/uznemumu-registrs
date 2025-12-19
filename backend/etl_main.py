#!/usr/bin/env python3
"""
ETL Service Entry Point
Runs ETL process once and exits (for Railway cron jobs or manual triggers)
"""
import logging
from etl import run_all_etl

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("🚀 Starting ETL Service (One-time run)")
    try:
        run_all_etl()
        logger.info("✅ ETL Service completed successfully")
    except Exception as e:
        logger.error(f"❌ ETL Service failed: {e}", exc_info=True)
        raise
