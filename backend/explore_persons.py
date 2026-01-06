"""Explore database schema for persons analytics"""
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    # Get persons columns
    print("=== PERSONS TABLE ===")
    result = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name='persons' 
        ORDER BY ordinal_position
    """))
    for row in result:
        print(f"  {row[0]}: {row[1]}")
    
    # Sample persons data
    print("\n=== SAMPLE PERSONS ===")
    result = conn.execute(text("SELECT * FROM persons LIMIT 3"))
    for row in result:
        print(row)
    
    # Get financial_reports columns
    print("\n=== FINANCIAL_REPORTS TABLE ===")
    result = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name='financial_reports' 
        ORDER BY ordinal_position
    """))
    for row in result:
        print(f"  {row[0]}: {row[1]}")
    
    # Count persons
    print("\n=== COUNTS ===")
    result = conn.execute(text("SELECT COUNT(*) FROM persons"))
    print(f"Total persons records: {result.scalar():,}")
    
    # Check roles
    print("\n=== ROLES ===")
    result = conn.execute(text("""
        SELECT role, COUNT(*) as cnt 
        FROM persons 
        GROUP BY role 
        ORDER BY cnt DESC 
        LIMIT 10
    """))
    for row in result:
        print(f"  {row[0]}: {row[1]:,}")
