
import sys
import os
import time
import logging
from sqlalchemy import text

# Add current directory to path to allow imports from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.routers.companies import engine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("db_runner")

def run_script(sql_file):
    if not os.path.exists(sql_file):
        logger.error(f"File not found: {sql_file}")
        return

    logger.info(f"Running SQL script: {sql_file}")
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql = f.read()
        
    start = time.time()
    try:
        with engine.connect() as conn:
            # We use execution_options to allow autocommit for some statements if needed,
            # but usually transaction is fine.
            # text() handles parameter binding, but here we run a raw script.
            # Some SQL scripts with multiple statements might need splitting, 
            # but this specific script is one large INSERT ... SELECT statement.
            conn.execute(text(sql))
            conn.commit()
            
        elapsed = time.time() - start
        logger.info(f"Success! Completed in {elapsed:.2f}s")
        
    except Exception as e:
        logger.error(f"Error executing script: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python backend/run_db_script.py <path_to_sql_file>")
        sys.exit(1)
        
    run_script(sys.argv[1])
