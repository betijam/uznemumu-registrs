from sqlalchemy import text
from etl.loader import engine

def check_address_dim():
    with engine.connect() as conn:
        print("--- Checking Address Dimension ---")
        
        # Check count
        count = conn.execute(text("SELECT COUNT(*) FROM address_dimension")).scalar()
        print(f"Total addresses in dimension: {count}")
        
        # Check sample
        if count > 0:
            print("\nSample Address Dimension entry:")
            row = conn.execute(text("SELECT * FROM address_dimension LIMIT 1")).fetchone()
            print(f"AddressID: {row.address_id}")
            print(f"City: {row.city_name} (Code: {row.city_code})")
            print(f"Muni: {row.municipality_name} (Code: {row.municipality_code})")
            
            # Check join with territories
            if row.municipality_code:
                print("\nChecking Territory Join:")
                terr = conn.execute(text("""
                    SELECT t.name, t.level, p.name as parent_name 
                    FROM territories t 
                    LEFT JOIN territories p ON t.parent_code = p.code
                    WHERE t.code = :code
                """), {"code": row.municipality_code}).fetchone()
                
                if terr:
                    print(f"Found Territory: {terr.name} (Level {terr.level})")
                    print(f"Parent Region: {terr.parent_name}")
                else:
                    print("Territory NOT FOUND for this code.")

if __name__ == "__main__":
    check_address_dim()
