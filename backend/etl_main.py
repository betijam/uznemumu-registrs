import os
import sys
import logging
from datetime import datetime, timezone

from etl import run_all_etl

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("etl_main")


def _env_truthy(value: str | None) -> bool:
    """Check if environment variable is set to a truthy value."""
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def main() -> int:
    """
    ETL entrypoint that NEVER runs ETL by default.
    To run ETL you must explicitly enable it:
      - ENV: RUN_ETL=true
      - or CLI: --run
    """

    # Explicit enablement
    run_flag = "--run" in sys.argv
    run_env = _env_truthy(os.getenv("RUN_ETL"))

    # Optional safety: require a "reason" (useful for logs)
    reason = os.getenv("ETL_REASON", "").strip()

    logger.info("=" * 60)
    logger.info("ETL Service Boot")
    logger.info("=" * 60)
    logger.info(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    logger.info(f"RUN_ETL env: {os.getenv('RUN_ETL')}")
    logger.info(f"CLI --run flag: {run_flag}")
    if reason:
        logger.info(f"ETL_REASON: {reason}")

    if not (run_flag or run_env):
        logger.info("")
        logger.info("🛑 ETL is DISABLED. Exiting without running anything.")
        logger.info("   To run ETL, set RUN_ETL=true or pass --run flag.")
        logger.info("=" * 60)
        return 0

    logger.info("")
    logger.info("🚀 Starting ETL (explicitly enabled)")
    logger.info("=" * 60)
    
    try:
        # Step 1: Run main ETL (companies, financial reports, etc.)
        run_all_etl()
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ Main ETL finished successfully")
        
        # Step 2: Process PVN data (VAT taxpayer registry)
        logger.info("")
        logger.info("📌 Processing PVN (VAT) data...")
        try:
            from etl.process_pvn import process_pvn_registry
            process_pvn_registry()
            logger.info("✅ PVN processing complete")
        except Exception as e:
            logger.warning(f"⚠️ PVN processing failed (non-critical): {e}")
        
        # Step 3: Calculate company sizes
        logger.info("")
        logger.info("📊 Calculating company sizes...")
        try:
            # Import and run from update_company_sizes
            import sys
            sys.path.insert(0, os.path.dirname(__file__))
            from update_company_sizes import process_company_sizes
            process_company_sizes()
            logger.info("✅ Company size calculation complete")
        except Exception as e:
            logger.warning(f"⚠️ Company size calculation failed (non-critical): {e}")
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ All ETL processes finished successfully")
        logger.info("=" * 60)
        return 0
    except Exception:
        logger.exception("❌ ETL failed")
        logger.info("=" * 60)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
