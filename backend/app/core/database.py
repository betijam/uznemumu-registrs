import os
import logging
from sqlalchemy import create_engine
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.error("DATABASE_URL is not set!")
    # Fallback to avoid crash, but will fail to connect
    DATABASE_URL = "postgresql://postgres:password@localhost:5432/ur_db"

# Optimized engine for API usage
# - pool_size=20: Keep 20 connections open (increases from default 5)
# - max_overflow=10: Allow 10 more during spikes
# - pool_pre_ping=True: Check connection health before using (avoids "closed connection" errors)
# - pool_recycle=1800: Recycle connections every 30 mins to prevent stale timeouts
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True
)

logger.info(f"Initialized API Database Engine with pool_size=20")
