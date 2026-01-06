"""Check and fix NaN values in person_analytics_cache"""
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    # Check for NaN values
    print("=== Checking for NaN values ===")
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN managed_turnover::text = 'NaN' THEN 1 END) as nan_turnover,
            COUNT(CASE WHEN net_worth::text = 'NaN' THEN 1 END) as nan_wealth
        FROM person_analytics_cache
    """))
    row = result.fetchone()
    print(f"Total records: {row.total:,}")
    print(f"NaN turnover: {row.nan_turnover:,}")
    print(f"NaN wealth: {row.nan_wealth:,}")
    
    # Get valid top managers
    print("\n=== Top 5 managers (excluding NaN) ===")
    result = conn.execute(text("""
        SELECT full_name, managed_turnover 
        FROM person_analytics_cache 
        WHERE managed_turnover IS NOT NULL 
          AND managed_turnover::text != 'NaN'
          AND managed_turnover > 0
        ORDER BY managed_turnover DESC 
        LIMIT 5
    """))
    for row in result:
        print(f"  {row.full_name}: €{row.managed_turnover:,.0f}")
    
    # Get valid top by wealth
    print("\n=== Top 5 by wealth (excluding NaN) ===")
    result = conn.execute(text("""
        SELECT full_name, net_worth 
        FROM person_analytics_cache 
        WHERE net_worth IS NOT NULL 
          AND net_worth::text != 'NaN'
          AND net_worth > 0
        ORDER BY net_worth DESC 
        LIMIT 5
    """))
    for row in result:
        print(f"  {row.full_name}: €{row.net_worth:,.0f}")
