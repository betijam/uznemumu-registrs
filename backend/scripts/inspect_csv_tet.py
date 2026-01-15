
import pandas as pd
import sys

# Path using the one we downloaded
CSV_PATH = "backend/data/financial_statements.csv"

def inspect_tet_csv():
    target_regcode = "40003052786"  # Tet
    
    print(f"🔎 Scanning {CSV_PATH} for regcode {target_regcode}...")
    
    # We only need specific columns to verify existence
    use_cols = ['legal_entity_registration_number', 'year', 'type', 'net_turnover', 'neto_apgrozijums']
    
    found_count = 0
    
    # Read in chunks to handle large file
    for chunk in pd.read_csv(CSV_PATH, sep=';', dtype=str, chunksize=100000, on_bad_lines='skip'):
        # Normalize column names slightly for checking
        chunk.columns = [c.lower() for c in chunk.columns]
        
        # Look for target
        if 'legal_entity_registration_number' in chunk.columns:
            matches = chunk[chunk['legal_entity_registration_number'] == target_regcode]
            
            for _, row in matches.iterrows():
                found_count += 1
                # Try to get turnover from either column name variant
                turnover = row.get('net_turnover') or row.get('neto_apgrozijums') or "N/A"
                st = row.get('source_type') or row.get('type')
                print(f"Found: Year={row.get('year')} | SourceType={st}")

    if found_count == 0:
        print("❌ No records found for Tet in CSV.")
    else:
        print(f"✅ Total records found: {found_count}")

if __name__ == "__main__":
    inspect_tet_csv()
