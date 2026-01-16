
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL is not set")
    exit(1)

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Check what location_statistics is
    result = conn.execute(text("""
        SELECT table_type 
        FROM information_schema.tables 
        WHERE table_name = 'location_statistics'
    """)).fetchone()
    
    if result:
        print(f"location_statistics is a: {result[0]}")
    else:
        # Check if it is a materialized view (not in information_schema.tables usually)
        result = conn.execute(text("""
            SELECT relkind 
            FROM pg_class 
            WHERE relname = 'location_statistics'
        """)).fetchone()
        if result:
            kind_map = {'r': 'table', 'v': 'view', 'm': 'materialized view'}
            print(f"location_statistics is a: {kind_map.get(result[0], result[0])}")
        else:
            print("location_statistics NOT FOUND")

    # Check row count
    try:
        count = conn.execute(text("SELECT COUNT(*) FROM location_statistics")).scalar()
        print(f"Row count: {count}")
    except Exception as e:
        print(f"Error counting rows: {e}")

