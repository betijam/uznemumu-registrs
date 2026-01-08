
import os
import sys
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load Env
load_dotenv()

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.routers.companies import engine

def check_cache(regcode):
    with engine.connect() as conn:
        print(f"Checking cache for {regcode}...")
        row = conn.execute(text("SELECT graph_data FROM company_graph_cache WHERE company_regcode = :r"), {"r": regcode}).fetchone()
        
        if row:
            print("Cache FOUND.")
            data = row.graph_data
            keys = list(data.keys())
            print(f"Keys: {keys}")
            if 'officers' in data:
                print(f"Officers count: {len(data['officers'])}")
            else:
                print("MISSING 'officers' key in cache!")
        else:
            print("Cache NOT FOUND for this company.")

if __name__ == "__main__":
    check_cache(210200787)
