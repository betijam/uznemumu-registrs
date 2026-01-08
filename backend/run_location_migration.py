from sqlalchemy import text
from etl.loader import engine

print("Running location_stats.sql migration...")

with open("db/location_stats.sql", "r", encoding="utf-8") as f:
    sql = f.read()

with engine.connect() as conn:
    conn.execute(text(sql))
    conn.commit()

print("✓ Location statistics view updated!")
