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
    SELECT year, turnover, profit, employees, cash_balance,
           current_ratio, quick_ratio, cash_ratio,
           net_profit_margin, roe, roa, debt_to_equity, equity_ratio, ebitda,
           interest_expenses, depreciation_expenses, provision_for_income_taxes, by_nature_labour_expenses,
           accounts_receivable, inventories, current_liabilities, non_current_liabilities, equity, total_assets, total_current_assets,
           cfo_im_net_operating_cash_flow, cff_net_financing_cash_flow, cfi_acquisition_of_fixed_assets_intangible_assets,
           cfo_im_income_taxes_paid
    FROM financial_reports 
    WHERE company_regcode = :r 
    ORDER BY year DESC
    LIMIT 3
""")

with engine.connect() as conn:
    result = conn.execute(query, {"r": int(REGCODE)})
    rows = result.fetchall()
    
    if not rows:
        print(f"No financial records found for regcode {REGCODE}")
    else:
        print(f"DEBUG: Financial records for {REGCODE}:")
        for row in rows:
            print(f"\nYear: {row.year}")
            print(f"  interest_expenses: {row.interest_expenses}")
            print(f"  depreciation_expenses: {row.depreciation_expenses}")
            print(f"  provision_for_income_taxes: {row.provision_for_income_taxes}")
            print(f"  by_nature_labour_expenses: {row.by_nature_labour_expenses}")
            print(f"  inventories: {row.inventories}")
            print(f"  non_current_liabilities: {row.non_current_liabilities}")
            print(f"  cfo_im_net_operating_cash_flow (CFO): {row.cfo_im_net_operating_cash_flow}")
            print(f"  cfo_im_income_taxes_paid (Taxes Paid): {row.cfo_im_income_taxes_paid}")
            print(f"  cfi_acquisition_of_fixed_assets_intangible_assets (CapEx): {row.cfi_acquisition_of_fixed_assets_intangible_assets}")
