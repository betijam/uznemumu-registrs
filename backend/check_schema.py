import os
import sys
from sqlalchemy import text, inspect
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Load env variables
load_dotenv()

# Force check env
if "DATABASE_URL" not in os.environ:
    print("❌ DATABASE_URL not set!")
    sys.exit(1)

print(f"Checking DB: {os.environ['DATABASE_URL'].split('@')[-1]}")

from etl.loader import engine

def check_schema():
    inspector = inspect(engine)
    columns = inspector.get_columns('procurements')
    
    found_end_date = False
    found_term_date = False
    
    print("\nColumns in 'procurements' table:")
    for col in columns:
        print(f" - {col['name']} ({col['type']})")
        if col['name'] == 'contract_end_date':
            found_end_date = True
        if col['name'] == 'termination_date':
            found_term_date = True
            
    print("\nStatus:")
    print(f" - contract_end_date: {'✅ FOUND' if found_end_date else '❌ MISSING'}")
    print(f" - termination_date: {'✅ FOUND' if found_term_date else '❌ MISSING'}")

if __name__ == "__main__":
    check_schema()
