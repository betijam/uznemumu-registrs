from app.core.database import engine
from sqlalchemy import text
import time

def check_mat_view():
    print("Checking materialized view...")
    with engine.connect() as conn:
        # Check if view exists
        exists = conn.execute(text("""
            SELECT EXISTS (
               SELECT FROM pg_matviews 
               WHERE matviewname = 'company_stats_materialized'
            );
        """)).scalar()
        print(f"Materialized View Exists: {exists}")
        
        if exists:
            # Profile a sample query
            start = time.time()
            res = conn.execute(text("""
                SELECT c.regcode, c.name, s.turnover 
                FROM companies c
                LEFT JOIN company_stats_materialized s ON s.regcode = c.regcode AND s.year = 2024
                WHERE s.turnover > 100000
                ORDER BY s.turnover DESC
                LIMIT 50
            """)).fetchall()
            print(f"List Query: {time.time() - start:.4f}s (Fetched {len(res)})")

            # Profile Stats Query (The likely bottleneck)
            print("Profiling Stats Query (DEFAULT - No Filters)...")
            start = time.time()
            # This mimics the query when user lands on /explore with no filters
            stats = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_count,
                    SUM(COALESCE(s.turnover, 0)) as total_turnover,
                    SUM(COALESCE(s.profit, 0)) as total_profit,
                    SUM(COALESCE(s.employees, 0)) as total_employees
                FROM companies c
                LEFT JOIN company_stats_materialized s ON s.regcode = c.regcode AND s.year = 2024
                WHERE 1=1
            """)).fetchone()
            print(f"Stats Query (Default): {time.time() - start:.4f}s")

        else:
            print("WARNING: MatView missing! This explains the slowness.")

if __name__ == "__main__":
    check_mat_view()
