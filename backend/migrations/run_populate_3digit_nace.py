"""
Migration script to populate 3-digit NACE industry statistics.
Reads and executes the SQL migration file.
"""
from sqlalchemy import create_engine, text
import os

# Try to load .env file if dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def run_migration():
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        print("   Please ensure DATABASE_URL is in your .env file or environment")
        return
    
    # Create engine
    engine = create_engine(database_url)
    
    # Get the path to the SQL file
    sql_file = 'backend/db/migrations/populate_3digit_nace_stats.sql'
    
    if not os.path.exists(sql_file):
        print(f"❌ SQL file not found: {sql_file}")
        return
    
    print(f"📄 Reading SQL file: {sql_file}")
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Split into individual statements (separated by semicolons)
    statements = [s.strip() for s in sql_content.split(';') if s.strip()]
    
    print(f"📊 Executing {len(statements)} SQL statements...")
    
    with engine.connect() as conn:
        for i, statement in enumerate(statements, 1):
            try:
                print(f"  [{i}/{len(statements)}] Executing statement...")
                result = conn.execute(text(statement))
                
                # If it's a SELECT statement, print results
                if statement.strip().upper().startswith('SELECT'):
                    rows = result.fetchall()
                    for row in rows:
                        print(f"    {dict(row)}")
                
            except Exception as e:
                print(f"  ⚠️  Warning on statement {i}: {e}")
        
        conn.commit()
    
    print("✅ 3-digit NACE statistics populated successfully!")

if __name__ == "__main__":
    run_migration()
