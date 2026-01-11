
import os
import sys
import logging
from sqlalchemy import create_engine, text

# Add backend directory to path so we can import app if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_materialized_view():
    """
    Drops and recreates the company_stats_materialized view 
    using the definition from db/materialized_stats.sql
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL env var not set")
        return

    logger.info(f"Connecting to database...")
    engine = create_engine(database_url)

    # Read the SQL file
    sql_file_path = os.path.join(os.path.dirname(__file__), "db", "materialized_stats.sql")
    try:
        with open(sql_file_path, "r", encoding="utf-8") as f:
            sql_content = f.read()
            
        logger.info("Executing materialized_stats.sql...")
        with engine.begin() as conn:
            # We need to execute the statements. 
            # The file might contain multiple statements separated by ;
            # But create materialized view usually needs to be one block or handled carefully.
            # Let's try executing the whole block if possible, or split by ; if simple.
            
            # Since the file has DROP and CREATE, running it as a block might work depending on driver.
            # But let's act safe and Execute explicit commands.
             
            # 1. Drop
            conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS company_stats_materialized CASCADE;"))
            logger.info("Dropped old view.")

            # 2. Create View Query - we need to extract the CREATE VIEW part or just run the file content if simple.
            # The file content is:
            # DROP ...;
            # CREATE MATERIALIZED VIEW ... AS ... WITH DATA;
            # CREATE INDEX ...;
            
            # Let's execute the file content directly.
            conn.execute(text(sql_content))
            
        logger.info("Successfully updated company_stats_materialized view!")
        
    except Exception as e:
        logger.error(f"Failed to update view: {e}")
        raise

if __name__ == "__main__":
    update_materialized_view()
