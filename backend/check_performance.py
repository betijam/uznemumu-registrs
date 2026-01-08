from sqlalchemy import text
from etl.loader import engine

def check_performance():
    with engine.connect() as conn:
        # 1. Check materialized views
        print("=== MATERIALIZED VIEWS ===")
        views = conn.execute(text("""
            SELECT schemaname, matviewname, 
                   pg_size_pretty(pg_total_relation_size(schemaname || '.' || matviewname)) as size
            FROM pg_matviews 
            WHERE schemaname = 'public'
            ORDER BY matviewname
        """)).fetchall()
        
        if not views:
            print("❌ NO MATERIALIZED VIEWS FOUND!")
        else:
            for v in views:
                print(f"  ✓ {v[1]} ({v[2]})")
        
        # 2. Check if views have data
        print("\n=== VIEW ROW COUNTS ===")
        for v in views:
            try:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {v[1]}")).scalar()
                print(f"  {v[1]}: {count:,} rows")
            except Exception as e:
                print(f"  {v[1]}: ERROR - {e}")
        
        # 3. Check indexes
        print("\n=== INDEX COUNT BY TABLE ===")
        indexes = conn.execute(text("""
            SELECT tablename, COUNT(*) as idx_count
            FROM pg_indexes 
            WHERE schemaname = 'public'
            GROUP BY tablename
            ORDER BY tablename
        """)).fetchall()
        
        for idx in indexes:
            print(f"  {idx[0]}: {idx[1]} indexes")
        
        # 4. Check slow query candidates - tables without indexes on commonly filtered columns
        print("\n=== TABLE SIZES ===")
        sizes = conn.execute(text("""
            SELECT relname, 
                   pg_size_pretty(pg_total_relation_size(relid)) as size,
                   n_live_tup as row_count
            FROM pg_stat_user_tables
            ORDER BY pg_total_relation_size(relid) DESC
            LIMIT 10
        """)).fetchall()
        
        for s in sizes:
            print(f"  {s[0]}: {s[1]} ({s[2]:,} rows)")

if __name__ == "__main__":
    check_performance()
