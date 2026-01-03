
import os
from dotenv import load_dotenv
import psycopg2
from app.routers.person import generate_person_url_id

# Load env
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def check_hash_state():
    print("--- DEBUGGING HASH STATE ---")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Get a person with a hash
    cursor.execute("SELECT person_code, person_name, person_hash FROM persons WHERE person_hash IS NOT NULL LIMIT 1")
    row = cursor.fetchone()
    
    if not row:
        print("No persons with hash found!")
        return

    code, name, db_hash = row
    print(f"Sample Person: {name} (Code: {code})")
    print(f"Stored DB Hash: {db_hash}")
    
    # Calculate Short Code Hash (Current Logic)
    # Using the imported function which has the fix
    short_hash = generate_person_url_id(code, name)
    print(f"Calculated SHORT Hash (Current Code): {short_hash}")
    
    # Calculate Full Code Hash (Old Logic)
    normalized_name = " ".join(sorted(name.lower().split()))
    hash_input_full = f"{code}|{normalized_name}"
    
    hash_val = 0
    for char in hash_input_full:
        hash_val = ((hash_val << 5) - hash_val) + ord(char)
        hash_val = hash_val & 0xFFFFFFFF
    full_hash = format(abs(hash_val) & 0xFFFFFFFF, '08x')[:8]
    
    print(f"Calculated FULL Hash (Old Logic):     {full_hash}")
    
    if db_hash == short_hash:
        print("\n✅ MATCH: Database matches Current Code (Short Hash)")
    elif db_hash == full_hash:
        print("\n❌ MISMATCH: Database matches OLD Logic (Full Hash)")
        print("-> CONCLUSION: Database Update REQUIRED to switch to Short Hash.")
    else:
        print("\n⚠️ MISMATCH: Database matches NEITHER. (Maybe non-normalized?)")
        
        # Check non-normalized
        hash_input_raw = f"{code}|{name}"
        hash_val = 0
        for char in hash_input_raw:
            hash_val = ((hash_val << 5) - hash_val) + ord(char)
            hash_val = hash_val & 0xFFFFFFFF
        raw_hash = format(abs(hash_val) & 0xFFFFFFFF, '08x')[:8]
        print(f"Calculated RAW Hash (No Normalization): {raw_hash}")
        
        if db_hash == raw_hash:
             print("-> CONCLUSION: Database has old RAW hashes.")
    
    conn.close()

if __name__ == "__main__":
    check_hash_state()
