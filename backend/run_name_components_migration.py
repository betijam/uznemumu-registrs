#!/usr/bin/env python3
"""
Run the add_company_name_components migration.
This script adds the new columns (name_in_quotes, type, type_text, addressid) to the companies table.
"""
import psycopg2
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def run_migration():
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    print("=" * 60)
    print("Running Company Name Components Migration")
    print("=" * 60)
    
    # Read migration SQL
    migration_file = os.path.join(
        os.path.dirname(__file__), 
        "db", 
        "migrations", 
        "add_company_name_components.sql"
    )
    
    if not os.path.exists(migration_file):
        print(f"❌ ERROR: Migration file not found: {migration_file}")
        sys.exit(1)
    
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    # Connect and run migration
    try:
        print("\n📡 Connecting to database...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("📝 Executing migration SQL...")
        cursor.execute(migration_sql)
        
        conn.commit()
        
        # Verify columns were added
        print("\n✅ Verifying migration...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'companies' 
            AND column_name IN ('name_in_quotes', 'type', 'type_text', 'addressid')
            ORDER BY column_name
        """)
        columns = [row[0] for row in cursor.fetchall()]
        
        if len(columns) == 4:
            print(f"✅ All columns added successfully: {', '.join(columns)}")
        else:
            print(f"⚠️  Warning: Only {len(columns)} columns found: {', '.join(columns)}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()
