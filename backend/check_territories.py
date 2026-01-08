from sqlalchemy import text
from etl.loader import engine

def check_territories():
    with engine.connect() as conn:
        print("--- Checking Territories Table ---")
        count = conn.execute(text("SELECT COUNT(*) FROM territories")).scalar()
        print(f"Total territories: {count}")
        
        if count > 0:
            print("\nSample Territories:")
            rows = conn.execute(text("SELECT code, name, type, level, parent_code FROM territories LIMIT 10")).fetchall()
            for r in rows:
                print(f"  {r.code} | {r.name} | {r.type} | Level {r.level} | Parent {r.parent_code}")
                
            print("\nChecking for 'Līvānu nov.':")
            livani = conn.execute(text("SELECT * FROM territories WHERE name ILIKE '%Līvānu%'")).fetchall()
            for l in livani:
                print(f"  Found: {l.name} (Code: {l.code}, Type: {l.type})")
        else:
             print("Territories table is EMPTY.")

if __name__ == "__main__":
    check_territories()
