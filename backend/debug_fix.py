
import os
import sys
import json
import time
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load Env
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.routers.companies import engine, build_full_profile

def check_and_fix(regcode):
    with engine.connect() as conn:
        # Check Persons
        print(f"Checking PERSONS for {regcode}...")
        count = conn.execute(text("SELECT COUNT(*) FROM persons WHERE company_regcode = :r"), {"r": regcode}).scalar()
        if count > 0:
            print("Company has persons. Running manual build_full_profile (this should populate cache if missing)...")
            from app.services.graph_service import calculate_company_graph
            print("Calculating Graph / Cache...")
            start = time.time()
            graph_data = calculate_company_graph(conn, regcode)
            print(f"Graph calculated in {time.time() - start:.4f}s")
            
            # Save to Cache Manually
            conn.execute(text("""
                INSERT INTO company_graph_cache (company_regcode, graph_data, updated_at)
                VALUES (:r, :d, NOW())
                ON CONFLICT (company_regcode) DO UPDATE SET graph_data = :d, updated_at = NOW()
            """), {"r": regcode, "d": json.dumps(graph_data)})
            conn.commit()
            print("Graph Cache Updated.")
            
    # Now run profile again outside the manual calc block, but we need a fresh call or just use build_full_profile
    # build_full_profile handles its own connections mostly, but wait...
    print("Running build_full_profile again...")
    start = time.time()
    # Mock base info
    base_info = {"regcode": regcode, "name": "TEST", "employee_count": 5, "tax_data_year": 2024}
    res = build_full_profile(regcode, base_info)
    print(f"Profile built in {time.time() - start:.4f}s")
    
    if 'graph' in res:
            print("SUCCESS: Profile contains graph data from cache.")
    else:
            print("FAILURE: Profile did not use cache.")

if __name__ == "__main__":
    check_and_fix(40203360721)
