import requests
import json

# Test company regcode
regcode = "40003520643"

# Test the financial history endpoint
url = f"http://localhost:8001/companies/{regcode}/financial-history"

print(f"Testing financial data for company {regcode}...")
print(f"URL: {url}\n")

try:
    response = requests.get(url)
    print(f"Status Code: {response.status_code}\n")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Number of years: {len(data)}\n")
        
        if len(data) > 0:
            latest = data[0]
            print("Latest year data:")
            print(f"Year: {latest.get('year')}")
            print(f"\n=== P&L Data ===")
            print(f"Turnover: {latest.get('turnover')}")
            print(f"Profit: {latest.get('profit')}")
            print(f"Labour costs: {latest.get('labour_costs')}")
            print(f"Interest payment: {latest.get('interest_payment')}")
            print(f"Depreciation: {latest.get('depreciation')}")
            print(f"Corporate income tax: {latest.get('corporate_income_tax')}")
            
            print(f"\n=== Balance Sheet Data ===")
            print(f"Total assets: {latest.get('total_assets')}")
            print(f"Equity: {latest.get('equity')}")
            print(f"Current liabilities: {latest.get('current_liabilities')}")
            print(f"Non-current liabilities: {latest.get('non_current_liabilities')}")
            print(f"Inventories: {latest.get('inventories')}")
            
            print(f"\n=== Cash Flow Data ===")
            print(f"CFO: {latest.get('cfo')}")
            print(f"Taxes paid (CF): {latest.get('taxes_paid_cf')}")
            print(f"CFI: {latest.get('cfi')}")
            print(f"CFF: {latest.get('cff')}")
            
            print(f"\n=== Full JSON ===")
            print(json.dumps(latest, indent=2, ensure_ascii=False))
        else:
            print("No financial data found!")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")
