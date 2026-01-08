import re
from sqlalchemy import text
from etl.loader import engine

def normalize_name(name):
    if not name:
        return ""
    # Remove common suffixes/prefixes
    n = name.lower()
    n = n.replace(" nov.", "").replace(" novads", "")
    n = n.replace(" pilsēta", "").replace(" valstspilsēta", "")
    n = n.replace(" pag.", "").replace(" pagasts", "")
    n = n.strip()
    return n

def populate_atvk():
    with engine.connect() as conn:
        print("--- Populating Companies ATVK from Address Dimension ---")
        
        # 1. Load Territories (Level 2 = Municipalities)
        print("Loading territories...")
        territories = conn.execute(text("SELECT code, name FROM territories WHERE level = 2")).fetchall()
        atvk_map = {}
        for t in territories:
            norm = normalize_name(t.name)
            atvk_map[norm] = t.code
            # Also map the exact name just in case
            atvk_map[t.name.lower()] = t.code
            
        print(f"Loaded {len(atvk_map)} matching keys from territories.")

        # 2. Load distinct municipalities from address_dimension
        print("Loading distinct municipalities from addresses...")
        muni_names = conn.execute(text("""
            SELECT DISTINCT municipality_name 
            FROM address_dimension 
            WHERE municipality_name IS NOT NULL
        """)).fetchall()
        
        matches = {}
        batch_size = 1000
        
        # Build update map
        for row in muni_names:
            raw_name = row.municipality_name
            norm_name = normalize_name(raw_name)
            
            if norm_name in atvk_map:
                matches[raw_name] = atvk_map[norm_name]
            else:
                # Try simple fuzzy (startswith)
                for k, v in atvk_map.items():
                    if k.startswith(norm_name) or norm_name.startswith(k):
                         matches[raw_name] = v
                         break

        print(f"Mapped {len(matches)} out of {len(muni_names)} distinct municipality names.")
        
        # 3. Perform Updates
        print("Updating companies...")
        
        # We'll use a temporary table to map address_id to atvk to speed up massive update
        conn.execute(text("CREATE TEMP TABLE temp_atvk_map (muni_name text, atvk_code text)"))
        
        # Insert mappings
        if matches:
            values = [{"name": k, "code": v} for k, v in matches.items()]
            conn.execute(text("INSERT INTO temp_atvk_map (muni_name, atvk_code) VALUES (:name, :code)"), values)
            
            # Update query
            # Disable indexes potentially? No, too risky.
            res = conn.execute(text("""
                UPDATE companies c
                SET atvk = t.atvk_code
                FROM address_dimension a -- companies join address on addressid
                JOIN temp_atvk_map t ON a.municipality_name = t.muni_name
                WHERE c.addressid = a.address_id 
                  AND c.atvk IS NULL
            """))
            conn.commit()
            print(f"Updated {res.rowcount} companies with ATVK codes.")
            
        else:
            print("No matches found to update.")

        # 4. Refresh Person Analytics
        print("Refreshing Person Analytics Cache...")
        conn.execute(text("REFRESH MATERIALIZED VIEW person_analytics_cache"))
        conn.commit()
        print("Done.")

if __name__ == "__main__":
    populate_atvk()
