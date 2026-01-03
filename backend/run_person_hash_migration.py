"""
Run SQL migration to add person_hash column and index
This script executes the SQL migration file using psycopg2
"""

import os
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def run_migration():
    """
    Execute the SQL migration to add person_hash column and index
    """
    print("Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True  # Required for CREATE INDEX IF NOT EXISTS
    cursor = conn.cursor()
    
    try:
        print("Running migration: add_person_hash.sql")
        
        # Step 1: Add person_hash column if it doesn't exist
        print("  - Adding person_hash column...")
        cursor.execute("ALTER TABLE persons ADD COLUMN IF NOT EXISTS person_hash VARCHAR(8)")
        print("  ✅ Column added (or already exists)")
        
        # Step 2: Create index for fast lookups
        print("  - Creating index idx_person_hash...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_person_hash ON persons(person_hash)")
        print("  ✅ Index created (or already exists)")
        
        # Step 3: Verify the schema
        print("  - Verifying schema...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'persons' AND column_name = 'person_hash'
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"  ✅ Verified: {result[0]} ({result[1]}, nullable: {result[2]})")
        else:
            print("  ⚠️  Column not found - migration may have failed")
        
        print("\n✅ Migration completed successfully!")
        print("\nNext step: Run 'python update_person_hashes.py' to populate the hash values")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    run_migration()
