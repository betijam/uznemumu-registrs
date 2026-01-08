
import os
import sys
import logging
import time
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Env
load_dotenv()

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.routers.companies import build_full_profile, engine

def run_debug():
    with engine.connect() as conn:
        # Get a real company
        row = conn.execute(text("SELECT * FROM companies LIMIT 1")).fetchone()
        if not row:
            print("No companies found.")
            return

        regcode = row.regcode
        print(f"Profiling Company: {regcode} - {row.name}")
        
        base_info = {
            "regcode": row.regcode,
            "name": row.name,
            "employee_count": row.employee_count,
            "tax_data_year": row.tax_data_year
        }
        
        start = time.time()
        result = build_full_profile(regcode, base_info)
        end = time.time()
        
        print(f"Total time: {end - start:.4f}s")

if __name__ == "__main__":
    run_debug()
