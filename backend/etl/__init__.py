from .config import DATA_URLS
from .download import download_all_data
from .process_companies import process_companies
from .process_persons import process_persons
from .process_risks import process_risks
from .process_finance import process_finance
from .process_procurements import process_procurements_etl
from .process_taxes import process_vid_data
from .process_nace import process_nace
from .loader import engine
from sqlalchemy import text
import logging
import os

logger = logging.getLogger(__name__)

def init_database():
    """Create all tables if they don't exist (for Railway/cloud deployment)"""
    logger.info("Initializing database tables...")
    
    # Read init.sql from the db folder
    init_sql_path = os.path.join(os.path.dirname(__file__), '..', 'db', 'init.sql')
    
    if not os.path.exists(init_sql_path):
        logger.warning(f"init.sql not found at {init_sql_path}")
        return False
    
    with open(init_sql_path, 'r', encoding='utf-8') as f:
        init_sql = f.read()
    
    with engine.connect() as conn:
        # Check if tables already exist
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'companies'
            );
        """))
        tables_exist = result.scalar()
        
        if tables_exist:
            logger.info("Tables already exist, skipping initialization.")
            return True
        
        # Execute init.sql statements
        try:
            # Split by semicolon and execute each statement
            statements = [s.strip() for s in init_sql.split(';') if s.strip()]
            for stmt in statements:
                if stmt:
                    conn.execute(text(stmt))
            conn.commit()
            logger.info("✅ Database tables created successfully!")
            return True
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            conn.rollback()
            return False

def run_all_etl():
    logger.info("Starting Full ETL Job...")
    
    # 0. Initialize database tables first
    init_database()
    
    # 1. Download
    files = download_all_data()
    
    # 2. Process Companies
    if 'register' in files:
         process_companies(files['register'], files.get('equity'))
    
    # 3. Process NACE Classification (must run after companies are loaded)
    nace_path = os.path.join(os.path.dirname(__file__), '..', '..', 'NACE.csv')
    if os.path.exists(nace_path):
        # VID tax data is downloaded by process_vid_data, but we can also use it here
        # For now, we'll integrate NACE with VID processing
        logger.info("NACE dictionary found, will process with VID data")
    else:
        logger.warning("NACE.csv not found in project root")
         
    # 4. Process Persons
    if 'officers' in files:
         process_persons(files['officers'], files.get('members'), files.get('ubo'))
         
    # 5. Process Risks
    if 'sanctions' in files:
         process_risks(files['sanctions'], files.get('liquidations'), files.get('prohibitions'), files.get('securing_measures'))
         
    # 6. Process Finance
    if 'financial_statements' in files:
         process_finance(files['financial_statements'], files.get('balance_sheets'), files.get('income_statements'))
         
    # 7. Process Procurements (Multi-year - downloads data internally)
    process_procurements_etl()
    
    # 8. Process VID Tax Data + NACE (downloads data internally)
    process_vid_data()
         
    logger.info("ETL Job Completed.")

