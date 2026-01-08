from sqlalchemy import text
from etl.loader import engine

def debug_regions_data():
    with engine.connect() as conn:
        print("--- Person Analytics Region Data ---")
        
        # 1. Check distinct regions
        regions = conn.execute(text("""
            SELECT main_region, COUNT(*) 
            FROM person_analytics_cache 
            WHERE main_region IS NOT NULL 
            GROUP BY main_region 
            ORDER BY COUNT(*) DESC 
            LIMIT 10
        """)).fetchall()
        
        print(f"Distinct Regions found: {len(regions)}")
        for r in regions:
            print(f" - {r[0]}: {r[1]}")
            
        if not regions:
             print("WARNING: No regions found in person_analytics_cache!")
             
             # Check source join
             print("\nChecking source data join sample:")
             sample = conn.execute(text("""
                SELECT c.regcode, ad.municipality_name, ad.city_name
                FROM companies c
                LEFT JOIN address_dimension ad ON c.addressid = ad.address_id
                LIMIT 5
             """)).fetchall()
             for s in sample:
                 print(f"Company {s.regcode}: Muni='{s.municipality_name}', City='{s.city_name}'")

if __name__ == "__main__":
    debug_regions_data()
