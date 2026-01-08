from app.core.database import engine
from sqlalchemy import text

def check_indexes():
    print("Checking indexes on company_stats_materialized...")
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'company_stats_materialized'")).fetchall()
        if not rows:
            print("NO INDEXES FOUND on company_stats_materialized!")
        else:
            for row in rows:
                print(f"- {row.indexname}: {row.indexdef}")

if __name__ == "__main__":
    check_indexes()
