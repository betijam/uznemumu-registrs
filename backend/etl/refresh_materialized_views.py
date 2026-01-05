import logging
import os
from sqlalchemy import text
from .loader import engine

logger = logging.getLogger(__name__)

def refresh_materialized_views():
    """
    Creates and Refreshes Materialized Views for high-performance analytics.
    """
    logger.info("Refreshing Materialized Views...")
    
    # Path to SQL definition
    sql_path = os.path.join(os.path.dirname(__file__), '..', 'db', 'materialized_stats.sql')
    
    if not os.path.exists(sql_path):
        logger.error("materialized_stats.sql not found!")
        return

    with open(sql_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    with engine.connect() as conn:
        # 1. Check if view exists
        view_exists = conn.execute(text("SELECT EXISTS (SELECT FROM pg_matviews WHERE matviewname = 'company_stats_materialized')")).scalar()
        
        if not view_exists:
            logger.info("Creating Materialized View for the first time...")
            # Execute the full SQL script (CREATE MATERIALIZED VIEW ...)
            # We need to split if there are multiple statements? The file has CREATE and indexes.
            # Using transaction to run it all.
             # Split by semicolon? Or just run block?
             # Simple split by ; might fail on complex bodies but this is simple SQL.
            statements = [s.strip() for s in sql_content.split(';') if s.strip()]
            for stmt in statements:
                conn.execute(text(stmt))
            logger.info("Materialized View Created.")
        else:
            logger.info("Refreshing Materialized View...")
            conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY company_stats_materialized"))
            logger.info("Refresh complete.")
            
        conn.commit()
