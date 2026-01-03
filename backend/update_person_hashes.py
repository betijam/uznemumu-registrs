"""
Update person_hash column with computed hash values
This script computes hash once per unique person_code+person_name combination
and updates all matching rows in batch for maximum speed
"""

import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def compute_hash(person_code: str, person_name: str) -> str:
    """
    Compute hash for a person (matching frontend/backend logic)
    """
    hash_input = f"{person_code}|{person_name}"
    
    hash_val = 0
    for char in hash_input:
        hash_val = ((hash_val << 5) - hash_val) + ord(char)
        hash_val = hash_val & 0xFFFFFFFF  # 32-bit integer
    
    # Convert to hex (8 characters)
    hash_hex = format(abs(hash_val) & 0xFFFFFFFF, '08x')[:8]
    return hash_hex


def update_person_hashes():
    """
    Update all person_hash values in the database using batch operations
    """
    print("Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    try:
        # Get count of persons without hash
        cursor.execute("SELECT COUNT(*) FROM persons WHERE person_hash IS NULL")
        null_count = cursor.fetchone()[0]
        print(f"Found {null_count} persons without hash")
        
        if null_count == 0:
            print("✅ All persons already have hashes!")
            return
        
        # Get DISTINCT person_code + person_name combinations (to avoid duplicate hash computation)
        print("Fetching unique person combinations...")
        cursor.execute("""
            SELECT DISTINCT person_code, person_name 
            FROM persons 
            WHERE person_hash IS NULL
        """)
        
        unique_persons = cursor.fetchall()
        print(f"Found {len(unique_persons)} unique person combinations to process")
        
        # Compute hashes for all unique combinations
        print("Computing hashes...")
        hash_map = {}
        for person_code, person_name in unique_persons:
            hash_val = compute_hash(person_code, person_name)
            hash_map[(person_code, person_name)] = hash_val
        
        print(f"Computed {len(hash_map)} unique hashes")
        
        # Batch update using a single UPDATE with VALUES
        print("Updating database in batch...")
        
        # Use PostgreSQL's UPDATE FROM with VALUES for maximum performance
        values = [(hash_val, pc, pn) for (pc, pn), hash_val in hash_map.items()]
        
        cursor.execute("""
            CREATE TEMP TABLE temp_person_hashes (
                person_hash VARCHAR(8),
                person_code VARCHAR(20),
                person_name VARCHAR(255)
            ) ON COMMIT DROP
        """)
        
        # Bulk insert into temp table
        execute_values(
            cursor,
            "INSERT INTO temp_person_hashes (person_hash, person_code, person_name) VALUES %s",
            values,
            page_size=1000
        )
        
        # Batch update using JOIN
        cursor.execute("""
            UPDATE persons p
            SET person_hash = t.person_hash
            FROM temp_person_hashes t
            WHERE p.person_code = t.person_code 
              AND p.person_name = t.person_name
              AND p.person_hash IS NULL
        """)
        
        updated_count = cursor.rowcount
        conn.commit()
        
        print(f"✅ Successfully updated {updated_count} person records!")
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM persons WHERE person_hash IS NULL")
        remaining = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT person_hash) FROM persons WHERE person_hash IS NOT NULL")
        unique_hashes = cursor.fetchone()[0]
        
        print(f"Remaining persons without hash: {remaining}")
        print(f"Total unique hashes in database: {unique_hashes}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    update_person_hashes()
