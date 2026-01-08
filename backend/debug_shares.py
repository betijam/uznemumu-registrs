from sqlalchemy import text
from etl.loader import engine

def debug_shares():
    with engine.connect() as conn:
        print("--- Checking Persons Table ---")
        
        # Check distribution of roles
        print("\nRole counts:")
        roles = conn.execute(text("SELECT role, COUNT(*) FROM persons GROUP BY role")).fetchall()
        for r in roles:
            print(f"  {r[0]}: {r[1]}")

        # Check share_percent for members
        print("\nChecking share_percent for role='member':")
        
        total_members = conn.execute(text("SELECT COUNT(*) FROM persons WHERE role = 'member'")).scalar()
        null_shares = conn.execute(text("SELECT COUNT(*) FROM persons WHERE role = 'member' AND share_percent IS NULL")).scalar()
        zero_shares = conn.execute(text("SELECT COUNT(*) FROM persons WHERE role = 'member' AND share_percent = 0")).scalar()
        valid_shares = total_members - null_shares - zero_shares
        
        print(f"  Total Members: {total_members}")
        print(f"  NULL share_percent: {null_shares}")
        print(f"  0.00 share_percent: {zero_shares}")
        print(f"  Valid share_percent (>0): {valid_shares}")
        
        if valid_shares > 0:
            print("\nSample valid shares:")
            sample = conn.execute(text("""
                SELECT person_name, share_percent, company_regcode 
                FROM persons 
                WHERE role = 'member' AND share_percent > 0 
                LIMIT 5
            """)).fetchall()
            for s in sample:
                print(f"  {s.person_name} ({s.company_regcode}): {s.share_percent}%")

        # Check if we rely on number_of_shares instead?
        non_null_nums = conn.execute(text("SELECT COUNT(*) FROM persons WHERE role = 'member' AND number_of_shares IS NOT NULL")).scalar()
        print(f"\n  Members with non-NULL number_of_shares: {non_null_nums}")

if __name__ == "__main__":
    debug_shares()
