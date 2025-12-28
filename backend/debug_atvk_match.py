import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load env from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("ERROR: DATABASE_URL not found")
    sys.exit(1)

engine = create_engine(db_url)

regcode = "40203360721"
atvk_code = "0038550"

with engine.connect() as conn:
    # Get company details
    company = conn.execute(text("SELECT regcode, name, address, atvk FROM companies WHERE regcode = :regcode"), {"regcode": regcode}).fetchone()
    print(f"--- Company {regcode} ---")
    if company:
        print(f"Name: {company.name}")
        print(f"Address: {company.address}")
        print(f"ATVK: {company.atvk}")
    else:
        print("Company not found")

    # Get territory details
    territory = conn.execute(text("SELECT code, name, type, valid_to FROM territories WHERE code = :code"), {"code": atvk_code}).fetchone()
    print(f"\n--- Territory {atvk_code} ---")
    if territory:
        print(f"Name: {territory.name}")
        print(f"Type: {territory.type}")
        print(f"Valid To: {territory.valid_to}")
    else:
        print("Territory not found")
