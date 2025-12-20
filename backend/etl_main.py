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
        run_all_etl()
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ ETL finished successfully")
        logger.info("=" * 60)
        return 0
    except Exception:
        logger.exception("❌ ETL failed")
        logger.info("=" * 60)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
