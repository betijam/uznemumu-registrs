from sqlalchemy import text
from etl.loader import engine
import time

print("Running person_analytics_fixed.sql migration...")
start_time = time.time()

with open("db/person_analytics_fixed.sql", "r", encoding="utf-8") as f:
    sql = f.read()

with engine.connect() as conn:
    print("Executing SQL (this might take a while for large datasets)...")
    conn.execute(text(sql))
    conn.commit()

duration = time.time() - start_time
print(f"✓ Person analytics view updated in {duration:.2f} seconds!")
