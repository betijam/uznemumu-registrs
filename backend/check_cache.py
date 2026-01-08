from sqlalchemy import text
from etl.loader import engine

def check_cache():
    with engine.connect() as conn:
        # Check dashboard_cache
        print("=== DASHBOARD CACHE ===")
        cache = conn.execute(text("SELECT key, pg_column_size(data) as size_bytes, updated_at FROM dashboard_cache")).fetchall()
        
        if not cache:
            print("❌ dashboard_cache IS EMPTY!")
            print("   Run: python backend/etl/refresh_dashboard_cache.py")
        else:
            for c in cache:
                print(f"  ✓ {c[0]}: {c[1]} bytes, updated: {c[2]}")
        
        # Check industry_stats_materialized
        print("\n=== INDUSTRY STATS ===")
        ind_count = conn.execute(text("SELECT COUNT(*) FROM industry_stats_materialized")).scalar()
        print(f"  industry_stats_materialized: {ind_count} rows")
        
        # Check if matviews are stale
        print("\n=== MATERIALIZED VIEW REFRESH DATES ===")
        # PostgreSQL doesn't track this by default, but we can check if they have recent data
        sample = conn.execute(text("""
            SELECT 'company_stats_materialized' as view_name, MAX(fr_year) as latest_year 
            FROM company_stats_materialized
        """)).fetchone()
        print(f"  company_stats_materialized: latest year = {sample[1] if sample else 'N/A'}")

if __name__ == "__main__":
    check_cache()
