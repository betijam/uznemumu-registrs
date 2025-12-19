from .config import DATA_URLS
from .download import download_all_data
from .process_companies import process_companies
from .process_persons import process_persons
from .process_risks import process_risks
from .process_finance import process_finance
from .process_procurements import process_procurements_etl
from .process_taxes import process_vid_data
import logging

logger = logging.getLogger(__name__)

def run_all_etl():
    logger.info("Starting Full ETL Job...")
    
    # 1. Download
    files = download_all_data()
    
    # 2. Process Companies
    if 'register' in files:
         process_companies(files['register'], files.get('equity'))
         
    # 3. Process Persons
    if 'officers' in files:
         process_persons(files['officers'], files.get('members'), files.get('ubo'))
         
    # 4. Process Risks
    if 'sanctions' in files:
         process_risks(files['sanctions'], files.get('liquidations'), files.get('prohibitions'), files.get('securing_measures'))
         
    # 5. Process Finance
    if 'financial_statements' in files:
         process_finance(files['financial_statements'], files.get('balance_sheets'), files.get('income_statements'))
         
    # 6. Process Procurements (Multi-year - downloads data internally)
    process_procurements_etl()
    
    # 7. Process VID Tax Data (downloads data internally)
    process_vid_data()
         
    logger.info("ETL Job Completed.")
