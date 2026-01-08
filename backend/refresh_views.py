from sqlalchemy import text
from etl.loader import engine
import time

print("=== Refreshing Materialized Views ===")

views_to_refresh = [
    "location_statistics",
    "company_stats_materialized",
    "person_analytics_cache",
    "industry_stats_materialized"
]

for view in views_to_refresh:
    print(f"Refreshing {view}...", end=" ", flush=True)
    start = time.time()
    
    # Use fresh connection for each view to avoid transaction issues
    with engine.connect() as conn:
        try:
            conn.execute(text(f"REFRESH MATERIALIZED VIEW {view}"))
            conn.commit()
            elapsed = time.time() - start
            print(f"OK ({elapsed:.1f}s)")
        except Exception as e:
            conn.rollback()
            print(f"ERROR: {str(e)[:80]}")

print("\n=== Done ===")
