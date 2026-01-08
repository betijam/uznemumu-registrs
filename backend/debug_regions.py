from sqlalchemy import text
from etl.loader import engine

def debug_regions():
    with engine.connect() as conn:
        print("--- Region Data Check ---")
        
        # 1. Check companies ATVK coverage
        total_companies = conn.execute(text("SELECT COUNT(*) FROM companies")).scalar()
        companies_with_atvk = conn.execute(text("SELECT COUNT(*) FROM companies WHERE atvk IS NOT NULL")).scalar()
        print(f"Total Companies: {total_companies}")
        print(f"Companies with ATVK: {companies_with_atvk} ({(companies_with_atvk/total_companies)*100:.1f}%)")

        # 2. Check Person Analytics Region coverage
        total_persons = conn.execute(text("SELECT COUNT(*) FROM person_analytics_cache")).scalar()
        persons_with_region = conn.execute(text("SELECT COUNT(*) FROM person_analytics_cache WHERE main_region IS NOT NULL")).scalar()
        print(f"Total Persons in Analytics: {total_persons}")
        print(f"Persons with Region: {persons_with_region} ({(persons_with_region/total_persons)*100:.1f}%)")

        # 3. Sample
        if persons_with_region > 0:
            print("\nSample Regions:")
            rows = conn.execute(text("SELECT DISTINCT main_region FROM person_analytics_cache LIMIT 10")).fetchall()
            for r in rows:
                print(f" - {r[0]}")

if __name__ == "__main__":
    debug_regions()
