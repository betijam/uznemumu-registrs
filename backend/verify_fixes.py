import requests
import json
from collections import Counter

BASE_URL = "http://localhost:8000/api"

def verify_fixes():
    print("=== Verifying Fixes ===\n")

    # 1. Test Municipalities (Was 500 Error)
    print("1. Testing /locations/municipalities...")
    try:
        r = requests.get(f"{BASE_URL}/locations/municipalities?limit=5")
        if r.status_code == 200:
            data = r.json()
            print(f"   ✅ Status 200 OK")
            print(f"   ✅ Retrieved {len(data)} items")
            if data and 'avg_salary' in data[0]:
                print(f"   ✅ 'avg_salary' field present in response")
            else:
                print(f"   ❌ 'avg_salary' field MISSING")
        else:
            print(f"   ❌ Failed: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")

    print("\n" + "-"*30 + "\n")

    # 2. Test Cities for Duplicates
    print("2. Testing /locations/cities for duplicates...")
    try:
        r = requests.get(f"{BASE_URL}/locations/cities?limit=100")
        if r.status_code == 200:
            data = r.json()
            names = [item['name'] for item in data]
            counts = Counter(names)
            duplicates = [n for n, c in counts.items() if c > 1]
            
            if not duplicates:
                print(f"   ✅ No duplicate cities found (Total: {len(names)})")
            else:
                print(f"   ❌ Duplicates found: {duplicates}")
        else:
            print(f"   ❌ Failed: {r.status_code}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")

if __name__ == "__main__":
    verify_fixes()
