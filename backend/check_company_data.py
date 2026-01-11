import os
import sqlalchemy as sa
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not found in environment")
    exit(1)

engine = sa.create_engine(DATABASE_URL)

REGCODE = "40003520643"

query = text("""
    SELECT 
        year,
        by_nature_labour_expenses,
        provision_for_income_taxes,
        depreciation_expenses,
        interest_expenses,
        inventories,
        non_current_liabilities,
        cfo_im_income_taxes_paid,
        cfi_acquisition_of_fixed_assets_intangible_assets
    FROM financial_reports
    WHERE company_regcode = :regcode
    ORDER BY year DESC
    LIMIT 3
""")

with engine.connect() as conn:
    result = conn.execute(query, {"regcode": int(REGCODE)})
    rows = result.fetchall()
    
    if not rows:
        print(f"No financial records found for regcode {REGCODE}")
    else:
        print(f"Financial records for {REGCODE}:")
        for row in rows:
            print(f"\nYear: {row.year}")
            print(f"  Labour Expenses (by_nature_labour_expenses): {row.by_nature_labour_expenses}")
            print(f"  Income Tax Provision (provision_for_income_taxes): {row.provision_for_income_taxes}")
            print(f"  Depreciation (depreciation_expenses): {row.depreciation_expenses}")
            print(f"  Interest Expenses (interest_expenses): {row.interest_expenses}")
            print(f"  Inventories (inventories): {row.inventories}")
            print(f"  Non-Current Liabilities (non_current_liabilities): {row.non_current_liabilities}")
            print(f"  Taxes Paid CF (cfo_im_income_taxes_paid): {row.cfo_im_income_taxes_paid}")
            print(f"  CapEx (cfi_acquisition_of_fixed_assets_intangible_assets): {row.cfi_acquisition_of_fixed_assets_intangible_assets}")
