
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
            # Split SQL file into separate commands
            # This is safer than executing the whole file as one block with SQLAlchemy
            commands = sql_content.split(';')
            
            for command in commands:
                command = command.strip()
                if command:
                    try:
                        conn.execute(text(command))
                    except Exception as cmd_error:
                        logger.warning(f"Warning executing command: {command[:50]}... -> {cmd_error}")
                        # Don't raise immediately, try to continue (e.g. if index exists)
            
        logger.info("Successfully updated company_stats_materialized view!")
        
    except Exception as e:
        logger.error(f"Failed to update view: {e}")
        raise

if __name__ == "__main__":
    update_materialized_view()
